/**
 * 管理後台 - 庫存管理頁面
 */
import { useState, useEffect, useCallback } from 'react';
import {
    getMaterials,
    getInventoryStats,
    adjustStock,
    createMaterial,
    getProducts,
    getBOMList,
    createBOM,
    deleteBOM,
} from '../../services/adminApi';
import type {
    Material,
    InventoryStats,
    Product,
    ProductMaterialBOM,
} from '../../services/adminApi';
import '../admin/AdminLayout.css';
import './AdminInventory.css';

export function AdminInventory() {
    // --- 資料狀態 ---
    const [materials, setMaterials] = useState<Material[]>([]);
    const [stats, setStats] = useState<InventoryStats>({ totalMaterials: 0, lowStockCount: 0, outOfStockCount: 0 });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // --- 補貨 ---
    const [showAddStock, setShowAddStock] = useState<string | null>(null);
    const [addAmount, setAddAmount] = useState<number>(0);
    const [adjusting, setAdjusting] = useState(false);

    // --- 新增物料 Modal ---
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [createForm, setCreateForm] = useState({ name: '', unit: '份', currentStock: 0, safetyStock: 0 });
    const [creating, setCreating] = useState(false);
    const [createError, setCreateError] = useState<string | null>(null);

    // --- BOM 管理 ---
    const [showBOM, setShowBOM] = useState<string | null>(null); // materialId being viewed
    const [bomList, setBomList] = useState<ProductMaterialBOM[]>([]);
    const [bomLoading, setBomLoading] = useState(false);
    const [products, setProducts] = useState<Product[]>([]);
    const [showAddBOM, setShowAddBOM] = useState(false);
    const [bomForm, setBomForm] = useState({ productId: '', quantity: 1 });
    const [bomCreating, setBomCreating] = useState(false);

    // --- 載入資料 ---
    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [materialsData, statsData] = await Promise.all([
                getMaterials(),
                getInventoryStats(),
            ]);
            setMaterials(materialsData);
            setStats(statsData);
        } catch (err: any) {
            setError(err?.response?.data?.detail || err?.message || '載入庫存資料失敗');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // --- 計算庫存狀態 ---
    const getStockStatus = (material: Material) => {
        if (material.currentStock <= 0) return 'out';
        if (material.currentStock <= material.safetyStock) return 'low';
        return 'normal';
    };

    // --- 補貨 ---
    const handleAddStock = async (materialId: string) => {
        if (addAmount <= 0) return;
        setAdjusting(true);
        try {
            const updated = await adjustStock(materialId, addAmount, '手動補貨');
            setMaterials(prev => prev.map(m => m.id === materialId ? updated : m));
            setShowAddStock(null);
            setAddAmount(0);
            // 重新載入統計
            const newStats = await getInventoryStats();
            setStats(newStats);
        } catch (err: any) {
            alert(err?.response?.data?.detail || '補貨失敗');
        } finally {
            setAdjusting(false);
        }
    };

    // --- 新增物料 ---
    const handleCreateMaterial = async () => {
        if (!createForm.name.trim()) {
            setCreateError('請輸入物料名稱');
            return;
        }
        setCreating(true);
        setCreateError(null);
        try {
            await createMaterial({
                name: createForm.name.trim(),
                unit: createForm.unit.trim() || '份',
                current_stock: createForm.currentStock,
                safety_stock: createForm.safetyStock,
            });
            setShowCreateModal(false);
            setCreateForm({ name: '', unit: '份', currentStock: 0, safetyStock: 0 });
            await fetchData();
        } catch (err: any) {
            setCreateError(err?.response?.data?.detail || '新增物料失敗');
        } finally {
            setCreating(false);
        }
    };

    // --- BOM 管理 ---
    const handleShowBOM = async (materialId: string) => {
        if (showBOM === materialId) {
            setShowBOM(null);
            return;
        }
        setShowBOM(materialId);
        setBomLoading(true);
        try {
            const [bomData, productsData] = await Promise.all([
                getBOMList({ materialId }),
                products.length > 0 ? Promise.resolve(products) : getProducts(),
            ]);
            setBomList(bomData);
            if (products.length === 0) setProducts(productsData);
        } catch {
            setBomList([]);
        } finally {
            setBomLoading(false);
        }
    };

    const handleAddBOM = async (materialId: string) => {
        if (!bomForm.productId || bomForm.quantity <= 0) return;
        setBomCreating(true);
        try {
            const newBom = await createBOM({
                productId: bomForm.productId,
                materialId,
                quantity: bomForm.quantity,
            });
            setBomList(prev => [...prev, newBom]);
            setShowAddBOM(false);
            setBomForm({ productId: '', quantity: 1 });
        } catch (err: any) {
            alert(err?.response?.data?.detail || '新增 BOM 失敗');
        } finally {
            setBomCreating(false);
        }
    };

    const handleDeleteBOM = async (bomId: string) => {
        if (!confirm('確定要刪除此商品物料關聯？')) return;
        try {
            await deleteBOM(bomId);
            setBomList(prev => prev.filter(b => b.id !== bomId));
        } catch (err: any) {
            alert(err?.response?.data?.detail || '刪除失敗');
        }
    };

    // --- 渲染 ---
    if (loading) {
        return (
            <div className="admin-inventory">
                <div className="admin-page-header">
                    <h1 className="admin-page-title">庫存管理</h1>
                </div>
                <div style={{ textAlign: 'center', padding: '3rem' }}>載入中...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="admin-inventory">
                <div className="admin-page-header">
                    <h1 className="admin-page-title">庫存管理</h1>
                </div>
                <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--color-error)' }}>
                    {error}
                    <br />
                    <button className="admin-action-btn admin-action-btn--primary" onClick={fetchData} style={{ marginTop: '1rem' }}>
                        重試
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="admin-inventory">
            <div className="admin-page-header">
                <h1 className="admin-page-title">庫存管理</h1>
                <button
                    className="admin-action-btn admin-action-btn--primary"
                    onClick={() => setShowCreateModal(true)}
                >
                    + 新增物料
                </button>
            </div>

            {/* 統計卡片 */}
            <div className="admin-stats">
                <div className="admin-stat-card">
                    <div className="admin-stat-card__label">總物料項目</div>
                    <div className="admin-stat-card__value">{stats.totalMaterials}</div>
                </div>
                <div className="admin-stat-card">
                    <div className="admin-stat-card__label">低庫存警示</div>
                    <div className="admin-stat-card__value" style={{ color: 'var(--color-warning)' }}>
                        {stats.lowStockCount}
                    </div>
                </div>
                <div className="admin-stat-card">
                    <div className="admin-stat-card__label">已缺貨</div>
                    <div className="admin-stat-card__value" style={{ color: 'var(--color-error)' }}>
                        {stats.outOfStockCount}
                    </div>
                </div>
            </div>

            {/* 庫存警示區塊 */}
            {(stats.lowStockCount > 0 || stats.outOfStockCount > 0) && (
                <div className="admin-inventory__alerts">
                    <h3>庫存警示</h3>
                    <div className="admin-inventory__alert-list">
                        {materials
                            .filter(m => getStockStatus(m) !== 'normal')
                            .map(m => (
                                <div
                                    key={m.id}
                                    className={`admin-inventory__alert-item admin-inventory__alert-item--${getStockStatus(m)}`}
                                >
                                    <span className="admin-inventory__alert-name">{m.name}</span>
                                    <span className="admin-inventory__alert-stock">
                                        {m.currentStock} {m.unit}
                                    </span>
                                    <span className="admin-inventory__alert-status">
                                        {getStockStatus(m) === 'out' ? '缺貨' : '低庫存'}
                                    </span>
                                </div>
                            ))}
                    </div>
                </div>
            )}

            {/* 物料列表 */}
            <div className="admin-card">
                <div className="admin-card__header">
                    <h3 className="admin-card__title">物料清單</h3>
                </div>
                <div className="admin-table-responsive">
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>物料名稱</th>
                                <th>單位</th>
                                <th>目前庫存</th>
                                <th>安全庫存</th>
                                <th>狀態</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            {materials.map((material) => {
                                const status = getStockStatus(material);
                                return (
                                    <tr key={material.id}>
                                        <td><strong>{material.name}</strong></td>
                                        <td>{material.unit}</td>
                                        <td>
                                            <span className={`admin-inventory__stock admin-inventory__stock--${status}`}>
                                                {material.currentStock}
                                            </span>
                                        </td>
                                        <td>{material.safetyStock}</td>
                                        <td>
                                            <span className={`admin-inventory__status admin-inventory__status--${status}`}>
                                                {status === 'out' ? '缺貨' : status === 'low' ? '低庫存' : '正常'}
                                            </span>
                                        </td>
                                        <td>
                                            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                                                {showAddStock === material.id ? (
                                                    <div className="admin-inventory__add-form">
                                                        <input
                                                            type="number"
                                                            min={1}
                                                            value={addAmount}
                                                            onChange={(e) => setAddAmount(parseInt(e.target.value) || 0)}
                                                            placeholder="數量"
                                                        />
                                                        <button
                                                            className="admin-action-btn admin-action-btn--primary"
                                                            onClick={() => handleAddStock(material.id)}
                                                            disabled={adjusting}
                                                        >
                                                            {adjusting ? '...' : '確認'}
                                                        </button>
                                                        <button
                                                            className="admin-action-btn admin-action-btn--secondary"
                                                            onClick={() => {
                                                                setShowAddStock(null);
                                                                setAddAmount(0);
                                                            }}
                                                        >
                                                            取消
                                                        </button>
                                                    </div>
                                                ) : (
                                                    <>
                                                        <button
                                                            className="admin-action-btn admin-action-btn--primary"
                                                            onClick={() => setShowAddStock(material.id)}
                                                        >
                                                            補貨
                                                        </button>
                                                        <button
                                                            className="admin-action-btn admin-action-btn--secondary"
                                                            onClick={() => handleShowBOM(material.id)}
                                                        >
                                                            {showBOM === material.id ? '收起 BOM' : 'BOM'}
                                                        </button>
                                                    </>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                            {materials.length === 0 && (
                                <tr>
                                    <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: '#999' }}>
                                        尚無物料資料，請點選「新增物料」建立
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* BOM 管理區塊 */}
            {showBOM && (
                <div className="admin-card" style={{ marginTop: 'var(--spacing-lg)' }}>
                    <div className="admin-card__header">
                        <h3 className="admin-card__title">
                            BOM 管理 - {materials.find(m => m.id === showBOM)?.name}
                        </h3>
                        <button
                            className="admin-action-btn admin-action-btn--primary"
                            onClick={() => setShowAddBOM(true)}
                        >
                            + 關聯商品
                        </button>
                    </div>

                    {bomLoading ? (
                        <div style={{ textAlign: 'center', padding: '1rem' }}>載入中...</div>
                    ) : (
                        <>
                            {/* 新增 BOM 表單 */}
                            {showAddBOM && (
                                <div className="admin-inventory__bom-form">
                                    <select
                                        value={bomForm.productId}
                                        onChange={(e) => setBomForm(prev => ({ ...prev, productId: e.target.value }))}
                                    >
                                        <option value="">-- 選擇商品 --</option>
                                        {products
                                            .filter(p => !bomList.some(b => b.productId === p.id))
                                            .map(p => (
                                                <option key={p.id} value={p.id}>{p.name}</option>
                                            ))}
                                    </select>
                                    <input
                                        type="number"
                                        min={0.01}
                                        step={0.01}
                                        value={bomForm.quantity}
                                        onChange={(e) => setBomForm(prev => ({ ...prev, quantity: parseFloat(e.target.value) || 0 }))}
                                        placeholder="用量"
                                        style={{ width: '80px' }}
                                    />
                                    <span style={{ fontSize: 'var(--font-size-sm)', color: '#666' }}>
                                        {materials.find(m => m.id === showBOM)?.unit}
                                    </span>
                                    <button
                                        className="admin-action-btn admin-action-btn--primary"
                                        onClick={() => handleAddBOM(showBOM)}
                                        disabled={bomCreating || !bomForm.productId}
                                    >
                                        {bomCreating ? '...' : '新增'}
                                    </button>
                                    <button
                                        className="admin-action-btn admin-action-btn--secondary"
                                        onClick={() => { setShowAddBOM(false); setBomForm({ productId: '', quantity: 1 }); }}
                                    >
                                        取消
                                    </button>
                                </div>
                            )}

                            {bomList.length === 0 ? (
                                <div style={{ textAlign: 'center', padding: '1.5rem', color: '#999', fontSize: 'var(--font-size-sm)' }}>
                                    此物料尚未關聯任何商品
                                </div>
                            ) : (
                                <div className="admin-table-responsive">
                                    <table className="admin-table">
                                        <thead>
                                            <tr>
                                                <th>商品名稱</th>
                                                <th>每份用量</th>
                                                <th>單位</th>
                                                <th>操作</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {bomList.map(bom => (
                                                <tr key={bom.id}>
                                                    <td>{bom.productName}</td>
                                                    <td>{bom.quantity}</td>
                                                    <td>{bom.unit}</td>
                                                    <td>
                                                        <button
                                                            className="admin-action-btn admin-action-btn--danger"
                                                            onClick={() => handleDeleteBOM(bom.id)}
                                                        >
                                                            移除
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </>
                    )}
                </div>
            )}

            {/* 新增物料 Modal */}
            {showCreateModal && (
                <div className="admin-inventory__modal-overlay" onClick={() => setShowCreateModal(false)}>
                    <div className="admin-inventory__modal" onClick={(e) => e.stopPropagation()}>
                        <h3 className="admin-inventory__modal-title">新增物料</h3>

                        {createError && (
                            <div className="admin-inventory__modal-error">{createError}</div>
                        )}

                        <div className="admin-inventory__modal-field">
                            <label>物料名稱 *</label>
                            <input
                                type="text"
                                value={createForm.name}
                                onChange={(e) => setCreateForm(prev => ({ ...prev, name: e.target.value }))}
                                placeholder="例：雞腿、白飯"
                                autoFocus
                            />
                        </div>

                        <div className="admin-inventory__modal-field">
                            <label>單位</label>
                            <input
                                type="text"
                                value={createForm.unit}
                                onChange={(e) => setCreateForm(prev => ({ ...prev, unit: e.target.value }))}
                                placeholder="例：份 / kg / 顆 / 片"
                            />
                        </div>

                        <div className="admin-inventory__modal-field">
                            <label>初始庫存</label>
                            <input
                                type="number"
                                min={0}
                                value={createForm.currentStock}
                                onChange={(e) => setCreateForm(prev => ({ ...prev, currentStock: parseFloat(e.target.value) || 0 }))}
                            />
                        </div>

                        <div className="admin-inventory__modal-field">
                            <label>安全庫存</label>
                            <input
                                type="number"
                                min={0}
                                value={createForm.safetyStock}
                                onChange={(e) => setCreateForm(prev => ({ ...prev, safetyStock: parseFloat(e.target.value) || 0 }))}
                            />
                        </div>

                        <div className="admin-inventory__modal-actions">
                            <button
                                className="admin-action-btn admin-action-btn--primary"
                                onClick={handleCreateMaterial}
                                disabled={creating}
                            >
                                {creating ? '建立中...' : '建立'}
                            </button>
                            <button
                                className="admin-action-btn admin-action-btn--secondary"
                                onClick={() => { setShowCreateModal(false); setCreateError(null); }}
                            >
                                取消
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default AdminInventory;
