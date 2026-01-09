import fitz  # PyMuPDF


def is_pdf_scanned(
    path: str,
    *,
    min_text_chars: int = 20,
    require_images: bool = True,
) -> bool:
    """
    Heuristically determine whether a PDF is scanned (image-based).

    Args:
        path: Path to PDF file
        min_text_chars: Minimum extracted characters to consider it text-based
        require_images: If True, scanned PDFs must contain images

    Returns:
        True if PDF is likely scanned, False otherwise
    """
    doc = fitz.open(path)

    total_text_chars = 0
    has_images = False

    for page in doc:
        text = page.get_text("text")
        total_text_chars += len(text.strip())

        if not has_images:
            images = page.get_images(full=True)
            if images:
                has_images = True

    if total_text_chars >= min_text_chars:
        return False

    if require_images:
        return has_images

    return True
