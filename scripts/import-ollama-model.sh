#!/bin/bash

# Ollama 모델을 가져오는 스크립트
# 폐쇄망 환경에서 사용

set -e

IMPORT_DIR="./ollama-models"

echo "=========================================="
echo "Ollama 모델 가져오기"
echo "=========================================="

# 디렉토리 확인
if [ ! -d "$IMPORT_DIR/models" ]; then
    echo "Error: $IMPORT_DIR/models 디렉토리가 없습니다."
    echo "export-ollama-model.sh를 먼저 실행하여 모델을 내보내세요."
    exit 1
fi

# Ollama 컨테이너가 실행 중인지 확인
if ! docker ps | grep -q ollama; then
    echo "Ollama 컨테이너 시작 중..."
    docker-compose up -d ollama
    echo "Ollama 시작 대기 중 (10초)..."
    sleep 10
fi

# 모델 파일 복사
echo "모델 파일을 Ollama 컨테이너로 복사 중..."
docker cp "$IMPORT_DIR/models" ollama:/root/.ollama/

# Ollama 재시작
echo "Ollama 재시작 중..."
docker-compose restart ollama

echo "Ollama 시작 대기 중 (5초)..."
sleep 5

# 모델 목록 확인
echo ""
echo "=========================================="
echo "설치된 모델 목록:"
echo "=========================================="
docker exec ollama ollama list

echo ""
echo "=========================================="
echo "모델 가져오기 완료!"
echo "=========================================="
