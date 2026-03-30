/**
 * 管理後台 - 主佈局
 */
import { useState, useEffect, useCallback } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { initializeLiff, getAccessToken, login as liffLogin, isLoggedIn as liffIsLoggedIn } from '../../services/liff';
import { authApi } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';
import './AdminLayout.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

type AuthState = 'loading' | 'ok' | 'no_token' | 'not_admin' | 'error';

export function AdminLayout() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [authState, setAuthState] = useState<AuthState>('loading');
    const [statusMsg, setStatusMsg] = useState('驗證中...');
    const navigate = useNavigate();
    const setAuth = useAuthStore((state) => state.setAuth);

    const verifyAdmin = useCallback(async (token: string) => {
        try {
            const res = await axios.get(`${API_BASE_URL}/auth/me`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.data.role === 'admin') {
                setAuthState('ok');
            } else {
                setAuthState('not_admin');
            }
        } catch (err: unknown) {
            if (axios.isAxiosError(err) && err.response?.status === 401) {
                localStorage.removeItem('access_token');
                setAuthState('no_token');
            } else if (axios.isAxiosError(err) && err.response?.status === 403) {
                setAuthState('not_admin');
            } else {
                setAuthState('error');
            }
        }
    }, []);

    useEffect(() => {
        const checkAuth = async () => {
            // 1. 先檢查是否已有有效的後端 JWT
            const existingToken = localStorage.getItem('access_token');
            if (existingToken) {
                await verifyAdmin(existingToken);
                return;
            }

            // 2. 沒有 token，嘗試用 LIFF 登入
            setStatusMsg('正在初始化 LINE 登入...');
            const liffState = await initializeLiff();

            if (liffState.isLoggedIn && liffIsLoggedIn()) {
                // LIFF 已登入，交換後端 JWT
                setStatusMsg('正在驗證身份...');
                const lineToken = getAccessToken();
                if (lineToken) {
                    try {
                        const result = await authApi.login(lineToken);
                        setAuth(result.user, result.accessToken);
                        await verifyAdmin(result.accessToken);
                        return;
                    } catch {
                        setAuthState('error');
                        return;
                    }
                }
            }

            // 3. LIFF 未登入，顯示登入按鈕
            setAuthState('no_token');
        };

        checkAuth();
    }, [verifyAdmin, setAuth]);

    const handleLineLogin = () => {
        // 用 LIFF login 並重導回當前 /admin 頁面
        const adminUrl = window.location.href;
        liffLogin(adminUrl);
    };

    if (authState === 'loading') {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', flexDirection: 'column', gap: '16px' }}>
                <div style={{ fontSize: '18px', color: '#666' }}>{statusMsg}</div>
            </div>
        );
    }

    if (authState === 'no_token') {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', flexDirection: 'column', gap: '16px', padding: '20px', textAlign: 'center' }}>
                <h2 style={{ margin: 0 }}>請先登入</h2>
                <p style={{ color: '#666', margin: 0 }}>管理後台需要透過 LINE 登入才能使用</p>
                <button
                    onClick={handleLineLogin}
                    style={{ padding: '12px 24px', backgroundColor: '#06C755', color: '#fff', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: 'bold', fontSize: '16px' }}
                >
                    透過 LINE 登入
                </button>
            </div>
        );
    }

    if (authState === 'not_admin') {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', flexDirection: 'column', gap: '16px', padding: '20px', textAlign: 'center' }}>
                <h2 style={{ margin: 0, color: '#e53e3e' }}>需要管理員權限</h2>
                <p style={{ color: '#666', margin: 0 }}>您的帳號沒有管理員權限，請聯繫店家管理員</p>
                <button
                    onClick={() => navigate('/')}
                    style={{ padding: '12px 24px', backgroundColor: '#4A90D9', color: '#fff', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}
                >
                    返回前台
                </button>
            </div>
        );
    }

    if (authState === 'error') {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', flexDirection: 'column', gap: '16px', padding: '20px', textAlign: 'center' }}>
                <h2 style={{ margin: 0, color: '#e53e3e' }}>連線錯誤</h2>
                <p style={{ color: '#666', margin: 0 }}>無法連線至伺服器，請稍後再試</p>
                <button
                    onClick={() => window.location.reload()}
                    style={{ padding: '12px 24px', backgroundColor: '#4A90D9', color: '#fff', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}
                >
                    重新整理
                </button>
            </div>
        );
    }

    const navItems = [
        { path: '/admin', icon: 'dashboard', label: '總覽', end: true },
        { path: '/admin/orders', icon: 'orders', label: '訂單管理' },
        { path: '/admin/kds', icon: 'kds', label: '廚房顯示' },
        { path: '/admin/products', icon: 'products', label: '商品管理' },
        { path: '/admin/inventory', icon: 'inventory', label: '庫存管理' },
        { path: '/admin/members', icon: 'members', label: '會員管理' },
        { path: '/admin/reports', icon: 'reports', label: '報表分析' },
        { path: '/admin/broadcast', icon: 'broadcast', label: '推播管理' },
        { path: '/admin/settings', icon: 'settings', label: '系統設定' },
    ];

    const renderIcon = (icon: string) => {
        switch (icon) {
            case 'dashboard':
                return (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect x="3" y="3" width="7" height="7" />
                        <rect x="14" y="3" width="7" height="7" />
                        <rect x="14" y="14" width="7" height="7" />
                        <rect x="3" y="14" width="7" height="7" />
                    </svg>
                );
            case 'orders':
                return (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                        <line x1="16" y1="13" x2="8" y2="13" />
                        <line x1="16" y1="17" x2="8" y2="17" />
                    </svg>
                );
            case 'products':
                return (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M18 8h1a4 4 0 0 1 0 8h-1" />
                        <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z" />
                    </svg>
                );
            case 'inventory':
                return (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                        <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                        <line x1="12" y1="22.08" x2="12" y2="12" />
                    </svg>
                );
            case 'kds':
                return (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect x="2" y="3" width="20" height="14" rx="2" />
                        <line x1="8" y1="21" x2="16" y2="21" />
                        <line x1="12" y1="17" x2="12" y2="21" />
                    </svg>
                );
            case 'members':
                return (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                        <circle cx="9" cy="7" r="4" />
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                    </svg>
                );
            case 'reports':
                return (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="18" y1="20" x2="18" y2="10" />
                        <line x1="12" y1="20" x2="12" y2="4" />
                        <line x1="6" y1="20" x2="6" y2="14" />
                    </svg>
                );
            case 'broadcast':
                return (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M22 2L11 13" />
                        <polygon points="22 2 15 22 11 13 2 9 22 2" />
                    </svg>
                );
            case 'settings':
                return (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="3" />
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                    </svg>
                );
            default:
                return null;
        }
    };

    return (
        <div className="admin-layout">
            {/* 側邊欄 */}
            <aside className={`admin-sidebar ${isSidebarOpen ? 'open' : ''}`}>
                <div className="admin-sidebar__header">
                    <h1 className="admin-sidebar__logo">一米粒</h1>
                    <span className="admin-sidebar__subtitle">管理後台</span>
                </div>

                <nav className="admin-sidebar__nav">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            end={item.end}
                            className={({ isActive }) =>
                                `admin-sidebar__link ${isActive ? 'active' : ''}`
                            }
                            onClick={() => setIsSidebarOpen(false)}
                        >
                            {renderIcon(item.icon)}
                            <span>{item.label}</span>
                        </NavLink>
                    ))}
                </nav>

                <div className="admin-sidebar__footer">
                    <button
                        className="admin-sidebar__back-btn"
                        onClick={() => navigate('/')}
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M19 12H5" />
                            <polyline points="12 19 5 12 12 5" />
                        </svg>
                        <span>返回前台</span>
                    </button>
                </div>
            </aside>

            {/* 遮罩層（手機版） */}
            {isSidebarOpen && (
                <div
                    className="admin-overlay"
                    onClick={() => setIsSidebarOpen(false)}
                />
            )}

            {/* 主內容區 */}
            <div className="admin-main">
                {/* 頂部導覽列 */}
                <header className="admin-header">
                    <button
                        className="admin-header__menu-btn"
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                    >
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="3" y1="12" x2="21" y2="12" />
                            <line x1="3" y1="6" x2="21" y2="6" />
                            <line x1="3" y1="18" x2="21" y2="18" />
                        </svg>
                    </button>
                    <div className="admin-header__title">管理後台</div>
                    <div className="admin-header__actions">
                        {/* 可以放通知、使用者資訊等 */}
                    </div>
                </header>

                {/* 頁面內容 */}
                <main className="admin-content">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}

export default AdminLayout;
