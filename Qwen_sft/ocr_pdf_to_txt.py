#!/usr/bin/env python3
import argparse
import os
import tempfile

import pypdfium2 as pdfium
from rapidocr_onnxruntime import RapidOCR


def ocr_pdf_to_txt(pdf_path: str, out_dir: str, scale: float = 2.0, max_pages: int | None = None) -> str:
    os.makedirs(out_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    out_txt = os.path.join(out_dir, f"{base_name}.txt")

    doc = pdfium.PdfDocument(pdf_path)
    ocr_engine = RapidOCR()
    total_pages = len(doc)
    pages_to_process = total_pages if max_pages is None else min(total_pages, max_pages)

    with tempfile.TemporaryDirectory(prefix="pdf_ocr_") as tmp_dir:
        with open(out_txt, "w", encoding="utf-8") as f:
            for i in range(pages_to_process):
                page = doc[i]
                image = page.render(scale=scale).to_pil()
                img_path = os.path.join(tmp_dir, f"page_{i + 1:04d}.png")
                image.save(img_path)

                result, _ = ocr_engine(img_path)
                lines = []
                if result:
                    for row in result:
                        if isinstance(row, (list, tuple)) and len(row) >= 2:
                            txt = row[1]
                            if isinstance(txt, str) and txt.strip():
                                lines.append(txt.strip())

                page_text = "\n".join(lines)
                f.write(f"=== Page {i + 1} ===\n{page_text}\n\n")
                f.flush()
                print(f"Processed page {i + 1}/{pages_to_process}", flush=True)

                page.close()

    doc.close()

    return out_txt


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR scanned PDF to TXT")
    parser.add_argument("--pdf", required=True, help="Path to input PDF")
    parser.add_argument("--out-dir", required=True, help="Directory for output TXT")
    parser.add_argument("--scale", type=float, default=2.0, help="Render scale for OCR quality")
    parser.add_argument("--max-pages", type=int, default=None, help="Optional limit of pages to process")
    args = parser.parse_args()

    out_txt = ocr_pdf_to_txt(args.pdf, args.out_dir, args.scale, args.max_pages)
    print(out_txt)


if __name__ == "__main__":
    main()