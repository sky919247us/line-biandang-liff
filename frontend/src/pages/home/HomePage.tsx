/**
 * 首頁元件
 * 
 * 顯示歡迎訊息、特色商品和快速入口
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { Header } from '../../components/layout/Header';
import { BottomNav } from '../../components/layout/BottomNav';
import { productApi } from '../../services/api';
import { shareMessage } from '../../services/liff';
import type { Product } from '../../types';
import './HomePage.css';

export function HomePage() {
    const navigate = useNavigate();
    const user = useAuthStore((state) => state.user);
    const [popularProducts, setPopularProducts] = useState<Product[]>([]);

    useEffect(() => {
        const loadPopular = async () => {
            try {
                const products = await productApi.getPopularProducts(6);
                setPopularProducts(products);
            } catch (err) {
                console.error('載入熱銷商品失敗:', err);
            }
        };
        loadPopular();
    }, []);

    const handleShare = async () => {
        try {
            const liffUrl = window.location.origin + '/menu';
            await shareMessage(`來一米粒弁当専門店點餐吧！\n${liffUrl}`);
        } catch (err) {
            console.error('分享失敗:', err);
        }
    };

    // 取得當前時段問候語
    const getGreeting = () => {
        const hour = new Date().getHours();
        if (hour < 11) return '早安';
        if (hour < 14) return '午安';
        if (hour < 17) return '下午好';
        return '晚安';
    };

    return (
        <div className="page home-page">
            <Header title="一米粒" showBack={false} />

            <main className="page-content">
                {/* 歡迎區塊 */}
                <section className="home-hero">
                    <div className="home-hero__content">
                        <h2 className="home-hero__greeting">
                            {getGreeting()}，{user?.displayName || '歡迎光臨'}！
                        </h2>
                        <p className="home-hero__subtitle">今天想吃什麼便當呢？</p>
                    </div>
                    <div className="home-hero__decoration" />
                </section>

                {/* 快速入口 */}
                <section className="home-quick-actions">
                    <button
                        className="quick-action-card quick-action-card--primary"
                        onClick={() => navigate('/menu')}
                    >
                        <div className="quick-action-card__icon">
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M18 8h1a4 4 0 0 1 0 8h-1" />
                                <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z" />
                                <line x1="6" y1="1" x2="6" y2="4" />
                                <line x1="10" y1="1" x2="10" y2="4" />
                                <line x1="14" y1="1" x2="14" y2="4" />
                            </svg>
                        </div>
                        <span className="quick-action-card__label">立即點餐</span>
                    </button>

                    <button
                        className="quick-action-card"
                        onClick={() => navigate('/orders')}
                    >
                        <div className="quick-action-card__icon">
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                <polyline points="14 2 14 8 20 8" />
                                <line x1="16" y1="13" x2="8" y2="13" />
                                <line x1="16" y1="17" x2="8" y2="17" />
                            </svg>
                        </div>
                        <span className="quick-action-card__label">訂單查詢</span>
                    </button>
                </section>

                {/* 店家資訊 */}
                <section className="home-section">
                    <h3 className="home-section__title">店家資訊</h3>
                    <div className="store-info-card">
                        <div className="store-info-card__row">
                            <div className="store-info-card__icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="12" cy="12" r="10" />
                                    <polyline points="12 6 12 12 16 14" />
                                </svg>
                            </div>
                            <div className="store-info-card__content">
                                <span className="store-info-card__label">營業時間</span>
                                <span className="store-info-card__value">10:00 - 16:30（週六日公休）</span>
                            </div>
                        </div>

                        <div className="store-info-card__row">
                            <div className="store-info-card__icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                                    <circle cx="12" cy="10" r="3" />
                                </svg>
                            </div>
                            <div className="store-info-card__content">
                                <span className="store-info-card__label">店家地址</span>
                                <span className="store-info-card__value">台中市中區興中街20號</span>
                            </div>
                        </div>

                        <div className="store-info-card__row">
                            <div className="store-info-card__icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7 2 2 0 0 1 1.72 2.04z" />
                                </svg>
                            </div>
                            <div className="store-info-card__content">
                                <span className="store-info-card__label">聯絡電話</span>
                                <span className="store-info-card__value">0909-998-952</span>
                            </div>
                        </div>
                    </div>
                </section>

                {/* 熱銷推薦 */}
                {popularProducts.length > 0 && (
                    <section className="home-section">
                        <h3 className="home-section__title">熱銷推薦</h3>
                        <div className="home-popular">
                            {popularProducts.map((product) => (
                                <button
                                    key={product.id}
                                    className="home-popular__item"
                                    onClick={() => navigate('/menu')}
                                >
                                    <div className="home-popular__img">
                                        {product.imageUrl ? (
                                            <img src={product.imageUrl} alt={product.name} />
                                        ) : (
                                            <div className="home-popular__placeholder">
                                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                                    <path d="M18 8h1a4 4 0 0 1 0 8h-1" />
                                                    <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z" />
                                                </svg>
                                            </div>
                                        )}
                                    </div>
                                    <span className="home-popular__name">{product.name}</span>
                                    <span className="home-popular__price">${product.price}</span>
                                </button>
                            ))}
                        </div>
                    </section>
                )}

                {/* 分享點餐 */}
                <section className="home-section">
                    <button className="home-share-btn" onClick={handleShare}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="18" cy="5" r="3" />
                            <circle cx="6" cy="12" r="3" />
                            <circle cx="18" cy="19" r="3" />
                            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
                            <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
                        </svg>
                        分享給朋友一起點餐
                    </button>
                </section>

                {/* 配送說明 */}
                <section className="home-section">
                    <h3 className="home-section__title">配送說明</h3>
                    <div className="delivery-info">
                        <div className="delivery-info__item">
                            <div className="delivery-info__icon delivery-info__icon--pickup">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                    <circle cx="12" cy="7" r="4" />
                                </svg>
                            </div>
                            <div className="delivery-info__content">
                                <span className="delivery-info__title">到店自取</span>
                                <span className="delivery-info__desc">免運費</span>
                            </div>
                        </div>

                        <div className="delivery-info__item">
                            <div className="delivery-info__icon delivery-info__icon--delivery">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <rect x="1" y="3" width="15" height="13" />
                                    <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
                                    <circle cx="5.5" cy="18.5" r="2.5" />
                                    <circle cx="18.5" cy="18.5" r="2.5" />
                                </svg>
                            </div>
                            <div className="delivery-info__content">
                                <span className="delivery-info__title">外送服務</span>
                                <span className="delivery-info__desc">5公里內 / 最低消費 $150</span>
                            </div>
                        </div>
                    </div>
                </section>
            </main>

            <BottomNav />
        </div>
    );
}

export default HomePage;
