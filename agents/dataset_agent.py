import pandas as pd


class DatasetAgent:

    def __init__(self):

        self.adc_names = set()

    def add(self, name):
        name = name.strip()
        name = name.lower()
        name = name.capitalize()
        self.adc_names.add(name)

    def save(self):

        df = pd.DataFrame({"ADC_Name": sorted(self.adc_names)})

        df.to_csv("adc_names.csv", index=False)

        print("Saved adc_names.csv with", len(self.adc_names), "ADC names")