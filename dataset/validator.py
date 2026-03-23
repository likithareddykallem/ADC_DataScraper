import re


def validate_row(row, source_text, required_columns=None):
    required_columns = required_columns or []
    raw_text = source_text or ""
    lowered_text = raw_text.lower()
    normalized_text = _normalize_text(raw_text)

    populated_fields = 0
    supported_fields = 0
    field_scores = []

    for key in required_columns:
        value = row.get(key)
        value_str = str(value or "").strip()
        if not value_str:
            continue

        populated_fields += 1
        score = _field_evidence_score(value_str, lowered_text, normalized_text)
        field_scores.append(score)
        if score >= 0.6:
            supported_fields += 1

    evidence_coverage = supported_fields / populated_fields if populated_fields else 0.0
    validation_score = sum(field_scores) / len(field_scores) if field_scores else 0.0

    return {
        "supported_fields": supported_fields,
        "populated_fields": populated_fields,
        "validation_evidence": round(evidence_coverage, 3),
        "validation_score": round(validation_score, 3),
        "is_valid": populated_fields > 0 and validation_score >= 0.6,
    }


def _field_evidence_score(value, lowered_text, normalized_text):
    value_lower = value.lower().strip()
    value_normalized = _normalize_text(value)

    if not value_normalized:
        return 0.0

    if value_lower in lowered_text or value_normalized in normalized_text:
        return 1.0

    tokens = [token for token in re.findall(r"[a-z0-9]+", value_lower) if len(token) >= 3]
    if not tokens:
        return 0.0

    hits = sum(1 for token in tokens if token in lowered_text)
    token_ratio = hits / len(tokens)

    if any(char.isdigit() for char in value_lower):
        compact_value = re.sub(r"\s+", "", value_lower)
        compact_text = re.sub(r"\s+", "", lowered_text)
        if compact_value in compact_text:
            return max(0.9, token_ratio)

    return round(token_ratio, 3)


def _normalize_text(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()
