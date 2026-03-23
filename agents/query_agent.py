import json

import ollama

from config import LLM_MODEL, MAX_QUERIES


class QueryAgent:

    def generate_queries(self, topic, columns):
        prompt = f"""
Generate high-quality scientific search queries.
Topic: {topic}
Columns/fields of interest: {columns}

Rules:
- Return {MAX_QUERIES} queries maximum.
- Every query should include topic + at least one column concept.
- Include exact phrase and synonym variants.
- Keep query length 4 to 14 words.

Return ONLY a JSON array of strings.
"""

        response = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = (response["message"]["content"] or "").strip()
        raw = raw.replace("```json", "").replace("```", "").strip()

        try:
            queries = json.loads(raw)
            if not isinstance(queries, list):
                raise ValueError("not list")
            out = [str(q).strip() for q in queries if str(q).strip()]
        except Exception:
            out = [topic]

        if topic not in out:
            out.append(topic)

        out = list(dict.fromkeys(out))
        return out[:MAX_QUERIES]
