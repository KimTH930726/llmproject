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

## Tech Stack

- **Backend:** FastAPI, SQLModel, httpx, psycopg2, Qdrant, Sentence Transformers
- **Frontend:** React 19, TypeScript, Vite 7, Tailwind CSS 4
- **LLM:** Ollama (llama3.2:1b)
- **DB:** PostgreSQL 16 (지원자 정보, Intent, Query Logs, Few-shots)
- **Vector DB:** Qdrant (문서 임베딩)

## Development Commands

### Docker (로컬 전체 스택)
```bash
# 전체 스택 시작 (PostgreSQL, Ollama, Qdrant 포함)
docker-compose -f docker-compose.dev.yml up -d

# Ollama 모델 다운로드 (최초 1회)
docker exec -it ollama ollama pull llama3.2:1b

# 로그 확인
docker-compose -f docker-compose.dev.yml logs -f backend

# 중지
docker-compose -f docker-compose.dev.yml down
```

### 로컬 개발 (Docker 없이)
```bash
# PostgreSQL 초기화
createdb -U postgres applicants_db
psql -U postgres -d applicants_db -f init.sql

# Qdrant 시작
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant:latest

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # DATABASE_URL, OLLAMA_BASE_URL, QDRANT_URL 설정
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

### 폐쇄망 배포

**전제 조건 (폐쇄망 서버에 이미 실행 중):**
- Docker & Docker Compose
- PostgreSQL (applicant_info, intents, query_logs, few_shots, few_shot_audit 테이블)
- Ollama (llama3.2:1b 모델)
- Qdrant

**임베딩 모델 개선 (2024-11-09):**
- ❌ 이전: sentence-transformers → 7.97GB
- ✅ 현재: FastEmbed (ONNX Runtime) → 778MB (**90% 감소!**)
- 다국어 모델: `paraphrase-multilingual-mpnet-base-v2` (한국어 포함, 768차원)

#### 배포 방식

| 방식 | 파일 크기 | 폐쇄망 작업 | 권장 상황 |
|------|----------|-----------|---------|
| **A. 빌드 이미지 전송** | **870MB** | 이미지 로드만 | 일반적인 경우 (빠름) |
| B. 베이스+패키지 전송 | 825MB | 빌드 5-10분 | 디버깅/보안검증 필요 시 |

---

#### 방식 A: 빌드 이미지 전송 (권장)

##### 1단계: 인터넷 환경에서 준비
```bash
cd /path/to/llmproject

# Linux AMD64용 빌드 (맥/윈도우도 --platform 필수)
docker build --platform linux/amd64 -t llmproject-backend:latest -f backend/Dockerfile backend/
docker build --platform linux/amd64 -t llmproject-frontend:latest -f frontend/Dockerfile frontend/

# 이미지 저장
docker save -o llmproject-backend.tar llmproject-backend:latest    # 767MB
docker save -o llmproject-frontend.tar llmproject-frontend:latest  # 50MB

# 프로젝트 코드 압축
cd ..
tar -czf llmproject-code.tar.gz \
  --exclude='llmproject/node_modules' \
  --exclude='llmproject/backend/__pycache__' \
  --exclude='llmproject/frontend/dist' \
  --exclude='llmproject/*.tar' \
  llmproject/                                                        # 50MB

# 총 3개 파일 ~870MB
```

##### 2단계: 폐쇄망 서버로 전송
USB나 내부망으로 3개 파일 복사

##### 3단계: 폐쇄망 서버에서 배포
```bash
# 이미지 로드
docker load -i llmproject-backend.tar
docker load -i llmproject-frontend.tar

# 프로젝트 압축 해제
tar -xzf llmproject-code.tar.gz
cd llmproject

# 환경 변수 설정 (기존 서비스 연결)
cat > backend/.env << 'EOF'
DATABASE_URL=postgresql://admin:admin123@postgres-container:5432/applicants_db
OLLAMA_BASE_URL=http://ollama-container:11434
OLLAMA_MODEL=llama3.2:1b
QDRANT_URL=http://qdrant-container:6333
EOF

# docker-compose.yml 수정 (build → image)
# vi docker-compose.yml에서 다음과 같이 수정:
#
# backend:
#   image: llmproject-backend:latest  # 추가
#   # build: ...  # 주석 처리
#
# frontend:
#   image: llmproject-frontend:latest  # 추가
#   # build: ...  # 주석 처리

# 실행
docker-compose up -d

# 확인
docker-compose logs -f backend
curl http://localhost:8000/docs  # Backend API
curl http://localhost/           # Frontend
```

---

#### 방식 B: 베이스+패키지 전송 (디버깅용)

##### 1단계: 인터넷 환경에서 준비
```bash
cd /path/to/llmproject

# 베이스 이미지 다운로드
docker pull --platform linux/amd64 python:3.11-slim
docker pull --platform linux/amd64 nginx:alpine
docker save -o python-3.11-slim.tar python:3.11-slim
docker save -o nginx-alpine.tar nginx:alpine

# Python 패키지 다운로드
mkdir -p python-packages
docker run --rm --platform linux/amd64 \
  -v $(pwd)/backend:/workspace/backend \
  -v $(pwd)/python-packages:/workspace/python-packages \
  -w /workspace/backend \
  python:3.11-slim \
  pip download -r requirements.txt -d /workspace/python-packages/

# 압축
cd ..
tar -czf llmproject-full.tar.gz llmproject/  # ~825MB (python-packages 압축)
```

##### 2단계: 폐쇄망 서버로 전송
USB나 내부망으로 llmproject-full.tar.gz 복사

##### 3단계: 폐쇄망 서버에서 배포
```bash
# 압축 해제
tar -xzf llmproject-full.tar.gz
cd llmproject

# 베이스 이미지 로드
docker load -i python-3.11-slim.tar
docker load -i nginx-alpine.tar

# 환경 변수 설정
cat > backend/.env << 'EOF'
DATABASE_URL=postgresql://admin:admin123@postgres-container:5432/applicants_db
OLLAMA_BASE_URL=http://ollama-container:11434
OLLAMA_MODEL=llama3.2:1b
QDRANT_URL=http://qdrant-container:6333
EOF

# 빌드 및 실행 (폐쇄망에서 python-packages로 설치)
docker-compose up -d --build

# 확인
docker-compose logs -f backend
```

---

#### 네트워크 연결 (기존 서비스와 통신)

docker-compose.yml의 networks 설정:
```yaml
networks:
  app-network:
    external: true  # 기존 네트워크 사용
    name: existing-network-name
```

또는 컨테이너 시작 후 연결:
```bash
docker network connect existing-network backend
docker network connect existing-network frontend
```

---

#### 배포 체크리스트

**사전 확인:**
- [ ] PostgreSQL, Ollama, Qdrant 실행 중
- [ ] init.sql로 테이블 생성 완료
- [ ] 네트워크 이름/컨테이너명 확인

**배포 후 검증:**
```bash
# API 확인
curl http://localhost:8000/docs
curl http://localhost/

# 로그 확인 (연결 오류 체크)
docker logs backend --tail 50
docker logs frontend --tail 50
```

**문제 해결:**
```bash
# 네트워크 확인
docker network ls
docker network inspect <network-name>

# DB 연결 테스트
docker exec backend curl http://postgres-container:5432

# 컨테이너 재시작
docker-compose restart backend
```

## Architecture

### Backend 디렉토리 구조
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
│   ├── applicant.py  # ApplicantInfo 모델
│   └── few_shot.py   # Intent, QueryLog, FewShot, FewShotAudit 모델
├── services/         # 비즈니스 로직 (싱글톤)
│   ├── ollama_service.py   # LLM 호출
│   ├── qdrant_service.py   # 벡터 DB 검색
│   ├── rag_service.py      # RAG 파이프라인
│   ├── query_router.py     # Intent 분류 (Two-tier)
│   └── sql_agent.py        # NL→SQL 변환
├── database.py       # DB 연결 및 세션 관리
└── main.py           # FastAPI 앱 및 라우터 등록
```

### 시스템 구조
```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────────────┐
│  Frontend (React + Nginx)                           │
│  - Applicant Analysis UI                            │
│  - RAG Chat UI                                      │
│  - Intent/Query Log/Few-shot Management UI          │
└──────┬──────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────┐
│  Backend (FastAPI)                                  │
│  ├─ Analysis API     (지원자 분석)                   │
│  ├─ Chat API         (RAG 채팅, QueryRouter)        │
│  ├─ Upload API       (문서 업로드)                   │
│  └─ Management APIs  (Intent/Query Log/Few-shot)    │
└─┬────┬────┬──────────────────────────────────────┬──┘
  │    │    │                                      │
  │    │    │ ┌────────────────────────────────┐  │
  │    │    └─┤ Qdrant (Vector DB)             │  │
  │    │      │ - 문서 임베딩 저장              │  │
  │    │      │ - 유사도 검색                   │  │
  │    │      └────────────────────────────────┘  │
  │    │                                           │
  │    │ ┌─────────────────────────────────────┐  │
  │    └─┤ Ollama (LLM)                        │  │
  │      │ - llama3.2:1b                       │  │
  │      │ - 요약/키워드/질문/답변 생성         │  │
  │      └─────────────────────────────────────┘  │
  │                                                │
  │ ┌──────────────────────────────────────────┐  │
  └─┤ PostgreSQL                               │◄─┘
    │ - applicant_info (지원자 정보)            │
    │ - intents (키워드 매칭)                   │
    │ - query_logs (질의 로그)                  │
    │ - few_shots (Few-shot 예제)               │
    │ - few_shot_audit (변경 이력)              │
    └──────────────────────────────────────────┘
```

### 데이터베이스 스키마
- `applicant_info` (id, reason, experience, skill) - 지원자 정보
- `intents` (keyword, intent_type, priority) - 키워드 기반 의도 매핑
- `query_logs` (query_text, detected_intent, response, is_converted_to_fewshot) - 질의 로그
- `few_shots` (source_query_log_id, intent_type, user_query, expected_response, is_active) - Few-shot 예제
- `few_shot_audit` (few_shot_id, action, old_value, new_value) - 변경 이력 (트리거 자동 생성)

### RAG 채팅 플로우
```
User Query
    ↓
QueryRouter (Intent 분류)
    ├─ intents 테이블 키워드 매칭 (빠름)
    └─ LLM 분류 (fallback)
    ↓
Intent Type 결정
    ├─ rag_search  → Qdrant 검색 + Few-shots + LLM 답변
    ├─ sql_query   → NL→SQL 변환 + PostgreSQL 조회 + 결과 해석
    └─ general     → Few-shots + LLM 대화
    ↓
Response 생성
    ↓
query_logs 자동 저장 (추후 Few-shot 승격 가능)
```

### 주요 패턴
1. **Two-tier Intent Classification**:
   - Tier 1: `intents` 테이블 키워드 매칭 (빠름, 결정적)
     - 1개 매칭 → 즉시 반환
     - 2+ 매칭 → LLM에 후보 전달하여 disambiguation
     - 0개 매칭 → LLM fallback
   - Tier 2: LLM 기반 분류 (느림, 유연함)

2. **Few-shot Integration**: 모든 서비스가 `_get_active_fewshots(session, intent_type="...")`로 활성 예제 조회하여 프롬프트에 포함

3. **Query Logging**: 모든 질의 자동 저장 → 관리 UI에서 검토 → 승격 버튼 → Few-shot 테이블 → 다음 질의에 반영

4. **Dependency Injection**: FastAPI `Depends(get_session)`로 DB 세션 관리

5. **Singleton Services**: 모듈 레벨에서 인스턴스화 (예: `ollama_service`, `rag_service`, `query_router`)
   ```python
   # services/ollama_service.py
   ollama_service = OllamaService()  # 싱글톤

   # api/analysis.py
   from app.services.ollama_service import ollama_service  # import로 재사용
   ```

6. **Security Pattern**: SQL Agent는 패턴 매칭만 사용 (동적 SQL 실행 금지, SQL injection 방지)

## Environment Variables

**필수:**
- `DATABASE_URL`: `postgresql://admin:admin123@postgres:5432/applicants_db`
- `OLLAMA_BASE_URL`: `http://ollama:11434`
- `OLLAMA_MODEL`: `llama3.2:1b`
- `QDRANT_URL`: `http://qdrant:6333`

**선택:**
- `DB_SCHEMA`: `public` (default)
- `QDRANT_COLLECTION_NAME`: `documents` (default)
- `EMBEDDING_MODEL`: `jhgan/ko-sroberta-multitask` (default)

## API Endpoints

### 지원자 분석
- `POST /api/analysis/summarize/{applicant_id}` - 요약
- `POST /api/analysis/keywords/{applicant_id}` - 키워드 추출
- `POST /api/analysis/interview-questions/{applicant_id}` - 면접 질문

### RAG 채팅
- `POST /api/chat/` - 자연어 질의 (QueryRouter 자동 라우팅)
- `POST /api/chat/classify` - 의도 분류 디버깅

### 문서 업로드
- `POST /api/upload/` - 파일 업로드 (PDF/DOCX/TXT/XLSX)
- `GET /api/upload/stats` - 업로드 통계

### Intent/Query Log/Few-shot 관리
- `GET/POST/PUT/DELETE /api/intent/`
- `GET/POST/DELETE /api/query-logs/`
- `POST /api/query-logs/convert-to-fewshot` - 질의 로그 → Few-shot 승격
- `GET/POST/PUT/DELETE /api/fewshot/`

API 문서: http://localhost:8000/docs

## Development Workflow

### Hot Reload
`docker-compose.dev.yml` 사용 시 `backend/app/` 볼륨 마운트 → 코드 변경 자동 반영

### 코드 변경
```bash
# Hot reload (docker-compose.dev.yml 사용 시 자동 반영)
# backend/app/ 디렉토리는 볼륨 마운트되어 있음

# 환경 변수 변경만: 재시작
docker-compose restart backend

# 의존성 변경 (requirements.txt): 재빌드 필요
docker-compose up -d --build backend

# 단일 파일 빠른 복사 (볼륨 미사용 시)
docker cp backend/app/api/analysis.py backend:/app/app/api/
docker-compose restart backend
```

### DB 마이그레이션
1. `migrations/` 디렉토리에 SQL 파일 생성 (예: `003_add_column.sql`)
2. 로컬 테스트: `psql -d applicants_db -f migrations/003_add_column.sql`
3. `init.sql` 업데이트 (새 설치 환경용)
4. 폐쇄망 서버: PostgreSQL 컨테이너에서 수동 실행

**Note:** Alembic 없음 - 수동 SQL 마이그레이션만 지원

## Adding Features

### 새 분석 API
1. `OllamaService`에 메서드 추가 ([ollama_service.py](backend/app/services/ollama_service.py))
   ```python
   async def new_analysis(self, text: str) -> str:
       prompt = f"Analyze: {text}"
       return await self.generate(prompt)
   ```
2. API 엔드포인트 추가 ([analysis.py](backend/app/api/analysis.py))
   ```python
   @router.post("/new-analysis/{applicant_id}")
   async def new_analysis(applicant_id: int, session: Session = Depends(get_session)):
       applicant = session.get(ApplicantInfo, applicant_id)
       result = await ollama_service.new_analysis(applicant.reason)
       return {"result": result}
   ```
3. `main.py`에 라우터 등록 (이미 analysis_router가 등록되어 있으면 자동 포함)

### 새 Intent Type
1. **관리 UI 또는 SQL로 `intents` 테이블에 추가**
   ```sql
   INSERT INTO intents (keyword, intent_type, priority, description)
   VALUES ('새키워드', 'new_intent', 5, '새로운 의도');
   ```
2. **`QueryRouter`의 `QueryIntent` enum 확장** ([query_router.py](backend/app/services/query_router.py))
   ```python
   class QueryIntent(str, Enum):
       RAG_SEARCH = "rag_search"
       SQL_QUERY = "sql_query"
       GENERAL = "general"
       NEW_INTENT = "new_intent"  # 추가
   ```
3. **서비스 핸들러 생성** (`backend/app/services/new_service.py`)
   - `_get_active_fewshots(session, intent_type="new_intent")` 필수 포함
   - Few-shots를 프롬프트에 주입
4. **Chat API에서 라우팅 추가** ([chat.py](backend/app/api/chat.py))
   ```python
   elif intent == QueryIntent.NEW_INTENT:
       result = await new_service.handle(query, session)
   ```
5. **테스트**: `POST /api/chat/classify {"query": "새키워드 포함 질문"}`
6. **관리 UI에서 Few-shot 예제 추가** (Query Logs → 승격)

### 새 RAG 서비스
1. **서비스 클래스 생성** (`backend/app/services/new_rag_service.py`)
   ```python
   class NewRagService:
       def __init__(self):
           self.ollama = ollama_service
           self.qdrant = qdrant_service

       async def handle(self, query: str, session: Session):
           # 1. Few-shots 조회
           few_shots = self._get_active_fewshots(session, "new_rag")

           # 2. Qdrant 검색 또는 다른 로직
           results = self.qdrant.search(query)

           # 3. 프롬프트 생성 (Few-shots 포함)
           prompt = self._build_prompt(query, results, few_shots)

           # 4. LLM 답변
           return await self.ollama.generate(prompt)

       def _get_active_fewshots(self, session, intent_type):
           statement = select(FewShot).where(
               FewShot.is_active == True,
               FewShot.intent_type == intent_type
           )
           return session.exec(statement).all()

       def _build_prompt(self, query, context, few_shots):
           parts = []
           if few_shots:
               parts.append("예제:\n")
               for fs in few_shots:
                   parts.append(f"Q: {fs.user_query}\nA: {fs.expected_response}\n")
           parts.append(f"Context: {context}\nQuestion: {query}\nAnswer:")
           return "\n".join(parts)

   new_rag_service = NewRagService()  # 싱글톤
   ```
2. **Chat API 라우팅 추가** ([chat.py](backend/app/api/chat.py))
3. **`intents` 테이블에 키워드 추가**

## Troubleshooting

### 연결 오류
```bash
# PostgreSQL
docker exec backend ping postgres
docker exec postgres psql -U admin -d applicants_db -c "SELECT 1"

# Ollama
docker exec backend curl http://ollama:11434/api/version

# Qdrant
docker exec backend curl http://qdrant:6333/collections
```

### 네트워크 문제
```bash
# 네트워크 확인
docker network inspect dev-network

# 네트워크 연결
docker network connect dev-network backend
```

### 데이터 확인
```bash
# 지원자 데이터
docker exec postgres psql -U admin -d applicants_db -c "SELECT id, length(reason), length(experience), length(skill) FROM applicant_info;"

# Few-shot 예제
docker exec postgres psql -U admin -d applicants_db -c "SELECT id, intent_type, is_active FROM few_shots;"
```

## Important Notes

- **Read-Only Applicant DB**: `applicant_info` 테이블은 읽기 전용 (분석 API만 제공, CRUD 없음)
- **No Auto-Migration**: FastAPI는 테이블 생성 안 함 (폐쇄망 서버는 `init.sql` 사전 실행 필요)
- **Manual Few-shot Curation**: Query logs → 관리 UI 검토 → 승격 버튼 → Few-shots
- **Audit Trail**: PostgreSQL 트리거 `log_few_shot_audit()`로 Few-shot 변경 이력 자동 기록
- **Korean LLM**: 모든 프롬프트는 한국어로 하드코딩 (임베딩: `jhgan/ko-sroberta-multitask`)
- **Offline Build**: `Dockerfile.offline` + `python-packages/` 디렉토리 사용
- **No Heavy Frameworks**: LangChain 없음 (커스텀 RAG), Alembic 없음 (SQL 마이그레이션 수동)

## Quick Reference

### 자주 사용하는 명령어
```bash
# 개발 환경 시작
docker-compose -f docker-compose.dev.yml up -d

# 로그 실시간 확인
docker-compose logs -f backend

# 백엔드 재시작 (코드 변경 후)
docker-compose restart backend

# DB 접속
docker exec -it postgres psql -U admin -d applicants_db

# Ollama 모델 테스트
docker exec backend curl -X POST http://ollama:11434/api/generate \
  -d '{"model":"llama3.2:1b","prompt":"안녕하세요","stream":false}'

# Qdrant 컬렉션 확인
docker exec backend curl http://qdrant:6333/collections/documents
```

### 디버깅 체크리스트
1. **Intent 분류 안됨**: `/api/chat/classify`로 의도 확인 → `intents` 테이블에 키워드 추가
2. **LLM 응답 없음**: Ollama 컨테이너 확인 (`docker logs ollama`), 모델 다운로드 확인
3. **RAG 답변 부정확**: Few-shot 예제 추가 (`/api/fewshot/`), Qdrant에 문서 확인
4. **DB 연결 실패**: `.env`의 `DATABASE_URL` 확인, 네트워크 연결 확인
5. **볼륨 마운트 안됨**: `docker-compose.dev.yml` 사용 확인, 컨테이너 재시작
