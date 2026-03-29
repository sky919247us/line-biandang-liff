/**
 * 個人資料頁面
 * 
 * 整合 LINE LIFF SDK 顯示使用者資訊
 */
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Header } from '../../components/layout/Header';
import { BottomNav } from '../../components/layout/BottomNav';
import { useAuthStore } from '../../stores/authStore';
import { useLiff } from '../../contexts/LiffContext';
import './ProfilePage.css';

export function ProfilePage() {
    const navigate = useNavigate();
    const { user } = useAuthStore();
    const { isLoggedIn, isLoading, login, logout, isInClient } = useLiff();
    const { t, i18n } = useTranslation();

    const toggleLanguage = () => {
        const newLang = i18n.language === 'zh-TW' ? 'en' : 'zh-TW';
        i18n.changeLanguage(newLang);
        localStorage.setItem('language', newLang);
    };

    const handleLogin = () => {
        login();
    };

    const handleLogout = () => {
        logout();
    };

    return (
        <div className="page profile-page">
            <Header title="我的" showBack={false} showCart={false} />

            <main className="page-content">
                {/* 使用者資訊 */}
                <div className="profile-header">
                    {isLoading ? (
                        <div className="profile-loading">
                            <div className="profile-avatar skeleton" />
                            <div className="profile-info">
                                <div className="skeleton" style={{ width: '120px', height: '24px' }} />
                                <div className="skeleton" style={{ width: '80px', height: '16px', marginTop: '8px' }} />
                            </div>
                        </div>
                    ) : isLoggedIn && user ? (
                        <>
                            <div className="profile-avatar">
                                {user.pictureUrl ? (
                                    <img src={user.pictureUrl} alt={user.displayName || ''} />
                                ) : (
                                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                        <circle cx="12" cy="7" r="4" />
                                    </svg>
                                )}
                            </div>
                            <div className="profile-info">
                                <h2 className="profile-name">{user.displayName}</h2>
                                {user.phone && (
                                    <p className="profile-phone">{user.phone}</p>
                                )}
                            </div>
                        </>
                    ) : (
                        <div className="profile-guest">
                            <div className="profile-avatar profile-avatar--guest">
                                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                    <circle cx="12" cy="7" r="4" />
                                </svg>
                            </div>
                            <div className="profile-info">
                                <h2 className="profile-name">訪客使用者</h2>
                                <p className="profile-hint">登入 LINE 帳號以使用完整功能</p>
                            </div>
                            <button className="btn btn-primary profile-login-btn" onClick={handleLogin}>
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M19.365 9.863c.349 0 .63.285.63.631 0 .345-.281.63-.63.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.281.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314" />
                                </svg>
                                LINE 登入
                            </button>
                        </div>
                    )}
                </div>

                {/* 功能選單 */}
                <div className="profile-menu">
                    <div className="profile-menu__section">
                        <h3 className="profile-menu__title">帳號設定</h3>

                        <button className="profile-menu__item" disabled={!isLoggedIn}>
                            <div className="profile-menu__icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                    <circle cx="12" cy="7" r="4" />
                                </svg>
                            </div>
                            <span className="profile-menu__label">個人資料</span>
                            <svg className="profile-menu__arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="9 18 15 12 9 6" />
                            </svg>
                        </button>

                        <button className="profile-menu__item" disabled={!isLoggedIn}>
                            <div className="profile-menu__icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                                    <circle cx="12" cy="10" r="3" />
                                </svg>
                            </div>
                            <span className="profile-menu__label">常用地址</span>
                            <svg className="profile-menu__arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="9 18 15 12 9 6" />
                            </svg>
                        </button>
                    </div>

                    <div className="profile-menu__section">
                        <h3 className="profile-menu__title">會員</h3>

                        <button
                            className="profile-menu__item"
                            onClick={() => navigate('/loyalty')}
                            disabled={!isLoggedIn}
                        >
                            <div className="profile-menu__icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                                </svg>
                            </div>
                            <span className="profile-menu__label">會員點數</span>
                            <svg className="profile-menu__arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="9 18 15 12 9 6" />
                            </svg>
                        </button>

                        <button
                            className="profile-menu__item"
                            onClick={() => navigate('/stamps')}
                            disabled={!isLoggedIn}
                        >
                            <div className="profile-menu__icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <rect x="3" y="3" width="18" height="18" rx="2" />
                                    <path d="M9 12l2 2 4-4" />
                                </svg>
                            </div>
                            <span className="profile-menu__label">集點卡</span>
                            <svg className="profile-menu__arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="9 18 15 12 9 6" />
                            </svg>
                        </button>

                        <button
                            className="profile-menu__item"
                            onClick={() => navigate('/referral')}
                            disabled={!isLoggedIn}
                        >
                            <div className="profile-menu__icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                                    <circle cx="8.5" cy="7" r="4" />
                                    <line x1="20" y1="8" x2="20" y2="14" />
                                    <line x1="23" y1="11" x2="17" y2="11" />
                                </svg>
                            </div>
                            <span className="profile-menu__label">推薦好友</span>
                            <svg className="profile-menu__arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="9 18 15 12 9 6" />
                            </svg>
                        </button>
                    </div>

                    <div className="profile-menu__section">
                        <h3 className="profile-menu__title">其他</h3>

                        <button className="profile-menu__item">
                            <div className="profile-menu__icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="12" cy="12" r="10" />
                                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                                    <line x1="12" y1="17" x2="12.01" y2="17" />
                                </svg>
                            </div>
                            <span className="profile-menu__label">常見問題</span>
                            <svg className="profile-menu__arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="9 18 15 12 9 6" />
                            </svg>
                        </button>

                        <button className="profile-menu__item">
                            <div className="profile-menu__icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
                                </svg>
                            </div>
                            <span className="profile-menu__label">聯絡我們</span>
                            <svg className="profile-menu__arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="9 18 15 12 9 6" />
                            </svg>
                        </button>

                        <button className="profile-menu__item" onClick={toggleLanguage}>
                            <div className="profile-menu__icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="12" cy="12" r="10" />
                                    <line x1="2" y1="12" x2="22" y2="12" />
                                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                                </svg>
                            </div>
                            <span className="profile-menu__label">{t('profile.language')}</span>
                            <span className="profile-menu__value">{i18n.language === 'zh-TW' ? '繁體中文' : 'English'}</span>
                            <svg className="profile-menu__arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="9 18 15 12 9 6" />
                            </svg>
                        </button>

                        {/* 管理後台入口（開發用） */}
                        <button
                            className="profile-menu__item"
                            onClick={() => navigate('/admin')}
                        >
                            <div className="profile-menu__icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="12" cy="12" r="3" />
                                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                                </svg>
                            </div>
                            <span className="profile-menu__label">管理後台</span>
                            <svg className="profile-menu__arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="9 18 15 12 9 6" />
                            </svg>
                        </button>
                    </div>

                    {isLoggedIn && (
                        <button className="profile-logout-btn" onClick={handleLogout}>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                                <polyline points="16 17 21 12 16 7" />
                                <line x1="21" y1="12" x2="9" y2="12" />
                            </svg>
                            登出
                        </button>
                    )}
                </div>

                {/* 狀態資訊 */}
                <div className="profile-status">
                    {isInClient && (
                        <span className="profile-status__badge profile-status__badge--line">
                            LINE App 內
                        </span>
                    )}
                </div>

                {/* 版本資訊 */}
                <div className="profile-version">
                    <p>一米粒 便當訂購系統 v1.0.0</p>
                </div>
            </main>

            <BottomNav />
        </div>
    );
}

export default ProfilePage;
