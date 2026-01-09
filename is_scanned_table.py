from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, List

import fitz  # PyMuPDF
import pytesseract
from PIL import Image


@dataclass
class OCRTableScanResult:
    page_number: int
    bbox: Tuple[float, float, float, float]
    pdf_text_chars: int
    ocr_text_chars: int
    scanned: bool
    confidence: float


def detect_scanned_table_by_ocr(
    pdf_path: str,
    page_number: int,
    bbox: Tuple[float, float, float, float],
    *,
    ocr_min_ratio: float = 5.0,
    min_ocr_chars: int = 50,
    dpi: int = 300,
) -> OCRTableScanResult:
    """
    Determine if a table region is scanned using OCR vs PDF-text comparison.

    scanned = OCR text >> PDF text
    """
    doc = fitz.open(pdf_path)
    page = doc[page_number]
    rect = fitz.Rect(bbox)

    # 1. Extract PDF text
    pdf_text = page.get_text("text", clip=rect)
    pdf_chars = len(pdf_text.strip())

    # 2. Render region to image
    pix = page.get_pixmap(clip=rect, dpi=dpi)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # 3. OCR
    ocr_text = pytesseract.image_to_string(img)
    ocr_chars = len(ocr_text.strip())

    # 4. Decide
    ratio = (ocr_chars / max(1, pdf_chars))
    scanned = ocr_chars >= min_ocr_chars and ratio >= ocr_min_ratio

    confidence = min(1.0, ratio / (ocr_min_ratio * 2))

    return OCRTableScanResult(
        page_number=page_number,
        bbox=bbox,
        pdf_text_chars=pdf_chars,
        ocr_text_chars=ocr_chars,
        scanned=scanned,
        confidence=confidence,
    )
