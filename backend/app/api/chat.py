"""
채팅 API
QueryRouter로 의도를 분류하고 RAG 또는 SQL Agent로 응답 생성
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session

from app.models.chat import ChatRequest, ChatResponse
from app.models.query_log import QueryLog
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
    5. 질의와 응답을 query_logs 테이블에 자동 저장

    - query: 사용자 질의
    """
    query = request.query
    answer = None
    intent_value = None

    try:
        # 1. 의도 분류 (간단한 규칙 기반 사용, LLM 기반으로 변경 가능)
        intent = await query_router.classify_intent_simple(query)
        intent_value = intent.value

        # 2. 의도별 처리
        if intent == QueryIntent.RAG_SEARCH:
            # RAG 검색 (session 전달하여 Few-shot 예제 활용)
            result = await rag_service.answer_question(query, top_k=3, session=session)
            answer = result["answer"]
            response = ChatResponse(
                answer=answer,
                intent=intent_value,
                sources=result.get("sources", [])
            )

        elif intent == QueryIntent.SQL_QUERY:
            # SQL Agent 실행
            result = await sql_agent.execute_query(query, session)
            answer = result["answer"]
            response = ChatResponse(
                answer=answer,
                intent=intent_value,
                sql=result.get("sql"),
                results=result.get("results")
            )

        else:  # QueryIntent.GENERAL
            # 일반 대화
            answer = await ollama_service.generate(query)
            response = ChatResponse(
                answer=answer,
                intent=intent_value
            )

        # 3. 질의 로그 자동 저장
        query_log = QueryLog(
            query_text=query,
            detected_intent=intent_value,
            response=answer
        )
        session.add(query_log)
        session.commit()

        return response

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
