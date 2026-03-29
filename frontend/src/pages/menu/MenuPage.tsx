/**
 * 菜單頁面
 * 
 * 顯示所有商品列表，支援分類過濾和搜尋
 */
import { useState, useEffect } from 'react';
import { Header } from '../../components/layout/Header';
import { BottomNav } from '../../components/layout/BottomNav';
import { ProductCard } from '../../components/features/ProductCard';
import { productApi } from '../../services/api';
import type { Product, Category } from '../../types';
import './MenuPage.css';

export function MenuPage() {
    const [products, setProducts] = useState<Product[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [isLoading, setIsLoading] = useState(true);

    // 載入分類和商品
    useEffect(() => {
        const loadData = async () => {
            setIsLoading(true);
            try {
                const [categoriesData, productsData] = await Promise.all([
                    productApi.getCategories(),
                    productApi.getProducts({ limit: 50 }),
                ]);
                setCategories(categoriesData);
                setProducts(productsData.items);
            } catch (error) {
                console.error('載入商品失敗:', error);
                // 使用模擬資料
                setProducts(getMockProducts());
                setCategories(getMockCategories());
            } finally {
                setIsLoading(false);
            }
        };

        loadData();
    }, []);

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

// ==================== 模擬資料（一米粒弁当専門店實際菜單）====================

const defaultProductFields = {
    salePrice: null,
    effectivePrice: 0, // will be overridden
    isCombo: false,
    availablePeriods: null,
    saleStart: null,
    saleEnd: null,
    customizationGroups: [],
};

function getMockProducts(): Product[] {
    return ([
        // 雞肉類
        {
            id: 'chicken-1',
            name: '戰斧雞腿',
            description: '人氣 NO.1！霸氣戰斧雞腿，外酥內嫩，份量十足',
            price: 120,
            imageUrl: null,
            categoryId: 'chicken',
            isAvailable: true,
            canOrder: true,
            dailyLimit: 30,
            todaySold: 0,
            customizationOptions: [
                { id: 'c1', name: '少飯', optionType: 'modifier', priceAdjustment: 0, isDefault: false },
                { id: 'c2', name: '加辣', optionType: 'modifier', priceAdjustment: 0, isDefault: false },
                { id: 'c3', name: '不要蔥', optionType: 'modifier', priceAdjustment: 0, isDefault: false },
            ],
        },
        {
            id: 'chicken-2',
            name: '醬燒揚雞',
            description: '日式醬燒風味，炸雞淋上特製醬汁',
            price: 120,
            imageUrl: null,
            categoryId: 'chicken',
            isAvailable: true,
            canOrder: true,
            dailyLimit: 0,
            todaySold: 0,
            customizationOptions: [
                { id: 'c1', name: '少飯', optionType: 'modifier', priceAdjustment: 0, isDefault: false },
                { id: 'c2', name: '加辣', optionType: 'modifier', priceAdjustment: 0, isDefault: false },
            ],
        },
        // 豬肉類
        {
            id: 'pork-1',
            name: '相撲豬太郎',
            description: '獨家招牌！大份量豬肉料理，吃飽吃滿',
            price: 120,
            imageUrl: null,
            categoryId: 'pork',
            isAvailable: true,
            canOrder: true,
            dailyLimit: 0,
            todaySold: 0,
            customizationOptions: [
                { id: 'c1', name: '少飯', optionType: 'modifier', priceAdjustment: 0, isDefault: false },
                { id: 'c2', name: '加辣', optionType: 'modifier', priceAdjustment: 0, isDefault: false },
            ],
        },
        {
            id: 'pork-2',
            name: '嫩嫩豬柳',
            description: '軟嫩豬柳條，口感滑嫩',
            price: 120,
            imageUrl: null,
            categoryId: 'pork',
            isAvailable: true,
            canOrder: true,
            dailyLimit: 0,
            todaySold: 0,
            customizationOptions: [
                { id: 'c1', name: '少飯', optionType: 'modifier', priceAdjustment: 0, isDefault: false },
            ],
        },
        {
            id: 'pork-3',
            name: '燒肉多多',
            description: '香氣四溢的燒肉，肉量超多',
            price: 120,
            imageUrl: null,
            categoryId: 'pork',
            isAvailable: true,
            canOrder: true,
            dailyLimit: 0,
            todaySold: 0,
            customizationOptions: [
                { id: 'c1', name: '少飯', optionType: 'modifier', priceAdjustment: 0, isDefault: false },
                { id: 'c2', name: '加辣', optionType: 'modifier', priceAdjustment: 0, isDefault: false },
            ],
        },
        {
            id: 'pork-4',
            name: '家鄉豬腳',
            description: '傳統滷製豬腳，軟Q入味',
            price: 120,
            imageUrl: null,
            categoryId: 'pork',
            isAvailable: true,
            canOrder: true,
            dailyLimit: 0,
            todaySold: 0,
            customizationOptions: [
                { id: 'c1', name: '少飯', optionType: 'modifier', priceAdjustment: 0, isDefault: false },
            ],
        },
        {
            id: 'pork-5',
            name: '五告厚豬排',
            description: '人氣 NO.2！超厚切豬排，外酥內多汁',
            price: 130,
            imageUrl: null,
            categoryId: 'pork',
            isAvailable: true,
            canOrder: true,
            dailyLimit: 20,
            todaySold: 0,
            customizationOptions: [
                { id: 'c1', name: '少飯', optionType: 'modifier', priceAdjustment: 0, isDefault: false },
                { id: 'c2', name: '加辣', optionType: 'modifier', priceAdjustment: 0, isDefault: false },
            ],
        },
        {
            id: 'pork-6',
            name: '藍帶豬排',
            description: '豬排內夾起司與火腿，香濃美味',
            price: 180,
            imageUrl: null,
            categoryId: 'pork',
            isAvailable: true,
            canOrder: true,
            dailyLimit: 15,
            todaySold: 0,
            customizationOptions: [
                { id: 'c1', name: '少飯', optionType: 'modifier', priceAdjustment: 0, isDefault: false },
            ],
        },
        // 牛肉類
        {
            id: 'beef-1',
            name: '牛逼菲力',
            description: '嚴選菲力牛排，軟嫩多汁',
            price: 150,
            imageUrl: null,
            categoryId: 'beef',
            isAvailable: true,
            canOrder: true,
            dailyLimit: 10,
            todaySold: 0,
            customizationOptions: [
                { id: 'c1', name: '少飯', optionType: 'modifier', priceAdjustment: 0, isDefault: false },
            ],
        },
        {
            id: 'beef-2',
            name: '鄉村燉牛肉',
            description: '慢燉牛肉，濃郁入味',
            price: 120,
            imageUrl: null,
            categoryId: 'beef',
            isAvailable: true,
            canOrder: true,
            dailyLimit: 0,
            todaySold: 0,
            customizationOptions: [
                { id: 'c1', name: '少飯', optionType: 'modifier', priceAdjustment: 0, isDefault: false },
                { id: 'c2', name: '加辣', optionType: 'modifier', priceAdjustment: 0, isDefault: false },
            ],
        },
        // 隱藏菜單
        {
            id: 'special-1',
            name: '隱藏菜單',
            description: '不定時更新，每日限量供應',
            price: 120,
            imageUrl: null,
            categoryId: 'special',
            isAvailable: true,
            canOrder: true,
            dailyLimit: 5,
            todaySold: 0,
            customizationOptions: [],
        },
    ] as Omit<Product, 'salePrice' | 'effectivePrice' | 'isCombo' | 'availablePeriods' | 'saleStart' | 'saleEnd' | 'customizationGroups'>[]).map(p => ({
        ...defaultProductFields,
        ...p,
        effectivePrice: p.price,
    })) as Product[];
}

function getMockCategories(): Category[] {
    return [
        { id: 'chicken', name: '雞', description: '雞肉類便當', imageUrl: null, productCount: 2 },
        { id: 'pork', name: '豬', description: '豬肉類便當', imageUrl: null, productCount: 6 },
        { id: 'beef', name: '牛', description: '牛肉類便當', imageUrl: null, productCount: 2 },
        { id: 'special', name: '?', description: '隱藏菜單', imageUrl: null, productCount: 1 },
    ];
}

export default MenuPage;
