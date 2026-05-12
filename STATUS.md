# SMU-Bab 진행 상태

기준일: 2026-05-12

## 완료

- Netlify는 프론트엔드 정적 사이트 용도로 유지했습니다.
- 백엔드는 원격 배포 없이 로컬 컴퓨터에서만 실행되도록 정리했습니다.
- Render 배포 설정 파일 `render.yaml`을 제거했습니다.
- 백엔드 `Dockerfile`을 제거했습니다.
- PostgreSQL/DATABASE_URL 의존을 제거하고 로컬 SQLite 저장 방식으로 정리했습니다.
- Netlify Functions 기반 메뉴/푸시 프록시를 제거했습니다.
- Netlify 환경변수 `BACKEND_API_URL`은 삭제했습니다.
- 웹/React Native/Flutter 기본 API 주소를 `http://127.0.0.1:8000` 기준으로 맞췄습니다.
- 메뉴 캐시는 로컬 백엔드 SQLite에 저장된 결과를 API로 즉시 제공하는 구조입니다.
- 서울캠퍼스/천안캠퍼스, 아침/점심 탭 UI는 웹앱에 적용되어 있습니다.

## 현재 운영 구조

```text
브라우저 또는 앱
  -> http://127.0.0.1:8000
  -> 로컬 FastAPI 백엔드
  -> backend/smubab.db SQLite 캐시
  -> 필요 시 상명대학교 식당 페이지 수집/OCR 갱신
```

Netlify에 올라간 웹앱도 같은 컴퓨터에서 실행 중인 로컬 백엔드에 직접 요청합니다. 따라서 Netlify 사이트만 열고 로컬 백엔드를 실행하지 않으면 메뉴가 표시되지 않습니다.

## 확인한 항목

- 백엔드 Python 문법 확인: 통과
- 웹 빌드 확인: 통과
- Render/PostgreSQL/Docker 배포 구성 제거: 완료
- Netlify Functions 제거: 완료

## 남은 작업

- 실제 운영 컴퓨터에서 백엔드를 계속 켜둘 실행 방식 선택
- 휴대폰 실기기 테스트 시 LAN IP 또는 터널 주소로 API 주소 조정
- 푸시 알림을 실제 기기에서 쓰려면 VAPID 키 설정 필요
- OCR 품질은 실제 천안캠퍼스 게시물 이미지 양식이 바뀔 때마다 재점검 필요

## 실행 요약

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

```powershell
cd web
npm run build
```
