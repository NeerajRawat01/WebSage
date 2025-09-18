import os
from typing import Dict, Optional, List

import google.generativeai as genai

from .provider import AIProvider


EXTRACTION_SYSTEM_PROMPT = (
    "You are WebSage. Extract concise business attributes from the given text. "
    "Return a compact JSON object with keys: industry, company_size, location, target_audience. "
    "If unknown, use null. Be factual and brief."
)


class GeminiProvider(AIProvider):
    def __init__(self, model: str = "gemini-1.5-pro"):
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    async def infer_company_attributes(self, context_text: str) -> Dict[str, Optional[str]]:
        prompt = (
            EXTRACTION_SYSTEM_PROMPT
            + "\n\nContext:\n"
            + context_text[:8000]
            + "\n\nTask: Extract industry, company_size, location, target_audience. JSON only."
        )
        resp = await self.model.generate_content_async(prompt)
        content = resp.text or "{}"
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
            resp = await self.model.generate_content_async(prompt)
            answer = (resp.text or "").strip()
            results.append({"question": q, "answer": answer})
        return results


