import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, RegisterRequest } from '../types/api.types';
import api from '../services/api';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  register: (data: RegisterRequest) => Promise<void>;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      
      login: async (email: string, password: string) => {
        const response = await api.post('/auth/login', {
          email,
          password,
        });
        
        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);
        
        // Fetch user profile
        const userResponse = await api.get('/auth/me');
        const user = userResponse.data;
        
        set({ user, token: access_token, isAuthenticated: true });
      },
      
      logout: () => {
        localStorage.removeItem('access_token');
        set({ user: null, token: null, isAuthenticated: false });
      },
      
      register: async (data: RegisterRequest) => {
        await api.post('/auth/register', data);
      },
      
      setUser: (user: User | null) => {
        set({ user, isAuthenticated: !!user });
      },
    }),
    { 
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user, token: state.token, isAuthenticated: state.isAuthenticated }),
    }
  )
);
