import axios from 'axios';

// 기본은 백엔드 API 사용, Netlify Functions는 명시적으로만 사용
// 프로덕션 환경에서도 VITE_API_URL이 있으면 해당 API를 사용
const isProduction = import.meta.env.PROD;
const apiBaseUrl = import.meta.env.VITE_API_URL || '';
const useNetlifyFunctions = isProduction && !apiBaseUrl;
const API_BASE_URL = apiBaseUrl;

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // Functions는 더 오래 걸릴 수 있음
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
  error?: string;
}

export interface MenuResponse {
  success: boolean;
  data: Menu[];
  message?: string;
  error?: string;
}

export const menuAPI = {
  getTodayMenus: async (): Promise<DailyMenuResponse> => {
    // Netlify Functions 사용
    const url = useNetlifyFunctions
      ? '/.netlify/functions/getTodayMenus'
      : '/api/menus/today';
    const response = await api.get<DailyMenuResponse>(url);
    return response.data;
  },

  getMenusByDate: async (date: string): Promise<DailyMenuResponse> => {
    const response = await api.get<DailyMenuResponse>(`/api/menus/date/${date}`);
    return response.data;
  },

  getWeeklyMenus: async (targetDate?: string): Promise<MenuResponse> => {
    // Netlify Functions 사용
    const url = useNetlifyFunctions
      ? '/.netlify/functions/getWeeklyMenus'
      : (targetDate 
        ? `/api/menus/week?target_date=${targetDate}`
        : '/api/menus/week');
    const response = await api.get<MenuResponse>(url);
    return response.data;
  },

  getRestaurants: async () => {
    const response = await api.get('/api/restaurants');
    return response.data;
  },

  refreshMenus: async () => {
    const response = await api.post('/api/menus/refresh');
    return response.data;
  },
};

export default api;
