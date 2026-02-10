#!/bin/bash

# Tesseract OCR 설치 스크립트

echo "📦 Tesseract OCR 설치 중..."

# Ubuntu/Debian
if command -v apt-get &> /dev/null; then
    echo "apt-get을 사용하여 설치합니다..."
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr tesseract-ocr-kor
    
# Mac
elif command -v brew &> /dev/null; then
    echo "Homebrew를 사용하여 설치합니다..."
    brew install tesseract tesseract-lang
    
else
    echo "⚠️  패키지 관리자를 찾을 수 없습니다."
    echo "Tesseract OCR을 수동으로 설치해주세요:"
    echo "- Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-kor"
    echo "- Mac: brew install tesseract tesseract-lang"
    echo "- Windows: https://github.com/UB-Mannheim/tesseract/wiki"
    exit 1
fi

# 설치 확인
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract 설치 완료!"
    tesseract --version
else
    echo "❌ Tesseract 설치 실패"
    exit 1
fi

echo ""
echo "한국어 언어 데이터 확인 중..."
tesseract --list-langs | grep kor && echo "✅ 한국어 OCR 준비 완료!" || echo "⚠️  한국어 데이터가 없습니다."
