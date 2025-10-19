#!/bin/bash

# Python 및 Node.js 의존성 패키지를 내보내는 스크립트
# 폐쇄망 이식을 위해 사용

set -e

EXPORT_DIR="./offline-packages"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "의존성 패키지 내보내기"
echo "=========================================="

# 내보내기 디렉토리 생성
mkdir -p "$EXPORT_DIR/python"
mkdir -p "$EXPORT_DIR/node"

# Python 패키지 다운로드
echo "1. Python 패키지 다운로드 중..."
if [ -f "./backend/requirements.txt" ]; then
    pip download -r ./backend/requirements.txt -d "$EXPORT_DIR/python"
    echo "Python 패키지 다운로드 완료"
else
    echo "Warning: backend/requirements.txt 파일을 찾을 수 없습니다."
fi

# Node.js 패키지 다운로드
echo ""
echo "2. Node.js 패키지 번들링 중..."
if [ -f "./frontend/package.json" ]; then
    cd frontend
    # package-lock.json을 기반으로 오프라인 캐시 생성
    npm ci --cache "../$EXPORT_DIR/node/.npm" --prefer-offline

    # node_modules를 tar로 압축
    echo "node_modules 압축 중..."
    tar -czf "../$EXPORT_DIR/node/node_modules_${TIMESTAMP}.tar.gz" node_modules

    cd ..
    echo "Node.js 패키지 번들링 완료"
else
    echo "Warning: frontend/package.json 파일을 찾을 수 없습니다."
fi

echo ""
echo "=========================================="
echo "내보내기 완료!"
echo "저장 위치: $EXPORT_DIR"
echo "=========================================="
echo ""
echo "디렉토리 크기:"
du -sh "$EXPORT_DIR"/*

echo ""
echo "=========================================="
echo "폐쇄망으로 이식 시:"
echo "  1. $EXPORT_DIR 디렉토리를 폐쇄망으로 복사"
echo "  2. ./scripts/import-dependencies.sh 실행"
echo "=========================================="
