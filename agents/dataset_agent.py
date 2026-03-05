import pandas as pd


# Common ADC payload suffixes
VALID_ADC_SUFFIXES = [
    "vedotin",
    "emtansine",
    "mafodonin",
    "mafodo tin",
    "mafodonin",
    "govitecan",
    "soravtansine",
    "deruxtecan"
]


# Known payload toxins (should NOT be treated as ADCs)
INVALID_PAYLOADS = [
    "mmae",
    "mmaf",
    "dm1",
    "dm4",
    "duocarmycin",
    "calicheamicin"
]


# Known small molecule drugs often incorrectly extracted
INVALID_DRUGS = [
    "lenvatinib",
    "sorafenib",
    "pazopanib"
]


def is_valid_adc(name):

    name_lower = name.lower()

    # remove obvious payload toxins
    for payload in INVALID_PAYLOADS:
        if name_lower == payload:
            return False

    # remove unrelated small molecule drugs
    for drug in INVALID_DRUGS:
        if name_lower == drug:
            return False

    # check for ADC suffix pattern
    for suffix in VALID_ADC_SUFFIXES:
        if suffix in name_lower:
            return True

    # allow experimental ADC patterns
    if "adc" in name_lower:
        return True

    if "-" in name_lower and "dxd" in name_lower:
        return True

    return False


class DatasetAgent:

    def __init__(self):

        self.adc_names = set()

    def add(self, names):

        for name in names:

            name = name.strip()

            if name and name.lower() != "none":

                if is_valid_adc(name):
                    self.adc_names.add(name)

    def save(self):

        df = pd.DataFrame({"ADC_Name": sorted(self.adc_names)})

        df.to_csv("adc_names.csv", index=False)

        print("Saved adc_names.csv with", len(self.adc_names), "ADC names")