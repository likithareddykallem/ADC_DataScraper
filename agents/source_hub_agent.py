import os

import requests
from bs4 import BeautifulSoup

from config import HTTP_TIMEOUT_SECONDS, MAX_PAPERS_PER_SOURCE


class SourceHubAgent:
    def __init__(self):
        self.core_api_key = os.getenv("CORE_API_KEY", "").strip()
        self.ieee_api_key = os.getenv("IEEE_API_KEY", "").strip()

    def search(self, query, sources, max_per_source=MAX_PAPERS_PER_SOURCE):
        papers = []
        for source in sources:
            source = self._normalize_source(source)
            try:
                if source == "pubmed":
                    papers.extend(self._search_pubmed(query, max_per_source))
                elif source == "arxiv":
                    papers.extend(self._search_arxiv(query, max_per_source))
                elif source == "biorxiv":
                    papers.extend(self._search_europepmc_preprints(query, "bioRxiv", "biorxiv", max_per_source))
                elif source == "medrxiv":
                    papers.extend(self._search_europepmc_preprints(query, "medRxiv", "medrxiv", max_per_source))
                elif source == "pubmed_central":
                    papers.extend(self._search_pubmed_central(query, max_per_source))
                elif source == "semantic_scholar":
                    papers.extend(self._search_semantic_scholar(query, max_per_source))
                elif source == "core":
                    papers.extend(self._search_core(query, max_per_source))
                elif source == "ieee_xplore":
                    papers.extend(self._search_ieee(query, max_per_source))
                elif source == "acm_digital_library":
                    papers.extend(self._site_search(query, "dl.acm.org", "acm_digital_library", max_per_source))
                elif source == "sciencedirect":
                    papers.extend(self._site_search(query, "www.sciencedirect.com", "sciencedirect", max_per_source))
                elif source == "drugbank":
                    papers.extend(self._site_search(query, "go.drugbank.com", "drugbank", max_per_source))
            except Exception:
                continue
        return self._dedupe_papers(papers)

    def _search_pubmed(self, query, max_results):
        esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {"db": "pubmed", "term": query, "retmode": "json", "retmax": max_results}
        response = requests.get(esearch_url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
        idlist = response.json().get("esearchresult", {}).get("idlist", [])

        out = []
        for pmid in idlist:
            efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            params = {"db": "pubmed", "id": pmid, "retmode": "xml"}
            r = requests.get(efetch_url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml-xml")
            title_tag = soup.find("ArticleTitle")
            abstract_tags = soup.find_all("AbstractText")
            title = title_tag.text if title_tag else ""
            abstract = " ".join(a.text for a in abstract_tags) if abstract_tags else ""
            out.append(
                {
                    "id": pmid,
                    "title": title,
                    "abstract": abstract,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "pdf_url": "",
                    "source": "pubmed",
                }
            )
        return out

    def _search_arxiv(self, query, max_results):
        url = "https://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        response = requests.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "xml")

        out = []
        for entry in soup.find_all("entry"):
            title = (entry.find("title").text or "").strip() if entry.find("title") else ""
            abstract = (entry.find("summary").text or "").strip() if entry.find("summary") else ""
            link = (entry.find("id").text or "").strip() if entry.find("id") else ""
            pdf_url = ""
            for entry_link in entry.find_all("link"):
                href = (entry_link.get("href") or "").strip()
                title_attr = (entry_link.get("title") or "").strip().lower()
                if "pdf" in title_attr or href.endswith(".pdf"):
                    pdf_url = href
                    break
            out.append(
                {
                    "id": link or title,
                    "title": title,
                    "abstract": abstract,
                    "url": link,
                    "pdf_url": pdf_url,
                    "source": "arxiv",
                }
            )
        return out

    def _search_europepmc_preprints(self, query, publisher, source_name, max_results):
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        params = {
            "query": f'(SRC:PPR AND PUBLISHER:"{publisher}") AND ({query})',
            "format": "json",
            "pageSize": max_results,
            "resultType": "core",
        }
        response = requests.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
        results = response.json().get("resultList", {}).get("result", [])

        out = []
        for r in results:
            title = (r.get("title") or "").strip()
            abstract = (r.get("abstractText") or "").strip()
            doi = (r.get("doi") or "").strip()
            out.append(
                {
                    "id": doi or title,
                    "title": title,
                    "abstract": abstract,
                    "url": f"https://doi.org/{doi}" if doi else "",
                    "pdf_url": "",
                    "source": source_name,
                }
            )
        return out

    def _search_pubmed_central(self, query, max_results):
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        params = {
            "query": f"(SRC:PMC) AND ({query})",
            "format": "json",
            "pageSize": max_results,
            "resultType": "core",
        }
        response = requests.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
        results = response.json().get("resultList", {}).get("result", [])

        out = []
        for r in results:
            pmcid = (r.get("pmcid") or "").strip()
            title = (r.get("title") or "").strip()
            abstract = (r.get("abstractText") or "").strip()
            out.append(
                {
                    "id": pmcid or title,
                    "title": title,
                    "abstract": abstract,
                    "url": f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/" if pmcid else "",
                    "pdf_url": f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/" if pmcid else "",
                    "source": "pubmed_central",
                }
            )
        return out

    def _search_semantic_scholar(self, query, max_results):
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {"query": query, "limit": max_results, "fields": "title,abstract,year,url,paperId,openAccessPdf"}
        response = requests.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
        results = response.json().get("data", [])

        out = []
        for r in results:
            out.append(
                {
                    "id": (r.get("paperId") or r.get("url") or r.get("title") or "").strip(),
                    "title": (r.get("title") or "").strip(),
                    "abstract": (r.get("abstract") or "").strip(),
                    "url": (r.get("url") or "").strip(),
                    "pdf_url": ((r.get("openAccessPdf") or {}).get("url") or "").strip(),
                    "source": "semantic_scholar",
                }
            )
        return out

    def _search_core(self, query, max_results):
        if self.core_api_key:
            url = "https://api.core.ac.uk/v3/search/works"
            headers = {"Authorization": f"Bearer {self.core_api_key}"}
            params = {"q": query, "limit": max_results}
            response = requests.get(url, headers=headers, params=params, timeout=HTTP_TIMEOUT_SECONDS)
            response.raise_for_status()
            results = response.json().get("results", [])
            out = []
            for r in results:
                title = (r.get("title") or "").strip()
                abstract = (r.get("abstract") or "").strip()
                url_value = (r.get("downloadUrl") or r.get("url") or "").strip()
                out.append(
                    {
                        "id": url_value or title,
                        "title": title,
                        "abstract": abstract,
                        "url": (r.get("url") or url_value or "").strip(),
                        "pdf_url": (r.get("downloadUrl") or "").strip(),
                        "source": "core",
                    }
                )
            return out
        return self._site_search(query, "core.ac.uk", "core", max_results)

    def _search_ieee(self, query, max_results):
        if self.ieee_api_key:
            url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
            params = {"apikey": self.ieee_api_key, "querytext": query, "max_records": max_results}
            response = requests.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
            response.raise_for_status()
            results = response.json().get("articles", [])
            out = []
            for r in results:
                title = (r.get("title") or "").strip()
                abstract = (r.get("abstract") or "").strip()
                url_value = (r.get("html_url") or r.get("pdf_url") or "").strip()
                out.append(
                    {
                        "id": url_value or title,
                        "title": title,
                        "abstract": abstract,
                        "url": (r.get("html_url") or url_value or "").strip(),
                        "pdf_url": (r.get("pdf_url") or "").strip(),
                        "source": "ieee_xplore",
                    }
                )
            return out
        return self._site_search(query, "ieeexplore.ieee.org", "ieee_xplore", max_results)

    def _site_search(self, query, domain, source_name, max_results):
        url = "https://duckduckgo.com/html/"
        params = {"q": f"site:{domain} {query}"}
        response = requests.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items = []
        for a in soup.select("a.result__a"):
            href = (a.get("href") or "").strip()
            title = (a.get_text(" ", strip=True) or "").strip()
            if not href or not title:
                continue
            abstract = ""
            result = a.find_parent(class_="result")
            if result:
                snippet = result.select_one(".result__snippet")
                if snippet:
                    abstract = snippet.get_text(" ", strip=True)
            items.append(
                {
                    "id": href,
                    "title": title,
                    "abstract": abstract,
                    "url": href,
                    "pdf_url": href if href.lower().endswith(".pdf") else "",
                    "source": source_name,
                }
            )
            if len(items) >= max_results:
                break
        return items

    def _normalize_source(self, source):
        s = str(source).strip().lower().replace(" ", "_")
        aliases = {
            "medriv": "medrxiv",
            "medrxiv": "medrxiv",
            "pubmedcentral": "pubmed_central",
            "pmc": "pubmed_central",
            "semantic_scholar": "semantic_scholar",
            "semanticscholar": "semantic_scholar",
            "ieee": "ieee_xplore",
            "ieee_xplore": "ieee_xplore",
            "acm": "acm_digital_library",
            "acm_digital_library": "acm_digital_library",
        }
        return aliases.get(s, s)

    def _dedupe_papers(self, papers):
        seen = set()
        out = []
        for p in papers:
            key = ((p.get("title") or "").strip().lower(), (p.get("url") or "").strip().lower())
            if key in seen:
                continue
            seen.add(key)
            out.append(p)
        return out
