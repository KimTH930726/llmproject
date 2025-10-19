#!/bin/bash

# Docker 이미지를 tar 파일로 내보내는 스크립트
# 폐쇄망 이식을 위해 사용

set -e

EXPORT_DIR="./docker-images"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "Docker 이미지 내보내기 시작"
echo "=========================================="

# 내보내기 디렉토리 생성
mkdir -p "$EXPORT_DIR"

# 프로젝트 이미지 빌드
echo "1. 프로젝트 이미지 빌드 중..."
docker-compose build

# 백엔드 이미지 내보내기
echo "2. 백엔드 이미지 내보내기 중..."
docker save -o "$EXPORT_DIR/backend_${TIMESTAMP}.tar" llmproject-backend:latest

# 프론트엔드 이미지 내보내기
echo "3. 프론트엔드 이미지 내보내기 중..."
docker save -o "$EXPORT_DIR/frontend_${TIMESTAMP}.tar" llmproject-frontend:latest

# Ollama 이미지 내보내기
echo "4. Ollama 이미지 내보내기 중..."
docker pull ollama/ollama:latest
docker save -o "$EXPORT_DIR/ollama_${TIMESTAMP}.tar" ollama/ollama:latest

# 추가 베이스 이미지들 (필요시)
echo "5. 베이스 이미지 내보내기 중..."
docker pull python:3.11-slim
docker save -o "$EXPORT_DIR/python_3.11-slim_${TIMESTAMP}.tar" python:3.11-slim

docker pull node:18-alpine
docker save -o "$EXPORT_DIR/node_18-alpine_${TIMESTAMP}.tar" node:18-alpine

docker pull nginx:alpine
docker save -o "$EXPORT_DIR/nginx_alpine_${TIMESTAMP}.tar" nginx:alpine

echo ""
echo "=========================================="
echo "내보내기 완료!"
echo "저장 위치: $EXPORT_DIR"
echo "=========================================="
echo ""
echo "내보낸 파일 목록:"
ls -lh "$EXPORT_DIR"/*.tar

echo ""
echo "=========================================="
echo "폐쇄망으로 이식 시 다음 명령어를 사용하세요:"
echo "  ./scripts/import-images.sh"
echo "=========================================="
