import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

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

  getWeeklyMenus: async (startDate?: string): Promise<MenuResponse> => {
    const url = startDate 
      ? `/api/menus/week?start_date=${startDate}`
      : '/api/menus/week';
    const response = await api.get<MenuResponse>(url);
    return response.data;
  },

  getMonthlyMenus: async (year?: number, month?: number): Promise<MenuResponse> => {
    let url = '/api/menus/month';
    if (year && month) {
      url += `?year=${year}&month=${month}`;
    }
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
