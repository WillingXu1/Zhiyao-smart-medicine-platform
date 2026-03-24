#!/usr/bin/env python3
import argparse
import json
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class ProxyHandler(BaseHTTPRequestHandler):
    upstream = "http://127.0.0.1:8001"

    def _proxy(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length > 0 else None

        target_url = f"{self.upstream}{self.path}"
        req = urllib.request.Request(target_url, data=body, method=self.command)

        for k, v in self.headers.items():
            lk = k.lower()
            if lk in {"host", "content-length", "connection", "accept-encoding"}:
                continue
            req.add_header(k, v)

        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = resp.read()
                self.send_response(resp.status)
                # Force UTF-8 charset for JSON to avoid PowerShell mojibake.
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            payload = json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    def do_GET(self):
        self._proxy()

    def do_POST(self):
        self._proxy()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()

    def log_message(self, fmt, *args):
        return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen-host", default="0.0.0.0")
    parser.add_argument("--listen-port", type=int, default=8002)
    parser.add_argument("--upstream", default="http://127.0.0.1:8001")
    args = parser.parse_args()

    ProxyHandler.upstream = args.upstream.rstrip("/")
    server = ThreadingHTTPServer((args.listen_host, args.listen_port), ProxyHandler)
    print(f"UTF-8 proxy listening on {args.listen_host}:{args.listen_port}, upstream={ProxyHandler.upstream}")
    server.serve_forever()


if __name__ == "__main__":
    main()
