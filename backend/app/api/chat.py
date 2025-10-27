"""
채팅 API
QueryRouter로 의도를 분류하고 RAG 또는 SQL Agent로 응답 생성
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session

from app.models.chat import ChatRequest, ChatResponse
from app.services.query_router import query_router, QueryIntent
from app.services.rag_service import rag_service
from app.services.sql_agent import sql_agent
from app.services.ollama_service import ollama_service
from app.database import get_session

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: Session = Depends(get_session)
):
    """
    사용자 질의에 대해 적절한 방식으로 응답 생성

    흐름:
    1. QueryRouter로 의도 분류 (RAG / SQL / General)
    2. RAG: Qdrant에서 문서 검색 후 LLM으로 답변
    3. SQL: 자연어를 SQL로 변환하여 DB 조회 후 답변
    4. General: LLM으로 직접 응답

    - query: 사용자 질의
    """
    query = request.query

    try:
        # 1. 의도 분류 (간단한 규칙 기반 사용, LLM 기반으로 변경 가능)
        intent = await query_router.classify_intent_simple(query)

        # 2. 의도별 처리
        if intent == QueryIntent.RAG_SEARCH:
            # RAG 검색
            result = await rag_service.answer_question(query, top_k=3)
            return ChatResponse(
                answer=result["answer"],
                intent=intent.value,
                sources=result.get("sources", [])
            )

        elif intent == QueryIntent.SQL_QUERY:
            # SQL Agent 실행
            result = await sql_agent.execute_query(query, session)
            return ChatResponse(
                answer=result["answer"],
                intent=intent.value,
                sql=result.get("sql"),
                results=result.get("results")
            )

        else:  # QueryIntent.GENERAL
            # 일반 대화
            answer = await ollama_service.generate(query)
            return ChatResponse(
                answer=answer,
                intent=intent.value
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 처리 실패: {str(e)}")


@router.post("/classify")
async def classify_query(request: ChatRequest):
    """
    질의 의도 분류만 수행 (디버깅용)

    - query: 사용자 질의
    """
    try:
        intent_simple = await query_router.classify_intent_simple(request.query)
        intent_llm = await query_router.classify_intent(request.query)

        return {
            "query": request.query,
            "intent_simple": intent_simple.value,
            "intent_llm": intent_llm.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분류 실패: {str(e)}")
