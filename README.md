# 지원자 자기소개서 분석 시스템

PostgreSQL에 저장된 채용 지원자의 자기소개서를 LLM으로 자동 분석하는 API 서비스입니다.

## 주요 기능

- **자기소개서 요약**: Ollama LLM을 사용하여 지원 동기, 경력, 기술을 종합 요약 (3-5개 핵심 문장)
- **키워드 추출**: 지원자 정보에서 중요한 키워드 5-10개 자동 추출
- **면접 예상 질문**: 지원자 정보 기반 면접 예상 질문 10개 자동 생성
- **RESTful API**: FastAPI 기반의 표준화된 API

> **중요**: 이 시스템은 **분석 전용**입니다. 지원자 데이터는 PostgreSQL에 이미 존재한다고 가정하며, CRUD 기능은 제공하지 않습니다.

## 기술 스택

### Backend
- **FastAPI** - Python 비동기 웹 프레임워크
- **SQLModel** - SQLAlchemy + Pydantic ORM
- **PostgreSQL 16** - 데이터베이스
- **Ollama** - LLM 서비스 (llama3.2:1b)
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
# 베이스 이미지 내보내기 (amd64 아키텍처)
docker pull --platform linux/amd64 python:3.11-slim && docker save -o python-3.11-slim.tar python:3.11-slim
docker pull --platform linux/amd64 node:20-alpine && docker save -o node-20-alpine.tar node:20-alpine
docker pull --platform linux/amd64 nginx:alpine && docker save -o nginx-alpine.tar nginx:alpine

# Python 패키지 다운로드 (Linux 서버용)
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
```

**네트워크 연결 예시:**
- 같은 Docker 네트워크: `http://ollama:11434`
- 다른 네트워크: `http://172.17.0.1:11434`
- 컨테이너 이름으로 연결: `http://<container-name>:11434`

---

## 📁 프로젝트 구조

```
llmproject/
├── backend/                    # FastAPI 백엔드
│   ├── app/
│   │   ├── api/
│   │   │   └── analysis.py     # 분석 API (요약, 키워드, 면접질문)
│   │   ├── models/
│   │   │   └── applicant.py    # 지원자 모델
│   │   ├── services/
│   │   │   └── ollama_service.py  # LLM 서비스
│   │   ├── database.py         # DB 연결
│   │   └── main.py             # FastAPI 앱
│   ├── Dockerfile.offline      # 오프라인 빌드용
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                   # React 프론트엔드
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
│
├── python-packages/            # 오프라인 Python 패키지 (준비 후 생성)
├── docker-compose.yml          # Backend, Frontend 설정
├── init.sql                    # DB 초기화 스크립트
├── SETUP-GUIDE.md              # 폐쇄망 배포 가이드
└── README.md
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
- [DEPLOY.md](DEPLOY.md) - 배포 및 문제 해결
- [CLAUDE.md](CLAUDE.md) - 개발 가이드 (Claude Code용)

---

## 🏗️ 아키텍처

### 요청 흐름
```
Client → Frontend (Nginx)
         ↓
      Backend (FastAPI)
         ↓
      PostgreSQL (조회) → Ollama (LLM 분석) → Response
```

### 주요 패턴
- **Dependency Injection**: FastAPI의 `Depends()`를 통한 세션 관리
- **Singleton Pattern**: `OllamaService` 인스턴스 재사용
- **분석 전용 API**: 읽기 전용 데이터베이스 접근

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
