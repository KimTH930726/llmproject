from sqlmodel import SQLModel, Field
from typing import Optional


class Applicant(SQLModel, table=True):
    """
    지원자 모델 (읽기 전용)
    PostgreSQL의 applicants 테이블과 매핑됨
    """
    __tablename__ = "applicants"

    id: Optional[int] = Field(default=None, primary_key=True)
    content: str  # 자기소개서 내용


class ApplicantRead(SQLModel):
    """지원자 조회 응답 모델"""
    id: int
    content: str
