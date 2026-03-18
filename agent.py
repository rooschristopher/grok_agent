import os

from openai import OpenAI


class Agent:
    def __init__(self):
        self.model = os.getenv("GROK_MODEL", "grok-beta")
        api_key = os.getenv("XAI_API_KEY")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1",
        )

    def generate(self, prompt):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
