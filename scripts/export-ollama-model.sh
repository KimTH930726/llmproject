#!/bin/bash

# Ollama 모델을 내보내는 스크립트
# 폐쇄망 이식을 위해 사용

set -e

EXPORT_DIR="./ollama-models"
MODEL_NAME=${1:-llama2}

echo "=========================================="
echo "Ollama 모델 내보내기"
echo "모델: $MODEL_NAME"
echo "=========================================="

# 내보내기 디렉토리 생성
mkdir -p "$EXPORT_DIR"

# Ollama가 실행 중인지 확인
if ! curl -s http://localhost:11434/api/version > /dev/null; then
    echo "Error: Ollama가 실행되고 있지 않습니다."
    echo "다음 명령어로 Ollama를 실행하세요:"
    echo "  docker-compose up -d ollama"
    exit 1
fi

# 모델이 설치되어 있는지 확인
if ! docker exec ollama ollama list | grep -q "$MODEL_NAME"; then
    echo "모델을 다운로드 중: $MODEL_NAME"
    docker exec ollama ollama pull "$MODEL_NAME"
fi

# 모델 파일 위치 찾기 및 복사
echo "모델 파일 복사 중..."
docker cp ollama:/root/.ollama/models "$EXPORT_DIR/"

echo ""
echo "=========================================="
echo "내보내기 완료!"
echo "저장 위치: $EXPORT_DIR"
echo "=========================================="
echo ""
echo "디렉토리 크기:"
du -sh "$EXPORT_DIR"

echo ""
echo "=========================================="
echo "폐쇄망으로 이식 시:"
echo "  1. $EXPORT_DIR 디렉토리를 폐쇄망으로 복사"
echo "  2. ./scripts/import-ollama-model.sh 실행"
echo "=========================================="
