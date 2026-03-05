import requests
from bs4 import BeautifulSoup


class PubMedAgent:

    def search(self, query, max_results=10):

        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max_results
        }

        response = requests.get(url, params=params, timeout=10)

        data = response.json()

        return data["esearchresult"]["idlist"]


    def fetch_paper(self, pmid):

        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

        params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml"
        }

        response = requests.get(url, params=params, timeout=10)

        soup = BeautifulSoup(response.text, "lxml-xml")

        title_tag = soup.find("ArticleTitle")
        abstract_tags = soup.find_all("AbstractText")

        title = title_tag.text if title_tag else ""

        abstract = " ".join([a.text for a in abstract_tags]) if abstract_tags else ""

        return {
            "pmid": pmid,
            "title": title,
            "abstract": abstract
        }