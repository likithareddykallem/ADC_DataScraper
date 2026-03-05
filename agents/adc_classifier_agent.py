import ollama


class ADCClassifierAgent:

    def __init__(self):

        self.model = "llama3.2:3b"

    def is_adc(self, name):

        prompt = f"""
Determine whether the following name refers to an antibody-drug conjugate (ADC).

Rules:
- ADC = monoclonal antibody chemically linked to cytotoxic payload
- Antibodies alone are NOT ADCs
- Payload molecules alone are NOT ADCs
- General biology terms are NOT ADCs

Examples:
Brentuximab vedotin → YES
Trastuzumab emtansine → YES
Mirvetuximab soravtansine → YES
T-DM1 → YES

MMAE → NO
Rituximab → NO
HER2 → NO
Duocarmycin → NO

Name: {name}

Answer only YES or NO.
"""

        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response["message"]["content"].strip().upper()

        return "YES" in answer