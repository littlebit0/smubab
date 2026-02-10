#!/bin/bash

# SMU-Bab Mobile App Start Script

echo "📱 상명대학교 학식 모바일 앱을 시작합니다..."
echo ""

# 모바일 디렉토리로 이동
cd "$(dirname "$0")"

# node_modules 확인
if [ ! -d "node_modules" ]; then
    echo "📦 의존성 설치 중... (시간이 걸릴 수 있습니다)"
    npm install --legacy-peer-deps
fi

echo ""
echo "✅ Expo 개발 서버를 시작합니다..."
echo ""
echo "🔧 API 서버 주소를 확인하세요:"
echo "   src/api/menuAPI.ts 파일에서 API_BASE_URL을 로컬 IP로 변경하세요."
echo ""
echo "📱 Expo Go 앱을 설치하고 QR 코드를 스캔하세요."
echo ""

# Expo 시작
npm start
