from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.services.ollama_service import ollama_service
from app.models.applicant import Applicant
from app.database import get_session

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class SummaryResponse(BaseModel):
    """요약 응답 모델"""
    applicant_id: int
    summary: str


class KeywordsResponse(BaseModel):
    """키워드 응답 모델"""
    applicant_id: int
    keywords: list[str]


@router.post("/summarize/{applicant_id}", response_model=SummaryResponse)
async def summarize_applicant(
    applicant_id: int,
    session: Session = Depends(get_session)
):
    """
    지원자 ID로 자기소개서 요약 API

    PostgreSQL에서 지원자 데이터를 조회하여 자기소개서를 요약합니다.

    - applicant_id: 지원자 ID
    """
    applicant = session.get(Applicant, applicant_id)
    if not applicant:
        raise HTTPException(status_code=404, detail="지원자를 찾을 수 없습니다")

    try:
        summary = await ollama_service.summarize_cover_letter(applicant.content)
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
    지원자 ID로 키워드 추출 API

    PostgreSQL에서 지원자 데이터를 조회하여 키워드를 추출합니다.

    - applicant_id: 지원자 ID
    """
    applicant = session.get(Applicant, applicant_id)
    if not applicant:
        raise HTTPException(status_code=404, detail="지원자를 찾을 수 없습니다")

    try:
        keywords = await ollama_service.extract_keywords(applicant.content)
        return KeywordsResponse(
            applicant_id=applicant_id,
            keywords=keywords
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"키워드 추출 실패: {str(e)}")
