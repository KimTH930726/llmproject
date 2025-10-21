import httpx
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class OllamaService:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama2")

    async def generate(self, prompt: str) -> str:
        """Ollama API를 호출하여 텍스트 생성"""
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")

    async def summarize_applicant(self, reason: str, experience: str, skill: str) -> str:
        """지원자 정보를 종합하여 요약"""
        prompt = f"""다음 지원자의 정보를 3-5개의 핵심 문장으로 요약해주세요.
전문적이고 간결하게 작성해주세요.

지원 동기:
{reason or '정보 없음'}

경력 및 경험:
{experience or '정보 없음'}

기술 스택 및 역량:
{skill or '정보 없음'}

요약:"""

        return await self.generate(prompt)

    async def extract_keywords(self, reason: str, experience: str, skill: str) -> list[str]:
        """지원자 정보에서 키워드 추출"""
        prompt = f"""다음 지원자의 정보에서 중요한 키워드를 5-10개 추출해주세요.
키워드는 쉼표로 구분하여 나열해주세요.

지원 동기:
{reason or '정보 없음'}

경력 및 경험:
{experience or '정보 없음'}

기술 스택 및 역량:
{skill or '정보 없음'}

키워드:"""

        response = await self.generate(prompt)
        # 응답을 쉼표로 분리하여 키워드 리스트 생성
        keywords = [kw.strip() for kw in response.split(",")]
        return keywords

    async def generate_interview_questions(self, reason: str, experience: str, skill: str) -> list[str]:
        """지원자 정보를 기반으로 면접 예상 질문 10개 생성"""
        prompt = f"""다음 지원자의 정보를 읽고 면접관이 물어볼만한 예상 질문 10개를 생성해주세요.
각 질문은 번호 없이 한 줄씩 작성하고, 각 줄은 줄바꿈으로 구분해주세요.

지원 동기:
{reason or '정보 없음'}

경력 및 경험:
{experience or '정보 없음'}

기술 스택 및 역량:
{skill or '정보 없음'}

면접 예상 질문:"""

        response = await self.generate(prompt)
        # 응답을 줄바꿈으로 분리하여 질문 리스트 생성
        questions = [q.strip() for q in response.split("\n") if q.strip() and not q.strip().isdigit()]
        # 번호 제거 (1., 2., 1), 2) 등의 형식)
        cleaned_questions = []
        for q in questions:
            # 앞부분의 번호 패턴 제거
            import re
            cleaned = re.sub(r'^\d+[\.\)]\s*', '', q)
            if cleaned:
                cleaned_questions.append(cleaned)

        # 정확히 10개만 반환
        return cleaned_questions[:10]

# 싱글톤 인스턴스
ollama_service = OllamaService()
