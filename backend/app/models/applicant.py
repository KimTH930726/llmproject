from sqlmodel import SQLModel, Field
from typing import Optional


class Applicant(SQLModel, table=True):
    """
    지원자 모델 (읽기 전용)
    PostgreSQL의 applicants 테이블과 매핑됨
    """
    __tablename__ = "applicants"

    id: Optional[int] = Field(default=None, primary_key=True)
    reason: Optional[str] = Field(default=None, max_length=4000)  # 지원 동기
    experience: Optional[str] = Field(default=None, max_length=4000)  # 경력 및 경험
    skill: Optional[str] = Field(default=None, max_length=4000)  # 기술 스택 및 역량


class ApplicantRead(SQLModel):
    """지원자 조회 응답 모델"""
    id: int
    reason: Optional[str] = None
    experience: Optional[str] = None
    skill: Optional[str] = None
