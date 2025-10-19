#!/bin/bash

# 전체 프로젝트를 폐쇄망으로 이식하기 위한 완전한 내보내기 스크립트

set -e

EXPORT_BASE="./export-package"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
EXPORT_DIR="${EXPORT_BASE}_${TIMESTAMP}"

echo "=========================================="
echo "전체 프로젝트 내보내기"
echo "내보내기 디렉토리: $EXPORT_DIR"
echo "=========================================="

# 내보내기 디렉토리 생성
mkdir -p "$EXPORT_DIR"

# 1. 소스 코드 복사 (git 제외)
echo ""
echo "1. 소스 코드 복사 중..."
rsync -av --progress \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='dist' \
    --exclude='export-package*' \
    --exclude='docker-images' \
    --exclude='ollama-models' \
    --exclude='offline-packages' \
    ./ "$EXPORT_DIR/source/"

# 2. Docker 이미지 내보내기
echo ""
echo "2. Docker 이미지 내보내기 중..."
mkdir -p "$EXPORT_DIR/docker-images"

# 임시로 docker-images 디렉토리 변경
ORIGINAL_DOCKER_EXPORT="./docker-images"
mv ./docker-images "$EXPORT_DIR/docker-images" 2>/dev/null || true

./scripts/export-images.sh

# docker-images를 export 디렉토리로 이동
if [ -d "./docker-images" ]; then
    mv ./docker-images/* "$EXPORT_DIR/docker-images/" 2>/dev/null || true
    rmdir ./docker-images 2>/dev/null || true
fi

# 3. Ollama 모델 내보내기
echo ""
echo "3. Ollama 모델 내보내기 중..."
mkdir -p "$EXPORT_DIR/ollama-models"

# 임시로 ollama-models 디렉토리 변경
./scripts/export-ollama-model.sh

if [ -d "./ollama-models" ]; then
    mv ./ollama-models/* "$EXPORT_DIR/ollama-models/" 2>/dev/null || true
    rmdir ./ollama-models 2>/dev/null || true
fi

# 4. 의존성 패키지 내보내기
echo ""
echo "4. 의존성 패키지 내보내기 중..."
mkdir -p "$EXPORT_DIR/offline-packages"

./scripts/export-dependencies.sh

if [ -d "./offline-packages" ]; then
    mv ./offline-packages/* "$EXPORT_DIR/offline-packages/" 2>/dev/null || true
    rmdir ./offline-packages 2>/dev/null || true
fi

# 5. 설치 가이드 생성
echo ""
echo "5. 설치 가이드 생성 중..."
cat > "$EXPORT_DIR/INSTALL.md" << 'EOF'
# 폐쇄망 설치 가이드

## 사전 요구사항

1. Docker 및 Docker Compose 설치
2. Python 3.10+ 설치
3. Node.js 18+ 설치

## 설치 순서

### 1. 프로젝트 파일 복사
```bash
cd source
```

### 2. Docker 이미지 가져오기
```bash
./scripts/import-images.sh
```

### 3. Ollama 모델 가져오기
```bash
./scripts/import-ollama-model.sh
```

### 4. 의존성 패키지 설치 (선택사항)
Docker를 사용하지 않고 직접 실행하려면:
```bash
./scripts/import-dependencies.sh
```

### 5. 환경 설정
```bash
cd backend
cp .env.example .env
# .env 파일을 환경에 맞게 수정
cd ..
```

### 6. 서비스 실행
```bash
docker-compose up -d
```

### 7. 서비스 확인
- 백엔드 API 문서: http://localhost:8000/docs
- 프론트엔드: http://localhost
- Ollama: http://localhost:11434

## 문제 해결

### 로그 확인
```bash
docker-compose logs -f
```

### 서비스 재시작
```bash
docker-compose restart
```

### 전체 재시작
```bash
docker-compose down
docker-compose up -d
```
EOF

# 6. 압축 (선택사항)
echo ""
echo "6. 전체 패키지 압축 중..."
tar -czf "${EXPORT_DIR}.tar.gz" "$EXPORT_DIR"

echo ""
echo "=========================================="
echo "전체 내보내기 완료!"
echo "=========================================="
echo ""
echo "내보낸 디렉토리: $EXPORT_DIR"
echo "압축 파일: ${EXPORT_DIR}.tar.gz"
echo ""
du -sh "$EXPORT_DIR"
du -sh "${EXPORT_DIR}.tar.gz"

echo ""
echo "=========================================="
echo "폐쇄망으로 이식 시:"
echo "  1. ${EXPORT_DIR}.tar.gz 파일을 폐쇄망으로 복사"
echo "  2. tar -xzf ${EXPORT_DIR}.tar.gz"
echo "  3. cd ${EXPORT_DIR}/source"
echo "  4. INSTALL.md 파일을 참고하여 설치"
echo "=========================================="
