/**
 * 管理後台 - 手動新增訂單
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Product, OrderType } from '../../types';
import '../admin/AdminLayout.css';

interface ManualOrderItem {
    productId: string;
    productName: string;
    quantity: number;
    unitPrice: number;
}

export function AdminManualOrder() {
    const navigate = useNavigate();
    const [products, setProducts] = useState<Product[]>([]);
    const [orderType, setOrderType] = useState<OrderType>('pickup');
    const [items, setItems] = useState<ManualOrderItem[]>([]);
    const [contactName, setContactName] = useState('');
    const [contactPhone, setContactPhone] = useState('');
    const [tableNumber, setTableNumber] = useState('');
    const [notes, setNotes] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        // Mock products for selection
        setProducts([
            { id: '1', name: '戰斧雞腿', price: 120 } as Product,
            { id: '2', name: '五告厚豬排', price: 130 } as Product,
            { id: '3', name: '牛逼菲力', price: 150 } as Product,
        ]);
    }, []);

    const addProduct = (product: Product) => {
        const existing = items.find(i => i.productId === product.id);
        if (existing) {
            setItems(items.map(i =>
                i.productId === product.id ? { ...i, quantity: i.quantity + 1 } : i
            ));
        } else {
            setItems([...items, {
                productId: product.id,
                productName: product.name,
                quantity: 1,
                unitPrice: product.effectivePrice ?? product.price,
            }]);
        }
    };

    const updateQty = (productId: string, qty: number) => {
        if (qty <= 0) {
            setItems(items.filter(i => i.productId !== productId));
        } else {
            setItems(items.map(i => i.productId === productId ? { ...i, quantity: qty } : i));
        }
    };

    const total = items.reduce((sum, i) => sum + i.unitPrice * i.quantity, 0);

    const handleSubmit = async () => {
        if (items.length === 0) return;
        setIsSubmitting(true);
        try {
            // POST /admin/orders/manual
            const response = await fetch('/api/v1/admin/orders/manual', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                },
                body: JSON.stringify({
                    order_type: orderType,
                    items: items.map(i => ({
                        product_id: i.productId,
                        quantity: i.quantity,
                    })),
                    contact_name: contactName || undefined,
                    contact_phone: contactPhone || undefined,
                    table_number: orderType === 'dine_in' ? tableNumber : undefined,
                    notes: notes || undefined,
                }),
            });
            if (response.ok) {
                navigate('/admin/orders');
            }
        } catch (err) {
            console.error('建立訂單失敗:', err);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="admin-manual-order">
            <div className="admin-page-header">
                <h1 className="admin-page-title">手動新增訂單</h1>
            </div>

            {/* 訂單類型 */}
            <div className="admin-card">
                <div className="admin-card__header">
                    <h3 className="admin-card__title">訂單類型</h3>
                </div>
                <div className="admin-card__body">
                    <div style={{ display: 'flex', gap: 8 }}>
                        {(['pickup', 'delivery', 'dine_in'] as OrderType[]).map(type => (
                            <button
                                key={type}
                                className={`admin-action-btn ${orderType === type ? 'admin-action-btn--primary' : ''}`}
                                onClick={() => setOrderType(type)}
                            >
                                {type === 'pickup' ? '自取' : type === 'delivery' ? '外送' : '內用'}
                            </button>
                        ))}
                    </div>
                    {orderType === 'dine_in' && (
                        <div style={{ marginTop: 12 }}>
                            <label className="form-label">桌號</label>
                            <input
                                type="text"
                                className="form-input"
                                value={tableNumber}
                                onChange={e => setTableNumber(e.target.value)}
                                placeholder="例：A1"
                            />
                        </div>
                    )}
                </div>
            </div>

            {/* 選擇商品 */}
            <div className="admin-card">
                <div className="admin-card__header">
                    <h3 className="admin-card__title">選擇商品</h3>
                </div>
                <div className="admin-card__body">
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
                        {products.map(p => (
                            <button
                                key={p.id}
                                className="admin-action-btn"
                                onClick={() => addProduct(p)}
                            >
                                {p.name} ${p.price}
                            </button>
                        ))}
                    </div>

                    {items.length > 0 && (
                        <table className="admin-table">
                            <thead>
                                <tr>
                                    <th>商品</th>
                                    <th>單價</th>
                                    <th>數量</th>
                                    <th>小計</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map(item => (
                                    <tr key={item.productId}>
                                        <td>{item.productName}</td>
                                        <td>${item.unitPrice}</td>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                                <button className="admin-action-btn" onClick={() => updateQty(item.productId, item.quantity - 1)}>-</button>
                                                <span>{item.quantity}</span>
                                                <button className="admin-action-btn" onClick={() => updateQty(item.productId, item.quantity + 1)}>+</button>
                                            </div>
                                        </td>
                                        <td><strong>${item.unitPrice * item.quantity}</strong></td>
                                        <td>
                                            <button className="admin-action-btn admin-action-btn--danger" onClick={() => updateQty(item.productId, 0)}>
                                                刪除
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>

            {/* 聯絡資訊 */}
            <div className="admin-card">
                <div className="admin-card__header">
                    <h3 className="admin-card__title">聯絡資訊</h3>
                </div>
                <div className="admin-card__body">
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                        <div className="form-group">
                            <label className="form-label">姓名</label>
                            <input type="text" className="form-input" value={contactName} onChange={e => setContactName(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">電話</label>
                            <input type="tel" className="form-input" value={contactPhone} onChange={e => setContactPhone(e.target.value)} />
                        </div>
                    </div>
                    <div className="form-group" style={{ marginTop: 12 }}>
                        <label className="form-label">備註</label>
                        <textarea className="form-input" value={notes} onChange={e => setNotes(e.target.value)} rows={2} />
                    </div>
                </div>
            </div>

            {/* 提交 */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 0' }}>
                <div style={{ fontSize: 20, fontWeight: 700 }}>
                    合計：<span style={{ color: 'var(--color-primary)' }}>${total}</span>
                </div>
                <button
                    className="btn btn-primary btn-lg"
                    onClick={handleSubmit}
                    disabled={isSubmitting || items.length === 0}
                >
                    {isSubmitting ? '建立中...' : '建立訂單'}
                </button>
            </div>
        </div>
    );
}

export default AdminManualOrder;
