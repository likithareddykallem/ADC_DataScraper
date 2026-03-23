import requests
from bs4 import BeautifulSoup

from retrieval.http_utils import get
from retrieval.pdf_processor import extract_pdf_text


def fetch_text_for_paper(paper, max_chars=12000):
    pdf_url = (paper.get("pdf_url") or "").strip()
    url = (paper.get("url") or "").strip()
    if pdf_url:
        try:
            return extract_pdf_text(pdf_url, max_chars=max_chars)
        except Exception:
            pass
    if url.endswith(".pdf"):
        try:
            return extract_pdf_text(url, max_chars=max_chars)
        except Exception:
            pass
    if url:
        try:
            response = get(url)
            pdf_candidate = _discover_pdf_url(url, response.text)
            if pdf_candidate:
                try:
                    return extract_pdf_text(pdf_candidate, max_chars=max_chars)
                except Exception:
                    pass
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(" ", strip=True)
            if text:
                return text[:max_chars]
        except Exception:
            pass
    return f"{paper.get('title') or ''}\n\n{paper.get('abstract') or ''}".strip()[:max_chars]


def _discover_pdf_url(base_url, html):
    soup = BeautifulSoup(html or "", "html.parser")
    meta = soup.find("meta", attrs={"name": "citation_pdf_url"})
    if meta and meta.get("content"):
        return meta.get("content").strip()
    for link in soup.find_all("a", href=True):
        href = (link.get("href") or "").strip()
        if not href:
            continue
        if ".pdf" in href.lower():
            return requests.compat.urljoin(base_url, href)
    return ""
