from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.services.ollama_service import ollama_service
from app.models.applicant import Applicant
from app.database import get_session

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class CoverLetterRequest(BaseModel):
    """자기소개서 요청 모델 (직접 텍스트 전달용)"""
    applicant_id: int
    cover_letter: str


class SummaryResponse(BaseModel):
    """요약 응답 모델"""
    applicant_id: int
    summary: str


class KeywordsResponse(BaseModel):
    """키워드 응답 모델"""
    applicant_id: int
    keywords: list[str]


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_cover_letter(request: CoverLetterRequest):
    """
    자기소개서 요약 API (직접 텍스트 전달)

    - applicant_id: 지원자 ID
    - cover_letter: 자기소개서 내용
    """
    try:
        summary = await ollama_service.summarize_cover_letter(request.cover_letter)
        return SummaryResponse(
            applicant_id=request.applicant_id,
            summary=summary
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 생성 실패: {str(e)}")


@router.post("/keywords", response_model=KeywordsResponse)
async def extract_keywords(request: CoverLetterRequest):
    """
    자기소개서 키워드 추출 API (직접 텍스트 전달)

    - applicant_id: 지원자 ID
    - cover_letter: 자기소개서 내용
    """
    try:
        keywords = await ollama_service.extract_keywords(request.cover_letter)
        return KeywordsResponse(
            applicant_id=request.applicant_id,
            keywords=keywords
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"키워드 추출 실패: {str(e)}")


@router.post("/summarize/{applicant_id}", response_model=SummaryResponse)
async def summarize_applicant_cover_letter(
    applicant_id: int,
    session: Session = Depends(get_session)
):
    """
    지원자 ID로 자기소개서 요약 API (DB 조회)

    - applicant_id: 지원자 ID
    """
    applicant = session.get(Applicant, applicant_id)
    if not applicant:
        raise HTTPException(status_code=404, detail="지원자를 찾을 수 없습니다")

    try:
        summary = await ollama_service.summarize_cover_letter(applicant.cover_letter)
        return SummaryResponse(
            applicant_id=applicant_id,
            summary=summary
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 생성 실패: {str(e)}")


@router.post("/keywords/{applicant_id}", response_model=KeywordsResponse)
async def extract_applicant_keywords(
    applicant_id: int,
    session: Session = Depends(get_session)
):
    """
    지원자 ID로 키워드 추출 API (DB 조회)

    - applicant_id: 지원자 ID
    """
    applicant = session.get(Applicant, applicant_id)
    if not applicant:
        raise HTTPException(status_code=404, detail="지원자를 찾을 수 없습니다")

    try:
        keywords = await ollama_service.extract_keywords(applicant.cover_letter)
        return KeywordsResponse(
            applicant_id=applicant_id,
            keywords=keywords
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"키워드 추출 실패: {str(e)}")
