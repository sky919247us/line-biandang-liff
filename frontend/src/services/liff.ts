/**
 * LINE LIFF SDK 服務
 * 
 * 封裝 LINE LIFF 相關操作
 */
import liff from '@line/liff';

// LIFF ID 從環境變數讀取
const LIFF_ID = import.meta.env.VITE_LIFF_ID || '';

/**
 * LIFF 初始化狀態
 */
interface LiffState {
    isInitialized: boolean;
    isLoggedIn: boolean;
    isInClient: boolean;
    error: Error | null;
}

let liffState: LiffState = {
    isInitialized: false,
    isLoggedIn: false,
    isInClient: false,
    error: null,
};

/**
 * 初始化 LIFF
 */
export async function initializeLiff(): Promise<LiffState> {
    if (liffState.isInitialized) {
        return liffState;
    }

    if (!LIFF_ID) {
        console.warn('LIFF ID 未設定，使用開發模式');
        liffState = {
            isInitialized: true,
            isLoggedIn: false,
            isInClient: false,
            error: null,
        };
        return liffState;
    }

    try {
        await liff.init({ liffId: LIFF_ID });

        liffState = {
            isInitialized: true,
            isLoggedIn: liff.isLoggedIn(),
            isInClient: liff.isInClient(),
            error: null,
        };

        console.log('LIFF 初始化成功', liffState);
        return liffState;
    } catch (error) {
        console.error('LIFF 初始化失敗:', error);
        liffState = {
            isInitialized: true,
            isLoggedIn: false,
            isInClient: false,
            error: error as Error,
        };
        return liffState;
    }
}

/**
 * 取得 LIFF 狀態
 */
export function getLiffState(): LiffState {
    return liffState;
}

/**
 * LINE 登入
 */
export function login(redirectUri?: string): void {
    if (!liff.isLoggedIn()) {
        liff.login({ redirectUri });
    }
}

/**
 * LINE 登出
 */
export function logout(): void {
    if (liff.isLoggedIn()) {
        liff.logout();
        window.location.reload();
    }
}

/**
 * 取得 LINE Access Token
 */
export function getAccessToken(): string | null {
    if (!liff.isLoggedIn()) {
        return null;
    }
    return liff.getAccessToken();
}

/**
 * 取得 LINE ID Token
 */
export function getIdToken(): string | null {
    if (!liff.isLoggedIn()) {
        return null;
    }
    return liff.getIDToken();
}

/**
 * 取得使用者 LINE Profile
 */
export async function getProfile(): Promise<{
    userId: string;
    displayName: string;
    pictureUrl?: string;
    statusMessage?: string;
} | null> {
    if (!liff.isLoggedIn()) {
        return null;
    }

    try {
        const profile = await liff.getProfile();
        return {
            userId: profile.userId,
            displayName: profile.displayName,
            pictureUrl: profile.pictureUrl,
            statusMessage: profile.statusMessage,
        };
    } catch (error) {
        console.error('取得 LINE Profile 失敗:', error);
        return null;
    }
}

/**
 * 檢查是否在 LINE App 內
 */
export function isInClient(): boolean {
    return liff.isInClient();
}

/**
 * 檢查是否已登入
 */
export function isLoggedIn(): boolean {
    return liff.isLoggedIn();
}

/**
 * 關閉 LIFF 視窗（僅在 LINE App 內有效）
 */
export function closeWindow(): void {
    if (liff.isInClient()) {
        liff.closeWindow();
    }
}

/**
 * 分享訊息到 LINE 聊天室
 */
export async function shareMessage(message: string): Promise<void> {
    if (!liff.isInClient()) {
        console.warn('分享功能僅在 LINE App 內可用');
        return;
    }

    try {
        await liff.shareTargetPicker([
            {
                type: 'text',
                text: message,
            },
        ]);
    } catch (error) {
        console.error('分享訊息失敗:', error);
    }
}

/**
 * 傳送訊息給 LINE 官方帳號
 */
export async function sendMessageToOA(message: string): Promise<void> {
    if (!liff.isInClient()) {
        console.warn('傳送訊息功能僅在 LINE App 內可用');
        return;
    }

    try {
        await liff.sendMessages([
            {
                type: 'text',
                text: message,
            },
        ]);
    } catch (error) {
        console.error('傳送訊息失敗:', error);
    }
}

/**
 * 取得 LIFF 版本
 */
export function getLiffVersion(): string | null {
    return liff.getVersion();
}

/**
 * 取得 OS 資訊
 */
export function getOS(): 'ios' | 'android' | 'web' {
    return liff.getOS() as 'ios' | 'android' | 'web';
}

/**
 * 取得語言設定
 */
export function getLanguage(): string {
    return liff.getLanguage();
}

// 匯出 liff 實例供直接使用
export { liff };
