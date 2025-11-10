# 채용 지원자 분석 시스템

채용 지원자 자기소개서 분석 및 RAG 기반 문서 검색 시스템

## 핵심 기능

1. **지원자 분석**: 요약, 키워드 추출, 면접 질문 생성
2. **RAG 문서 검색**: PDF/DOCX/TXT/XLSX 업로드 → Qdrant → LLM 답변
3. **자연어 SQL**: 질의 → SQL 변환 → DB 조회 → 결과 해석
4. **Intent & Few-shot**: 키워드 매칭 + LLM 분류, 질의 로그 → Few-shot 예제

## 기술 스택

| 구분 | 기술 | 비고 |
|------|------|------|
| **Backend** | FastAPI, SQLModel, Qdrant, **FastEmbed** | **FastEmbed**: ONNX 기반 경량 임베딩 (778MB) |
| **Frontend** | React 19, TypeScript, Vite 7, Tailwind CSS 4 | - |
| **LLM** | Ollama (llama3.2:1b) | 폐쇄망용 |
| **DB** | PostgreSQL 16, Qdrant | 지원자 정보, 벡터 검색 |
| **배포** | Docker, Docker Compose | **폐쇄망 배포 전용** |

### 임베딩 모델 (FastEmbed)
- 현재: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (768차원, 한국어 포함)
- 이전 대비: **90% 크기 감소** (sentence-transformers 7.97GB → FastEmbed 778MB)

---

## 폐쇄망 배포

> **전제 조건**: Docker, Docker Compose, PostgreSQL, Ollama (llama3.2:1b), Qdrant 실행 중

### 방식 A: 빌드 이미지 전송 (권장, 1.05GB)

```bash
# 1. 인터넷 환경 - FastEmbed 모델 다운로드 필수!
mkdir -p backend/fastembed_cache
docker run --rm --platform linux/amd64 \
  -v $(pwd)/backend/fastembed_cache:/cache \
  python:3.11-slim \
  bash -c "pip install fastembed==0.3.1 && python -c \"from fastembed import TextEmbedding; TextEmbedding(model_name='sentence-transformers/paraphrase-multilingual-mpnet-base-v2', cache_dir='/cache')\""

docker build --platform linux/amd64 -t llmproject-backend:latest -f backend/Dockerfile backend/
docker build --platform linux/amd64 -t llmproject-frontend:latest -f frontend/Dockerfile frontend/
docker save -o llmproject-backend.tar llmproject-backend:latest
docker save -o llmproject-frontend.tar llmproject-frontend:latest
tar -czf llmproject-code.tar.gz --exclude=frontend/node_modules --exclude=*.tar llmproject/

# 2. 폐쇄망 서버
docker load -i llmproject-backend.tar
docker load -i llmproject-frontend.tar
tar -xzf llmproject-code.tar.gz && cd llmproject

# 환경 변수 설정 (FastEmbed 캐시 경로 추가)
cat > backend/.env << 'EOF'
DATABASE_URL=postgresql://admin:admin123@postgres-container:5432/applicants_db
OLLAMA_BASE_URL=http://ollama-container:11434
OLLAMA_MODEL=llama3.2:1b
QDRANT_URL=http://qdrant-container:6333
FASTEMBED_CACHE_PATH=/app/fastembed_cache
EOF

# docker-compose.yml 수정 (build → image, fastembed_cache 볼륨)
vi docker-compose.yml  # backend에 image + volumes 추가

# 실행
docker-compose up -d
```

**상세 가이드**: [CLAUDE.md - 폐쇄망 배포](CLAUDE.md#폐쇄망-배포)

---

## API

### 지원자 분석
- `POST /api/analysis/summarize/{applicant_id}` - 요약
- `POST /api/analysis/keywords/{applicant_id}` - 키워드
- `POST /api/analysis/interview-questions/{applicant_id}` - 면접 질문

### RAG 검색
- `POST /api/chat/` - 자연어 질의 (Intent 자동 분류)
- `POST /api/upload/` - 문서 업로드

### 관리
- `GET/POST /api/intent/` - Intent 관리
- `GET/POST /api/fewshot/` - Few-shot 관리
- `GET/POST /api/query-logs/` - Query Log 관리

**API 문서**: http://localhost:8000/docs

---

## 문서

| 문서 | 내용 |
|------|------|
| [CLAUDE.md](CLAUDE.md) | 프로젝트 개요, 폐쇄망 배포, 아키텍처 |
| [DOCUMENT_STRUCTURING_GUIDE.md](DOCUMENT_STRUCTURING_GUIDE.md) | 문서 구조화 전략 (섹션 추출, 청킹) |
| [EMBEDDING_MODEL_GUIDE.md](EMBEDDING_MODEL_GUIDE.md) | FastEmbed 모델 변경 가이드 |

---

## 라이선스

MIT License
