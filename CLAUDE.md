# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

채용 지원자 자기소개서 분석 시스템 - LLM을 활용하여 지원자의 자기소개서를 요약하고 키워드를 추출하는 API 서비스

### Core Features
1. **요약 API** - 지원자 자기소개서를 조회하여 LLM으로 요약 생성
2. **키워드 생성 API** - 자기소개서에서 주요 키워드 추출

## Tech Stack

### Backend
- **FastAPI** (Python) - Web framework
- **SQLModel** - ORM for database operations
- **SQLite** - Database (지원자 정보 저장)
- **Ollama** - LLM integration (자기소개서 분석용)

### Frontend
- **React** + **TypeScript**
- **Vite** - Build tool
- **Tailwind CSS** - Styling

## Architecture

### Data Flow
1. Database에서 지원자의 자기소개서(cover letter/personal statement) 컬럼 조회
2. 조회된 텍스트 + 프롬프트를 Ollama LLM에 전송
3. LLM 응답 처리 및 클라이언트에 반환

### Backend Structure
- FastAPI REST API endpoints
  - 요약 API endpoint
  - 키워드 생성 API endpoint
- SQLModel로 지원자 데이터 모델 정의
- Ollama 연동 로직
- SQLite database에 지원자 자기소개서 저장

### Frontend Structure
- React + TypeScript SPA
- Vite로 빌드
- Tailwind CSS로 스타일링
- Backend API 호출하여 요약/키워드 결과 표시

## Development Commands

### Docker를 사용한 개발 (권장)

```bash
# 전체 서비스 시작
docker-compose up -d

# Ollama 모델 다운로드
docker exec ollama ollama pull llama2

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down
```

### Prerequisites (Docker 없이 로컬 개발 시)
1. Python 3.10+ 설치
2. Node.js 18+ 설치
3. Ollama 설치 및 실행 (`ollama serve`)
4. Ollama 모델 다운로드 (`ollama pull llama2`)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # .env 파일을 생성하고 설정 수정
```

### Backend Commands
```bash
cd backend
source venv/bin/activate  # venv 활성화 (필요시)

# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API 문서 확인
# 서버 실행 후 http://localhost:8000/docs 접속
```

### Frontend Setup
```bash
cd frontend
npm install
```

### Frontend Commands
```bash
cd frontend

# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build

# 빌드 결과 미리보기
npm run preview
```

## API Endpoints

### 지원자 관리
- `POST /api/applicants/` - 지원자 생성
- `GET /api/applicants/` - 지원자 목록 조회
- `GET /api/applicants/{id}` - 특정 지원자 조회
- `PATCH /api/applicants/{id}` - 지원자 정보 수정
- `DELETE /api/applicants/{id}` - 지원자 삭제

### 자기소개서 분석
- `POST /api/analysis/summarize` - 자기소개서 요약 (텍스트 직접 전달)
- `POST /api/analysis/keywords` - 키워드 추출 (텍스트 직접 전달)
- `POST /api/analysis/summarize/{applicant_id}` - 지원자 ID로 요약 (DB 조회)
- `POST /api/analysis/keywords/{applicant_id}` - 지원자 ID로 키워드 추출 (DB 조회)

## Project Structure

```
.
├── backend/              # FastAPI 백엔드
│   ├── app/
│   │   ├── api/              # API 라우터
│   │   │   ├── analysis.py   # 분석 API (요약, 키워드)
│   │   │   └── applicants.py # 지원자 CRUD API
│   │   ├── models/           # SQLModel 데이터 모델
│   │   │   └── applicant.py
│   │   ├── services/         # 비즈니스 로직
│   │   │   └── ollama_service.py  # Ollama 연동
│   │   ├── database.py       # DB 연결 및 세션 관리
│   │   └── main.py           # FastAPI 앱 엔트리포인트
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/            # React 프론트엔드
│   ├── src/
│   │   ├── components/  # React 컴포넌트
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css   # Tailwind CSS
│   ├── Dockerfile
│   ├── nginx.conf      # Nginx 설정
│   ├── package.json
│   └── vite.config.ts
│
├── scripts/            # 유틸리티 스크립트
│   ├── export-images.sh           # Docker 이미지 내보내기
│   ├── import-images.sh           # Docker 이미지 가져오기
│   ├── export-ollama-model.sh     # Ollama 모델 내보내기
│   ├── import-ollama-model.sh     # Ollama 모델 가져오기
│   ├── export-dependencies.sh     # 의존성 패키지 내보내기
│   ├── import-dependencies.sh     # 의존성 패키지 가져오기
│   └── full-export.sh             # 전체 프로젝트 내보내기
│
├── docker-compose.yml  # Docker Compose 설정
├── CLAUDE.md          # Claude Code 개발 가이드
└── README.md          # 프로젝트 문서
```

## 폐쇄망 이식

이 프로젝트는 사내 폐쇄망으로 이식 가능하도록 설계되었습니다.

### 전체 내보내기 (인터넷 연결 환경)
```bash
./scripts/full-export.sh
```

이 스크립트는 다음을 수행합니다:
1. 소스 코드 복사
2. Docker 이미지 내보내기 (backend, frontend, ollama, base images)
3. Ollama 모델 내보내기
4. Python/Node.js 의존성 패키지 내보내기
5. 설치 가이드 생성
6. 전체를 tar.gz로 압축

### 개별 내보내기/가져오기

**Docker 이미지:**
```bash
./scripts/export-images.sh  # 내보내기
./scripts/import-images.sh  # 가져오기
```

**Ollama 모델:**
```bash
./scripts/export-ollama-model.sh  # 내보내기
./scripts/import-ollama-model.sh  # 가져오기
```

**의존성 패키지:**
```bash
./scripts/export-dependencies.sh  # 내보내기
./scripts/import-dependencies.sh  # 가져오기
```

### 폐쇄망 설치
1. `export-package_*.tar.gz` 파일을 폐쇄망으로 복사
2. 압축 해제: `tar -xzf export-package_*.tar.gz`
3. `cd export-package_*/source`
4. `INSTALL.md` 파일 참고하여 설치

## Important Notes

### 환경 변수
- 백엔드의 `.env` 파일에서 Ollama URL, 데이터베이스 경로 설정 가능
- Docker Compose 사용 시 `docker-compose.yml`에서 환경 변수 관리

### 데이터 영속성
- Docker 볼륨을 사용하여 데이터베이스와 Ollama 모델 데이터 유지
- `docker-compose down -v` 실행 시 모든 데이터 삭제됨 (주의!)

### API 개발
- FastAPI의 자동 문서화 기능 활용: `/docs` (Swagger UI), `/redoc` (ReDoc)
- 새로운 API 추가 시 `backend/app/api/` 디렉토리에 라우터 파일 생성
- `main.py`에서 `app.include_router()` 호출하여 등록
