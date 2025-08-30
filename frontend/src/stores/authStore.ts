import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, LoginRequest, RegisterRequest, AuthResponse } from '../types';
import api from '../services/api';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AuthActions {
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => void;
  clearError: () => void;
  updateUser: (userData: Partial<User>) => void;
}

export const useAuthStore = create<AuthState & AuthActions>()(persist(
  (set, get) => ({
    // 状态
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,

    // 登录
    login: async (credentials: LoginRequest) => {
      set({ isLoading: true, error: null });
      try {
        const response: AuthResponse = await api.post('/auth/login', credentials);
        const { access_token, user } = response;
        
        // 保存token到localStorage
        localStorage.setItem('token', access_token);
        
        set({
          user,
          token: access_token,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
      } catch (error: any) {
        set({
          isLoading: false,
          error: error.response?.data?.message || '登录失败',
        });
        throw error;
      }
    },

    // 注册
    register: async (userData: RegisterRequest) => {
      set({ isLoading: true, error: null });
      try {
        const response: AuthResponse = await api.post('/auth/register', userData);
        const { access_token, user } = response;
        
        // 保存token到localStorage
        localStorage.setItem('token', access_token);
        
        set({
          user,
          token: access_token,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
      } catch (error: any) {
        set({
          isLoading: false,
          error: error.response?.data?.message || '注册失败',
        });
        throw error;
      }
    },

    // 登出
    logout: () => {
      localStorage.removeItem('token');
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        error: null,
      });
    },

    // 清除错误
    clearError: () => {
      set({ error: null });
    },

    // 更新用户信息
    updateUser: (userData: Partial<User>) => {
      const { user } = get();
      if (user) {
        set({ user: { ...user, ...userData } });
      }
    },
  }),
  {
    name: 'auth-storage',
    partialize: (state) => ({
      user: state.user,
      token: state.token,
      isAuthenticated: state.isAuthenticated,
    }),
  }
));