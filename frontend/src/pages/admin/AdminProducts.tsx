/**
 * 管理後台 - 商品管理頁面
 */
import { useState, useEffect } from 'react';
import type { Product, Category } from '../../types';
import '../admin/AdminLayout.css';
import './AdminProducts.css';

// 模擬商品共用預設值
const productDefaults: Pick<Product, 'salePrice' | 'effectivePrice' | 'isCombo' | 'availablePeriods' | 'saleStart' | 'saleEnd' | 'customizationGroups'> = {
    salePrice: null,
    effectivePrice: 0,
    isCombo: false,
    availablePeriods: null,
    saleStart: null,
    saleEnd: null,
    customizationGroups: [],
};

// 模擬商品資料
const mockProducts: Product[] = [
    {
        ...productDefaults,
        id: 'chicken-1',
        name: '戰斧雞腿',
        description: '人氣 NO.1！霸氣戰斧雞腿，外酥內嫩，份量十足',
        price: 120,
        effectivePrice: 120,
        imageUrl: null,
        categoryId: 'chicken',
        isAvailable: true,
        canOrder: true,
        dailyLimit: 30,
        todaySold: 12,
        customizationOptions: [],
    },
    {
        ...productDefaults,
        id: 'chicken-2',
        name: '醬燒揚雞',
        description: '日式醬燒風味，炸雞淋上特製醬汁',
        price: 120,
        effectivePrice: 120,
        imageUrl: null,
        categoryId: 'chicken',
        isAvailable: true,
        canOrder: true,
        dailyLimit: 0,
        todaySold: 8,
        customizationOptions: [],
    },
    {
        ...productDefaults, id: 'pork-1', name: '相撲豬太郎',
        description: '獨家招牌！大份量豬肉料理，吃飽吃滿',
        price: 120, effectivePrice: 120, imageUrl: null, categoryId: 'pork',
        isAvailable: true, canOrder: true, dailyLimit: 0, todaySold: 5, customizationOptions: [],
    },
    {
        ...productDefaults, id: 'pork-2', name: '嫩嫩豬柳',
        description: '軟嫩豬柳條，口感滑嫩',
        price: 120, effectivePrice: 120, imageUrl: null, categoryId: 'pork',
        isAvailable: true, canOrder: true, dailyLimit: 0, todaySold: 3, customizationOptions: [],
    },
    {
        ...productDefaults, id: 'pork-3', name: '燒肉多多',
        description: '香氣四溢的燒肉，肉量超多',
        price: 120, effectivePrice: 120, imageUrl: null, categoryId: 'pork',
        isAvailable: true, canOrder: true, dailyLimit: 0, todaySold: 6, customizationOptions: [],
    },
    {
        ...productDefaults, id: 'pork-4', name: '家鄉豬腳',
        description: '傳統滷製豬腳，軟Q入味',
        price: 120, effectivePrice: 120, imageUrl: null, categoryId: 'pork',
        isAvailable: false, canOrder: false, dailyLimit: 0, todaySold: 0, customizationOptions: [],
    },
    {
        ...productDefaults, id: 'pork-5', name: '五告厚豬排',
        description: '人氣 NO.2！超厚切豬排，外酥內多汁',
        price: 130, effectivePrice: 130, imageUrl: null, categoryId: 'pork',
        isAvailable: true, canOrder: true, dailyLimit: 20, todaySold: 15, customizationOptions: [],
    },
    {
        ...productDefaults, id: 'pork-6', name: '藍帶豬排',
        description: '豬排內夾起司與火腿，香濃美味',
        price: 180, effectivePrice: 180, imageUrl: null, categoryId: 'pork',
        isAvailable: true, canOrder: true, dailyLimit: 15, todaySold: 10, customizationOptions: [],
    },
    {
        ...productDefaults, id: 'beef-1', name: '牛逼菲力',
        description: '嚴選菲力牛排，軟嫩多汁',
        price: 150, effectivePrice: 150, imageUrl: null, categoryId: 'beef',
        isAvailable: true, canOrder: true, dailyLimit: 10, todaySold: 8, customizationOptions: [],
    },
    {
        ...productDefaults, id: 'beef-2', name: '鄉村燉牛肉',
        description: '慢燉牛肉，濃郁入味',
        price: 120, effectivePrice: 120, imageUrl: null, categoryId: 'beef',
        isAvailable: true, canOrder: true, dailyLimit: 0, todaySold: 4, customizationOptions: [],
    },
    {
        ...productDefaults, id: 'special-1', name: '隱藏菜單',
        description: '不定時更新，每日限量供應',
        price: 120, effectivePrice: 120, imageUrl: null, categoryId: 'special',
        isAvailable: true, canOrder: true, dailyLimit: 5, todaySold: 3, customizationOptions: [],
    },
];

const mockCategories: Category[] = [
    { id: 'chicken', name: '雞', description: '雞肉類便當', imageUrl: null, productCount: 2 },
    { id: 'pork', name: '豬', description: '豬肉類便當', imageUrl: null, productCount: 6 },
    { id: 'beef', name: '牛', description: '牛肉類便當', imageUrl: null, productCount: 2 },
    { id: 'special', name: '?', description: '隱藏菜單', imageUrl: null, productCount: 1 },
];

export function AdminProducts() {
    const [products, setProducts] = useState<Product[]>([]);
    const [categories] = useState<Category[]>(mockCategories);
    const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
    const [editingProduct, setEditingProduct] = useState<Product | null>(null);

    useEffect(() => {
        setProducts(mockProducts);
    }, []);

    const filteredProducts = selectedCategory
        ? products.filter(p => p.categoryId === selectedCategory)
        : products;

    const getCategoryName = (categoryId: string | null) => {
        if (!categoryId) return '未分類';
        return categories.find(c => c.id === categoryId)?.name || '未分類';
    };

    const handleToggleAvailable = (productId: string) => {
        setProducts(prev => prev.map(p => {
            if (p.id === productId) {
                const newAvailable = !p.isAvailable;
                return { ...p, isAvailable: newAvailable, canOrder: newAvailable };
            }
            return p;
        }));
    };

    const handleUpdateDailyLimit = (productId: string, newLimit: number) => {
        setProducts(prev => prev.map(p => {
            if (p.id === productId) {
                return { ...p, dailyLimit: newLimit };
            }
            return p;
        }));
    };

    const handleResetSold = (productId: string) => {
        setProducts(prev => prev.map(p => {
            if (p.id === productId) {
                return { ...p, todaySold: 0 };
            }
            return p;
        }));
    };

    return (
        <div className="admin-products">
            <div className="admin-page-header">
                <h1 className="admin-page-title">商品管理</h1>
                <button className="btn btn-primary">
                    + 新增商品
                </button>
            </div>

            {/* 分類篩選 */}
            <div className="admin-products__categories">
                <button
                    className={`admin-products__category-btn ${!selectedCategory ? 'active' : ''}`}
                    onClick={() => setSelectedCategory(null)}
                >
                    全部 ({products.length})
                </button>
                {categories.map(cat => (
                    <button
                        key={cat.id}
                        className={`admin-products__category-btn ${selectedCategory === cat.id ? 'active' : ''}`}
                        onClick={() => setSelectedCategory(cat.id)}
                    >
                        {cat.name} ({products.filter(p => p.categoryId === cat.id).length})
                    </button>
                ))}
            </div>

            {/* 商品列表 */}
            <div className="admin-card">
                <div className="admin-table-responsive">
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>商品名稱</th>
                                <th>分類</th>
                                <th>價格</th>
                                <th>每日限量</th>
                                <th>今日銷量</th>
                                <th>狀態</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredProducts.map((product) => (
                                <tr key={product.id}>
                                    <td>
                                        <div className="admin-products__name">
                                            <strong>{product.name}</strong>
                                            <span className="admin-products__desc">{product.description}</span>
                                        </div>
                                    </td>
                                    <td>{getCategoryName(product.categoryId)}</td>
                                    <td><strong>${product.price}</strong></td>
                                    <td>
                                        <input
                                            type="number"
                                            className="admin-products__limit-input"
                                            value={product.dailyLimit}
                                            min={0}
                                            onChange={(e) => handleUpdateDailyLimit(product.id, parseInt(e.target.value) || 0)}
                                        />
                                    </td>
                                    <td>
                                        <div className="admin-products__sold">
                                            <span>{product.todaySold}</span>
                                            {product.dailyLimit > 0 && (
                                                <span className="admin-products__sold-limit">/ {product.dailyLimit}</span>
                                            )}
                                            <button
                                                className="admin-products__reset-btn"
                                                onClick={() => handleResetSold(product.id)}
                                                title="重置銷量"
                                            >
                                                ↺
                                            </button>
                                        </div>
                                    </td>
                                    <td>
                                        <label className="admin-products__toggle">
                                            <input
                                                type="checkbox"
                                                checked={product.isAvailable}
                                                onChange={() => handleToggleAvailable(product.id)}
                                            />
                                            <span className="admin-products__toggle-slider"></span>
                                            <span className="admin-products__toggle-label">
                                                {product.isAvailable ? '上架' : '下架'}
                                            </span>
                                        </label>
                                    </td>
                                    <td>
                                        <div className="admin-actions">
                                            <button
                                                className="admin-action-btn admin-action-btn--secondary"
                                                onClick={() => setEditingProduct(product)}
                                            >
                                                編輯
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* 編輯 Modal（簡化版） */}
            {editingProduct && (
                <div className="admin-modal-overlay" onClick={() => setEditingProduct(null)}>
                    <div className="admin-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="admin-modal__header">
                            <h3>編輯商品</h3>
                            <button onClick={() => setEditingProduct(null)}>✕</button>
                        </div>
                        <div className="admin-modal__body">
                            <div className="form-group">
                                <label>商品名稱</label>
                                <input type="text" className="form-input" value={editingProduct.name} readOnly />
                            </div>
                            <div className="form-group">
                                <label>價格</label>
                                <input type="number" className="form-input" value={editingProduct.price} readOnly />
                            </div>
                            <div className="form-group">
                                <label>描述</label>
                                <textarea className="form-textarea" value={editingProduct.description || ''} readOnly />
                            </div>
                            <p className="admin-modal__note">
                                完整編輯功能開發中...
                            </p>
                        </div>
                        <div className="admin-modal__footer">
                            <button className="btn btn-secondary" onClick={() => setEditingProduct(null)}>
                                關閉
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default AdminProducts;
