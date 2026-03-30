/**
 * 管理後台 - 商品管理頁面
 */
import { useState, useEffect, useCallback } from 'react';
import type { Category } from '../../types';
import {
    getProducts,
    getCategories,
    toggleProductAvailability,
    resetProductSold,
    updateProduct,
    createProduct,
} from '../../services/adminApi';
import type { Product, CustomizationOption } from '../../services/adminApi';
import '../admin/AdminLayout.css';
import './AdminProducts.css';

// ==================== 新增商品 Modal ====================

interface CreateProductModalProps {
    categories: Category[];
    onClose: () => void;
    onCreated: () => void;
}

function CreateProductModal({ categories, onClose, onCreated }: CreateProductModalProps) {
    const [name, setName] = useState('');
    const [categoryId, setCategoryId] = useState(categories[0]?.id || '');
    const [price, setPrice] = useState<number>(120);
    const [description, setDescription] = useState('');
    const [dailyLimit, setDailyLimit] = useState<number>(0);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async () => {
        if (!name.trim()) {
            setError('請輸入商品名稱');
            return;
        }
        if (price <= 0) {
            setError('價格必須大於 0');
            return;
        }
        setSaving(true);
        setError(null);
        try {
            await createProduct({
                name: name.trim(),
                category_id: categoryId,
                price,
                description: description.trim() || undefined,
                daily_limit: dailyLimit,
            });
            onCreated();
        } catch (err: any) {
            setError(err.response?.data?.detail || '新增失敗，請稍後再試');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="admin-modal-overlay" onClick={onClose}>
            <div className="admin-modal" onClick={(e) => e.stopPropagation()}>
                <div className="admin-modal__header">
                    <h3>新增商品</h3>
                    <button onClick={onClose}>✕</button>
                </div>
                <div className="admin-modal__body">
                    {error && <div className="admin-products__error">{error}</div>}
                    <div className="form-group">
                        <label>商品名稱 *</label>
                        <input
                            type="text"
                            className="form-input"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="請輸入商品名稱"
                        />
                    </div>
                    <div className="form-group">
                        <label>分類</label>
                        <select
                            className="form-input"
                            value={categoryId}
                            onChange={(e) => setCategoryId(e.target.value)}
                        >
                            {categories.map((cat) => (
                                <option key={cat.id} value={cat.id}>
                                    {cat.name}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="form-group">
                        <label>價格 *</label>
                        <input
                            type="number"
                            className="form-input"
                            value={price}
                            min={1}
                            onChange={(e) => setPrice(parseInt(e.target.value) || 0)}
                        />
                    </div>
                    <div className="form-group">
                        <label>描述</label>
                        <textarea
                            className="form-textarea"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="請輸入商品描述"
                        />
                    </div>
                    <div className="form-group">
                        <label>每日限量（0 = 不限量）</label>
                        <input
                            type="number"
                            className="form-input"
                            value={dailyLimit}
                            min={0}
                            onChange={(e) => setDailyLimit(parseInt(e.target.value) || 0)}
                        />
                    </div>
                </div>
                <div className="admin-modal__footer">
                    <button className="btn btn-secondary" onClick={onClose} disabled={saving}>
                        取消
                    </button>
                    <button className="btn btn-primary" onClick={handleSubmit} disabled={saving}>
                        {saving ? '儲存中...' : '新增'}
                    </button>
                </div>
            </div>
        </div>
    );
}

// ==================== 編輯商品 Modal ====================

interface EditProductModalProps {
    product: Product;
    categories: Category[];
    onClose: () => void;
    onSaved: () => void;
}

interface EditableCustomizationGroup {
    name: string;
    options: CustomizationOption[];
}

function EditProductModal({ product, categories, onClose, onSaved }: EditProductModalProps) {
    const [name, setName] = useState(product.name);
    const [categoryId, setCategoryId] = useState(product.categoryId || '');
    const [price, setPrice] = useState(product.price);
    const [description, setDescription] = useState(product.description || '');
    const [dailyLimit, setDailyLimit] = useState(product.dailyLimit);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Group customization options by optionType for display
    const buildGroups = (options: CustomizationOption[]): EditableCustomizationGroup[] => {
        const groupMap = new Map<string, CustomizationOption[]>();
        for (const opt of options) {
            const key = opt.optionType || 'other';
            if (!groupMap.has(key)) groupMap.set(key, []);
            groupMap.get(key)!.push(opt);
        }
        const groupLabels: Record<string, string> = {
            rice_amount: '飯量調整',
            exclude: '不要',
            extra: '額外需求',
        };
        return Array.from(groupMap.entries()).map(([key, opts]) => ({
            name: groupLabels[key] || key,
            options: opts,
        }));
    };

    const [groups, setGroups] = useState<EditableCustomizationGroup[]>(
        buildGroups(product.customizationOptions)
    );

    // New option input state per group
    const [newOptionInputs, setNewOptionInputs] = useState<Record<number, string>>({});

    const handleAddOption = (groupIndex: number) => {
        const optionName = (newOptionInputs[groupIndex] || '').trim();
        if (!optionName) return;
        setGroups((prev) => {
            const updated = [...prev];
            const group = { ...updated[groupIndex] };
            const optionTypeMap: Record<string, string> = {
                '飯量調整': 'rice_amount',
                '不要': 'exclude',
                '額外需求': 'extra',
            };
            group.options = [
                ...group.options,
                {
                    id: `new-${Date.now()}`,
                    name: optionName,
                    optionType: optionTypeMap[group.name] || 'other',
                    priceAdjustment: 0,
                },
            ];
            updated[groupIndex] = group;
            return updated;
        });
        setNewOptionInputs((prev) => ({ ...prev, [groupIndex]: '' }));
    };

    const handleRemoveOption = (groupIndex: number, optionIndex: number) => {
        setGroups((prev) => {
            const updated = [...prev];
            const group = { ...updated[groupIndex] };
            group.options = group.options.filter((_, i) => i !== optionIndex);
            updated[groupIndex] = group;
            return updated;
        });
    };

    const handleAddGroup = () => {
        setGroups((prev) => [...prev, { name: '新群組', options: [] }]);
    };

    const handleSubmit = async () => {
        if (!name.trim()) {
            setError('請輸入商品名稱');
            return;
        }
        if (price <= 0) {
            setError('價格必須大於 0');
            return;
        }
        setSaving(true);
        setError(null);
        try {
            await updateProduct(product.id, {
                name: name.trim(),
                categoryId: categoryId || null,
                price,
                description: description.trim() || null,
                dailyLimit,
            });
            onSaved();
        } catch (err: any) {
            setError(err.response?.data?.detail || '更新失敗，請稍後再試');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="admin-modal-overlay" onClick={onClose}>
            <div className="admin-modal" onClick={(e) => e.stopPropagation()}>
                <div className="admin-modal__header">
                    <h3>編輯商品</h3>
                    <button onClick={onClose}>✕</button>
                </div>
                <div className="admin-modal__body">
                    {error && <div className="admin-products__error">{error}</div>}
                    <div className="form-group">
                        <label>商品名稱 *</label>
                        <input
                            type="text"
                            className="form-input"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                        />
                    </div>
                    <div className="form-group">
                        <label>分類</label>
                        <select
                            className="form-input"
                            value={categoryId}
                            onChange={(e) => setCategoryId(e.target.value)}
                        >
                            <option value="">未分類</option>
                            {categories.map((cat) => (
                                <option key={cat.id} value={cat.id}>
                                    {cat.name}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="form-group">
                        <label>價格 *</label>
                        <input
                            type="number"
                            className="form-input"
                            value={price}
                            min={1}
                            onChange={(e) => setPrice(parseInt(e.target.value) || 0)}
                        />
                    </div>
                    <div className="form-group">
                        <label>描述</label>
                        <textarea
                            className="form-textarea"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                        />
                    </div>
                    <div className="form-group">
                        <label>每日限量（0 = 不限量）</label>
                        <input
                            type="number"
                            className="form-input"
                            value={dailyLimit}
                            min={0}
                            onChange={(e) => setDailyLimit(parseInt(e.target.value) || 0)}
                        />
                    </div>

                    {/* 客製化選項群組 */}
                    <div className="admin-products__customization-section">
                        <div className="admin-products__customization-header">
                            <h4>客製化選項</h4>
                            <button
                                className="btn btn-secondary btn--sm"
                                onClick={handleAddGroup}
                            >
                                + 新增群組
                            </button>
                        </div>
                        {groups.length === 0 && (
                            <p className="admin-products__empty-hint">尚無客製化選項</p>
                        )}
                        {groups.map((group, gi) => (
                            <div key={gi} className="admin-products__customization-group">
                                <div className="admin-products__customization-group-title">
                                    {group.name}
                                </div>
                                <div className="admin-products__customization-options">
                                    {group.options.map((opt, oi) => (
                                        <div key={opt.id} className="admin-products__customization-option">
                                            <span>{opt.name}</span>
                                            {opt.priceAdjustment !== 0 && (
                                                <span className="admin-products__price-adj">
                                                    {opt.priceAdjustment > 0 ? '+' : ''}{opt.priceAdjustment}
                                                </span>
                                            )}
                                            <button
                                                className="admin-products__remove-option-btn"
                                                onClick={() => handleRemoveOption(gi, oi)}
                                                title="移除"
                                            >
                                                ✕
                                            </button>
                                        </div>
                                    ))}
                                </div>
                                <div className="admin-products__add-option-row">
                                    <input
                                        type="text"
                                        className="form-input form-input--sm"
                                        placeholder="新增選項名稱"
                                        value={newOptionInputs[gi] || ''}
                                        onChange={(e) =>
                                            setNewOptionInputs((prev) => ({ ...prev, [gi]: e.target.value }))
                                        }
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter') handleAddOption(gi);
                                        }}
                                    />
                                    <button
                                        className="btn btn-primary btn--sm"
                                        onClick={() => handleAddOption(gi)}
                                    >
                                        新增
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
                <div className="admin-modal__footer">
                    <button className="btn btn-secondary" onClick={onClose} disabled={saving}>
                        取消
                    </button>
                    <button className="btn btn-primary" onClick={handleSubmit} disabled={saving}>
                        {saving ? '儲存中...' : '儲存'}
                    </button>
                </div>
            </div>
        </div>
    );
}

// ==================== 主元件 ====================

export function AdminProducts() {
    const [products, setProducts] = useState<Product[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
    const [editingProduct, setEditingProduct] = useState<Product | null>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [productsData, categoriesData] = await Promise.all([
                getProducts(),
                getCategories(),
            ]);
            setProducts(productsData);
            setCategories(categoriesData);
        } catch (err: any) {
            setError(err.response?.data?.detail || '載入資料失敗，請稍後再試');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const filteredProducts = selectedCategory
        ? products.filter((p) => p.categoryId === selectedCategory)
        : products;

    const getCategoryName = (categoryId: string | null) => {
        if (!categoryId) return '未分類';
        return categories.find((c) => c.id === categoryId)?.name || '未分類';
    };

    const handleToggleAvailable = async (productId: string) => {
        try {
            const newAvailable = await toggleProductAvailability(productId);
            setProducts((prev) =>
                prev.map((p) =>
                    p.id === productId ? { ...p, isAvailable: newAvailable } : p
                )
            );
        } catch {
            alert('切換狀態失敗，請稍後再試');
        }
    };

    const handleResetSold = async (productId: string) => {
        try {
            await resetProductSold(productId);
            setProducts((prev) =>
                prev.map((p) =>
                    p.id === productId ? { ...p, todaySold: 0 } : p
                )
            );
        } catch {
            alert('重置銷量失敗，請稍後再試');
        }
    };

    const handleProductCreated = () => {
        setShowCreateModal(false);
        fetchData();
    };

    const handleProductSaved = () => {
        setEditingProduct(null);
        fetchData();
    };

    if (loading) {
        return (
            <div className="admin-products">
                <div className="admin-page-header">
                    <h1 className="admin-page-title">商品管理</h1>
                </div>
                <div className="admin-products__loading">載入中...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="admin-products">
                <div className="admin-page-header">
                    <h1 className="admin-page-title">商品管理</h1>
                </div>
                <div className="admin-products__error">
                    {error}
                    <button className="btn btn-primary" onClick={fetchData} style={{ marginLeft: 12 }}>
                        重試
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="admin-products">
            <div className="admin-page-header">
                <h1 className="admin-page-title">商品管理</h1>
                <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
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
                {categories.map((cat) => (
                    <button
                        key={cat.id}
                        className={`admin-products__category-btn ${selectedCategory === cat.id ? 'active' : ''}`}
                        onClick={() => setSelectedCategory(cat.id)}
                    >
                        {cat.name} ({products.filter((p) => p.categoryId === cat.id).length})
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
                                        <span className="admin-products__limit-display">
                                            {product.dailyLimit === 0 ? '不限' : product.dailyLimit}
                                        </span>
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
                            {filteredProducts.length === 0 && (
                                <tr>
                                    <td colSpan={7} style={{ textAlign: 'center', padding: '2rem' }}>
                                        尚無商品資料
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* 新增商品 Modal */}
            {showCreateModal && (
                <CreateProductModal
                    categories={categories}
                    onClose={() => setShowCreateModal(false)}
                    onCreated={handleProductCreated}
                />
            )}

            {/* 編輯商品 Modal */}
            {editingProduct && (
                <EditProductModal
                    product={editingProduct}
                    categories={categories}
                    onClose={() => setEditingProduct(null)}
                    onSaved={handleProductSaved}
                />
            )}
        </div>
    );
}

export default AdminProducts;
