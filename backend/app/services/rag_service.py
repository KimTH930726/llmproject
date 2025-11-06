"""
RAG (Retrieval-Augmented Generation) 서비스
Qdrant에서 관련 문서를 검색하고 Ollama LLM으로 답변 생성
"""
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select
from app.services.qdrant_service import qdrant_service
from app.services.ollama_service import ollama_service
from app.models.few_shot import FewShot


class RAGService:
    """RAG 기반 질의응답 서비스"""

    def __init__(self):
        self.qdrant = qdrant_service
        self.ollama = ollama_service

    async def answer_question(
        self,
        question: str,
        top_k: int = 3,
        session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        질문에 대해 RAG 방식으로 답변 생성

        Args:
            question: 사용자 질문
            top_k: 검색할 관련 문서 개수
            session: DB 세션 (Few-shot 예제 조회용, optional)

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

        # 3. Few-shot 예제 가져오기 (session이 제공된 경우)
        few_shots = self._get_active_fewshots(session, intent_type="rag_search") if session else []

        # 4. LLM 프롬프트 생성 및 답변 생성
        prompt = self._build_prompt(question, context, few_shots)
        answer = await self.ollama.generate(prompt)

        # 5. 결과 반환
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

    def _get_active_fewshots(
        self,
        session: Optional[Session],
        intent_type: Optional[str] = None
    ) -> List[FewShot]:
        """
        활성화된 Few-shot 예제 조회

        Args:
            session: DB 세션
            intent_type: Intent 타입 필터 (optional)

        Returns:
            활성화된 Few-shot 예제 리스트
        """
        if not session:
            return []

        try:
            statement = select(FewShot).where(FewShot.is_active == True)
            if intent_type:
                statement = statement.where(FewShot.intent_type == intent_type)

            results = session.exec(statement).all()
            return list(results)
        except Exception as e:
            print(f"Few-shot 조회 실패: {e}")
            return []

    def _build_prompt(
        self,
        question: str,
        context: str,
        few_shots: List[FewShot] = None
    ) -> str:
        """RAG 프롬프트 생성 (Few-shot 예제 포함)"""
        prompt_parts = []

        # Few-shot 예제 추가
        if few_shots:
            prompt_parts.append("다음은 질문-답변 예제입니다:\n")
            for idx, fs in enumerate(few_shots, 1):
                prompt_parts.append(f"예제 {idx}:")
                prompt_parts.append(f"질문: {fs.user_query}")
                if fs.expected_response:
                    prompt_parts.append(f"답변: {fs.expected_response}")
                prompt_parts.append("")
            prompt_parts.append("---\n")

        # 기본 프롬프트
        prompt_parts.append("""다음 문서들을 참고하여 질문에 답변해주세요.
문서에 없는 내용은 추측하지 말고, 문서 내용을 바탕으로만 답변하세요.

참고 문서:""")
        prompt_parts.append(context)
        prompt_parts.append(f"\n질문: {question}\n")
        prompt_parts.append("답변:")

        return "\n".join(prompt_parts)


# 싱글톤 인스턴스
rag_service = RAGService()
