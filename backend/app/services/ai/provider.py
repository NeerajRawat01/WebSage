from typing import Dict, Optional


class AIProvider:
    async def infer_company_attributes(self, context_text: str) -> Dict[str, Optional[str]]:
        raise NotImplementedError

    async def answer_questions(self, context_text: str, questions: list[str]) -> list[Dict[str, str]]:
        raise NotImplementedError


