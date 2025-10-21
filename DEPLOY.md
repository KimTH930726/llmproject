# 폐쇄망 서버 배포 가이드

## 📋 사전 준비 (인터넷 연결 환경)

### 1. 베이스 Docker 이미지 내보내기

```bash
# Python 베이스 이미지 (Backend용)
docker pull python:3.11-slim
docker save -o python-3.11-slim.tar python:3.11-slim

# Node.js 베이스 이미지 (Frontend 빌드용)
docker pull node:20-alpine
docker save -o node-20-alpine.tar node:20-alpine

# Nginx 베이스 이미지 (Frontend 서빙용)
docker pull nginx:alpine
docker save -o nginx-alpine.tar nginx:alpine
```

### 2. Python 패키지 다운로드 (오프라인 설치용)

```bash
# backend 디렉토리에서 실행
cd backend
pip download -r requirements.txt -d ../python-packages/
```

### 3. 서버로 전송할 파일 목록

```
llmproject/
├── backend/              # 백엔드 소스코드
├── frontend/             # 프론트엔드 소스코드
├── python-packages/      # Python 패키지들 (오프라인)
├── docker-compose.yml    # Docker Compose 설정
├── init.sql             # DB 테이블 생성 스크립트 (참고용)
├── python-3.11-slim.tar # 베이스 이미지
├── node-20-alpine.tar   # 베이스 이미지
└── nginx-alpine.tar     # 베이스 이미지
```

---

## 🚀 폐쇄망 서버 배포 (수동 실행)

### 1. 베이스 이미지 로드

```bash
# 베이스 이미지 3개를 Docker에 로드
docker load -i python-3.11-slim.tar
docker load -i node-20-alpine.tar
docker load -i nginx-alpine.tar

# 로드 확인
docker images | grep -E "python|node|nginx"
```

### 2. 환경 변수 설정

서버의 기존 PostgreSQL, Ollama 정보를 입력합니다.

```bash
# .env 파일 생성
cd backend
cp .env.example .env
vi .env
```

**수정할 항목:**

```bash
# Ollama 설정 - 서버의 Ollama 컨테이너 주소
OLLAMA_BASE_URL=http://ollama-container-name:11434
OLLAMA_MODEL=llama3.2:1b

# PostgreSQL 설정 - 서버의 PostgreSQL 컨테이너 주소
DATABASE_URL=postgresql://user:password@postgres-container-name:5432/dbname
```

**컨테이너 이름 확인 방법:**
```bash
# 실행 중인 컨테이너 확인
docker ps

# 네트워크 확인
docker network ls
docker network inspect <network-name>
```

**연결 예시:**
- 같은 Docker 네트워크: `http://ollama:11434`, `postgresql://user:pass@postgres:5432/db`
- 호스트 네트워크: `http://host.docker.internal:11434`
- Docker 브리지 게이트웨이: `http://172.17.0.1:11434`

### 3. 서버의 기존 Docker 네트워크 연결 (옵션)

Backend/Frontend를 서버의 기존 PostgreSQL, Ollama와 연결하려면:

**방법 1: 기존 네트워크 사용**
```bash
# docker-compose.yml 수정
vi docker-compose.yml

# networks 섹션을 수정:
networks:
  app-network:
    external: true
    name: existing-network-name  # 서버의 기존 네트워크 이름
```

**방법 2: 외부 네트워크 연결**
```bash
# Backend/Frontend 실행 후
docker network connect existing-network backend
docker network connect existing-network frontend
```

### 4. PostgreSQL 테이블 생성

서버의 PostgreSQL에 `applicants` 테이블을 생성합니다.

```bash
# 서버의 PostgreSQL 컨테이너에 접속
docker exec -it postgres-container-name psql -U admin -d applicants_db

# 또는 init.sql 파일 실행
docker exec -i postgres-container-name psql -U admin -d applicants_db < init.sql
```

**테이블 구조 (init.sql 참고):**
```sql
CREATE TABLE IF NOT EXISTS applicants (
    id BIGSERIAL PRIMARY KEY,
    reason VARCHAR(4000),
    experience VARCHAR(4000),
    skill VARCHAR(4000)
);
```

### 5. 빌드 및 실행

```bash
# Backend, Frontend 빌드 + 실행 (한 번에)
docker-compose up -d --build

# 빌드 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend
```

**빌드 시간:**
- Backend: 약 2-3분 (Python 패키지 설치)
- Frontend: 약 5-10분 (npm 패키지 설치 + React 빌드)

### 6. 확인

```bash
# 컨테이너 상태 확인
docker-compose ps

# Backend API 확인
curl http://localhost:8000/health
curl http://localhost:8000/docs

# Frontend 확인
curl http://localhost

# 로그 확인
docker-compose logs -f
```

---

## 🔧 문제 해결

### PostgreSQL 연결 실패

**증상:** `could not connect to server`

**해결:**
```bash
# 1. 네트워크 연결 확인
docker exec backend ping postgres-container-name

# 2. PostgreSQL 컨테이너 확인
docker ps | grep postgres

# 3. .env 파일 확인
docker exec backend cat /app/.env

# 4. 연결 테스트
docker exec backend python -c "
from sqlmodel import create_engine
import os
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('DATABASE_URL')
print(f'Connecting to: {url}')
engine = create_engine(url)
print('Connection successful!')
"
```

### Ollama 연결 실패

**증상:** `Connection refused` on port 11434

**해결:**
```bash
# 1. Ollama 컨테이너 확인
docker ps | grep ollama

# 2. 네트워크 연결 확인
docker exec backend curl http://ollama-container-name:11434/api/version

# 3. .env 파일에서 OLLAMA_BASE_URL 확인
```

### .env 파일 수정 후 재시작

```bash
# 환경 변수만 변경한 경우 (빌드 불필요)
docker-compose restart backend

# 소스 코드 변경한 경우 (재빌드 필요)
docker-compose up -d --build backend
```

### 전체 재시작

```bash
# 중지
docker-compose down

# 재빌드 + 실행
docker-compose up -d --build
```

---

## 📝 베이스 이미지 목록

| 이미지 | 용도 | 크기 (약) |
|--------|------|-----------|
| `python:3.11-slim` | Backend 실행 환경 | ~150MB |
| `node:20-alpine` | Frontend 빌드 | ~180MB |
| `nginx:alpine` | Frontend 서빙 | ~40MB |

---

## 🔐 보안 고려사항

### 운영 환경 설정

**1. 기본 비밀번호 변경**
```bash
# backend/.env 파일에서
DATABASE_URL=postgresql://admin:강력한비밀번호@postgres:5432/applicants_db
```

**2. 포트 제한 (필요 시)**
```yaml
# docker-compose.yml 수정
services:
  backend:
    ports:
      - "127.0.0.1:8000:8000"  # localhost만 허용
  frontend:
    ports:
      - "0.0.0.0:80:80"  # 모든 IP 허용
```

**3. 네트워크 격리**
- Backend, Frontend, PostgreSQL, Ollama를 같은 Docker 네트워크에 배치
- 외부 노출이 필요한 Frontend만 포트 오픈

---

## 📌 참고사항

### Docker 네트워크 연결 방법

**1. 컨테이너 이름으로 연결 (권장)**
```bash
OLLAMA_BASE_URL=http://ollama:11434
DATABASE_URL=postgresql://admin:pass@postgres:5432/db
```

**2. IP 주소로 연결**
```bash
# PostgreSQL 컨테이너 IP 확인
docker inspect postgres-container-name | grep IPAddress

# .env에 IP 입력
DATABASE_URL=postgresql://admin:pass@172.17.0.2:5432/db
```

**3. 호스트 네트워크 사용**
```bash
# docker-compose.yml 수정
services:
  backend:
    network_mode: "host"
```

### Python 패키지 오프라인 설치

현재 `backend/Dockerfile`에서 인터넷을 통해 설치합니다.
오프라인 설치가 필요한 경우 Dockerfile을 수정하세요:

```dockerfile
# Dockerfile에 추가
COPY python-packages/ /tmp/packages/
RUN pip install --no-index --find-links=/tmp/packages/ -r requirements.txt
```
