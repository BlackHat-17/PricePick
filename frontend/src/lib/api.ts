/**
 * API Client for PricePick Backend (Firebase Auth Version)
 * Handles all HTTP requests to the backend API
 */

import { getAuth } from "firebase/auth"; // ✅ Use official Firebase SDK
import { app } from "../services/firebase/firebase"; // ✅ Adjust this path if needed (where your firebase config is)

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

// ----------------------
// Type Definitions
// ----------------------

export interface ApiError {
  detail: string;
  status?: number;
}

export interface Product {
  id: string;
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

// ----------------------
// Firebase Token Helper
// ----------------------

const getAuthToken = async (): Promise<string | null> => {
  const auth = getAuth(app);
  const user = auth.currentUser;
  if (!user) return null;
  try {
    return await user.getIdToken();
  } catch (err) {
    console.error("Failed to get Firebase token:", err);
    return null;
  }
};

// ----------------------
// Core Request Handler
// ----------------------

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAuthToken();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  } else {
    console.warn("⚠️ No Firebase token found — unauthenticated request");
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

  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return response.json();
  }

  return {} as T;
}

// ----------------------
// Products API
// ----------------------

export const productsApi = {
  list: async (params?: {
    skip?: number;
    limit?: number;
    platform?: string;
    category?: string;
    brand?: string;
    is_tracking?: boolean;
    search?: string;
  }): Promise<{ items: Product[]; total?: number }> => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null)
          queryParams.append(key, String(value));
      });
    }
    const query = queryParams.toString();
    return apiRequest(`/products/?${query}`);
  },

  get: async (id: string): Promise<Product> => {
    return apiRequest<Product>(`/products/${id}`);
  },

  create: async (product: ProductCreate): Promise<Product> => {
    return apiRequest<Product>("/products/", {
      method: "POST",
      body: JSON.stringify(product),
    });
  },

  update: async (id: string, product: ProductUpdate): Promise<Product> => {
    return apiRequest<Product>(`/products/${id}`, {
      method: "PUT",
      body: JSON.stringify(product),
    });
  },

  delete: async (id: string): Promise<void> => {
    return apiRequest<void>(`/products/${id}`, {
      method: "DELETE",
    });
  },
};

// ----------------------
// Health Check API
// ----------------------

export const healthApi = {
  check: async (): Promise<any> => {
    return fetch(`${API_BASE_URL.replace("/api/v1", "")}/health`).then((res) =>
      res.json()
    );
  },
};
