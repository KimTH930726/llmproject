from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from app.models.applicant import (
    Applicant,
    ApplicantCreate,
    ApplicantRead,
    ApplicantUpdate
)
from app.database import get_session

router = APIRouter(prefix="/api/applicants", tags=["applicants"])


@router.post("/", response_model=ApplicantRead)
def create_applicant(
    applicant: ApplicantCreate,
    session: Session = Depends(get_session)
):
    """지원자 생성"""
    db_applicant = Applicant.model_validate(applicant)
    session.add(db_applicant)
    session.commit()
    session.refresh(db_applicant)
    return db_applicant


@router.get("/", response_model=List[ApplicantRead])
def read_applicants(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """지원자 목록 조회"""
    statement = select(Applicant).offset(skip).limit(limit)
    applicants = session.exec(statement).all()
    return applicants


@router.get("/{applicant_id}", response_model=ApplicantRead)
def read_applicant(
    applicant_id: int,
    session: Session = Depends(get_session)
):
    """특정 지원자 조회"""
    applicant = session.get(Applicant, applicant_id)
    if not applicant:
        raise HTTPException(status_code=404, detail="지원자를 찾을 수 없습니다")
    return applicant


@router.patch("/{applicant_id}", response_model=ApplicantRead)
def update_applicant(
    applicant_id: int,
    applicant_update: ApplicantUpdate,
    session: Session = Depends(get_session)
):
    """지원자 정보 업데이트"""
    applicant = session.get(Applicant, applicant_id)
    if not applicant:
        raise HTTPException(status_code=404, detail="지원자를 찾을 수 없습니다")

    applicant_data = applicant_update.model_dump(exclude_unset=True)
    for key, value in applicant_data.items():
        setattr(applicant, key, value)

    applicant.updated_at = datetime.utcnow()
    session.add(applicant)
    session.commit()
    session.refresh(applicant)
    return applicant


@router.delete("/{applicant_id}")
def delete_applicant(
    applicant_id: int,
    session: Session = Depends(get_session)
):
    """지원자 삭제"""
    applicant = session.get(Applicant, applicant_id)
    if not applicant:
        raise HTTPException(status_code=404, detail="지원자를 찾을 수 없습니다")

    session.delete(applicant)
    session.commit()
    return {"message": "지원자가 삭제되었습니다"}
