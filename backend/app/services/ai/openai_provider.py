import os
from typing import Dict, Optional, List

from openai import AsyncOpenAI

from .provider import AIProvider


EXTRACTION_SYSTEM_PROMPT = (
    "You are WebSage. Extract concise business attributes from the given text. "
    "Return a compact JSON object with keys: industry, company_size, location, target_audience. "
    "If unknown, use null. Be factual and brief."
)


class OpenAIProvider(AIProvider):
    def __init__(self, model: str = "gpt-4o-mini"):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def infer_company_attributes(self, context_text: str) -> Dict[str, Optional[str]]:
        prompt = (
            "Context:\n" + context_text[:8000] + "\n\n"
            "Task: Extract industry, company_size, location, target_audience. JSON only."
        )
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        try:
            import json

            data = json.loads(content)
            return {
                "industry": data.get("industry"),
                "company_size": data.get("company_size"),
                "location": data.get("location"),
                "target_audience": data.get("target_audience"),
            }
        except Exception:
            return {"industry": None, "company_size": None, "location": None, "target_audience": None}

    async def answer_questions(self, context_text: str, questions: List[str]) -> List[Dict[str, str]]:
        results: List[Dict[str, str]] = []
        for q in questions:
            prompt = (
                "Context:\n" + context_text[:8000] + "\n\nQuestion: " + q + "\nAnswer briefly and factually. If unknown, say 'insufficient information'."
            )
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "You are WebSage."}, {"role": "user", "content": prompt}],
                temperature=0.2,
            )
            answer = resp.choices[0].message.content or ""
            results.append({"question": q, "answer": answer.strip()})
        return results


