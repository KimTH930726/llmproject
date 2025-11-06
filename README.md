# 지원자 자기소개서 분석 시스템

PostgreSQL에 저장된 채용 지원자의 자기소개서를 LLM으로 자동 분석하는 API 서비스입니다.

## 주요 기능

### 지원자 분석
- **자기소개서 요약**: Ollama LLM을 사용하여 지원 동기, 경력, 기술을 종합 요약 (3-5개 핵심 문장)
- **키워드 추출**: 지원자 정보에서 중요한 키워드 5-10개 자동 추출
- **면접 예상 질문**: 지원자 정보 기반 면접 예상 질문 10개 자동 생성

### RAG 기반 문서 검색
- **문서 업로드**: PDF, DOCX, TXT, XLSX 파일 업로드 및 Qdrant 벡터 DB 저장
- **RAG 검색**: 업로드된 문서에서 관련 정보를 검색하여 LLM으로 답변 생성
- **자연어 SQL**: 자연어 질의를 SQL로 변환하여 데이터베이스 조회

### 지능형 Intent & Few-shot 학습
- **Two-tier Intent 분류**: 키워드 매칭 → LLM 분류 (빠르고 정확)
- **Query Logging**: 모든 사용자 질의 자동 저장 및 추적
- **Few-shot Learning**: 질의 로그를 Few-shot 예제로 승격하여 LLM 프롬프트에 활용

> **중요**: 이 시스템은 **폐쇄망 서버 배포**를 위해 설계되었습니다. PostgreSQL, Ollama, Qdrant는 서버에 이미 실행 중이어야 합니다.

## 기술 스택

### Backend
- **FastAPI** - Python 비동기 웹 프레임워크
- **SQLModel** - SQLAlchemy + Pydantic ORM
- **PostgreSQL 16** - 지원자 정보 저장 + Query Logging
- **Ollama** - LLM 서비스 (llama3.2:1b)
- **Qdrant** - 벡터 데이터베이스 (문서 임베딩)
- **Sentence Transformers** - 한국어 임베딩 (jhgan/ko-sroberta-multitask)
- **httpx** - 비동기 HTTP 클라이언트

### Frontend
- **React 19** + **TypeScript**
- **Vite 7** - 빌드 도구
- **Tailwind CSS 4** - 스타일링
- **Nginx** - 프로덕션 서버

### Infrastructure
- **Docker & Docker Compose** - 컨테이너화
- 폐쇄망 배포 지원

---

## 🚀 빠른 시작

### 사전 요구사항

이 프로젝트는 **폐쇄망 서버 배포**를 위해 설계되었습니다.

**서버 환경:**
- Docker 20.10+
- Docker Compose 2.0+
- PostgreSQL (Docker 실행 중)
- Ollama (Docker 실행 중, 모델 포함)

### 폐쇄망 서버 배포

상세한 배포 가이드는 [SETUP-GUIDE.md](SETUP-GUIDE.md)를 참고하세요.

#### 1. 인터넷 환경에서 준비

```bash
# 베이스 이미지 내보내기 (Linux AMD64 아키텍처)
# 맥/윈도우에서 실행 시 --platform linux/amd64 필수!
docker pull --platform linux/amd64 python:3.11-slim && docker save -o python-3.11-slim.tar python:3.11-slim
docker pull --platform linux/amd64 node:20-alpine && docker save -o node-20-alpine.tar node:20-alpine
docker pull --platform linux/amd64 nginx:alpine && docker save -o nginx-alpine.tar nginx:alpine

# Python 패키지 다운로드 (Linux 서버용)
# 프로젝트 루트에서 실행
mkdir -p python-packages
docker run --rm --platform linux/amd64 \
  -v $(pwd)/backend:/workspace/backend \
  -v $(pwd)/python-packages:/workspace/python-packages \
  -w /workspace/backend \
  python:3.11-slim \
  pip download -r requirements.txt -d /workspace/python-packages/

# 전체 압축
cd ../..
tar -czf llmproject.tar.gz llmproject/
```

#### 2. 폐쇄망 서버에서 실행

```bash
# 압축 해제
tar -xzf llmproject.tar.gz && cd llmproject

# 베이스 이미지 로드
docker load -i python-3.11-slim.tar
docker load -i node-20-alpine.tar
docker load -i nginx-alpine.tar

# 환경 변수 설정 (서버의 PostgreSQL, Ollama 정보 입력)
cd backend
cp .env.example .env
vi .env  # OLLAMA_BASE_URL, DATABASE_URL 수정

# 빌드 + 실행
cd ..
docker-compose up -d --build
```

---

## 📡 API 엔드포인트

### 1. 요약 API
```http
POST /api/analysis/summarize/{applicant_id}
```

**Response:**
```json
{
  "applicant_id": 1,
  "summary": "5년간 백엔드 개발 경력을 쌓은 엔지니어로, FastAPI와 Django를 활용한 RESTful API 설계 및 대용량 트래픽 처리에 강점을 가지고 있습니다..."
}
```

### 2. 키워드 추출 API
```http
POST /api/analysis/keywords/{applicant_id}
```

**Response:**
```json
{
  "applicant_id": 1,
  "keywords": ["Python", "FastAPI", "PostgreSQL", "Redis", "AWS", "Docker", "LLM"]
}
```

### 3. 면접 예상 질문 API
```http
POST /api/analysis/interview-questions/{applicant_id}
```

**Response:**
```json
{
  "applicant_id": 1,
  "questions": [
    "5년간의 백엔드 개발 경력 중 가장 도전적이었던 프로젝트는 무엇인가요?",
    "대용량 트래픽 처리 시 어떤 전략을 사용하셨나요?",
    "Redis 캐싱 전략을 통해 응답 속도를 30% 개선한 과정을 설명해주세요.",
    ...
  ]
}
```

> API 문서: http://localhost:8000/docs

---

## 💾 데이터베이스 스키마

### applicant_info 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL (PK) | 지원자 ID |
| reason | VARCHAR(4000) | 지원 동기 |
| experience | VARCHAR(4000) | 경력 및 경험 |
| skill | VARCHAR(4000) | 기술 스택 및 역량 |

**테이블 생성 (참고):**
```sql
CREATE TABLE IF NOT EXISTS applicant_info (
    id BIGSERIAL PRIMARY KEY,
    reason VARCHAR(4000),
    experience VARCHAR(4000),
    skill VARCHAR(4000)
);
```

> **참고:** `init.sql` 파일에 테이블 생성 스크립트와 샘플 데이터가 포함되어 있습니다.

---

## ⚙️ 환경 변수 설정

`backend/.env` 파일 수정:

```bash
# Ollama 설정 (서버의 Ollama 컨테이너)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:1b

# PostgreSQL 설정 (서버의 PostgreSQL 컨테이너)
DATABASE_URL=postgresql://admin:admin123@postgres:5432/applicants_db
DB_SCHEMA=public

# Qdrant 설정 (서버의 Qdrant 컨테이너) - RAG 기능용
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION_NAME=documents

# 임베딩 모델 설정 (한국어 지원)
EMBEDDING_MODEL=jhgan/ko-sroberta-multitask
```

**네트워크 연결 예시:**
- 같은 Docker 네트워크: `http://ollama:11434`, `http://qdrant:6333`
- 다른 네트워크: `http://172.17.0.1:11434`, `http://172.17.0.1:6333`
- 컨테이너 이름으로 연결: `http://<container-name>:11434`

---

## 📁 프로젝트 구조

```
llmproject/
├── backend/                        # FastAPI 백엔드
│   ├── app/
│   │   ├── api/                    # API 라우터
│   │   │   ├── analysis.py         # 지원자 분석 API (요약, 키워드, 면접질문)
│   │   │   ├── chat.py             # RAG 채팅 API (QueryRouter 라우팅)
│   │   │   ├── upload.py           # 문서 업로드 API
│   │   │   ├── intent.py           # Intent 관리 CRUD API
│   │   │   ├── query_log.py        # 질의 로그 관리 API
│   │   │   └── fewshot.py          # Few-shot 관리 CRUD API
│   │   ├── models/                 # 데이터 모델
│   │   │   ├── applicant.py        # Applicant 테이블 모델
│   │   │   ├── chat.py             # 채팅 요청/응답 모델
│   │   │   ├── query_log.py        # QueryLog 테이블 모델
│   │   │   └── few_shot.py         # Intent, FewShot, FewShotAudit 모델
│   │   ├── services/               # 비즈니스 로직
│   │   │   ├── ollama_service.py   # Ollama LLM 연동
│   │   │   ├── qdrant_service.py   # Qdrant 벡터 DB 연동
│   │   │   ├── rag_service.py      # RAG 검색 및 답변 생성
│   │   │   ├── query_router.py     # Intent 분류 (Two-tier)
│   │   │   └── sql_agent.py        # 자연어 → SQL 변환 및 실행
│   │   ├── utils/                  # 유틸리티
│   │   │   └── text_extractor.py   # 파일 텍스트 추출 (PDF/DOCX/TXT/XLSX)
│   │   ├── database.py             # PostgreSQL 연결 및 세션 관리
│   │   └── main.py                 # FastAPI 앱 엔트리포인트
│   ├── Dockerfile                  # 일반 빌드용
│   ├── Dockerfile.offline          # 오프라인 빌드용 (python-packages 사용)
│   ├── requirements.txt            # Python 의존성 (RAG 패키지 포함)
│   └── .env.example                # 환경 변수 템플릿
│
├── frontend/                       # React 프론트엔드
│   ├── src/
│   │   ├── components/
│   │   │   ├── IntentManagement.tsx       # Intent 관리 UI
│   │   │   ├── QueryLogManagement.tsx     # 질의 로그 관리 UI
│   │   │   └── FewShotManagement.tsx      # Few-shot 관리 UI
│   │   ├── App.tsx                 # 메인 앱
│   │   ├── main.tsx
│   │   └── index.css
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.ts
│
├── migrations/                     # 데이터베이스 마이그레이션 스크립트
│   ├── 001_create_fewshot_tables.sql
│   └── 002_update_fewshot_to_querylog.sql
│
├── python-packages/                # 오프라인 Python 패키지 (준비 후 생성)
├── docker-compose.yml              # Backend, Frontend 설정 (폐쇄망용)
├── docker-compose.dev.yml          # 전체 스택 설정 (로컬 개발용)
├── init.sql                        # DB 초기화 스크립트 (모든 테이블 + 샘플 데이터)
│
├── SETUP-GUIDE.md                  # 폐쇄망 배포 상세 가이드
├── LOCAL-DEV-GUIDE.md              # 로컬 개발 환경 가이드
├── DEPLOY.md                       # 배포 및 문제 해결 가이드
├── CLAUDE.md                       # Claude Code 개발 가이드
├── TECH-COMPARISON.md              # 기술 비교 분석 (LangChain 등)
├── FEWSHOT_FEATURE_GUIDE.md        # Few-shot 기능 사용 가이드
├── RAG_IMPLEMENTATION.md           # RAG 기능 구현 보고서
├── EMBEDDING_MODEL_GUIDE.md        # 임베딩 모델 변경 가이드
└── README.md                       # 프로젝트 문서 (이 파일)
```

---

## 🔧 문제 해결

### PostgreSQL 연결 실패

```bash
# 네트워크 연결 확인
docker exec backend ping postgres

# .env 파일 확인
docker exec backend cat /app/.env

# PostgreSQL 컨테이너 확인
docker ps | grep postgres
```

### Ollama 연결 실패

```bash
# Ollama 컨테이너 확인
docker ps | grep ollama

# Ollama API 테스트
docker exec backend curl http://ollama:11434/api/version
```

### 로그 확인

```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 서비스 재시작

```bash
# .env 파일 수정 후
docker-compose restart backend

# 소스 코드 수정 후
docker-compose up -d --build backend
```

---

## 📖 추가 문서

- [SETUP-GUIDE.md](SETUP-GUIDE.md) - 폐쇄망 서버 배포 상세 가이드
- [LOCAL-DEV-GUIDE.md](LOCAL-DEV-GUIDE.md) - 로컬 개발 환경 가이드
- [DEPLOY.md](DEPLOY.md) - 배포 및 문제 해결
- [CLAUDE.md](CLAUDE.md) - 개발 가이드 (Claude Code용)
- [TECH-COMPARISON.md](TECH-COMPARISON.md) - 기술 비교 분석 (LangChain 등)
- [FEWSHOT_FEATURE_GUIDE.md](FEWSHOT_FEATURE_GUIDE.md) - Few-shot 기능 사용 가이드
- [RAG_IMPLEMENTATION.md](RAG_IMPLEMENTATION.md) - RAG 기능 구현 보고서
- [EMBEDDING_MODEL_GUIDE.md](EMBEDDING_MODEL_GUIDE.md) - 임베딩 모델 변경 가이드

---

## 🏗️ 아키텍처

### 시스템 구조
```
Client (Browser)
    ↓
Frontend (React + Nginx)
    ↓
Backend (FastAPI)
    ├── PostgreSQL (지원자 정보, Intent, Query Logs, Few-shots)
    ├── Ollama (LLM - llama3.2:1b)
    └── Qdrant (Vector DB - 문서 임베딩)
```

### 주요 패턴
- **Two-tier Intent Classification**: 키워드 매칭 (빠름) → LLM 분류 (fallback)
- **Few-shot Integration**: 모든 서비스가 DB에서 활성 예제 조회하여 프롬프트에 포함
- **Query Logging**: 모든 질의 자동 저장 → 관리 UI에서 Few-shot으로 승격 가능
- **Dependency Injection**: FastAPI `Depends()`를 통한 세션 관리
- **Singleton Services**: OllamaService, QdrantService 등 싱글톤 인스턴스
- **읽기 전용 DB**: PostgreSQL 지원자 데이터는 조회만 가능

---

## 🔐 보안 고려사항

1. **기본 비밀번호 변경**
   ```bash
   # .env 파일에서
   DATABASE_URL=postgresql://admin:강력한비밀번호@postgres:5432/applicants_db
   ```

2. **포트 제한**
   ```yaml
   # docker-compose.yml
   ports:
     - "127.0.0.1:8000:8000"  # localhost만 허용
   ```

3. **네트워크 격리**
   - Backend, Frontend를 PostgreSQL, Ollama와 같은 Docker 네트워크에 배치

---

## 📝 라이센스

이 프로젝트는 내부 사용을 위한 것입니다.
