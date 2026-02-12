import axios from 'axios';

const API_BASE_URL = '';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
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
  getTodayMenus: async (): Promise<DailyMenuResponse> => {
    const response = await api.get<DailyMenuResponse>('/api/menus/today');
    return response.data;
  },

  getMenusByDate: async (date: string): Promise<DailyMenuResponse> => {
    const response = await api.get<DailyMenuResponse>(`/api/menus/date/${date}`);
    return response.data;
  },

  getWeeklyMenus: async (targetDate?: string): Promise<MenuResponse> => {
    const url = targetDate 
      ? `/api/menus/week?target_date=${targetDate}`
      : '/api/menus/week';
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
