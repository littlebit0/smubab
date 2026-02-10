import axios from 'axios';

// 개발 시에는 로컬 IP로 변경 필요
// 예: http://192.168.0.10:8000
const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface MenuItem {
  name: string;
  price?: number;
  calories?: number;
}

export interface Menu {
  id?: number;
  date: string;
  restaurant: string;
  meal_type: string;
  items: MenuItem[];
}

export interface DailyMenuResponse {
  success: boolean;
  date: string;
  menus: Menu[];
  message?: string;
}

export interface MenuResponse {
  success: boolean;
  data: Menu[];
  message?: string;
}

export const menuAPI = {
  // 오늘의 메뉴
  getTodayMenus: async (): Promise<DailyMenuResponse> => {
    const response = await api.get<DailyMenuResponse>('/api/menus/today');
    return response.data;
  },

  // 특정 날짜 메뉴
  getMenusByDate: async (date: string): Promise<DailyMenuResponse> => {
    const response = await api.get<DailyMenuResponse>(`/api/menus/date/${date}`);
    return response.data;
  },

  // 주간 메뉴
  getWeeklyMenus: async (startDate?: string): Promise<MenuResponse> => {
    const url = startDate 
      ? `/api/menus/week?start_date=${startDate}`
      : '/api/menus/week';
    const response = await api.get<MenuResponse>(url);
    return response.data;
  },

  // 식당별 메뉴
  getMenusByRestaurant: async (restaurant: string, date?: string): Promise<MenuResponse> => {
    const url = date
      ? `/api/menus/restaurant/${restaurant}?target_date=${date}`
      : `/api/menus/restaurant/${restaurant}`;
    const response = await api.get<MenuResponse>(url);
    return response.data;
  },

  // 식당 목록
  getRestaurants: async () => {
    const response = await api.get('/api/restaurants');
    return response.data;
  },

  // 메뉴 갱신
  refreshMenus: async () => {
    const response = await api.post('/api/menus/refresh');
    return response.data;
  },

  // 헬스 체크
  healthCheck: async () => {
    const response = await api.get('/api/health');
    return response.data;
  },
};

export default api;
