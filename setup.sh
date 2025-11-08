#!/bin/bash

echo "===================================="
echo "  스미싱 지킴이 초기 설정"
echo "===================================="
echo

# Python 버전 확인
if ! command -v python3 &> /dev/null; then
    echo "[오류] Python이 설치되어 있지 않습니다."
    echo "Python 3.9 이상을 설치해주세요: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

echo "[1/4] Python 가상환경 생성 중..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ 가상환경 생성 완료"
else
    echo "✓ 가상환경이 이미 존재합니다"
fi

echo
echo "[2/4] 가상환경 활성화 중..."
source venv/bin/activate

echo
echo "[3/4] 패키지 설치 중..."
python -m pip install --upgrade pip
pip install -r requirements.txt
echo "✓ 패키지 설치 완료"

echo
echo "[4/4] 환경변수 파일 생성 중..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ .env 파일이 생성되었습니다"
    echo
    echo "===================================="
    echo "  중요: OpenAI API 키 설정 필요!"
    echo "===================================="
    echo
    echo ".env 파일을 열어서 OPENAI_API_KEY를 입력하세요."
    echo "1. https://platform.openai.com/api-keys 에서 API 키 발급"
    echo "2. .env 파일에 키 입력"
    echo "3. ./run_app.sh 실행"
else
    echo "✓ .env 파일이 이미 존재합니다"
fi

echo
echo "===================================="
echo "  설정 완료!"
echo "===================================="
echo
echo "다음 단계:"
echo "1. .env 파일에 OpenAI API 키 입력"
echo "2. ./run_app.sh 실행"
echo
