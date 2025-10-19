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

    async def summarize_cover_letter(self, cover_letter: str) -> str:
        """자기소개서 요약"""
        prompt = f"""다음 자기소개서를 3-5개의 핵심 문장으로 요약해주세요.
전문적이고 간결하게 작성해주세요.

자기소개서:
{cover_letter}

요약:"""

        return await self.generate(prompt)

    async def extract_keywords(self, cover_letter: str) -> list[str]:
        """자기소개서에서 키워드 추출"""
        prompt = f"""다음 자기소개서에서 중요한 키워드를 5-10개 추출해주세요.
키워드는 쉼표로 구분하여 나열해주세요.

자기소개서:
{cover_letter}

키워드:"""

        response = await self.generate(prompt)
        # 응답을 쉼표로 분리하여 키워드 리스트 생성
        keywords = [kw.strip() for kw in response.split(",")]
        return keywords

# 싱글톤 인스턴스
ollama_service = OllamaService()
