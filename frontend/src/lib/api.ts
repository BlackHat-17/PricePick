/**
 * API Client for PricePick Backend
 * Handles all HTTP requests to the backend API
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Types
export interface ApiError {
  detail: string;
  status?: number;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  is_active: boolean;
  is_verified: boolean;
  is_premium: boolean;
  email_notifications: boolean;
  price_drop_alerts: boolean;
  weekly_summary: boolean;
  marketing_emails: boolean;
  notification_frequency: string;
  price_change_threshold: string;
  preferred_currency: string;
  timezone: string;
  language: string;
  last_login?: string;
  login_count: number;
  api_usage_count: number;
  api_usage_limit: number;
  preferences?: Record<string, any>;
  created_at: string;
  updated_at: string;
  full_name?: string; // Computed field
}

export interface Product {
  id: number;
  name: string;
  description?: string;
  product_url: string;
  platform: string;
  category?: string;
  brand?: string;
  image_url?: string;
  current_price?: number;
  currency: string;
  is_tracking: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Price {
  id: number;
  product_id: number;
  price: number;
  currency: string;
  platform: string;
  is_sale: boolean;
  is_available: boolean;
  created_at: string;
}

export interface PriceAlert {
  id: number;
  user_id: number;
  product_id: number;
  alert_type: 'price_drop' | 'price_increase' | 'target_price';
  target_price?: number;
  threshold_percentage?: number;
  is_active: boolean;
  is_triggered: boolean;
  triggered_at?: string;
  created_at: string;
}

export interface ProductCreate {
  name: string;
  description?: string;
  product_url: string;
  platform: string;
  category?: string;
  brand?: string;
}

export interface ProductUpdate {
  name?: string;
  description?: string;
  category?: string;
  brand?: string;
  is_tracking?: boolean;
}

export interface PriceAlertCreate {
  product_id: number;
  alert_type: 'price_drop' | 'price_increase' | 'target_price';
  target_price?: number;
  threshold_percentage?: number;
}

// Helper function to get auth token
const getAuthToken = (): string | null => {
  return localStorage.getItem('auth_token');
};

// Helper function to set auth token
const setAuthToken = (token: string): void => {
  localStorage.setItem('auth_token', token);
};

// Helper function to remove auth token
const removeAuthToken = (): void => {
  localStorage.removeItem('auth_token');
};

// Base fetch function with error handling
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      detail: `HTTP ${response.status}: ${response.statusText}`,
    }));
    error.status = response.status;
    throw error;
  }

  // Handle empty responses
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json();
  }
  
  return {} as T;
}

// Auth API
export const authApi = {
  login: async (credentials: LoginRequest): Promise<TokenResponse> => {
    const response = await apiRequest<TokenResponse>('/users/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    if (response.access_token) {
      setAuthToken(response.access_token);
    }
    return response;
  },

  register: async (userData: RegisterRequest): Promise<TokenResponse> => {
    const response = await apiRequest<TokenResponse>('/users/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    if (response.access_token) {
      setAuthToken(response.access_token);
    }
    return response;
  },

  getCurrentUser: async (): Promise<User> => {
    return apiRequest<User>('/users/me');
  },

  updateUser: async (userData: Partial<User>): Promise<User> => {
    return apiRequest<User>('/users/me', {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  },

  logout: (): void => {
    removeAuthToken();
  },

  isAuthenticated: (): boolean => {
    return !!getAuthToken();
  },
};

// Products API
export const productsApi = {
  list: async (params?: {
    skip?: number;
    limit?: number;
    platform?: string;
    category?: string;
    brand?: string;
    is_tracking?: boolean;
    search?: string;
  }): Promise<{ items: Product[]; total: number; skip: number; limit: number }> => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value));
        }
      });
    }
    const query = queryParams.toString();
    return apiRequest(`/products/?${query}`);
  },

  get: async (id: number): Promise<Product> => {
    return apiRequest<Product>(`/products/${id}`);
  },

  create: async (product: ProductCreate): Promise<Product> => {
    return apiRequest<Product>('/products/', {
      method: 'POST',
      body: JSON.stringify(product),
    });
  },

  update: async (id: number, product: ProductUpdate): Promise<Product> => {
    return apiRequest<Product>(`/products/${id}`, {
      method: 'PUT',
      body: JSON.stringify(product),
    });
  },

  delete: async (id: number): Promise<void> => {
    return apiRequest<void>(`/products/${id}`, {
      method: 'DELETE',
    });
  },

  scrape: async (id: number): Promise<any> => {
    return apiRequest(`/products/${id}/scrape`, {
      method: 'POST',
    });
  },
};

// Prices API
export const pricesApi = {
  list: async (params?: {
    product_id?: number;
    platform?: string;
    currency?: string;
    is_sale?: boolean;
    is_available?: boolean;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }): Promise<Price[]> => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value));
        }
      });
    }
    const query = queryParams.toString();
    return apiRequest(`/prices/?${query}`);
  },

  getHistory: async (productId: number): Promise<Price[]> => {
    return apiRequest<Price[]>(`/prices/product/${productId}/history`);
  },

  getPriceDrops: async (): Promise<any> => {
    return apiRequest('/prices/alerts/price-drops');
  },

  getPopularTrends: async (): Promise<any> => {
    return apiRequest('/prices/trends/popular');
  },
};

// Alerts API
export const alertsApi = {
  list: async (params?: {
    user_id?: number;
    is_active?: boolean;
    alert_type?: string;
    product_id?: number;
    skip?: number;
    limit?: number;
  }): Promise<PriceAlert[]> => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value));
        }
      });
    }
    const query = queryParams.toString();
    return apiRequest(`/monitoring/alerts?${query}`);
  },

  create: async (alert: PriceAlertCreate, userId: number): Promise<PriceAlert> => {
    const queryParams = new URLSearchParams({ user_id: String(userId) });
    return apiRequest<PriceAlert>(`/monitoring/alerts?${queryParams}`, {
      method: 'POST',
      body: JSON.stringify(alert),
    });
  },

  update: async (id: number, alert: Partial<PriceAlertCreate>): Promise<PriceAlert> => {
    return apiRequest<PriceAlert>(`/monitoring/alerts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(alert),
    });
  },

  delete: async (id: number): Promise<void> => {
    return apiRequest<void>(`/monitoring/alerts/${id}`, {
      method: 'DELETE',
    });
  },
};

// Search API
export const searchApi = {
  search: async (query: string, platforms?: string[]): Promise<any> => {
    return apiRequest('/search', {
      method: 'POST',
      body: JSON.stringify({
        query,
        platforms: platforms || [],
      }),
    });
  },
};

// Health check
export const healthApi = {
  check: async (): Promise<any> => {
    return fetch(`${API_BASE_URL.replace('/api/v1', '')}/health`).then((res) => res.json());
  },
};

