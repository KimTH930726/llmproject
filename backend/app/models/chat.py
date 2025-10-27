"""
채팅 및 문서 업로드 관련 Pydantic 모델
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    query: str


class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    answer: str
    intent: str  # rag_search, sql_query, general
    sources: Optional[List[Dict[str, Any]]] = None
    sql: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None


class UploadResponse(BaseModel):
    """파일 업로드 응답 모델"""
    message: str
    filename: str
    doc_id: str
    text_length: int
