# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

채용 지원자 자기소개서 분석 시스템 - PostgreSQL에 저장된 지원자 자기소개서를 LLM으로 요약하고 키워드를 추출하는 분석 전용 API 서비스

### Core Features
1. **요약 API** - PostgreSQL에서 지원자 ID로 지원 동기, 경력, 기술을 조회하여 LLM으로 종합 요약 생성
2. **키워드 추출 API** - 지원자 정보에서 주요 키워드 추출
3. **면접 예상 질문 API** - 지원자 정보 기반 면접 예상 질문 10개 자동 생성

**중요**: 이 시스템은 **분석 전용**입니다. 지원자 데이터는 PostgreSQL에 이미 존재하며, CRUD 기능은 제공하지 않습니다.

## Tech Stack

### Backend
- **FastAPI** (Python) - Web framework with async support
- **SQLModel** - ORM combining SQLAlchemy + Pydantic
- **PostgreSQL 16** - Database (지원자 정보 저장, 읽기 전용)
- **Ollama** - LLM integration using llama3.2:1b model
- **httpx** - Async HTTP client for Ollama API calls
- **psycopg2-binary** - PostgreSQL driver

### Frontend
- **React 19** + **TypeScript**
- **Vite 7** - Build tool and dev server
- **Tailwind CSS 4** - Utility-first styling

## Architecture

### Database Schema
PostgreSQL `applicant_info` 테이블:
- `id` (BIGSERIAL PRIMARY KEY) - 지원자 ID
- `reason` (VARCHAR(4000)) - 지원 동기
- `experience` (VARCHAR(4000)) - 경력 및 경험
- `skill` (VARCHAR(4000)) - 기술 스택 및 역량

**폐쇄망 서버**: 테이블이 이미 생성되어 있어야 합니다
**개발/테스트 환경**: [init.sql](init.sql)로 테이블 생성 및 샘플 데이터 삽입 가능

### Request Flow
**Analysis by ID**: Client → FastAPI → PostgreSQL (SELECT applicant by ID) → Ollama Service → LLM → Response

### Key Architectural Patterns

#### Analysis-Only API
- PostgreSQL 데이터베이스는 **읽기 전용**으로 사용됨
- 지원자 조회 API 없음 (ID를 이미 알고 있다고 가정)
- 분석 API만 제공 (요약, 키워드 추출, 면접 예상 질문)
- FastAPI는 테이블을 생성하지 않음 (폐쇄망 서버에서는 테이블이 이미 존재)

#### Dependency Injection
- SQLModel `Session` is injected via FastAPI's `Depends(get_session)`
- Sessions are context-managed in [database.py](backend/app/database.py:16-19) with `yield`
- Ensures proper connection lifecycle management

#### Singleton Service Pattern
- `OllamaService` is instantiated as singleton: `ollama_service` in [ollama_service.py](backend/app/services/ollama_service.py:57)
- All API endpoints import and use the same instance
- Configuration loaded once from environment variables

#### API Router Organization
- [analysis.py](backend/app/api/analysis.py) - LLM-powered analysis endpoints (요약, 키워드 추출, 면접 예상 질문)
- Router registered in [main.py](backend/app/main.py:23) using `app.include_router()`

#### Model Structure
- **Table Model**: `Applicant` (SQLModel with `table=True`, 4 columns: id, reason, experience, skill)
- **Response Models**: `SummaryResponse`, `KeywordsResponse`, `InterviewQuestionsResponse` (분석 결과 응답용)
- No CRUD models (분석 전용)

## Development Commands

### Docker Development

**중요**: 이 프로젝트는 **폐쇄망 서버 배포**를 위해 설계되었습니다. docker-compose.yml은 backend와 frontend만 포함하며, PostgreSQL과 Ollama는 서버에 이미 실행 중이어야 합니다.

```bash
# 환경 변수 설정 (서버의 PostgreSQL, Ollama 정보)
cd backend
cp .env.example .env
vi .env  # OLLAMA_BASE_URL, DATABASE_URL 수정

# Backend + Frontend 빌드 및 실행
cd ..
docker-compose up -d --build

# 로그 확인
docker-compose logs -f
docker-compose logs -f backend  # specific service

# 코드 수정 후 재시작
docker-compose restart backend

# 전체 중지
docker-compose down
```

**Service URLs:**
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**환경 변수 (.env 파일):**
- `OLLAMA_BASE_URL`: 서버의 Ollama 컨테이너 주소 (예: http://ollama:11434)
- `OLLAMA_MODEL`: llama3.2:1b
- `DATABASE_URL`: 서버의 PostgreSQL 주소 (예: postgresql://admin:admin123@postgres:5432/applicants_db)

### Local Development (without Docker)

**Prerequisites:**
- Python 3.10+
- Node.js 18+
- PostgreSQL 16+ installed and running
- Ollama installed and running

**PostgreSQL Setup:**
```bash
# 1. PostgreSQL 서버가 실행 중인지 확인
pg_isready

# 2. 데이터베이스 생성
createdb -U postgres applicants_db

# 3. init.sql 실행하여 테이블 생성 및 샘플 데이터 삽입
psql -U postgres -d applicants_db -f init.sql

# 또는 직접 SQL 실행:
psql -U postgres -d applicants_db
# psql 내에서:
# \i init.sql
# \dt  -- 테이블 확인
# SELECT * FROM applicants;  -- 데이터 확인
```

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Configure DATABASE_URL for local PostgreSQL

# Run dev server with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install

# Dev server (hot module replacement enabled)
npm run dev

# Production build
npm run build

# Lint
npm run lint

# Preview production build
npm run preview
```

**Ollama:**
```bash
# Start Ollama server
ollama serve

# Download model (in another terminal)
ollama pull llama3.2:1b
```

## API Endpoints

### 자기소개서 분석 (분석 전용)
- `POST /api/analysis/summarize/{applicant_id}` - 지원자 ID로 요약
  - Path Parameter: `applicant_id` (int)
  - Response: `{ "applicant_id": int, "summary": string }`
  - 지원 동기, 경력, 기술을 종합하여 3-5개 핵심 문장으로 요약

- `POST /api/analysis/keywords/{applicant_id}` - 지원자 ID로 키워드 추출
  - Path Parameter: `applicant_id` (int)
  - Response: `{ "applicant_id": int, "keywords": string[] }`
  - 지원자 정보에서 중요한 키워드 5-10개 추출

- `POST /api/analysis/interview-questions/{applicant_id}` - 지원자 ID로 면접 예상 질문 생성
  - Path Parameter: `applicant_id` (int)
  - Response: `{ "applicant_id": int, "questions": string[] }`
  - 지원자 정보 기반 면접 예상 질문 10개 생성

**Note**: 지원자 조회 API는 없습니다. 분석 API 호출 시 지원자 ID를 이미 알고 있어야 합니다.

API 문서: http://localhost:8000/docs

## Project Structure

```
.
├── backend/              # FastAPI 백엔드
│   ├── app/
│   │   ├── api/              # API 라우터
│   │   │   └── analysis.py   # 분석 API (요약, 키워드, 면접질문)
│   │   ├── models/           # SQLModel 데이터 모델
│   │   │   └── applicant.py  # Applicant (테이블 모델, 4개 컬럼)
│   │   ├── services/         # 비즈니스 로직
│   │   │   └── ollama_service.py  # Ollama 연동 (3개 파라미터)
│   │   ├── database.py       # PostgreSQL 연결 및 세션 관리
│   │   └── main.py           # FastAPI 앱 엔트리포인트
│   ├── Dockerfile            # 일반 빌드용 (인터넷 필요)
│   ├── Dockerfile.offline    # 오프라인 빌드용 (python-packages/ 사용)
│   ├── requirements.txt
│   └── .env.example          # 환경 변수 템플릿
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
├── python-packages/    # 오프라인 Python 패키지 (준비 후 생성)
├── init.sql           # PostgreSQL 초기화 스크립트 (테이블 생성 + 샘플 데이터)
├── docker-compose.yml # Docker Compose 설정 (backend, frontend만)
├── SETUP-GUIDE.md     # 폐쇄망 배포 상세 가이드
├── DEPLOY.md          # 배포 및 문제 해결 가이드
├── CLAUDE.md          # Claude Code 개발 가이드
└── README.md          # 프로젝트 문서 (폐쇄망 배포 중심)
```

## 폐쇄망 배포

이 프로젝트는 **완전 폐쇄망 서버 배포**를 위해 설계되었습니다.

### 배포 전제 조건
서버에 이미 다음이 실행 중이어야 합니다:
- PostgreSQL (Docker 컨테이너)
- Ollama (Docker 컨테이너, llama3.2:1b 모델 포함)
- `applicants` 테이블 생성 완료

### 인터넷 환경 준비 (사전 작업)

```bash
# 1. 베이스 Docker 이미지 내보내기
docker pull python:3.11-slim && docker save -o python-3.11-slim.tar python:3.11-slim
docker pull node:20-alpine && docker save -o node-20-alpine.tar node:20-alpine
docker pull nginx:alpine && docker save -o nginx-alpine.tar nginx:alpine

# 2. Python 패키지 다운로드 (오프라인 설치용, Linux 서버용)
cd backend
pip download \
  --platform manylinux2014_x86_64 \
  --platform manylinux_2_17_x86_64 \
  --platform linux_x86_64 \
  --only-binary=:all: \
  --python-version 311 \
  -r requirements.txt \
  -d ../python-packages/
pip download --no-deps -r requirements.txt -d ../python-packages/

# 3. 전체 압축
cd ../..
tar -czf llmproject.tar.gz llmproject/
```

### 폐쇄망 서버 배포

```bash
# 1. 압축 해제
tar -xzf llmproject.tar.gz && cd llmproject

# 2. 베이스 이미지 로드
docker load -i python-3.11-slim.tar
docker load -i node-20-alpine.tar
docker load -i nginx-alpine.tar

# 3. 환경 변수 설정 (서버의 PostgreSQL, Ollama 정보)
cd backend
cp .env.example .env
vi .env  # OLLAMA_BASE_URL, DATABASE_URL 수정

# 4. 빌드 + 실행
cd ..
docker-compose up -d --build
```

**상세 가이드**: [SETUP-GUIDE.md](SETUP-GUIDE.md) 참조

## Important Development Notes

### Environment Configuration
- Backend: Configure via [.env](backend/.env.example) file
  - `OLLAMA_BASE_URL`: 서버의 Ollama 컨테이너 주소
    - 같은 네트워크: `http://ollama:11434`
    - 다른 네트워크: `http://172.17.0.1:11434` (IP 주소)
  - `OLLAMA_MODEL`: Model name (default: llama3.2:1b)
  - `DATABASE_URL`: 서버의 PostgreSQL 컨테이너 주소
    - 같은 네트워크: `postgresql://admin:admin123@postgres:5432/applicants_db`
    - 다른 네트워크: IP 주소 사용
- Docker: Environment variables loaded from `.env` file
- CORS: Currently allows http://localhost:5173 (Vite dev server) in [main.py](backend/app/main.py)

### Database Management
- **Analysis-Only**: 이 애플리케이션은 데이터를 읽기만 하며, 조회 API도 없음 (분석 API만 제공)
- **폐쇄망 서버**: `applicant_info` 테이블이 이미 존재해야 함 (id, reason, experience, skill)
- **개발/테스트 환경**: [init.sql](init.sql)로 테이블 생성 및 샘플 데이터 삽입 가능
  - 수동 실행: `psql -d applicants_db -f init.sql`
- FastAPI는 테이블을 생성하지 않음 (no lifespan events)
- **Migration strategy**: Manual SQL scripts (no Alembic configured)

### PostgreSQL Connection
- Connection pooling handled by SQLModel/SQLAlchemy
- Connection string format: `postgresql://user:password@host:port/dbname`
- psycopg2-binary required for PostgreSQL driver
- **폐쇄망 서버**: 서버의 기존 PostgreSQL 컨테이너에 연결 (Docker 네트워크 내)
- **로컬 개발 시**: PostgreSQL 서버가 실행 중이어야 하며, init.sql을 수동으로 실행해야 함

### LLM Integration
- Ollama API called via async `httpx.AsyncClient` with 120s timeout in [ollama_service.py](backend/app/services/ollama_service.py:23)
- Non-streaming mode (`"stream": False`) for simplicity
- Prompts are hardcoded in Korean in service methods
- All service methods accept 3 parameters: `reason`, `experience`, `skill`
- **폐쇄망 서버**: Ollama 컨테이너가 llama3.2:1b 모델과 함께 이미 실행 중이어야 함

### Adding New Features

**New Analysis Endpoint:**
1. Add method to `OllamaService` class in [ollama_service.py](backend/app/services/ollama_service.py)
2. Create endpoint in [analysis.py](backend/app/api/analysis.py)
3. Use dependency injection: `session: Session = Depends(get_session)`
4. Endpoint must be `async def` for LLM calls

**Modify Database Schema:**
1. Edit [init.sql](init.sql) to add/modify columns (개발/테스트용)
2. Update `Applicant` model in [applicant.py](backend/app/models/applicant.py)
3. Update all `OllamaService` methods if parameter changes are needed
4. **폐쇄망 서버**: 서버의 PostgreSQL에 직접 SQL 실행 필요
5. **Note**: No migration tool configured - manual SQL changes required

**Offline Package Installation (폐쇄망 배포):**
1. Backend uses [Dockerfile.offline](backend/Dockerfile.offline) for offline installation
2. Python packages from `python-packages/` directory (prepared in internet environment)
3. Frontend requires internet for npm install during build (또는 사전에 이미지 빌드 후 내보내기)
4. Build context in docker-compose.yml is project root (`.`) for accessing python-packages/
