import ollama


class RelevanceAgent:

    def check(self, text):

        prompt = f"""
Determine if the following text discusses a specific antibody-drug conjugate (ADC)
or contains information about ADC components like antibody, payload, linker, or DAR.

Answer ONLY YES or NO.

Text:
{text}
"""

        response = ollama.chat(
            model="llama3.2:3b",
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response["message"]["content"].strip().upper()

        return answer == "YES"