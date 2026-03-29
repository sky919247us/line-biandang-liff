/**
 * 管理後台 - 庫存管理頁面
 */
import { useState, useEffect } from 'react';
import '../admin/AdminLayout.css';
import './AdminInventory.css';

interface Material {
    id: string;
    name: string;
    unit: string;
    currentStock: number;
    safetyStock: number;
    usedToday: number;
}

// 模擬物料資料
const mockMaterials: Material[] = [
    { id: '1', name: '雞腿', unit: '份', currentStock: 25, safetyStock: 10, usedToday: 20 },
    { id: '2', name: '豬排', unit: '份', currentStock: 18, safetyStock: 10, usedToday: 22 },
    { id: '3', name: '菲力牛排', unit: '份', currentStock: 5, safetyStock: 5, usedToday: 8 },
    { id: '4', name: '白飯', unit: 'kg', currentStock: 8, safetyStock: 3, usedToday: 4 },
    { id: '5', name: '高麗菜', unit: '顆', currentStock: 12, safetyStock: 5, usedToday: 3 },
    { id: '6', name: '紅蘿蔔', unit: '條', currentStock: 20, safetyStock: 10, usedToday: 5 },
    { id: '7', name: '蛋', unit: '顆', currentStock: 45, safetyStock: 20, usedToday: 15 },
    { id: '8', name: '起司片', unit: '片', currentStock: 8, safetyStock: 10, usedToday: 10 },
    { id: '9', name: '火腿片', unit: '片', currentStock: 12, safetyStock: 10, usedToday: 10 },
    { id: '10', name: '豬腳', unit: '份', currentStock: 0, safetyStock: 5, usedToday: 0 },
];

export function AdminInventory() {
    const [materials, setMaterials] = useState<Material[]>([]);
    const [showAddStock, setShowAddStock] = useState<string | null>(null);
    const [addAmount, setAddAmount] = useState<number>(0);

    useEffect(() => {
        setMaterials(mockMaterials);
    }, []);

    // 計算庫存狀態
    const getStockStatus = (material: Material) => {
        if (material.currentStock === 0) return 'out';
        if (material.currentStock <= material.safetyStock) return 'low';
        return 'normal';
    };

    // 統計
    const stats = {
        total: materials.length,
        low: materials.filter(m => getStockStatus(m) === 'low').length,
        out: materials.filter(m => getStockStatus(m) === 'out').length,
    };

    // 補貨
    const handleAddStock = (materialId: string) => {
        if (addAmount <= 0) return;

        setMaterials(prev => prev.map(m => {
            if (m.id === materialId) {
                return { ...m, currentStock: m.currentStock + addAmount };
            }
            return m;
        }));

        setShowAddStock(null);
        setAddAmount(0);
    };

    return (
        <div className="admin-inventory">
            <div className="admin-page-header">
                <h1 className="admin-page-title">庫存管理</h1>
            </div>

            {/* 統計卡片 */}
            <div className="admin-stats">
                <div className="admin-stat-card">
                    <div className="admin-stat-card__label">總物料項目</div>
                    <div className="admin-stat-card__value">{stats.total}</div>
                </div>
                <div className="admin-stat-card">
                    <div className="admin-stat-card__label">低庫存警示</div>
                    <div className="admin-stat-card__value" style={{ color: 'var(--color-warning)' }}>
                        {stats.low}
                    </div>
                </div>
                <div className="admin-stat-card">
                    <div className="admin-stat-card__label">已缺貨</div>
                    <div className="admin-stat-card__value" style={{ color: 'var(--color-error)' }}>
                        {stats.out}
                    </div>
                </div>
            </div>

            {/* 庫存警示區塊 */}
            {(stats.low > 0 || stats.out > 0) && (
                <div className="admin-inventory__alerts">
                    <h3>⚠️ 庫存警示</h3>
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
                                <th>今日消耗</th>
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
                                        <td>{material.usedToday}</td>
                                        <td>
                                            <span className={`admin-inventory__status admin-inventory__status--${status}`}>
                                                {status === 'out' ? '缺貨' : status === 'low' ? '低庫存' : '正常'}
                                            </span>
                                        </td>
                                        <td>
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
                                                    >
                                                        確認
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
                                                <button
                                                    className="admin-action-btn admin-action-btn--primary"
                                                    onClick={() => setShowAddStock(material.id)}
                                                >
                                                    補貨
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

export default AdminInventory;
