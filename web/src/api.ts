import axios from 'axios';

// 기본은 백엔드 API 사용, Netlify Functions는 명시적으로만 사용
// 프로덕션 환경에서도 VITE_API_URL이 있으면 해당 API를 사용
const isProduction = import.meta.env.PROD;
const apiBaseUrl = import.meta.env.VITE_API_URL || '';
const pushApiBaseUrl = import.meta.env.VITE_PUSH_API_URL || apiBaseUrl || '';
const useNetlifyFunctions = isProduction && !apiBaseUrl;
const useNetlifyPushFunctions = isProduction && !pushApiBaseUrl;
const API_BASE_URL = apiBaseUrl;

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // Functions는 더 오래 걸릴 수 있음
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

export const pushAPI = {
  isConfigured: () => !!pushApiBaseUrl || useNetlifyPushFunctions,

  getPublicKey: async (): Promise<string | null> => {
    const response = useNetlifyPushFunctions
      ? await api.get<{ success: boolean; publicKey?: string | null }>(
        '/.netlify/functions/getPushPublicKey'
      )
      : await pushApi.get<{ success: boolean; publicKey?: string | null }>(
        '/api/push/public-key'
      );
    if (!response.data?.success) return null;
    return response.data.publicKey || null;
  },

  subscribe: async (subscription: PushSubscriptionPayload) => {
    const response = useNetlifyPushFunctions
      ? await api.post('/.netlify/functions/subscribePush', { subscription })
      : await pushApi.post('/api/push/subscribe', { subscription });
    return response.data;
  },

  unsubscribe: async (endpoint: string) => {
    const response = useNetlifyPushFunctions
      ? await api.post('/.netlify/functions/unsubscribePush', { endpoint })
      : await pushApi.post('/api/push/unsubscribe', { endpoint });
    return response.data;
  },

  sendTestPush: async () => {
    const response = useNetlifyPushFunctions
      ? await api.post('/.netlify/functions/testPush')
      : await pushApi.post('/api/push/test');
    return response.data as {
      success: boolean;
      message: string;
      delaySeconds: number;
      subscriptionCount: number;
    };
  },
};

export default api;
