class KeywordFilterAgent:

    KEYWORDS = [
        "antibody drug conjugate",
        "adc",
        "payload",
        "linker",
        "drug antibody ratio",
        "dar"
    ]

    def filter(self, paper):

        text = (paper["title"] + " " + paper["abstract"]).lower()

        score = sum(keyword in text for keyword in self.KEYWORDS)

        return score >= 1