# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

채용 지원자 자기소개서 분석 시스템 - PostgreSQL에 저장된 지원자 자기소개서를 LLM으로 요약하고 키워드를 추출하는 분석 전용 API 서비스

### Core Features
1. **요약 API** - PostgreSQL에서 지원자 ID로 자기소개서를 조회하여 LLM으로 요약 생성
2. **키워드 추출 API** - 지원자 ID로 자기소개서에서 주요 키워드 추출

**중요**: 이 시스템은 **분석 전용**입니다. 지원자 데이터는 PostgreSQL에 이미 존재하며, 조회/생성/수정/삭제 기능은 제공하지 않습니다.

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
PostgreSQL `applicants` 테이블:
- `id` (SERIAL PRIMARY KEY) - 지원자 ID
- `content` (TEXT NOT NULL) - 자기소개서 내용

**Docker 환경**: [init.sql](init.sql)에서 Docker Compose 시작 시 자동 생성
**로컬 환경**: 수동으로 `init.sql` 실행 필요 (아래 참조)

### Request Flow
**Analysis by ID**: Client → FastAPI → PostgreSQL (SELECT applicant by ID) → Ollama Service → LLM → Response

### Key Architectural Patterns

#### Analysis-Only API
- PostgreSQL 데이터베이스는 **읽기 전용**으로 사용됨
- 지원자 조회 API 없음 (ID를 이미 알고 있다고 가정)
- 분석 API만 제공 (요약, 키워드 추출)
- FastAPI는 테이블을 생성하지 않음 (init.sql이 담당)

#### Dependency Injection
- SQLModel `Session` is injected via FastAPI's `Depends(get_session)`
- Sessions are context-managed in [database.py](backend/app/database.py:16-19) with `yield`
- Ensures proper connection lifecycle management

#### Singleton Service Pattern
- `OllamaService` is instantiated as singleton: `ollama_service` in [ollama_service.py](backend/app/services/ollama_service.py:57)
- All API endpoints import and use the same instance
- Configuration loaded once from environment variables

#### API Router Organization
- [analysis.py](backend/app/api/analysis.py) - LLM-powered analysis endpoints (요약, 키워드 추출)
- Router registered in [main.py](backend/app/main.py:23) using `app.include_router()`

#### Model Structure
- **Table Model**: `Applicant` (SQLModel with `table=True`, 2 columns: id, content)
- **Response Models**: `SummaryResponse`, `KeywordsResponse` (분석 결과 응답용)
- No CRUD models (분석 전용)

## Development Commands

### Docker Development (권장)

```bash
# Start all services (postgres, backend, frontend, ollama)
docker-compose up -d

# PostgreSQL은 init.sql로 자동 초기화됨 (applicants 테이블 + 샘플 데이터)

# Download Ollama model (required on first run)
docker exec ollama ollama pull llama3.2:1b

# View logs
docker-compose logs -f
docker-compose logs -f backend  # specific service
docker-compose logs -f postgres  # database logs

# Restart after code changes
docker-compose restart backend

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes database)
docker-compose down -v
```

**Service URLs:**
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Ollama: http://localhost:11434

**Default PostgreSQL Credentials:**
- Database: `applicants_db`
- User: `admin`
- Password: `admin123`

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

- `POST /api/analysis/keywords/{applicant_id}` - 지원자 ID로 키워드 추출
  - Path Parameter: `applicant_id` (int)
  - Response: `{ "applicant_id": int, "keywords": string[] }`

**Note**: 지원자 조회 API는 없습니다. 분석 API 호출 시 지원자 ID를 이미 알고 있어야 합니다.

API 문서: http://localhost:8000/docs

## Project Structure

```
.
├── backend/              # FastAPI 백엔드
│   ├── app/
│   │   ├── api/              # API 라우터
│   │   │   └── analysis.py   # 분석 API (요약, 키워드)
│   │   ├── models/           # SQLModel 데이터 모델
│   │   │   └── applicant.py  # Applicant (테이블 모델만)
│   │   ├── services/         # 비즈니스 로직
│   │   │   └── ollama_service.py  # Ollama 연동
│   │   ├── database.py       # PostgreSQL 연결 및 세션 관리
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
├── init.sql           # PostgreSQL 초기화 스크립트 (테이블 생성 + 샘플 데이터)
├── docker-compose.yml # Docker Compose 설정 (postgres, ollama, backend, frontend)
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
2. Docker 이미지 내보내기 (backend, frontend, ollama, postgres, base images)
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

## Important Development Notes

### Environment Configuration
- Backend: Configure via [.env](backend/.env.example) file
  - `OLLAMA_BASE_URL`: Ollama API endpoint (default: http://localhost:11434)
  - `OLLAMA_MODEL`: Model name (default: llama3.2:1b)
  - `DATABASE_URL`: PostgreSQL connection string
    - Docker: `postgresql://admin:admin123@postgres:5432/applicants_db`
    - Local: `postgresql://admin:admin123@localhost:5432/applicants_db`
- Docker: Environment variables set in [docker-compose.yml](docker-compose.yml)
- CORS: Currently allows http://localhost:5173 (Vite dev server) in [main.py](backend/app/main.py)

### Database Management
- **Analysis-Only**: 이 애플리케이션은 데이터를 읽기만 하고 조회 API도 없음
- **Docker**: [init.sql](init.sql)이 PostgreSQL 컨테이너 시작 시 자동 실행됨
- **Local**: `psql -d applicants_db -f init.sql` 명령으로 수동 실행 필요
- Sample data included in init.sql for testing
- FastAPI does NOT auto-create tables (no lifespan events)
- **Migration strategy**: Manual SQL scripts (no Alembic configured)
- Reset database: `docker-compose down -v && docker-compose up -d`

### PostgreSQL Connection
- Connection pooling handled by SQLModel/SQLAlchemy
- Connection string format: `postgresql://user:password@host:port/dbname`
- psycopg2-binary required for PostgreSQL driver
- **로컬 개발 시**: PostgreSQL 서버가 실행 중이어야 하며, init.sql을 수동으로 실행해야 함

### LLM Integration
- Ollama API called via async `httpx.AsyncClient` with 120s timeout in [ollama_service.py](backend/app/services/ollama_service.py:23)
- Non-streaming mode (`"stream": False`) for simplicity
- Prompts are hardcoded in Korean in service methods
- Model must be pulled before first use: `ollama pull llama3.2:1b`

### Adding New Features

**New Analysis Endpoint:**
1. Add method to `OllamaService` class in [ollama_service.py](backend/app/services/ollama_service.py)
2. Create endpoint in [analysis.py](backend/app/api/analysis.py)
3. Use dependency injection: `session: Session = Depends(get_session)`
4. Endpoint must be `async def` for LLM calls

**Modify Database Schema:**
1. Edit [init.sql](init.sql) to add/modify columns
2. Update `Applicant` model in [applicant.py](backend/app/models/applicant.py)
3. **Docker**: `docker-compose down -v && docker-compose up -d` (자동 재생성)
4. **Local**: Drop and recreate database, then run `psql -d applicants_db -f init.sql`
5. **Note**: No migration tool configured - manual SQL changes required
