from agents.query_agent import QueryAgent
from agents.column_suggester_agent import ColumnSuggesterAgent
from agents.source_selector_agent import SourceSelectorAgent
from agents.source_hub_agent import SourceHubAgent
from agents.filter_agent import KeywordFilterAgent
from agents.relevance_agent import RelevanceAgent
from agents.extraction_agent import ADCExtractionAgent
from agents.dataset_agent import DatasetAgent
from dataset.validator import validate_row
from retrieval.fulltext_fetcher import fetch_text_for_paper

from tqdm import tqdm
from config import (
    DEFAULT_SUGGESTED_COLUMNS,
    MAX_FULLTEXT_FETCHES,
    MAX_NAMES,
    MAX_PAPERS_PER_QUERY,
    MAX_PAPERS_TOTAL,
    VALIDATION_SCORE_THRESHOLD,
)


query_agent = QueryAgent()
column_suggester_agent = ColumnSuggesterAgent()
source_selector_agent = SourceSelectorAgent()
source_hub = SourceHubAgent()
filter_agent = KeywordFilterAgent()
relevance_agent = RelevanceAgent()
extraction_agent = ADCExtractionAgent()
dataset_agent = DatasetAgent()


def run_pipeline():

    topic = input("\nEnter research topic: ").strip()
    cols = input("\nEnter columns (comma separated) or press Enter: ").strip()
    if cols:
        columns = [c.strip() for c in cols.split(",") if c.strip()]
    else:
        columns = column_suggester_agent.suggest(topic, max_fields=DEFAULT_SUGGESTED_COLUMNS)

    print("\nSelected columns:", ", ".join(columns))

    queries = query_agent.generate_queries(topic, columns)
    sources = source_selector_agent.select_sources(topic, columns)

    print("\nSelected sources:", ", ".join(sources))
    print("Queries:")
    for i, q in enumerate(queries, start=1):
        print(f"{i}. {q}")

    papers = []
    for query in queries:
        source_hits = source_hub.search(query, sources, max_per_source=MAX_PAPERS_PER_QUERY)
        papers.extend((query, p) for p in source_hits)

    print("Total papers retrieved:", len(papers))

    fulltext_fetch_count = 0
    for i, (query, paper) in enumerate(tqdm(papers)):
        if i >= MAX_PAPERS_TOTAL:
            print("Reached paper limit.")
            break
        if len(dataset_agent.rows) >= MAX_NAMES:
            print(f"Reached {MAX_NAMES} rows. Stopping early.")
            break

        try:
            if not paper.get("abstract"):
                continue
            if not filter_agent.filter(paper, topic, columns):
                continue

            snippet = ((paper.get("title") or "") + " " + (paper.get("abstract") or ""))[:2000]
            if not relevance_agent.check(snippet, topic, columns):
                continue

            if fulltext_fetch_count >= MAX_FULLTEXT_FETCHES:
                print(f"Reached full-text/PDF fetch limit of {MAX_FULLTEXT_FETCHES}.")
                break

            full_text = fetch_text_for_paper(paper)
            fulltext_fetch_count += 1
            extraction_text = full_text or snippet
            extracted_rows = extraction_agent.extract(extraction_text, columns)
            validated_rows = []
            for row in extracted_rows:
                validation = validate_row(row, extraction_text, required_columns=columns)
                row.update(validation)
                if row.get("validation_score", 0.0) < VALIDATION_SCORE_THRESHOLD:
                    continue
                if not row.get("is_valid", False):
                    continue
                row["confidence_score"] = round(
                    (0.55 * float(row.get("validity_score", 0.0)))
                    + (0.45 * float(row.get("validation_score", 0.0))),
                    3,
                )
                validated_rows.append(row)

            dataset_agent.add(validated_rows, paper, query, columns)
        except Exception as e:
            print("Skipping paper due to error:", e)
            continue


    dataset_agent.save(topic, columns)


if __name__ == "__main__":

    run_pipeline()
