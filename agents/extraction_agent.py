import json
import re

import ollama

from config import LLM_MODEL, VALIDITY_THRESHOLD

class ADCExtractionAgent:
    def extract(self, text, columns):
        prompt = f"""
Extract structured data from text.

Requested columns: {columns}

Return ONLY JSON.
If the paper contains one relevant record, return a single JSON object.
If the paper contains multiple distinct records, return a JSON array of objects.
Every object must contain exactly the requested columns plus "validity_score".
Use null for missing values.
Rules:
- validity_score should reflect confidence from text evidence.
- Do not invent values not supported by the text.

Text:
{text}
"""

        response = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )

        output = (response["message"]["content"] or "").strip()
        output = output.replace("```json", "").replace("```", "").strip()

        try:
            rows = json.loads(output)
            if isinstance(rows, dict):
                rows = [rows]
            if not isinstance(rows, list):
                return []
            out = []
            text_lower = text.lower()
            for row in rows:
                if not isinstance(row, dict):
                    continue
                normalized = self._align_row(row, columns)
                score = float(row.get("validity_score", 0.0))
                if score < VALIDITY_THRESHOLD:
                    continue
                if not self._has_evidence(normalized, text_lower):
                    continue
                normalized["validity_score"] = score
                out.append(normalized)
            return out
        except Exception:
            return []

    def _align_row(self, row, columns):
        index = {self._normalize(key): key for key in row}
        aligned = {}
        for column in columns:
            value = row.get(column)
            if value is None:
                matched = index.get(self._normalize(column))
                if matched is not None:
                    value = row.get(matched)
            aligned[column] = value
        return aligned

    def _has_evidence(self, row, text_lower):
        checked = 0
        hits = 0
        for value in row.values():
            if value is None:
                continue
            value_str = str(value).strip()
            if not value_str:
                continue
            checked += 1
            if value_str.lower() in text_lower or _name_token_overlap(value_str, text_lower):
                hits += 1
        if checked == 0:
            return False
        return hits >= max(1, checked // 2)

    def _normalize(self, value):
        return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def _name_token_overlap(name, text_lower):
    tokens = [t for t in name.lower().replace("-", " ").split() if len(t) > 2]
    if not tokens:
        return False
    hits = sum(1 for t in tokens if t in text_lower)
    return hits >= max(1, len(tokens) // 2)
