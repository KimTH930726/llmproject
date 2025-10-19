#!/bin/bash

# Python 및 Node.js 의존성 패키지를 가져오는 스크립트
# 폐쇄망 환경에서 사용

set -e

IMPORT_DIR="./offline-packages"

echo "=========================================="
echo "의존성 패키지 가져오기"
echo "=========================================="

# 디렉토리 확인
if [ ! -d "$IMPORT_DIR" ]; then
    echo "Error: $IMPORT_DIR 디렉토리가 없습니다."
    exit 1
fi

# Python 패키지 설치
if [ -d "$IMPORT_DIR/python" ]; then
    echo "1. Python 패키지 설치 중..."
    cd backend

    # 가상환경이 없으면 생성
    if [ ! -d "venv" ]; then
        python -m venv venv
    fi

    # 가상환경 활성화
    source venv/bin/activate

    # 오프라인 패키지 설치
    pip install --no-index --find-links="../$IMPORT_DIR/python" -r requirements.txt

    deactivate
    cd ..
    echo "Python 패키지 설치 완료"
else
    echo "Warning: $IMPORT_DIR/python 디렉토리가 없습니다."
fi

# Node.js 패키지 설치
echo ""
if [ -d "$IMPORT_DIR/node" ]; then
    echo "2. Node.js 패키지 설치 중..."
    cd frontend

    # node_modules tar 파일 찾기
    NODE_MODULES_TAR=$(find "../$IMPORT_DIR/node" -name "node_modules_*.tar.gz" | head -n 1)

    if [ -n "$NODE_MODULES_TAR" ]; then
        echo "node_modules 압축 해제 중..."
        tar -xzf "$NODE_MODULES_TAR"
        echo "Node.js 패키지 설치 완료"
    else
        echo "Warning: node_modules tar 파일을 찾을 수 없습니다."
    fi

    cd ..
else
    echo "Warning: $IMPORT_DIR/node 디렉토리가 없습니다."
fi

echo ""
echo "=========================================="
echo "의존성 패키지 가져오기 완료!"
echo "=========================================="
