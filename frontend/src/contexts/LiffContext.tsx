/**
 * LIFF Context Provider
 * 
 * 提供 LIFF 狀態給整個應用程式使用
 */
import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import * as liffService from '../services/liff';
import { useAuthStore } from '../stores/authStore';

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

                // 如果已登入，取得使用者資訊
                if (state.isLoggedIn) {
                    const profile = await liffService.getProfile();
                    const accessToken = liffService.getAccessToken();

                    if (profile && accessToken) {
                        // 設定使用者資訊到 store
                        setUser({
                            id: profile.userId,
                            lineUserId: profile.userId,
                            displayName: profile.displayName,
                            pictureUrl: profile.pictureUrl || null,
                            phone: null,
                            defaultAddress: null,
                        });
                        setToken(accessToken);
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
