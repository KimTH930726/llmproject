# 지원자 자기소개서 분석 시스템

LLM을 활용하여 채용 지원자의 자기소개서를 자동으로 요약하고 키워드를 추출하는 웹 애플리케이션입니다.

## 주요 기능

- **자기소개서 요약**: Ollama LLM을 사용하여 지원자의 자기소개서를 3-5개 핵심 문장으로 요약
- **키워드 추출**: 자기소개서에서 중요한 키워드 5-10개 자동 추출
- **지원자 관리**: 지원자 정보 CRUD (생성, 조회, 수정, 삭제)
- **RESTful API**: FastAPI 기반의 표준화된 API

## 기술 스택

### 백엔드
- FastAPI (Python)
- SQLModel (ORM)
- SQLite (데이터베이스)
- Ollama (LLM)

### 프론트엔드
- React + TypeScript
- Vite
- Tailwind CSS

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

3. Ollama 모델 다운로드
```bash
docker exec ollama ollama pull llama2
```

4. 서비스 접속
- 프론트엔드: http://localhost
- 백엔드 API 문서: http://localhost:8000/docs
- Ollama API: http://localhost:11434

### 서비스 중지
```bash
docker-compose down
```

## 로컬 개발 (Docker 없이)

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
# .env 파일을 수정하여 Ollama URL 등 설정
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
ollama pull llama2
```

## API 엔드포인트

### 지원자 관리
- `POST /api/applicants/` - 지원자 생성
- `GET /api/applicants/` - 지원자 목록 조회
- `GET /api/applicants/{id}` - 특정 지원자 조회
- `PATCH /api/applicants/{id}` - 지원자 정보 수정
- `DELETE /api/applicants/{id}` - 지원자 삭제

### 자기소개서 분석
- `POST /api/analysis/summarize` - 자기소개서 요약 (텍스트 직접 전달)
- `POST /api/analysis/keywords` - 키워드 추출 (텍스트 직접 전달)
- `POST /api/analysis/summarize/{applicant_id}` - 지원자 ID로 요약
- `POST /api/analysis/keywords/{applicant_id}` - 지원자 ID로 키워드 추출

API 문서는 서버 실행 후 http://localhost:8000/docs 에서 확인할 수 있습니다.

## 폐쇄망 이식

폐쇄망(인터넷이 차단된 환경)으로 프로젝트를 이식해야 하는 경우:

### 1. 내보내기 (인터넷 가능한 환경)

전체 프로젝트를 한 번에 내보내기:
```bash
./scripts/full-export.sh
```

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
│   │   ├── models/      # 데이터 모델
│   │   ├── services/    # 비즈니스 로직
│   │   ├── database.py  # DB 설정
│   │   └── main.py      # 엔트리포인트
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/            # React 프론트엔드
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── scripts/             # 유틸리티 스크립트
│   ├── export-images.sh
│   ├── import-images.sh
│   ├── export-ollama-model.sh
│   ├── import-ollama-model.sh
│   ├── export-dependencies.sh
│   ├── import-dependencies.sh
│   └── full-export.sh
├── docker-compose.yml
├── CLAUDE.md           # Claude Code 개발 가이드
└── README.md
```

## 문제 해결

### 로그 확인
```bash
# 모든 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f ollama
```

### 서비스 재시작
```bash
docker-compose restart
```

### 컨테이너 상태 확인
```bash
docker-compose ps
```

### 데이터베이스 초기화
```bash
docker-compose down -v
docker-compose up -d
```

## 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.
