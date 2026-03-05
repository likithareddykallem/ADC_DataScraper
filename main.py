from agents.query_agent import QueryAgent
from agents.pubmed_agent import PubMedAgent
from agents.ner_agent import NERAgent
from agents.adc_classifier_agent import ADCClassifierAgent
from agents.dataset_agent import DatasetAgent

from tqdm import tqdm


query_agent = QueryAgent()
pubmed_agent = PubMedAgent()
ner_agent = NERAgent()
classifier_agent = ADCClassifierAgent()
dataset_agent = DatasetAgent()


def run_pipeline():

    queries = query_agent.generate_queries()

    all_ids = set()

    print("Searching PubMed...")

    for query in queries:

        ids = pubmed_agent.search(query)

        all_ids.update(ids)

    print("Total papers retrieved:", len(all_ids))


    for pmid in tqdm(all_ids):

        try:

            paper = pubmed_agent.fetch_paper(pmid)

            text = paper["title"] + " " + paper["abstract"]

            if not text.strip():
                continue

            # Step 1: NER entity detection
            entities = ner_agent.extract_entities(text)

            # Step 2: LLM classification
            for entity in entities:

                if classifier_agent.is_adc(entity):

                    dataset_agent.add(entity)

        except Exception as e:

            print("Skipping paper:", pmid, e)


    dataset_agent.save()


if __name__ == "__main__":

    run_pipeline()