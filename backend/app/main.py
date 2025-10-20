from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analysis


app = FastAPI(
    title="지원자 자기소개서 분석 API",
    description="PostgreSQL에 저장된 지원자 자기소개서를 LLM으로 요약 및 키워드 추출하는 서비스",
    version="1.0.0"
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

@app.get("/")
async def root():
    return {"message": "지원자 자기소개서 분석 API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
