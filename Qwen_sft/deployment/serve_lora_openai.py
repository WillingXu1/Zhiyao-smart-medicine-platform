#!/usr/bin/env python3
import argparse
import asyncio
import time
import uuid
from typing import Any

import torch
from fastapi import FastAPI, HTTPException
from peft import PeftModel
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    max_tokens: int | None = 64
    temperature: float | None = 0.0


class LoRAChatServer:
    def __init__(
        self,
        base_model: str,
        adapter: str,
        model_name: str,
        max_new_tokens_default: int,
        max_concurrent_generations: int,
        enable_cuda_graph: bool,
    ) -> None:
        self.base_model = base_model
        self.adapter = adapter
        self.model_name = model_name
        self.max_new_tokens_default = max_new_tokens_default
        self.max_concurrent_generations = max_concurrent_generations
        self.enable_cuda_graph = enable_cuda_graph

        self.tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        base = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )
        self.model = PeftModel.from_pretrained(base, adapter)
        self.model.eval()

        # Use torch.compile in reduce-overhead mode to enable CUDA-graph-friendly execution.
        if self.enable_cuda_graph and torch.cuda.is_available():
            try:
                self.model = torch.compile(self.model, mode="reduce-overhead")
            except Exception as exc:
                print(f"[WARN] torch.compile disabled due to: {exc}")

        self.lock = asyncio.Semaphore(max_concurrent_generations)

    def _build_prompt(self, messages: list[dict[str, str]]) -> str:
        filtered = []
        for m in messages:
            role = m.get("role", "")
            if role in {"system", "user", "assistant"}:
                filtered.append({"role": role, "content": m.get("content", "")})
        return self.tokenizer.apply_chat_template(
            filtered,
            tokenize=False,
            add_generation_prompt=True,
        )

    def _generate(self, prompt: str, max_new_tokens: int) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                temperature=0.0,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        gen_ids = out[0][inputs["input_ids"].shape[1] :]
        return self.tokenizer.decode(gen_ids, skip_special_tokens=True).strip()


def create_app(server: LoRAChatServer) -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "model": server.model_name}

    @app.get("/v1/models")
    async def models() -> dict[str, Any]:
        return {
            "object": "list",
            "data": [
                {
                    "id": server.model_name,
                    "object": "model",
                    "owned_by": "local",
                }
            ],
        }

    @app.post("/v1/chat/completions")
    async def chat(req: ChatRequest) -> dict[str, Any]:
        if not req.messages:
            raise HTTPException(status_code=400, detail="messages is required")

        max_new_tokens = req.max_tokens or server.max_new_tokens_default
        prompt = server._build_prompt([m.model_dump() for m in req.messages])

        started = time.time()
        async with server.lock:
            try:
                text = await asyncio.to_thread(server._generate, prompt, max_new_tokens)
            except Exception as exc:
                raise HTTPException(status_code=500, detail=str(exc))

        latency = time.time() - started
        now = int(time.time())
        prompt_tokens = len(server.tokenizer(prompt, add_special_tokens=False)["input_ids"])
        completion_tokens = len(server.tokenizer(text, add_special_tokens=False)["input_ids"])

        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
            "object": "chat.completion",
            "created": now,
            "model": server.model_name,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            "server_metrics": {
                "latency_sec": latency,
            },
        }

    return app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--max-new-tokens-default", type=int, default=384)
    parser.add_argument("--max-concurrent-generations", type=int, default=1)
    parser.add_argument("--enable-cuda-graph", type=lambda x: x.lower() in {"1", "true", "yes", "y"}, default=True)
    args = parser.parse_args()

    server = LoRAChatServer(
        base_model=args.base_model,
        adapter=args.adapter,
        model_name=args.model_name,
        max_new_tokens_default=args.max_new_tokens_default,
        max_concurrent_generations=args.max_concurrent_generations,
        enable_cuda_graph=args.enable_cuda_graph,
    )
    app = create_app(server)

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
