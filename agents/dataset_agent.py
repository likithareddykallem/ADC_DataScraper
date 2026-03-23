import csv

from config import OUTPUT_PATH, VALIDITY_THRESHOLD


class DatasetAgent:

    def __init__(self):

        self.rows = []
        self._seen = set()

    def add(self, extracted_rows, paper, query, columns):

        for item in extracted_rows:
            validity_score = float(item.get("validity_score", 0.0))
            if validity_score < VALIDITY_THRESHOLD:
                continue

            row = {column: item.get(column) for column in columns}
            row["confidence_score"] = item.get("confidence_score")
            row["validation_score"] = item.get("validation_score")
            row["validation_evidence"] = item.get("validation_evidence")
            if not any(self._has_value(row.get(column)) for column in columns):
                continue

            row["paper_url"] = paper.get("url", "")
            key = repr(sorted(row.items()))
            if key in self._seen:
                continue

            self._seen.add(key)
            self.rows.append(row)

    def save(self, topic, columns, output_path=OUTPUT_PATH):
        fieldnames = list(
            dict.fromkeys(
                list(columns or [])
                + [
                    "paper_url",
                    "validation_score",
                    "validation_evidence",
                    "confidence_score",
                ]
            )
        )
        with open(output_path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in self.rows:
                writer.writerow({name: row.get(name) for name in fieldnames})
        print(f"Saved {output_path} with {len(self.rows)} rows")

    def _has_value(self, value):
        if value is None:
            return False
        return bool(str(value).strip())
