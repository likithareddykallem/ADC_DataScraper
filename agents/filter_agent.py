import re


class KeywordFilterAgent:
    def filter(self, paper, topic="", columns=None):
        text = f"{paper.get('title') or ''} {paper.get('abstract') or ''}".lower()
        if not text.strip():
            return False

        keywords = self._keywords(topic, columns or [])
        if not keywords:
            return True

        hits = sum(1 for keyword in keywords if keyword in text)
        min_hits = 1 if len(keywords) < 4 else 2
        return hits >= min_hits

    def _keywords(self, topic, columns):
        values = [topic] + list(columns or [])
        tokens = []
        for value in values:
            for token in re.findall(r"[a-z0-9]+", str(value).lower()):
                if len(token) >= 4:
                    tokens.append(token)
        return list(dict.fromkeys(tokens))
