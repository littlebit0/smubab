import axios from 'axios';

const localBackendUrl = 'http://127.0.0.1:8000';
const apiBaseUrl = (import.meta.env.VITE_API_URL || localBackendUrl).replace(/\/$/, '');
const pushApiBaseUrl = (import.meta.env.VITE_PUSH_API_URL || apiBaseUrl).replace(/\/$/, '');

const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30000,
});

const pushApi = axios.create({
  baseURL: pushApiBaseUrl,
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
  error?: string;
}

export interface MenuResponse {
  success: boolean;
  data: Menu[];
  message?: string;
  error?: string;
}

export interface PushSubscriptionPayload {
  endpoint: string;
  expirationTime: number | null;
  keys: {
    p256dh: string;
    auth: string;
  };
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

export const pushAPI = {
  isConfigured: () => !!pushApiBaseUrl,

  getPublicKey: async (): Promise<string | null> => {
    const response = await pushApi.get<{ success: boolean; publicKey?: string | null }>(
      '/api/push/public-key',
    );
    if (!response.data?.success) return null;
    return response.data.publicKey || null;
  },

  subscribe: async (subscription: PushSubscriptionPayload) => {
    const response = await pushApi.post('/api/push/subscribe', { subscription });
    return response.data;
  },

  unsubscribe: async (endpoint: string) => {
    const response = await pushApi.post('/api/push/unsubscribe', { endpoint });
    return response.data;
  },

  sendTestPush: async () => {
    const response = await pushApi.post('/api/push/test');
    return response.data as {
      success: boolean;
      message: string;
      delaySeconds: number;
      subscriptionCount: number;
    };
  },
};

export default api;
