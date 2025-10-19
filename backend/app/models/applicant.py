from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Applicant(SQLModel, table=True):
    """지원자 모델"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    phone: Optional[str] = None
    cover_letter: str  # 자기소개서
    position: Optional[str] = None  # 지원 포지션
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ApplicantCreate(SQLModel):
    """지원자 생성 요청 모델"""
    name: str
    email: str
    phone: Optional[str] = None
    cover_letter: str
    position: Optional[str] = None


class ApplicantRead(SQLModel):
    """지원자 조회 응답 모델"""
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    cover_letter: str
    position: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ApplicantUpdate(SQLModel):
    """지원자 업데이트 요청 모델"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    cover_letter: Optional[str] = None
    position: Optional[str] = None
