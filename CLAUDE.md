# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

채용 지원자 자기소개서 분석 및 RAG 기반 문서 검색 시스템 - PostgreSQL 지원자 분석과 Qdrant 벡터 DB를 활용한 문서 검색 통합 서비스

### Core Features

#### 지원자 분석 (기존)
1. **요약 API** - PostgreSQL에서 지원자 ID로 지원 동기, 경력, 기술을 조회하여 LLM으로 종합 요약 생성
2. **키워드 추출 API** - 지원자 정보에서 주요 키워드 추출
3. **면접 예상 질문 API** - 지원자 정보 기반 면접 예상 질문 10개 자동 생성

#### RAG 기반 채팅 (신규)
4. **문서 업로드** - PDF, DOCX, TXT, XLSX 파일 업로드 및 Qdrant 벡터 DB 저장
5. **RAG 검색** - 업로드된 문서에서 관련 정보를 검색하여 LLM으로 답변 생성
6. **자연어 SQL** - 자연어 질의를 SQL로 변환하여 데이터베이스 조회
7. **QueryRouter** - 사용자 질의 의도 자동 분류 (문서 검색 vs DB 쿼리 vs 일반 대화)

#### Intent & Few-shot 관리 (신규)
8. **Intent 관리** - 키워드 기반 의도 분류 (LLM 우회하여 빠른 응답)
9. **질의 로그** - 모든 사용자 질의 자동 저장 및 추적
10. **Few-shot 관리** - 질의 로그를 Few-shot 예제로 승격하여 LLM 프롬프트에 활용

## Tech Stack

### Backend
- **FastAPI** (Python) - Web framework with async support
- **SQLModel** - ORM combining SQLAlchemy + Pydantic
- **PostgreSQL 16** - Database (지원자 정보 저장, 읽기 전용)
- **Ollama** - LLM integration using llama3.2:1b model
- **httpx** - Async HTTP client for Ollama API calls
- **psycopg2-binary** - PostgreSQL driver
- **Qdrant** - Vector database for document embeddings (신규)
- **Sentence Transformers** - Korean text embedding (jhgan/ko-sroberta-multitask) (신규)
- **PyPDF2, python-docx, openpyxl** - Document text extraction (신규)

### Frontend
- **React 19** + **TypeScript**
- **Vite 7** - Build tool and dev server
- **Tailwind CSS 4** - Utility-first styling

## Architecture

### Database Schema

#### Applicant Info (기존)
PostgreSQL `applicant_info` 테이블:
- `id` (BIGSERIAL PRIMARY KEY) - 지원자 ID
- `reason` (VARCHAR(4000)) - 지원 동기
- `experience` (VARCHAR(4000)) - 경력 및 경험
- `skill` (VARCHAR(4000)) - 기술 스택 및 역량

#### Intent & Few-shot Tables (신규)

**intents** 테이블 - 키워드 기반 의도 매핑:
- `id` (SERIAL PRIMARY KEY)
- `keyword` (VARCHAR(200)) - 키워드 (예: "계약서", "지원자")
- `intent_type` (VARCHAR(100)) - 의도 타입 (rag_search, sql_query, general)
- `priority` (INTEGER) - 우선순위 (높을수록 먼저 매칭)
- `description` (VARCHAR(500))
- `created_at`, `updated_at` (TIMESTAMP)

**query_logs** 테이블 - 모든 사용자 질의 자동 저장:
- `id` (BIGSERIAL PRIMARY KEY)
- `query_text` (TEXT) - 질의 내용
- `detected_intent` (VARCHAR(100)) - 감지된 의도
- `response` (TEXT) - 응답 내용
- `is_converted_to_fewshot` (BOOLEAN) - Few-shot으로 승격 여부
- `created_at` (TIMESTAMP)

**few_shots** 테이블 - Few-shot 학습 예제:
- `id` (SERIAL PRIMARY KEY)
- `source_query_log_id` (BIGINT) - 원본 질의 로그 ID (FK to query_logs)
- `intent_type` (VARCHAR(100)) - 의도 타입
- `user_query` (TEXT) - 사용자 질의 예제
- `expected_response` (TEXT) - 예상 응답
- `is_active` (BOOLEAN) - 활성화 여부 (프롬프트 포함 여부)
- `created_at`, `updated_at` (TIMESTAMP)

**few_shot_audit** 테이블 - Few-shot 변경 이력 (트리거 자동 생성):
- `id` (SERIAL PRIMARY KEY)
- `few_shot_id` (INTEGER) - FK to few_shots
- `action` (VARCHAR(20)) - INSERT, UPDATE, DELETE
- `old_value` (JSONB) - 변경 전 값
- `new_value` (JSONB) - 변경 후 값
- `changed_by` (VARCHAR(100)) - 변경자
- `created_at` (TIMESTAMP)

**폐쇄망 서버**: 모든 테이블이 이미 생성되어 있어야 합니다
**개발/테스트 환경**: [init.sql](init.sql)로 모든 테이블 생성 및 샘플 데이터 삽입 가능

### Request Flow

#### 1. 지원자 분석 (기존)
**Analysis by ID**: Client → FastAPI → PostgreSQL (SELECT applicant by ID) → Ollama Service → LLM → Response

#### 2. 문서 업로드 (신규)
**Upload**: Client → Upload API → TextExtractor → Qdrant Service → Embedding Model → Qdrant Vector DB

#### 3. RAG 채팅 (신규)
**Chat with RAG**:
```
User Query → ChatAPI → QueryRouter (Intent 분류)
                           ↓
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                  ↓
   RAG Search         SQL Agent         General Chat
        ↓                  ↓                  ↓
   Qdrant Search    Natural Language      Ollama LLM
        ↓              to SQL                 ↓
   Top-K Docs            ↓               Direct Answer
        ↓           PostgreSQL
   Context Build         ↓
        ↓           Result Interpretation
   Ollama LLM            ↓
        ↓           Natural Language
   Answer + Sources      ↓
        └──────────────────┴──────────────────┘
                           ↓
                    ChatResponse
```

#### 4. Intent & Few-shot Workflow (신규)
**Intent-based Classification**:
```
User Query → Check intents table (keyword matching)
                ↓
         Match found? ─Yes→ Use matched intent_type (bypass LLM)
                ↓
               No
                ↓
           LLM-based classification
```

**Few-shot Learning Workflow**:
```
1. User Query → Auto-save to query_logs table
2. Admin reviews query_logs in management UI
3. Admin clicks "승격" button on selected query
4. Query converted to few_shots table with:
   - source_query_log_id (links back to original)
   - intent_type, user_query, expected_response
   - is_active = true (included in prompts)
5. When generating LLM prompts:
   - Fetch all few_shots where is_active = true
   - Include as examples in prompt
6. Admin can toggle is_active or delete few_shot
   - Deleting resets query_log.is_converted_to_fewshot flag
```

### Key Architectural Patterns

#### Analysis-Only API (기존)
- PostgreSQL 데이터베이스는 **읽기 전용**으로 사용됨
- 지원자 조회 API 없음 (ID를 이미 알고 있다고 가정)
- 분석 API만 제공 (요약, 키워드 추출, 면접 예상 질문)
- FastAPI는 테이블을 생성하지 않음 (폐쇄망 서버에서는 테이블이 이미 존재)

#### RAG Integration Pattern (신규)
- **QueryRouter**: 사용자 질의의 의도를 분류하여 적절한 서비스로 라우팅
  - RAG Search: 문서 내용 검색이 필요한 질문
  - SQL Query: 데이터베이스 조회가 필요한 질문
  - General: 일반 대화
- **Vector Search**: Qdrant에서 의미 기반 유사도 검색 (코사인 유사도)
- **Text Extraction**: 다양한 파일 형식 (PDF, DOCX, TXT, XLSX)에서 텍스트 추출
- **Embedding Model**: 한국어 지원 Sentence Transformer (jhgan/ko-sroberta-multitask)

#### Intent & Few-shot Pattern (신규)
- **Two-tier Intent Classification**:
  - Tier 1: Keyword-based matching (fast, deterministic, bypasses LLM)
  - Tier 2: LLM-based classification (fallback for unmatched queries)
- **Query Logging**: All user queries automatically saved to `query_logs` table
- **Manual Curation**: Admins review logs and promote valuable queries to few-shots
- **Active Learning**: Only `is_active=true` few-shots included in prompts
- **Audit Trail**: PostgreSQL triggers automatically log all few-shot changes to `few_shot_audit`
- **Bidirectional Updates**: Deleting few-shot resets `query_log.is_converted_to_fewshot` flag

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

**로컬 개발 환경**: 전체 스택(PostgreSQL, Ollama, Qdrant 포함)을 로컬에서 실행하려면 `docker-compose.dev.yml`을 사용하세요:

```bash
# 전체 스택 시작 (모든 서비스 포함)
docker-compose -f docker-compose.dev.yml up -d

# Ollama 모델 다운로드 (최초 1회)
docker exec -it ollama ollama pull llama3.2:1b

# 상세 가이드는 LOCAL-DEV-GUIDE.md 참조
```

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

### 1. 자기소개서 분석 (기존)
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

### 2. 문서 업로드 (신규)
- `POST /api/upload/` - 문서 파일 업로드 및 벡터 DB 저장
  - Request: `multipart/form-data` with file
  - Supported formats: PDF, DOCX, TXT, XLSX
  - Response: `{ "message": string, "filename": string, "doc_id": string, "text_length": int }`
  - 파일을 업로드하면 텍스트 추출 후 Qdrant에 임베딩하여 저장

- `GET /api/upload/stats` - 업로드된 문서 통계
  - Response: `{ "total_documents": int, "collection_name": string }`

### 3. RAG 채팅 (신규)
- `POST /api/chat/` - 자연어 질의 응답 (QueryRouter 자동 라우팅)
  - Request: `{ "query": string }`
  - Response: `{ "answer": string, "intent": string, "sources": [], "sql": string, "results": [] }`
  - QueryRouter가 자동으로 의도 분류:
    - `rag_search`: 문서 검색 기반 답변 (sources 포함)
    - `sql_query`: DB 쿼리 기반 답변 (sql, results 포함)
    - `general`: 일반 대화

- `POST /api/chat/classify` - 질의 의도 분류 (디버깅용)
  - Request: `{ "query": string }`
  - Response: `{ "query": string, "intent_simple": string, "intent_llm": string }`
  - 규칙 기반과 LLM 기반 분류 결과 비교

### 4. Intent 관리 (신규)
- `GET /api/intent/` - 모든 Intent 목록 조회
- `GET /api/intent/{id}` - 특정 Intent 조회
- `POST /api/intent/` - Intent 생성
  - Request: `{ "keyword": string, "intent_type": string, "priority": int, "description": string }`
- `PUT /api/intent/{id}` - Intent 수정
- `DELETE /api/intent/{id}` - Intent 삭제

### 5. 질의 로그 관리 (신규)
- `GET /api/query-logs/` - 질의 로그 목록 조회 (필터링 가능)
  - Query params: `skip`, `limit`, `intent`, `converted_only`, `search`
- `POST /api/query-logs/` - 질의 로그 생성 (자동 호출용)
- `DELETE /api/query-logs/{id}` - 질의 로그 삭제
- `POST /api/query-logs/convert-to-fewshot` - 질의 로그를 Few-shot으로 승격
  - Request: `{ "query_log_id": int, "intent_type": string, "expected_response": string, "is_active": bool }`
  - 자동으로 `is_converted_to_fewshot` 플래그 설정
- `GET /api/query-logs/stats/summary` - 질의 로그 통계 (총 개수, 변환율, Intent별 분포)

### 6. Few-shot 관리 (신규)
- `GET /api/fewshot/` - Few-shot 목록 조회 (필터링 가능)
  - Query params: `intent_type`, `is_active`
- `GET /api/fewshot/{id}` - 특정 Few-shot 조회
- `POST /api/fewshot/` - Few-shot 생성
  - Request: `{ "source_query_log_id": int, "intent_type": string, "user_query": string, "expected_response": string, "is_active": bool }`
- `PUT /api/fewshot/{id}` - Few-shot 수정 (is_active 토글 가능)
- `DELETE /api/fewshot/{id}` - Few-shot 삭제
  - 자동으로 연결된 query_log의 `is_converted_to_fewshot` 플래그를 false로 리셋
- `GET /api/fewshot/audit/` - Few-shot 변경 이력 조회
- `GET /api/fewshot/audit/{few_shot_id}` - 특정 Few-shot의 변경 이력

API 문서: http://localhost:8000/docs

## Project Structure

```
.
├── backend/              # FastAPI 백엔드
│   ├── app/
│   │   ├── api/              # API 라우터
│   │   │   ├── analysis.py   # 분석 API (요약, 키워드, 면접질문) - 기존
│   │   │   ├── chat.py       # RAG 채팅 API (QueryRouter 라우팅) - 신규
│   │   │   ├── upload.py     # 문서 업로드 API - 신규
│   │   │   ├── intent.py     # Intent 관리 CRUD API - 신규
│   │   │   ├── query_log.py  # 질의 로그 관리 API - 신규
│   │   │   └── fewshot.py    # Few-shot 관리 CRUD API - 신규
│   │   ├── models/           # Pydantic/SQLModel 데이터 모델
│   │   │   ├── applicant.py  # Applicant (테이블 모델, 4개 컬럼) - 기존
│   │   │   ├── chat.py       # 채팅 요청/응답 모델 - 신규
│   │   │   ├── query_log.py  # QueryLog (질의 로그 테이블) - 신규
│   │   │   └── few_shot.py   # Intent, FewShot, FewShotAudit 모델 - 신규
│   │   ├── services/         # 비즈니스 로직
│   │   │   ├── ollama_service.py  # Ollama LLM 연동 - 기존
│   │   │   ├── qdrant_service.py  # Qdrant 벡터 DB 연동 - 신규
│   │   │   ├── rag_service.py     # RAG 검색 및 답변 생성 - 신규
│   │   │   ├── query_router.py    # Intent 분류 (RAG/SQL/General) - 신규
│   │   │   └── sql_agent.py       # 자연어 → SQL 변환 및 실행 - 신규
│   │   ├── utils/            # 유틸리티
│   │   │   └── text_extractor.py  # 파일 텍스트 추출 (PDF, DOCX, TXT, XLSX) - 신규
│   │   ├── database.py       # PostgreSQL 연결 및 세션 관리
│   │   └── main.py           # FastAPI 앱 엔트리포인트
│   ├── Dockerfile            # 일반 빌드용 (인터넷 필요)
│   ├── Dockerfile.offline    # 오프라인 빌드용 (python-packages/ 사용)
│   ├── requirements.txt      # 의존성 (RAG 패키지 추가됨)
│   └── .env.example          # 환경 변수 템플릿 (Qdrant 설정 추가)
│
├── frontend/            # React 프론트엔드
│   ├── src/
│   │   ├── components/  # React 컴포넌트
│   │   │   ├── IntentManagement.tsx      # Intent 관리 UI - 신규
│   │   │   ├── QueryLogManagement.tsx    # 질의 로그 관리 UI - 신규
│   │   │   └── FewShotManagement.tsx     # Few-shot 관리 UI - 신규
│   │   ├── App.tsx      # 메인 앱 (3 탭: Intent, QueryLog, FewShot)
│   │   ├── main.tsx
│   │   └── index.css   # Tailwind CSS
│   ├── Dockerfile
│   ├── nginx.conf      # Nginx 설정
│   ├── package.json
│   └── vite.config.ts
│
├── migrations/             # 데이터베이스 마이그레이션 스크립트
│   ├── 001_create_fewshot_tables.sql  # 초기 Few-shot 테이블 생성
│   └── 002_update_fewshot_to_querylog.sql  # QueryLog 워크플로우 전환
├── python-packages/        # 오프라인 Python 패키지 (준비 후 생성)
├── init.sql               # PostgreSQL 초기화 스크립트 (모든 테이블 + 샘플 데이터)
├── docker-compose.yml     # Docker Compose 설정 (backend, frontend만 - 폐쇄망용)
├── docker-compose.dev.yml # Docker Compose 설정 (전체 스택 - 로컬 개발용)
├── SETUP-GUIDE.md         # 폐쇄망 배포 상세 가이드
├── LOCAL-DEV-GUIDE.md     # 로컬 개발 환경 가이드
├── DEPLOY.md              # 배포 및 문제 해결 가이드
├── FEWSHOT_FEATURE_GUIDE.md  # Few-shot 기능 사용 가이드
├── RAG_IMPLEMENTATION.md  # RAG 기능 구현 보고서
├── CLAUDE.md              # Claude Code 개발 가이드
└── README.md              # 프로젝트 문서 (폐쇄망 배포 중심)
```

## 폐쇄망 배포

이 프로젝트는 **완전 폐쇄망 서버 배포**를 위해 설계되었습니다.

### 배포 전제 조건
서버에 이미 다음이 실행 중이어야 합니다:
- **PostgreSQL** (Docker 컨테이너) - 지원자 정보 저장
- **Ollama** (Docker 컨테이너, llama3.2:1b 모델 포함) - LLM 추론
- **Qdrant** (Docker 컨테이너) - 벡터 DB (RAG용, 신규)
- `applicant_info` 테이블 생성 완료

**Qdrant 설치 (서버에서)**:
```bash
docker run -d --name qdrant \
  -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```

### 인터넷 환경 준비 (사전 작업)

```bash
# 1. 베이스 Docker 이미지 내보내기 (Linux AMD64용)
docker pull --platform linux/amd64 python:3.11-slim && docker save -o python-3.11-slim.tar python:3.11-slim
docker pull --platform linux/amd64 node:20-alpine && docker save -o node-20-alpine.tar node:20-alpine
docker pull --platform linux/amd64 nginx:alpine && docker save -o nginx-alpine.tar nginx:alpine

# 2. Python 패키지 다운로드 (오프라인 설치용, Linux 서버용)
# 프로젝트 루트에서 실행
# 맥/윈도우에서도 Linux용 패키지를 다운로드하기 위해 --platform 사용
mkdir -p python-packages
docker run --rm --platform linux/amd64 \
  -v $(pwd)/backend:/workspace/backend \
  -v $(pwd)/python-packages:/workspace/python-packages \
  -w /workspace/backend \
  python:3.11-slim \
  pip download -r requirements.txt -d /workspace/python-packages/

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
- **Analysis-Only**: 이 애플리케이션은 지원자 데이터를 읽기만 하며, 조회 API도 없음 (분석 API만 제공)
- **폐쇄망 서버**: 모든 테이블이 이미 존재해야 함
  - `applicant_info` (id, reason, experience, skill)
  - `intents`, `query_logs`, `few_shots`, `few_shot_audit`
- **개발/테스트 환경**: [init.sql](init.sql)로 모든 테이블 생성 및 샘플 데이터 삽입 가능
  - 수동 실행: `psql -d applicants_db -f init.sql`
- FastAPI는 테이블을 생성하지 않음 (no lifespan events)
- **Migration strategy**: Manual SQL scripts in `migrations/` directory (no Alembic configured)
  - `001_create_fewshot_tables.sql` - 초기 Intent/Few-shot 테이블
  - `002_update_fewshot_to_querylog.sql` - QueryLog 워크플로우 전환
  - 실행 방법: `psql -d applicants_db -f migrations/002_update_fewshot_to_querylog.sql`

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

### RAG & Embedding Configuration
- **Embedding Model**: Sentence Transformers (default: `jhgan/ko-sroberta-multitask`)
  - Vector dimension: 768
  - Supports Korean language
  - Models are auto-downloaded on first run (or can be pre-cached for offline)
- **Vector Database**: Qdrant
  - Collection name: configurable via `QDRANT_COLLECTION_NAME` env var
  - Distance metric: Cosine similarity (default)
  - Auto-creates collection on startup if not exists
- **Changing Models**: See [EMBEDDING_MODEL_GUIDE.md](EMBEDDING_MODEL_GUIDE.md) for detailed instructions
  - How to change embedding model
  - How to change vector dimension
  - Performance optimization tips
  - Troubleshooting guide

### Intent & Few-shot Workflow
- **Intent Usage**: Pre-emptive keyword-based intent detection
  - When user query arrives, check `intents` table first (keyword matching)
  - If matched, use that `intent_type` directly (bypasses LLM)
  - If no match, fall back to LLM-based classification
  - Higher priority intents are checked first
- **Few-shot Usage**: Manual curation of valuable examples
  - All user queries automatically logged to `query_logs` table
  - Admin reviews logs in management UI (http://localhost)
  - Admin clicks "승격" button to convert valuable queries to few-shots
  - Only `is_active=true` few-shots are included in LLM prompts
  - Admin can toggle `is_active` or delete few-shots as needed
  - Deleting few-shot automatically resets `query_log.is_converted_to_fewshot` flag
- **Audit Trail**: All few-shot changes automatically logged via PostgreSQL triggers
  - Triggers execute on INSERT, UPDATE, DELETE
  - Old/new values stored as JSONB in `few_shot_audit` table
  - See [FEWSHOT_FEATURE_GUIDE.md](FEWSHOT_FEATURE_GUIDE.md) for detailed usage

### Adding New Features

**New Analysis Endpoint:**
1. Add method to `OllamaService` class in [ollama_service.py](backend/app/services/ollama_service.py)
2. Create endpoint in [analysis.py](backend/app/api/analysis.py)
3. Use dependency injection: `session: Session = Depends(get_session)`
4. Endpoint must be `async def` for LLM calls

**Modify Database Schema:**
1. Edit [init.sql](init.sql) to add/modify columns (개발/테스트용)
2. Update `Applicant` model in [applicant.py](backend/app/models/applicant.py)
   - Use `sa_column=Column(String(length))` for VARCHAR columns to ensure proper SQLAlchemy mapping
   - Example: `Field(default=None, sa_column=Column(String(4000)))`
3. Update all `OllamaService` methods if parameter changes are needed
4. **폐쇄망 서버**: 서버의 PostgreSQL에 직접 SQL 실행 필요
5. **Note**: No migration tool configured - manual SQL changes required

**Offline Package Installation (폐쇄망 배포):**
1. Backend uses [Dockerfile.offline](backend/Dockerfile.offline) for offline installation
2. Python packages from `python-packages/` directory (prepared in internet environment)
3. Frontend requires internet for npm install during build (또는 사전에 이미지 빌드 후 내보내기)
4. Build context in docker-compose.yml is project root (`.`) for accessing python-packages/

## Troubleshooting

### 500 Error on Analysis API

**Common Causes:**
1. **Database Connection Failure**
   - Symptom: `sqlalchemy.exc.OperationalError: connection refused`
   - Solution: Check `DATABASE_URL` in `.env` - must use container name or IP, NOT `localhost` when running in Docker
   - Verify: `docker exec backend ping postgres-container-name`

2. **Ollama Connection Failure**
   - Symptom: `httpx.ConnectError` or timeout errors
   - Solution: Check `OLLAMA_BASE_URL` in `.env` - must use container name or IP, NOT `localhost`
   - Verify: `docker exec backend curl http://ollama:11434/api/version`

3. **Empty Data Retrieved from Database**
   - Symptom: 200 response but summary/keywords are empty or generic
   - Debug: Add logging in [analysis.py](backend/app/api/analysis.py) to check data lengths
   - Check: Verify table name is `applicant_info` and columns are `reason`, `experience`, `skill`
   - Verify data exists: `docker exec postgres-container psql -U admin -d applicants_db -c "SELECT id, length(reason), length(experience), length(skill) FROM applicant_info;"`

### Docker Network Issues

**Container cannot connect to PostgreSQL/Ollama:**
- Containers must be on the same Docker network OR use host IP
- Check network: `docker network inspect network-name`
- Connect to network: `docker network connect network-name backend`

### Code Changes Without Rebuilding

**When you only modify Python/JavaScript files:**
```bash
# Copy modified files to running container (no package changes)
docker cp backend/app/models/applicant.py backend:/app/app/models/
docker cp backend/app/api/analysis.py backend:/app/app/api/

# Restart container
docker-compose restart backend
```

**Note:** Only works if no new packages added to requirements.txt
