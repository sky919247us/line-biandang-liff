/**
 * LIFF Context Provider
 * 
 * 提供 LIFF 狀態給整個應用程式使用
 */
import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import * as liffService from '../services/liff';
import { useAuthStore } from '../stores/authStore';
import { authApi } from '../services/api';

interface LiffContextType {
    isInitialized: boolean;
    isLoggedIn: boolean;
    isInClient: boolean;
    isLoading: boolean;
    error: Error | null;
    login: () => void;
    logout: () => void;
}

const LiffContext = createContext<LiffContextType | null>(null);

interface LiffProviderProps {
    children: ReactNode;
}

export function LiffProvider({ children }: LiffProviderProps) {
    const [isInitialized, setIsInitialized] = useState(false);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [isInClient, setIsInClient] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    const setAuth = useAuthStore((state) => state.setAuth);
    const setUser = useAuthStore((state) => state.setUser);
    const setToken = useAuthStore((state) => state.setToken);

    useEffect(() => {
        const initLiff = async () => {
            setIsLoading(true);

            try {
                const state = await liffService.initializeLiff();
                setIsInitialized(state.isInitialized);
                setIsLoggedIn(state.isLoggedIn);
                setIsInClient(state.isInClient);
                setError(state.error);

                // 如果已登入，取得使用者資訊並交換後端 JWT
                if (state.isLoggedIn) {
                    const lineAccessToken = liffService.getAccessToken();

                    if (lineAccessToken) {
                        try {
                            // 用 LINE access token 向後端交換 JWT
                            const result = await authApi.login(lineAccessToken);
                            setAuth(result.user, result.accessToken);
                        } catch (err) {
                            console.error('後端認證失敗，使用 LINE profile 作為備用:', err);
                            // 備用：至少存 LINE profile
                            const profile = await liffService.getProfile();
                            if (profile) {
                                setUser({
                                    id: profile.userId,
                                    lineUserId: profile.userId,
                                    displayName: profile.displayName,
                                    pictureUrl: profile.pictureUrl || null,
                                    phone: null,
                                    defaultAddress: null,
                                });
                            }
                        }
                    }
                }
            } catch (err) {
                console.error('LIFF 初始化錯誤:', err);
                setError(err as Error);
            } finally {
                setIsLoading(false);
            }
        };

        initLiff();
    }, [setUser, setToken]);

    const login = () => {
        liffService.login();
    };

    const logout = () => {
        liffService.logout();
        // 清除 store 中的使用者資訊
        setUser(null);
        setToken(null);
    };

    return (
        <LiffContext.Provider
            value={{
                isInitialized,
                isLoggedIn,
                isInClient,
                isLoading,
                error,
                login,
                logout,
            }}
        >
            {children}
        </LiffContext.Provider>
    );
}

/**
 * 使用 LIFF Context 的 Hook
 */
export function useLiff(): LiffContextType {
    const context = useContext(LiffContext);
    if (!context) {
        throw new Error('useLiff 必須在 LiffProvider 內使用');
    }
    return context;
}
