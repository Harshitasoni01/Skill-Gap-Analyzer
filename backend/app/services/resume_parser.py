import io

import docx

try:
    import pymupdf as fitz  # newer PyMuPDF versions
except ImportError:  # older versions only provide the 'fitz' name
    import fitz


def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    pdf = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        for page in pdf:
            text += page.get_text()
    finally:
        pdf.close()
    return text.strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    # python-docx expects a file, so BytesIO wraps the raw bytes to look like one.
    document = docx.Document(io.BytesIO(file_bytes))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    return text.strip()


def extract_text_from_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="ignore").strip()


def extract_text(filename: str, file_bytes: bytes) -> str:
    """Pick the right extractor from the file extension."""
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    if name.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    if name.endswith(".txt"):
        return extract_text_from_txt(file_bytes)
    raise ValueError(f"Unsupported file type: {filename}. Use PDF, DOCX or TXT.")
