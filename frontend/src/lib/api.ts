/**
 * Axios API client with JWT interceptors
 */

import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Create axios instance with interceptors
 */
export function createApiClient(): AxiosInstance {
  const api = axios.create({
    baseURL: `${API_BASE_URL}/api/v1`,
    headers: {
      "Content-Type": "application/json",
    },
    withCredentials: true,
  });

  // Request interceptor: Add JWT token
  api.interceptors.request.use(
    async (config: InternalAxiosRequestConfig) => {
      // Get token from cookie or memory
      const token = getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      // Add tenant header
      const tenantId = getTenantId();
      if (tenantId) {
        config.headers["X-Tenant-ID"] = tenantId;
      }

      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor: Handle 401 and token refresh
  api.interceptors.response.use(
    (response: AxiosResponse) => response,
    async (error) => {
      const originalRequest = error.config;

      // If 401 and not already retried, try to refresh token
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const refreshToken = getRefreshToken();
          if (refreshToken) {
            const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh/`, {
              refresh: refreshToken,
            });

            const { access, refresh: newRefresh } = response.data;
            
            // Save new tokens
            setAccessToken(access);
            setRefreshToken(newRefresh);

            // Retry original request
            originalRequest.headers.Authorization = `Bearer ${access}`;
            return api(originalRequest);
          }
        } catch (refreshError) {
          // Clear tokens and redirect to login
          clearTokens();
          window.location.href = "/login";
          return Promise.reject(refreshError);
        }
      }

      return Promise.reject(error);
    }
  );

  return api;
}

/**
 * Get access token from memory/cookie
 */
function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  
  // Try memory first
  const memoryToken = (window as any).__accessToken;
  if (memoryToken) return memoryToken;

  // Try cookie
  const cookies = document.cookie.split(";");
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split("=");
    if (name === "access_token") {
      return value;
    }
  }

  return null;
}

/**
 * Set access token
 */
function setAccessToken(token: string): void {
  if (typeof window === "undefined") return;
  (window as any).__accessToken = token;
  // Also set in cookie for server-side
  document.cookie = `access_token=${token}; path=/; max-age=86400; SameSite=Lax`;
}

/**
 * Get refresh token
 */
function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  
  const cookies = document.cookie.split(";");
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split("=");
    if (name === "refresh_token") {
      return value;
    }
  }

  return null;
}

/**
 * Set refresh token
 */
function setRefreshToken(token: string): void {
  if (typeof window === "undefined") return;
  document.cookie = `refresh_token=${token}; path=/; max-age=604800; SameSite=Lax`;
}

/**
 * Clear tokens
 */
function clearTokens(): void {
  if (typeof window === "undefined") return;
  (window as any).__accessToken = null;
  document.cookie = "access_token=; path=/; max-age=0";
  document.cookie = "refresh_token=; path=/; max-age=0";
}

/**
 * Get tenant ID
 */
function getTenantId(): string | null {
  if (typeof window === "undefined") return null;
  
  const tenantId = (window as any).__tenantId;
  return tenantId || null;
}

/**
 * Set tenant ID
 */
function setTenantId(tenantId: string): void {
  if (typeof window === "undefined") return;
  (window as any).__tenantId = tenantId;
}

// Export singleton instance
export const api = createApiClient();

export default api;