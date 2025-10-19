from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import analysis, applicants
from app.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 데이터베이스 테이블 생성
    create_db_and_tables()
    yield
    # 종료 시 실행할 코드 (필요시 추가)


app = FastAPI(
    title="지원자 자기소개서 분석 API",
    description="LLM을 활용한 지원자 자기소개서 요약 및 키워드 추출 서비스",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite 기본 포트
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(analysis.router)
app.include_router(applicants.router)

@app.get("/")
async def root():
    return {"message": "지원자 자기소개서 분석 API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
