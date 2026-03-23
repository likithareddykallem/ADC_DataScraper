import ollama
import json

from config import LLM_MODEL, RELEVANCE_THRESHOLD

class RelevanceAgent:

    def check(self, text, topic, columns):

        prompt = f"""
Score relevance for this paper snippet.
Topic: {topic}
Columns: {columns}

Return ONLY JSON:
{{
  "score": <0 to 1>,
  "relevant": <true/false>,
  "reason": "<short>"
}}

Text:
{text}
"""

        response = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = (response["message"]["content"] or "").strip()
        raw = raw.replace("```json", "").replace("```", "").strip()

        try:
            data = json.loads(raw)
            score = float(data.get("score", 0.0))
            return score >= RELEVANCE_THRESHOLD
        except Exception:
            return self._fallback_score(text, topic, columns) >= RELEVANCE_THRESHOLD

    def _fallback_score(self, text, topic, columns):
        text_lower = (text or "").lower()
        words = set()
        for value in [topic] + list(columns or []):
            for token in str(value).lower().replace("_", " ").split():
                if len(token) >= 4:
                    words.add(token)
        if not words:
            return 0.0
        hits = sum(1 for word in words if word in text_lower)
        return hits / len(words)
