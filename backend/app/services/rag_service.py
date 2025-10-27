"""
RAG (Retrieval-Augmented Generation) 서비스
Qdrant에서 관련 문서를 검색하고 Ollama LLM으로 답변 생성
"""
from typing import List, Dict, Any
from app.services.qdrant_service import qdrant_service
from app.services.ollama_service import ollama_service


class RAGService:
    """RAG 기반 질의응답 서비스"""

    def __init__(self):
        self.qdrant = qdrant_service
        self.ollama = ollama_service

    async def answer_question(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """
        질문에 대해 RAG 방식으로 답변 생성

        Args:
            question: 사용자 질문
            top_k: 검색할 관련 문서 개수

        Returns:
            답변 및 참조 문서 정보
        """
        # 1. Qdrant에서 관련 문서 검색
        search_results = self.qdrant.search(query=question, limit=top_k)

        if not search_results:
            return {
                "answer": "관련 문서를 찾을 수 없습니다. 다른 질문을 시도해보세요.",
                "sources": [],
                "has_sources": False
            }

        # 2. 검색된 문서를 컨텍스트로 결합
        context = self._build_context(search_results)

        # 3. LLM 프롬프트 생성 및 답변 생성
        prompt = self._build_prompt(question, context)
        answer = await self.ollama.generate(prompt)

        # 4. 결과 반환
        return {
            "answer": answer,
            "sources": [
                {
                    "text": result["text"][:200] + "..." if len(result["text"]) > 200 else result["text"],
                    "score": result["score"],
                    "metadata": result["metadata"]
                }
                for result in search_results
            ],
            "has_sources": True
        }

    def _build_context(self, search_results: List[Dict[str, Any]]) -> str:
        """검색 결과를 컨텍스트 문자열로 결합"""
        contexts = []
        for idx, result in enumerate(search_results, 1):
            contexts.append(f"[문서 {idx}]\n{result['text']}\n")
        return "\n".join(contexts)

    def _build_prompt(self, question: str, context: str) -> str:
        """RAG 프롬프트 생성"""
        return f"""다음 문서들을 참고하여 질문에 답변해주세요.
문서에 없는 내용은 추측하지 말고, 문서 내용을 바탕으로만 답변하세요.

참고 문서:
{context}

질문: {question}

답변:"""


# 싱글톤 인스턴스
rag_service = RAGService()
