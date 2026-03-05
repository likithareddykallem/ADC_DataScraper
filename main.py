from agents.query_agent import QueryAgent
from agents.pubmed_agent import PubMedAgent
from agents.filter_agent import KeywordFilterAgent
from agents.relevance_agent import RelevanceAgent
from agents.extraction_agent import ADCExtractionAgent
from agents.dataset_agent import DatasetAgent

from tqdm import tqdm


query_agent = QueryAgent()
pubmed_agent = PubMedAgent()
filter_agent = KeywordFilterAgent()
relevance_agent = RelevanceAgent()
extraction_agent = ADCExtractionAgent()
dataset_agent = DatasetAgent()


MAX_NAMES = 10
MAX_PAPERS = 100


def run_pipeline():

    queries = query_agent.generate_queries()

    all_ids = set()

    print("Searching PubMed...")

    for query in queries:

        ids = pubmed_agent.search(query)

        all_ids.update(ids)

    print("Total papers retrieved:", len(all_ids))


    for i, pmid in enumerate(tqdm(all_ids)):

        if i >= MAX_PAPERS:
            print("Reached paper limit.")
            break

        if len(dataset_agent.adc_names) >= MAX_NAMES:
            print("Reached 10 ADC names. Stopping early.")
            break

        try:

            paper = pubmed_agent.fetch_paper(pmid)

            if not paper["abstract"]:
                continue

            if not filter_agent.filter(paper):
                continue

            text = (paper["title"] + " " + paper["abstract"])[:500]

            if not relevance_agent.check(text):
                continue

            names = extraction_agent.extract(text)

            dataset_agent.add(names)

        except Exception as e:

            print("Skipping paper:", pmid, "Error:", e)

            continue


    dataset_agent.save()


if __name__ == "__main__":

    run_pipeline()