/**
 * 認證狀態管理
 * 
 * 管理使用者登入狀態
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '../types';

interface AuthState {
    /** 是否已登入 */
    isAuthenticated: boolean;

    /** 當前使用者 */
    user: User | null;

    /** Access Token */
    accessToken: string | null;

    /** LIFF 是否已初始化 */
    isLiffInitialized: boolean;

    /** 設定認證資訊 */
    setAuth: (user: User, token: string) => void;

    /** 設定使用者 */
    setUser: (user: User | null) => void;

    /** 設定 Token */
    setToken: (token: string | null) => void;

    /** 清除認證 */
    clearAuth: () => void;

    /** 更新使用者資訊 */
    updateUser: (user: Partial<User>) => void;

    /** 設定 LIFF 初始化狀態 */
    setLiffInitialized: (initialized: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set, get) => ({
            isAuthenticated: false,
            user: null,
            accessToken: null,
            isLiffInitialized: false,

            setAuth: (user, token) => {
                localStorage.setItem('access_token', token);
                set({
                    isAuthenticated: true,
                    user,
                    accessToken: token,
                });
            },

            setUser: (user) => {
                set({
                    user,
                    isAuthenticated: user !== null,
                });
            },

            setToken: (token) => {
                if (token) {
                    localStorage.setItem('access_token', token);
                } else {
                    localStorage.removeItem('access_token');
                }
                set({ accessToken: token });
            },

            clearAuth: () => {
                localStorage.removeItem('access_token');
                set({
                    isAuthenticated: false,
                    user: null,
                    accessToken: null,
                });
            },

            updateUser: (userData) => {
                const currentUser = get().user;
                if (currentUser) {
                    set({
                        user: { ...currentUser, ...userData },
                    });
                }
            },

            setLiffInitialized: (initialized) => {
                set({ isLiffInitialized: initialized });
            },
        }),
        {
            name: 'biandang-auth',
            partialize: (state) => ({
                accessToken: state.accessToken,
            }),
        }
    )
);
