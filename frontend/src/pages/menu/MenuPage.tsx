/**
 * 菜單頁面
 * 
 * 顯示所有商品列表，支援分類過濾和搜尋
 */
import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Header } from '../../components/layout/Header';
import { BottomNav } from '../../components/layout/BottomNav';
import { ProductCard } from '../../components/features/ProductCard';
import { productApi } from '../../services/api';
import type { Product, Category } from '../../types';
import './MenuPage.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

interface StoreStatus {
    is_open: boolean;
    message: string;
    open_time: string;
    close_time: string;
}

export function MenuPage() {
    const [products, setProducts] = useState<Product[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [storeStatus, setStoreStatus] = useState<StoreStatus | null>(null);

    // 載入分類和商品
    const loadData = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            // 同時載入營業狀態和商品資料
            const [statusRes, categoriesData, productsData] = await Promise.all([
                axios.get(`${API_BASE_URL}/store/status`).catch(() => null),
                productApi.getCategories(),
                productApi.getProducts({ limit: 50 }),
            ]);
            if (statusRes?.data) {
                setStoreStatus(statusRes.data);
            }
            setCategories(categoriesData);
            setProducts(productsData.items);
        } catch (error) {
            console.error('載入商品失敗:', error);
            setError('無法載入商品資料，請稍後再試');
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    // 過濾商品
    const filteredProducts = products.filter((product) => {
        const matchesCategory = !selectedCategory || product.categoryId === selectedCategory;
        const matchesSearch = !searchQuery ||
            product.name.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesCategory && matchesSearch;
    });

    return (
        <div className="page menu-page">
            <Header title="菜單" showBack={false} />

            <main className="page-content">
                {/* 非營業時間提示 */}
                {storeStatus && !storeStatus.is_open && (
                    <div style={{
                        background: 'linear-gradient(135deg, #ff6b35, #f7931e)',
                        color: '#fff',
                        padding: '12px 16px',
                        borderRadius: '12px',
                        marginBottom: '12px',
                        textAlign: 'center',
                        fontSize: '14px',
                        fontWeight: 600,
                    }}>
                        <div style={{ fontSize: '16px', marginBottom: '4px' }}>
                            {storeStatus.message}
                        </div>
                        <div style={{ opacity: 0.9, fontSize: '13px' }}>
                            營業時間：{storeStatus.open_time} - {storeStatus.close_time}
                        </div>
                    </div>
                )}

                {/* 搜尋欄 */}
                <div className="menu-search">
                    <div className="menu-search__input-wrapper">
                        <svg className="menu-search__icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="11" cy="11" r="8" />
                            <line x1="21" y1="21" x2="16.65" y2="16.65" />
                        </svg>
                        <input
                            type="text"
                            className="menu-search__input"
                            placeholder="搜尋便當..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                        {searchQuery && (
                            <button
                                className="menu-search__clear"
                                onClick={() => setSearchQuery('')}
                            >
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <line x1="18" y1="6" x2="6" y2="18" />
                                    <line x1="6" y1="6" x2="18" y2="18" />
                                </svg>
                            </button>
                        )}
                    </div>
                </div>

                {/* 分類標籤 */}
                <div className="menu-categories hide-scrollbar">
                    <button
                        className={`menu-category-tag ${!selectedCategory ? 'active' : ''}`}
                        onClick={() => setSelectedCategory(null)}
                    >
                        全部
                    </button>
                    {categories.map((category) => (
                        <button
                            key={category.id}
                            className={`menu-category-tag ${selectedCategory === category.id ? 'active' : ''}`}
                            onClick={() => setSelectedCategory(category.id)}
                        >
                            {category.name}
                        </button>
                    ))}
                </div>

                {/* 商品列表 */}
                <div className="menu-products">
                    {isLoading ? (
                        // 載入中骨架
                        Array.from({ length: 4 }).map((_, index) => (
                            <div key={index} className="product-skeleton">
                                <div className="product-skeleton__image skeleton" />
                                <div className="product-skeleton__content">
                                    <div className="product-skeleton__title skeleton" />
                                    <div className="product-skeleton__desc skeleton" />
                                    <div className="product-skeleton__price skeleton" />
                                </div>
                            </div>
                        ))
                    ) : error ? (
                        <div className="menu-empty">
                            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <circle cx="12" cy="12" r="10" />
                                <line x1="12" y1="8" x2="12" y2="12" />
                                <line x1="12" y1="16" x2="12.01" y2="16" />
                            </svg>
                            <p>{error}</p>
                            <button className="btn btn-primary" onClick={loadData} style={{ marginTop: '12px' }}>
                                重新載入
                            </button>
                        </div>
                    ) : filteredProducts.length > 0 ? (
                        filteredProducts.map((product) => (
                            <ProductCard key={product.id} product={product} />
                        ))
                    ) : (
                        <div className="menu-empty">
                            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <circle cx="11" cy="11" r="8" />
                                <line x1="21" y1="21" x2="16.65" y2="16.65" />
                            </svg>
                            <p>找不到符合的商品</p>
                        </div>
                    )}
                </div>
            </main>

            <BottomNav />
        </div>
    );
}

export default MenuPage;
