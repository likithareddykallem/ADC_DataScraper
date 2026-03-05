import ollama


class ADCExtractionAgent:

    def extract(self, text):

        prompt = f"""
Extract names of antibody drug conjugates mentioned in the text.

Return ONLY a comma separated list.

If none exist return NONE.

Text:
{text}
"""

        response = ollama.chat(
            model="llama3.2:3b",
            messages=[{"role": "user", "content": prompt}]
        )

        output = response["message"]["content"].strip()

        if output.lower() == "none":
            return []

        names = [name.strip() for name in output.split(",")]

        return names