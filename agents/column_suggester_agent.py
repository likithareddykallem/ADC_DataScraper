import json
import re

import ollama

from config import LLM_MODEL


class ColumnSuggesterAgent:
    def suggest(self, topic, max_fields=8):
        prompt = f"""
Suggest the {max_fields} most relevant dataset columns for this topic.
Topic: {topic}

Rules:
- Return ONLY a JSON array of strings.
- Use concise snake_case field names.
- Prioritize fields that are commonly requested in scientific extraction tasks.
- Return exactly {max_fields} fields.
"""
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = (response["message"]["content"] or "").strip()
        raw = raw.replace("```json", "").replace("```", "").strip()

        columns = []
        try:
            values = json.loads(raw)
            if isinstance(values, list):
                columns = [self._to_snake_case(v) for v in values if str(v).strip()]
        except Exception:
            columns = []

        columns = [c for c in columns if c]
        columns = list(dict.fromkeys(columns))

        if len(columns) < max_fields:
            columns.extend(self._topic_driven_fallback(topic, max_fields - len(columns)))
            columns = list(dict.fromkeys(columns))

        return columns[:max_fields]

    def _to_snake_case(self, value):
        s = str(value).strip().lower()
        s = re.sub(r"[^a-z0-9]+", "_", s)
        s = re.sub(r"_+", "_", s).strip("_")
        return s

    def _topic_driven_fallback(self, topic, n):
        tokens = [t for t in re.findall(r"[a-z0-9]+", (topic or "").lower()) if len(t) > 3]
        out = []
        for i, t in enumerate(tokens[:n], start=1):
            out.append(f"{t}_attribute_{i}")
        while len(out) < n:
            out.append(f"derived_field_{len(out)+1}")
        return out
