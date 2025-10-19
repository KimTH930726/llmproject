#!/bin/bash

# Docker 이미지를 tar 파일에서 가져오는 스크립트
# 폐쇄망 환경에서 사용

set -e

IMPORT_DIR="./docker-images"

echo "=========================================="
echo "Docker 이미지 가져오기 시작"
echo "=========================================="

# 디렉토리 확인
if [ ! -d "$IMPORT_DIR" ]; then
    echo "Error: $IMPORT_DIR 디렉토리가 없습니다."
    exit 1
fi

# tar 파일 목록 확인
TAR_FILES=$(find "$IMPORT_DIR" -name "*.tar" | sort)

if [ -z "$TAR_FILES" ]; then
    echo "Error: $IMPORT_DIR 에 .tar 파일이 없습니다."
    exit 1
fi

echo "가져올 이미지 파일 목록:"
echo "$TAR_FILES"
echo ""

# 각 tar 파일 가져오기
for tar_file in $TAR_FILES; do
    echo "가져오는 중: $tar_file"
    docker load -i "$tar_file"
    echo "완료: $tar_file"
    echo ""
done

echo "=========================================="
echo "모든 이미지 가져오기 완료!"
echo "=========================================="
echo ""
echo "로드된 이미지 목록:"
docker images

echo ""
echo "=========================================="
echo "다음 단계:"
echo "  1. Ollama 모델 가져오기: ./scripts/export-ollama-model.sh (내보내기)"
echo "  2. Ollama 모델 설치: ./scripts/import-ollama-model.sh (가져오기)"
echo "  3. 서비스 실행: docker-compose up -d"
echo "=========================================="
