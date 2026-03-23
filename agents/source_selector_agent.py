import json

import ollama

from config import LLM_MODEL


class SourceSelectorAgent:

    ALLOWED = [
        "pubmed",
        "pubmed_central",
        "arxiv",
        "biorxiv",
        "medrxiv",
        "semantic_scholar",
        "core",
        "ieee_xplore",
        "acm_digital_library",
        "sciencedirect",
        "drugbank",
    ]

    def select_sources(self, topic, columns):
        prompt = f"""
Choose best literature sources for this request.
Topic: {topic}
Columns: {columns}

Allowed sources: {self.ALLOWED}
Prefer biomedical relevance and data completeness.

Return ONLY a JSON array from allowed sources.
"""
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = (response["message"]["content"] or "").strip()
        raw = raw.replace("```json", "").replace("```", "").strip()

        try:
            values = json.loads(raw)
            if not isinstance(values, list):
                raise ValueError("not list")
            sources = [str(v).strip().lower() for v in values]
            sources = [s for s in sources if s in self.ALLOWED]
            if not sources:
                raise ValueError("empty")
            return list(dict.fromkeys(sources))
        except Exception:
            return self.ALLOWED
