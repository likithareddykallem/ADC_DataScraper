# ADC Agent

This project builds a structured literature dataset from a research topic.

The current live entrypoint is [`main.py`](c:\Users\Kalle\OneDrive\Desktop\Desktop\Paradigm\adc_agent\main.py). It uses a local Ollama model to:

- suggest extraction columns when you do not provide them
- generate search queries
- choose relevant literature sources
- score paper relevance
- extract structured rows from paper text

The final output is written as a CSV file, currently `dataset.csv`.

## Approach

The pipeline follows this sequence:

1. The user enters a research topic.
2. The user can optionally provide required columns.
3. If no columns are provided, the app asks the LLM to suggest them.
4. The app generates up to 8 literature search queries from the topic and columns.
5. The app selects suitable sources such as PubMed, PubMed Central, arXiv, bioRxiv, medRxiv, Semantic Scholar, CORE, IEEE Xplore, ACM, ScienceDirect, and DrugBank.
6. For each query, it retrieves papers from the selected sources.
7. Retrieved papers are filtered first with a keyword filter, then with an LLM relevance check.
8. For relevant papers, the app attempts to fetch full text from PDF or HTML. If that fails, it falls back to title plus abstract.
9. The LLM extracts structured rows matching the requested columns.
10. Each extracted row is validated against the source text and assigned a confidence score.
11. Only rows that pass the thresholds are saved to CSV.

In short:

`topic -> columns -> queries -> source selection -> paper retrieval -> filtering -> full-text fetch -> extraction -> validation -> CSV`

## Current Limits

The runtime and retrieval limits are defined in [`config.py`](c:\Users\Kalle\OneDrive\Desktop\Desktop\Paradigm\adc_agent\config.py):

- `MAX_QUERIES = 8`
- `MAX_PAPERS_PER_QUERY = 10`
- `MAX_PAPERS_TOTAL = 100`
- `MAX_FULLTEXT_FETCHES = 100`
- `MAX_NAMES = 100`
- `DEFAULT_SUGGESTED_COLUMNS = 8`

What these mean in practice:

- The app will generate at most 8 search queries.
- Each query asks each selected source for up to 10 papers.
- Even if more papers are retrieved, the main processing loop stops after 100 paper entries.
- Full-text or PDF extraction also stops after 100 fetches.
- Dataset creation stops early once 100 rows are collected.

These limits were added to keep runtime, API calls, and extraction cost under control.

## Validation And Confidence

Validation happens after extraction and before saving.

The validator is implemented in [`dataset/validator.py`](c:\Users\Kalle\OneDrive\Desktop\Desktop\Paradigm\adc_agent\dataset\validator.py). It does not penalize a row for being incomplete. Instead, it evaluates only the fields that were actually extracted.

For each populated required field, the validator checks whether the value is supported by the paper text:

- exact text match gets full credit
- normalized text match also gets full credit
- otherwise it falls back to token-overlap evidence
- numeric values get an extra compact-match check

It produces:

- `validation_score`: average evidence strength across populated extracted fields
- `validation_evidence`: fraction of populated fields with decent support
- `is_valid`: row-level pass/fail flag

The pipeline then combines:

- `validity_score` from the extraction LLM output
- `validation_score` from the evidence checker

to compute:

- `confidence_score`

At the moment, the important thresholds are:

- `VALIDITY_THRESHOLD = 0.70`
- `VALIDATION_SCORE_THRESHOLD = 0.65`

Only rows above those thresholds are saved.

## Output Format

The saved file is a CSV with:

- the required columns
- `paper_url`
- `validation_score`
- `validation_evidence`
- `confidence_score`

This makes it easier to inspect the extracted evidence quality row by row.

## Sources And Retrieval

Source retrieval is centralized in [`agents/source_hub_agent.py`](c:\Users\Kalle\OneDrive\Desktop\Desktop\Paradigm\adc_agent\agents\source_hub_agent.py).

It supports:

- PubMed
- PubMed Central
- arXiv
- bioRxiv
- medRxiv
- Semantic Scholar
- CORE
- IEEE Xplore
- ACM Digital Library
- ScienceDirect
- DrugBank

Some sources use official APIs directly, while others fall back to site-restricted search when needed.

Optional environment variables:

- `CORE_API_KEY`
- `IEEE_API_KEY`

If these are not set, the project falls back to broader site search for those sources.

## Main Files

- [`main.py`](c:\Users\Kalle\OneDrive\Desktop\Desktop\Paradigm\adc_agent\main.py): live CLI pipeline
- [`config.py`](c:\Users\Kalle\OneDrive\Desktop\Desktop\Paradigm\adc_agent\config.py): runtime limits and thresholds
- [`agents/source_hub_agent.py`](c:\Users\Kalle\OneDrive\Desktop\Desktop\Paradigm\adc_agent\agents\source_hub_agent.py): paper retrieval across sources
- [`agents/extraction_agent.py`](c:\Users\Kalle\OneDrive\Desktop\Desktop\Paradigm\adc_agent\agents\extraction_agent.py): structured extraction
- [`dataset/validator.py`](c:\Users\Kalle\OneDrive\Desktop\Desktop\Paradigm\adc_agent\dataset\validator.py): evidence-based validation
- [`agents/dataset_agent.py`](c:\Users\Kalle\OneDrive\Desktop\Desktop\Paradigm\adc_agent\agents\dataset_agent.py): CSV writing and deduplication

## Running The App

Activate the virtual environment in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies if needed:

```powershell
pip install -r requirements.txt
```

Run the pipeline:

```powershell
python main.py
```

You will be prompted for:

- a research topic
- optional comma-separated required columns

If you leave the columns blank, the app will suggest them automatically.

## Notes

- The project relies on a local Ollama model configured in [`config.py`](c:\Users\Kalle\OneDrive\Desktop\Desktop\Paradigm\adc_agent\config.py).
- The currently configured model is `llama3.2:3b`.
- The active application flow is the CLI pipeline in [`main.py`](c:\Users\Kalle\OneDrive\Desktop\Desktop\Paradigm\adc_agent\main.py).
