#!/bin/bash

# SMU-Bab Backend Server Start Script

echo "🚀 상명대학교 학식 백엔드 서버를 시작합니다..."
echo ""

# 백엔드 디렉토리로 이동
cd "$(dirname "$0")"

# 의존성 확인
echo "📦 의존성 확인 중..."
if ! pip show fastapi > /dev/null 2>&1; then
    echo "⚠️  의존성이 설치되지 않았습니다. 설치를 시작합니다..."
    pip install -r requirements.txt
fi

echo ""
echo "✅ 서버를 시작합니다..."
echo "📡 API 문서: http://localhost:8000/docs"
echo "📡 Health Check: http://localhost:8000/api/health"
echo ""
echo "종료하려면 Ctrl+C를 누르세요."
echo ""

# 서버 실행
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
