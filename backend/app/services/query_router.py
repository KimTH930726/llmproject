"""
QueryRouter - 사용자 질의의 의도를 분류하는 서비스
RAG 검색 vs SQL 쿼리를 판단
"""
from enum import Enum
from app.services.ollama_service import ollama_service


class QueryIntent(str, Enum):
    """질의 의도 타입"""
    RAG_SEARCH = "rag_search"  # 문서 검색 기반 답변
    SQL_QUERY = "sql_query"    # 데이터베이스 쿼리 기반 답변
    GENERAL = "general"        # 일반 대화


class QueryRouter:
    """사용자 질의를 분석하여 적절한 처리 방식을 결정"""

    def __init__(self):
        self.ollama = ollama_service

    async def classify_intent(self, query: str) -> QueryIntent:
        """
        질의를 분석하여 의도 분류

        Args:
            query: 사용자 질의

        Returns:
            QueryIntent (rag_search, sql_query, general)
        """
        # LLM을 사용한 의도 분류
        prompt = f"""다음 질문의 유형을 분류해주세요.

질문 유형:
1. rag_search: 문서 내용 검색이 필요한 질문 (예: "계약서 내용이 뭐야?", "문서에서 금액은?")
2. sql_query: 데이터베이스 조회가 필요한 질문 (예: "지원자 목록 보여줘", "지원자 수는?", "ID 1번 지원자 정보")
3. general: 일반 대화 (예: "안녕", "고마워", "어떻게 사용해?")

질문: {query}

위 질문의 유형을 rag_search, sql_query, general 중 하나만 답하세요:"""

        response = await self.ollama.generate(prompt)
        response_lower = response.strip().lower()

        # 응답에서 의도 추출
        if "sql" in response_lower or "sql_query" in response_lower:
            return QueryIntent.SQL_QUERY
        elif "rag" in response_lower or "rag_search" in response_lower:
            return QueryIntent.RAG_SEARCH
        else:
            return QueryIntent.GENERAL

    async def classify_intent_simple(self, query: str) -> QueryIntent:
        """
        간단한 규칙 기반 의도 분류 (빠른 처리용)

        Args:
            query: 사용자 질의

        Returns:
            QueryIntent
        """
        query_lower = query.lower()

        # SQL 쿼리 키워드
        sql_keywords = ["지원자", "applicant", "목록", "리스트", "몇 명", "수", "count", "id"]

        # RAG 검색 키워드
        rag_keywords = ["문서", "document", "내용", "계약", "설명", "찾아"]

        # 일반 대화 키워드
        general_keywords = ["안녕", "고마워", "감사", "hello", "hi", "thanks"]

        # 우선순위: 일반 대화 > SQL > RAG
        if any(keyword in query_lower for keyword in general_keywords):
            return QueryIntent.GENERAL

        if any(keyword in query_lower for keyword in sql_keywords):
            return QueryIntent.SQL_QUERY

        if any(keyword in query_lower for keyword in rag_keywords):
            return QueryIntent.RAG_SEARCH

        # 기본값: RAG 검색
        return QueryIntent.RAG_SEARCH


# 싱글톤 인스턴스
query_router = QueryRouter()
