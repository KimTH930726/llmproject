# 지원자 자기소개서 분석 시스템

PostgreSQL에 저장된 채용 지원자의 자기소개서를 LLM으로 자동 요약하고 키워드를 추출하는 분석 전용 API 서비스입니다.

## 주요 기능

- **자기소개서 요약**: Ollama LLM(llama3.2:1b)을 사용하여 지원자의 자기소개서를 3-5개 핵심 문장으로 요약
- **키워드 추출**: 자기소개서에서 중요한 키워드 5-10개 자동 추출
- **RESTful API**: FastAPI 기반의 표준화된 API

> **중요**: 이 시스템은 **분석 전용**입니다. 지원자 데이터는 PostgreSQL에 이미 존재한다고 가정하며, 조회/생성/수정/삭제 기능은 제공하지 않습니다. 지원자 ID만 알면 분석 API를 호출할 수 있습니다.

## 기술 스택

### 백엔드
- FastAPI (Python)
- SQLModel (ORM)
- PostgreSQL 16 (데이터베이스)
- Ollama (LLM - llama3.2:1b)
- psycopg2-binary (PostgreSQL driver)

### 프론트엔드
- React 19 + TypeScript
- Vite 7
- Tailwind CSS 4

### 인프라
- Docker & Docker Compose
- Nginx (프로덕션 서버)

## 빠른 시작 (Docker 사용)

### 사전 요구사항
- Docker 20.10+
- Docker Compose 2.0+

### 실행 방법

1. 저장소 클론
```bash
git clone <repository-url>
cd llmproject
```

2. Docker Compose로 실행
```bash
docker-compose up -d
```

PostgreSQL 데이터베이스가 자동으로 초기화됩니다:
- `applicants` 테이블 생성 (id, content 컬럼)
- 샘플 데이터 3개 자동 삽입

3. Ollama 모델 다운로드
```bash
docker exec ollama ollama pull llama3.2:1b
```

4. 서비스 접속
- 프론트엔드: http://localhost
- 백엔드 API 문서: http://localhost:8000/docs
- PostgreSQL: localhost:5432 (admin/admin123)
- Ollama API: http://localhost:11434

### 로그 확인
```bash
# 모든 서비스
docker-compose logs -f

# 특정 서비스만
docker-compose logs -f backend
docker-compose logs -f postgres
```

### 서비스 중지
```bash
docker-compose down

# 데이터베이스 포함 완전 삭제 (주의!)
docker-compose down -v
```

## 로컬 개발 (Docker 없이)

### PostgreSQL 설정

1. PostgreSQL 설치 및 실행

2. 데이터베이스 생성 및 테이블 초기화
```bash
# 데이터베이스 생성
createdb -U postgres applicants_db

# init.sql 실행하여 테이블 생성 및 샘플 데이터 삽입
psql -U postgres -d applicants_db -f init.sql

# 또는 psql 내에서:
# psql -U postgres -d applicants_db
# \i init.sql
# \dt  -- 테이블 확인
# SELECT * FROM applicants;  -- 데이터 확인
```

### 백엔드 설정

1. Python 가상환경 생성 및 활성화
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일 수정:
# DATABASE_URL=postgresql://postgres:password@localhost:5432/applicants_db
```

4. 서버 실행
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 프론트엔드 설정

1. 의존성 설치
```bash
cd frontend
npm install
```

2. 개발 서버 실행
```bash
npm run dev
```

3. 프로덕션 빌드
```bash
npm run build
```

### Ollama 설정

1. Ollama 설치 (https://ollama.ai)

2. Ollama 서버 실행
```bash
ollama serve
```

3. 모델 다운로드
```bash
ollama pull llama3.2:1b
```

## API 엔드포인트

### 자기소개서 분석 (분석 전용)

**요약 API**
- **Endpoint**: `POST /api/analysis/summarize/{applicant_id}`
- **Path Parameter**: `applicant_id` (integer) - 지원자 ID
- **Response**:
  ```json
  {
    "applicant_id": 1,
    "summary": "3-5개의 핵심 문장으로 요약된 내용..."
  }
  ```

**키워드 추출 API**
- **Endpoint**: `POST /api/analysis/keywords/{applicant_id}`
- **Path Parameter**: `applicant_id` (integer) - 지원자 ID
- **Response**:
  ```json
  {
    "applicant_id": 1,
    "keywords": ["Python", "FastAPI", "LLM", "백엔드", "AI"]
  }
  ```

> **Note**: 지원자 조회 API는 제공하지 않습니다. 분석 API 호출 시 지원자 ID를 이미 알고 있어야 합니다.

API 문서는 서버 실행 후 http://localhost:8000/docs 에서 확인할 수 있습니다.

## 데이터베이스 스키마

### applicants 테이블

| 컬럼    | 타입         | 설명          |
|---------|--------------|---------------|
| id      | SERIAL (PK)  | 지원자 ID     |
| content | TEXT         | 자기소개서 내용 |

**테이블 생성 방법:**
- **Docker 환경**: `docker-compose up` 시 `init.sql`이 자동 실행되어 테이블 생성
- **로컬 환경**: `psql -d applicants_db -f init.sql` 명령으로 수동 실행

## 폐쇄망 이식

폐쇄망(인터넷이 차단된 환경)으로 프로젝트를 이식해야 하는 경우:

### 1. 내보내기 (인터넷 가능한 환경)

전체 프로젝트를 한 번에 내보내기:
```bash
./scripts/full-export.sh
```

생성된 `export-package_*.tar.gz` 파일에 포함된 내용:
- 소스 코드
- Docker 이미지 (backend, frontend, ollama, postgres)
- Ollama 모델 (llama3.2:1b)
- Python/Node.js 의존성 패키지
- 설치 가이드 (INSTALL.md)

또는 개별적으로 내보내기:
```bash
# Docker 이미지 내보내기
./scripts/export-images.sh

# Ollama 모델 내보내기
./scripts/export-ollama-model.sh

# Python/Node.js 의존성 내보내기
./scripts/export-dependencies.sh
```

### 2. 가져오기 (폐쇄망 환경)

전체 패키지 압축 해제 후:
```bash
tar -xzf export-package_*.tar.gz
cd export-package_*/source
```

설치:
```bash
# Docker 이미지 가져오기
./scripts/import-images.sh

# Ollama 모델 가져오기
./scripts/import-ollama-model.sh

# 의존성 설치 (Docker 미사용 시)
./scripts/import-dependencies.sh
```

자세한 내용은 생성된 `INSTALL.md` 파일을 참고하세요.

## 프로젝트 구조

```
.
├── backend/              # FastAPI 백엔드
│   ├── app/
│   │   ├── api/         # API 라우터
│   │   │   └── analysis.py   # 분석 API (요약, 키워드)
│   │   ├── models/      # 데이터 모델
│   │   │   └── applicant.py  # Applicant
│   │   ├── services/    # 비즈니스 로직
│   │   │   └── ollama_service.py  # Ollama 연동
│   │   ├── database.py  # PostgreSQL 연결
│   │   └── main.py      # 엔트리포인트
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/            # React 프론트엔드
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── scripts/             # 유틸리티 스크립트
├── init.sql            # PostgreSQL 초기화 스크립트
├── docker-compose.yml  # Docker Compose 설정
├── CLAUDE.md          # Claude Code 개발 가이드
└── README.md
```

## 문제 해결

### PostgreSQL 연결 오류
```bash
# 컨테이너 상태 확인
docker-compose ps

# PostgreSQL 로그 확인
docker-compose logs postgres

# PostgreSQL 재시작
docker-compose restart postgres
```

### 로컬 개발 시 테이블이 없음
```bash
# init.sql을 다시 실행
psql -U postgres -d applicants_db -f init.sql

# 또는 데이터베이스 재생성
dropdb -U postgres applicants_db
createdb -U postgres applicants_db
psql -U postgres -d applicants_db -f init.sql
```

### Ollama 모델 로딩 실패
```bash
# Ollama 컨테이너 내부에서 모델 확인
docker exec -it ollama ollama list

# 모델 재다운로드
docker exec ollama ollama pull llama3.2:1b
```

### 데이터베이스 초기화
```bash
# 모든 데이터 삭제 후 재시작 (주의!)
docker-compose down -v
docker-compose up -d
# init.sql이 자동 실행되어 테이블 재생성됨
```

### 로그 확인
```bash
# 모든 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f ollama
```

### 서비스 재시작
```bash
# 전체 재시작
docker-compose restart

# 특정 서비스만 재시작
docker-compose restart backend
```

## 개발 참고사항

### 환경 변수
- `OLLAMA_BASE_URL`: Ollama API 주소 (default: http://localhost:11434)
- `OLLAMA_MODEL`: 사용할 모델명 (default: llama3.2:1b)
- `DATABASE_URL`: PostgreSQL 연결 문자열
  - Docker: `postgresql://admin:admin123@postgres:5432/applicants_db`
  - Local: `postgresql://postgres:password@localhost:5432/applicants_db`

### 데이터베이스 스키마 변경
1. `init.sql` 파일 수정
2. `backend/app/models/applicant.py`의 모델 수정
3. **Docker**: `docker-compose down -v && docker-compose up -d` (자동 재생성)
4. **Local**: `psql -d applicants_db -f init.sql` (수동 재실행)

### 새로운 분석 기능 추가
1. `backend/app/services/ollama_service.py`에 메서드 추가
2. `backend/app/api/analysis.py`에 엔드포인트 추가
3. API 문서에서 확인: http://localhost:8000/docs

## 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.
