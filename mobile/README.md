# SMU-Bab Mobile

상명대학교 학식 정보를 제공하는 React Native 모바일 애플리케이션입니다.

## 기능

- 📅 오늘의 메뉴 보기
- 📆 주간 메뉴 보기
- 🍽️ 식당별 메뉴 구분
- 💰 가격 정보
- 🔔 메뉴 알림 기능

## 개발 환경 설정

### 필수 요구사항

- Node.js 16+
- npm 또는 yarn
- Expo CLI

### 설치

```bash
npm install
# 또는
yarn install
```

## 실행

### 개발 모드

```bash
npm start
# 또는
expo start
```

Expo Go 앱을 설치한 후 QR 코드를 스캔하여 실행할 수 있습니다.

### Android

```bash
npm run android
```

### iOS

```bash
npm run ios
```

## 백엔드 연결

`src/api/menuAPI.ts` 파일에서 API 서버 주소를 설정하세요.

개발 시에는 로컬 네트워크 IP 주소를 사용해야 합니다:

```typescript
const API_BASE_URL = 'http://192.168.0.10:8000';  // 자신의 IP로 변경
```

자신의 IP 주소 확인:
- Windows: `ipconfig`
- Mac/Linux: `ifconfig` 또는 `ip addr`

## 프로젝트 구조

```
mobile/
├── App.tsx                    # 메인 앱 컴포넌트
├── src/
│   ├── api/
│   │   └── menuAPI.ts        # API 통신
│   └── screens/
│       ├── TodayScreen.tsx   # 오늘 메뉴 화면
│       ├── WeeklyScreen.tsx  # 주간 메뉴 화면
│       └── SettingsScreen.tsx # 설정 화면
├── app.json                   # Expo 설정
├── package.json
└── tsconfig.json
```

## 알림 기능

알림 기능을 사용하려면:

1. 앱 설정에서 알림 권한 허용
2. 원하는 시간대(아침/점심/저녁) 알림 활성화

## 빌드

### Android APK

```bash
eas build --platform android
```

### iOS

```bash
eas build --platform ios
```

EAS Build를 사용하기 위해서는 Expo 계정이 필요합니다.

## 라이선스

MIT
