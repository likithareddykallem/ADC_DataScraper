from io import BytesIO

try:
    import fitz
except Exception:  # pragma: no cover
    fitz = None

from retrieval.http_utils import get


def extract_pdf_text(pdf_url, max_chars=12000):
    if fitz is None:
        return ""
    response = get(pdf_url)
    doc = fitz.open(stream=BytesIO(response.content), filetype="pdf")
    chunks = []
    for page in doc:
        chunks.append(page.get_text("text"))
        if sum(len(chunk) for chunk in chunks) >= max_chars:
            break
    return "\n".join(chunks)[:max_chars]
