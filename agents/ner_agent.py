import spacy
import re


class NERAgent:

    def __init__(self):

        self.nlp = spacy.load("en_ner_bc5cdr_md")

        # patterns for ADC-like names
        self.adc_patterns = [
            re.compile(r"\b\w*mab\s+\w+", re.IGNORECASE),  # trastuzumab emtansine
            re.compile(r"\b[A-Z]-[A-Z0-9]+\b"),            # T-DM1
            re.compile(r"\b[A-Za-z0-9]+-ADC\b", re.IGNORECASE)  # HER2-ADC
        ]

    def is_candidate(self, name):

        for pattern in self.adc_patterns:
            if pattern.search(name):
                return True

        return False

    def extract_entities(self, text):

        doc = self.nlp(text)

        candidates = set()

        for ent in doc.ents:

            name = ent.text.strip()

            if len(name) < 4:
                continue

            if self.is_candidate(name):
                candidates.add(name)

        return list(candidates)