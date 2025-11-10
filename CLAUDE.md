# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

채용 지원자 자기소개서 분석 및 RAG 기반 문서 검색 시스템

**핵심 기능:**
1. 지원자 분석 (요약, 키워드 추출, 면접 질문 생성)
2. RAG 문서 검색 (PDF/DOCX/TXT/XLSX 업로드 → Qdrant 벡터 DB → LLM 답변)
3. 자연어 SQL 변환 (질의 → SQL → DB 조회 → 결과 해석)
4. Intent & Few-shot 학습 (키워드 매칭 + LLM 분류, 질의 로그 → Few-shot 예제)

**배포 환경:** 폐쇄망 서버 (PostgreSQL, Ollama, Qdrant가 이미 실행 중)

**상세 문서:** [README.md](README.md), [DEPLOY.md](DEPLOY.md), [FEWSHOT_FEATURE_GUIDE.md](FEWSHOT_FEATURE_GUIDE.md)

## Tech Stack

- **Backend:** FastAPI, SQLModel, Qdrant, FastEmbed (ONNX-based, 778MB vs sentence-transformers 7.97GB)
- **Frontend:** React 19, TypeScript, Vite 7, Tailwind CSS 4
- **LLM:** Ollama (llama3.2:1b)
- **DB:** PostgreSQL 16 (지원자 정보, Intent, Query Logs, Few-shots)
- **Vector DB:** Qdrant (문서 임베딩)
- **Embedding Model:** `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (한국어 지원, 768차원)

## Development Commands

### 로컬 개발 (Docker 전체 스택)
```bash
# 전체 스택 시작 (PostgreSQL, Ollama, Qdrant 포함)
docker-compose -f docker-compose.dev.yml up -d

# Ollama 모델 다운로드 (최초 1회)
docker exec -it ollama ollama pull llama3.2:1b

# 로그 확인
docker-compose -f docker-compose.dev.yml logs -f backend

# 백엔드 재시작 (코드 변경 후)
docker-compose restart backend

# 중지
docker-compose -f docker-compose.dev.yml down
```

### 로컬 개발 (Python/Node 직접)
```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install && npm run dev
```

**참고:** 폐쇄망 배포는 [DEPLOY.md](DEPLOY.md) 참조 (FastEmbed 모델 다운로드, Docker 이미지 전송 등)

## Architecture

### 핵심 아키텍처 패턴

#### 1. Two-Tier Intent Classification ([query_router.py](backend/app/services/query_router.py))
질의를 3가지 유형으로 분류 (rag_search, sql_query, general):
- **Tier 1 (Fast)**: `intents` 테이블에서 키워드 매칭 (PostgreSQL `LIKE` 쿼리)
  - 1개 매칭 → 즉시 반환
  - 2+ 매칭 → LLM에 후보 전달하여 disambiguation
  - 0개 매칭 → Tier 2로 fallback
- **Tier 2 (Flexible)**: LLM 기반 분류 (Ollama llama3.2:1b)

**핵심 코드:**
```python
# backend/app/services/query_router.py
async def classify_intent_simple(self, query: str, session: Optional[Session]) -> QueryIntent:
    # 1. intents 테이블 키워드 매칭
    result = self._check_intent_table(query, session)
    if isinstance(result, QueryIntent):
        return result  # 1개만 매칭
    # 2. LLM 기반 분류 (fallback)
    return await self.classify_intent(query, intent_candidates=result)
```

#### 2. Few-Shot Integration Pattern
모든 서비스가 `_get_active_fewshots(session, intent_type)` 메서드를 구현하여 활성 예제를 프롬프트에 주입:
- [rag_service.py](backend/app/services/rag_service.py): RAG 검색 답변 개선
- [sql_agent.py](backend/app/services/sql_agent.py): SQL 쿼리 생성 개선
- [ollama_service.py](backend/app/services/ollama_service.py): 일반 대화 품질 개선

**핵심 플로우:**
```
User Query → QueryRouter (intent 분류) → Service (_get_active_fewshots) → LLM (프롬프트 + few-shots) → Response → query_logs 저장
```

관리 UI에서 `query_logs` → Few-shot 승격 → 다음 질의부터 자동 반영

#### 3. Singleton Service Pattern
모든 서비스는 모듈 레벨에서 인스턴스화 (FastAPI 라이프사이클과 독립):
```python
# backend/app/services/ollama_service.py
class OllamaService:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        # ...

ollama_service = OllamaService()  # 싱글톤

# backend/app/api/analysis.py
from app.services.ollama_service import ollama_service  # import로 재사용
```

#### 4. DB Session Management (Dependency Injection)
FastAPI `Depends(get_session)`으로 DB 세션 자동 관리:
```python
# backend/app/api/chat.py
@router.post("/")
async def chat(request: ChatRequest, session: Session = Depends(get_session)):
    # session은 자동으로 생성/종료
    intent = await query_router.classify_intent_simple(request.query, session)
```

### 데이터베이스 스키마 (PostgreSQL)
- `applicant_info`: 지원자 정보 (읽기 전용, CRUD 없음)
- `intents`: 키워드 → intent_type 매핑 (Two-tier 분류 Tier 1)
- `query_logs`: 모든 질의 자동 저장 (Few-shot 후보)
- `few_shots`: 승격된 Few-shot 예제 (LLM 프롬프트에 주입)
- `few_shot_audit`: 변경 이력 (PostgreSQL 트리거로 자동 기록)

상세 스키마: [init.sql](init.sql)

### 디렉토리 구조
```
backend/app/
├── api/              # API 엔드포인트
│   ├── analysis.py   # 지원자 분석 API
│   ├── chat.py       # RAG 채팅 API (QueryRouter 사용)
│   ├── upload.py     # 문서 업로드 API
│   ├── intent.py     # Intent 관리 API
│   ├── query_log.py  # Query Log 관리 API
│   └── fewshot.py    # Few-shot 관리 API
├── models/           # 데이터 모델 (SQLModel)
├── services/         # 비즈니스 로직 (싱글톤)
│   ├── ollama_service.py   # LLM 호출
│   ├── qdrant_service.py   # 벡터 DB 검색
│   ├── rag_service.py      # RAG 파이프라인
│   ├── query_router.py     # Intent 분류 (Two-tier)
│   └── sql_agent.py        # NL→SQL 변환
├── database.py       # DB 연결 및 세션 관리
└── main.py           # FastAPI 앱 및 라우터 등록
```

## Environment Variables

**필수 (.env):**
- `DATABASE_URL`: PostgreSQL 연결 (예: `postgresql://admin:admin123@postgres:5432/applicants_db`)
- `OLLAMA_BASE_URL`: Ollama API (예: `http://ollama:11434`)
- `OLLAMA_MODEL`: `llama3.2:1b`
- `QDRANT_URL`: Qdrant API (예: `http://qdrant:6333`)
- `FASTEMBED_CACHE_PATH`: FastEmbed 모델 캐시 디렉토리 (예: `/app/fastembed_cache`)

**선택:**
- `QDRANT_COLLECTION_NAME`: `documents` (default)
- `EMBEDDING_MODEL`: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (default)

## Development Workflow

### 코드 변경
```bash
# Hot reload (docker-compose.dev.yml 사용 시 자동 반영)
# backend/app/ 디렉토리는 볼륨 마운트되어 있음

# 환경 변수 변경: 재시작만
docker-compose restart backend

# 의존성 변경 (requirements.txt): 재빌드
docker-compose up -d --build backend
```

### DB 마이그레이션
1. SQL 파일 작성 (수동, Alembic 없음)
2. `psql`로 로컬 테스트
3. `init.sql` 업데이트 (새 설치 환경용)
4. 폐쇄망 서버: PostgreSQL 컨테이너에서 수동 실행

### API 테스트
- API 문서: http://localhost:8000/docs
- Intent 분류 디버깅: `POST /api/chat/classify {"query": "..."}`

## Adding Features

### 새 Intent Type 추가
1. **`QueryRouter`의 `QueryIntent` enum 확장** ([query_router.py](backend/app/services/query_router.py:12))
   ```python
   class QueryIntent(str, Enum):
       RAG_SEARCH = "rag_search"
       SQL_QUERY = "sql_query"
       GENERAL = "general"
       NEW_INTENT = "new_intent"  # 추가
   ```

2. **서비스 핸들러 생성** (예: `backend/app/services/new_service.py`)
   - 필수: `_get_active_fewshots(session, intent_type="new_intent")` 메서드 구현
   - Few-shots를 프롬프트에 주입하여 LLM 호출

3. **Chat API 라우팅 추가** ([chat.py](backend/app/api/chat.py))
   ```python
   elif intent == QueryIntent.NEW_INTENT:
       result = await new_service.handle(query, session)
   ```

4. **`intents` 테이블에 키워드 추가** (관리 UI 또는 SQL)
   ```sql
   INSERT INTO intents (keyword, intent_type, priority, description)
   VALUES ('새키워드', 'new_intent', 10, '새로운 의도');
   ```

5. **Few-shot 예제 추가** (관리 UI: Query Logs → 승격)

6. **테스트**: `POST /api/chat/classify {"query": "새키워드 포함 질문"}`

### 새 분석 API 추가
1. `OllamaService`에 메서드 추가 ([ollama_service.py](backend/app/services/ollama_service.py))
2. API 엔드포인트 추가 ([analysis.py](backend/app/api/analysis.py))
3. `main.py`에 라우터 자동 포함됨 (analysis_router 이미 등록)

## Troubleshooting

### 연결 오류
```bash
# PostgreSQL 연결 확인
docker exec postgres psql -U admin -d applicants_db -c "SELECT 1"

# Ollama 연결 확인
docker exec backend curl http://ollama:11434/api/version

# Qdrant 연결 확인
docker exec backend curl http://qdrant:6333/collections
```

### 네트워크 문제
```bash
docker network inspect dev-network
docker network connect dev-network backend
```

## Important Constraints

- **Read-Only Applicant DB**: `applicant_info` 테이블은 읽기 전용 (CRUD 없음, 분석만)
- **No Auto-Migration**: 테이블 생성 안 함 (폐쇄망 서버는 `init.sql` 사전 실행 필수)
- **Manual Few-shot Curation**: Query logs → 관리 UI 검토 → 승격 버튼 (자동 승격 없음)
- **Audit Trail**: PostgreSQL 트리거로 Few-shot 변경 이력 자동 기록
- **Korean-Only**: 모든 프롬프트 한국어 (다국어 지원 없음)
- **No Heavy Frameworks**: LangChain 없음 (커스텀 RAG), Alembic 없음 (수동 마이그레이션)
- **Offline Deployment**: `Dockerfile.offline` + 사전 다운로드된 패키지 사용 ([DEPLOY.md](DEPLOY.md))
- **Security**: SQL Agent는 패턴 매칭만 사용 (동적 SQL 실행 금지, SQL injection 방지)

## Quick Reference

### 자주 사용하는 명령어
```bash
# 개발 환경 시작/중지
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml down

# 로그 확인
docker-compose logs -f backend

# DB 접속
docker exec -it postgres psql -U admin -d applicants_db

# Ollama 테스트
docker exec backend curl -X POST http://ollama:11434/api/generate \
  -d '{"model":"llama3.2:1b","prompt":"안녕하세요","stream":false}'
```

### 디버깅 체크리스트
1. **Intent 분류 안됨**: `POST /api/chat/classify` → `intents` 테이블 키워드 추가
2. **LLM 응답 없음**: `docker logs ollama` → 모델 다운로드 확인
3. **RAG 답변 부정확**: Few-shot 예제 추가, Qdrant 문서 확인
4. **DB 연결 실패**: `.env` `DATABASE_URL` 확인, 네트워크 연결 확인
5. **임베딩 모델 로드 실패**: `FASTEMBED_CACHE_PATH` 볼륨 마운트 확인
