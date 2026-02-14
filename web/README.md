# SMU-Bab Web

상명대학교 학식 정보를 확인할 수 있는 웹 애플리케이션입니다.

## 기술 스택

- React 18
- TypeScript
- Vite
- Axios
- date-fns

## 설치 및 실행

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 빌드
npm run build

# 빌드 미리보기
npm run preview
```

## 개발 서버

- 개발 서버: http://localhost:3000
- 백엔드 API: http://localhost:8000

## 기능

- 📅 오늘의 메뉴 보기
- 📆 주간 메뉴 보기
- 🍽️ 식당별 메뉴 구분
- 💰 가격 정보
- 🔄 메뉴 새로고침
- 🔔 홈 화면 앱(iOS Safari) 웹 푸시 알림

## 웹 푸시 알림 설정

1. `VITE_PUSH_API_URL`(또는 `VITE_API_URL`)을 백엔드 주소로 설정
2. 백엔드에 `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_CLAIMS_SUB` 설정
3. iOS Safari에서 사이트를 홈 화면에 추가 후 앱 실행
4. 앱 하단의 "메뉴 업데이트 알림 켜기" 버튼으로 권한 허용

## 배포

```bash
npm run build
```

빌드된 파일은 `dist` 폴더에 생성됩니다.
