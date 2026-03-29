/**
 * 加入群組點餐頁面
 *
 * 透過分享代碼加入群組訂單，選擇商品，檢視參與者
 * 建立者可鎖定及送出訂單
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { Header } from '../../components/layout/Header';
import { BottomNav } from '../../components/layout/BottomNav';
import './GroupOrder.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const STATUS_TEXT: Record<string, string> = {
    open: '開放中',
    locked: '已鎖定',
    ordered: '已下單',
    completed: '已完成',
    cancelled: '已取消',
};

interface Product {
    id: string;
    name: string;
    price: number;
    description?: string;
    is_available?: boolean;
}

interface ParticipantItem {
    product_id: string;
    product_name: string;
    quantity: number;
    unit_price: number;
    subtotal: number;
}

interface Participant {
    user_id: string;
    display_name: string;
    is_creator: boolean;
    items: ParticipantItem[];
    subtotal: number;
}

interface GroupOrderDetail {
    id: string;
    title: string;
    status: string;
    share_code: string;
    max_participants: number | null;
    creator_id: string;
    participants: Participant[];
    total_amount: number;
}

function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
}

export function JoinGroupPage() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const codeFromUrl = searchParams.get('code') || '';

    const [code, setCode] = useState(codeFromUrl);
    const [detail, setDetail] = useState<GroupOrderDetail | null>(null);
    const [products, setProducts] = useState<Product[]>([]);
    const [selectedItems, setSelectedItems] = useState<Record<string, number>>({});
    const [isJoining, setIsJoining] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [isLocking, setIsLocking] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [message, setMessage] = useState<{ type: string; text: string } | null>(null);
    const [isCreator, setIsCreator] = useState(false);
    const [hasJoined, setHasJoined] = useState(false);

    const showMessage = (type: string, text: string) => {
        setMessage({ type, text });
        if (type !== 'error') {
            setTimeout(() => setMessage(null), 3000);
        }
    };

    const loadDetail = useCallback(async (shareCode: string) => {
        try {
            const res = await axios.get(`${API_BASE}/group-orders/${shareCode}`, {
                headers: getAuthHeaders(),
            });
            const data: GroupOrderDetail = res.data;
            setDetail(data);

            // Determine if current user is the creator
            const token = localStorage.getItem('access_token');
            if (token) {
                try {
                    const payload = JSON.parse(atob(token.split('.')[1]));
                    const userId = payload.sub || payload.user_id;
                    setIsCreator(data.creator_id === userId);
                    // Check if user already joined
                    const joined = data.participants.some((p) => p.user_id === userId);
                    setHasJoined(joined);
                    // Pre-fill selected items from user's existing items
                    if (joined) {
                        const myParticipant = data.participants.find((p) => p.user_id === userId);
                        if (myParticipant) {
                            const items: Record<string, number> = {};
                            myParticipant.items.forEach((item) => {
                                items[item.product_id] = item.quantity;
                            });
                            setSelectedItems(items);
                        }
                    }
                } catch {
                    // token parsing failed; ignore
                }
            }
        } catch (err) {
            console.error('載入群組詳情失敗:', err);
            showMessage('error', '載入群組詳情失敗');
        }
    }, []);

    const loadProducts = useCallback(async () => {
        try {
            const res = await axios.get(`${API_BASE}/products`, {
                headers: getAuthHeaders(),
            });
            const items = Array.isArray(res.data) ? res.data : res.data.items || [];
            setProducts(items.filter((p: Product) => p.is_available !== false));
        } catch (err) {
            console.error('載入商品失敗:', err);
        }
    }, []);

    // Auto-join/load if code comes from URL
    useEffect(() => {
        if (codeFromUrl) {
            handleJoin(codeFromUrl);
            loadProducts();
        }
    }, [codeFromUrl]); // eslint-disable-line react-hooks/exhaustive-deps

    const handleJoin = async (shareCode?: string) => {
        const c = (shareCode || code).trim().toUpperCase();
        if (!c) return;
        setIsJoining(true);
        setMessage(null);
        try {
            await axios.post(
                `${API_BASE}/group-orders/${c}/join`,
                {},
                { headers: getAuthHeaders() },
            );
            setCode(c);
            setHasJoined(true);
            await loadDetail(c);
            if (!products.length) {
                await loadProducts();
            }
        } catch (err: unknown) {
            // If already joined (409 or similar), still load detail
            if (axios.isAxiosError(err) && err.response && (err.response.status === 409 || err.response.status === 400)) {
                setHasJoined(true);
                await loadDetail(c);
                if (!products.length) {
                    await loadProducts();
                }
            } else {
                console.error('加入群組失敗:', err);
                showMessage('error', '加入群組失敗，請確認代碼是否正確');
            }
        } finally {
            setIsJoining(false);
        }
    };

    const handleQuantityChange = (productId: string, delta: number) => {
        setSelectedItems((prev) => {
            const current = prev[productId] || 0;
            const next = current + delta;
            if (next <= 0) {
                const { [productId]: _, ...rest } = prev;
                return rest;
            }
            return { ...prev, [productId]: next };
        });
    };

    const handleSaveItems = async () => {
        if (!code) return;
        setIsSaving(true);
        setMessage(null);
        try {
            const items = Object.entries(selectedItems).map(([product_id, quantity]) => ({
                product_id,
                quantity,
            }));
            await axios.put(
                `${API_BASE}/group-orders/${code}/items`,
                { items },
                { headers: getAuthHeaders() },
            );
            showMessage('success', '品項已更新');
            await loadDetail(code);
        } catch (err) {
            console.error('更新品項失敗:', err);
            showMessage('error', '更新品項失敗');
        } finally {
            setIsSaving(false);
        }
    };

    const handleLock = async () => {
        if (!code) return;
        setIsLocking(true);
        try {
            await axios.post(
                `${API_BASE}/group-orders/${code}/lock`,
                {},
                { headers: getAuthHeaders() },
            );
            showMessage('success', '群組訂單已鎖定');
            await loadDetail(code);
        } catch (err) {
            console.error('鎖定失敗:', err);
            showMessage('error', '鎖定失敗');
        } finally {
            setIsLocking(false);
        }
    };

    const handleSubmit = async () => {
        if (!code) return;
        setIsSubmitting(true);
        try {
            await axios.post(
                `${API_BASE}/group-orders/${code}/submit`,
                {},
                { headers: getAuthHeaders() },
            );
            showMessage('success', '訂單已送出');
            await loadDetail(code);
        } catch (err) {
            console.error('送出失敗:', err);
            showMessage('error', '送出訂單失敗');
        } finally {
            setIsSubmitting(false);
        }
    };

    const canEdit = detail?.status === 'open' && hasJoined;

    return (
        <div className="page group-page">
            <Header title="群組點餐" showBack onBack={() => navigate('/group')} />

            <main className="page-content">
                {/* 訊息提示 */}
                {message && (
                    <div className={`group-message group-message--${message.type}`}>
                        {message.text}
                    </div>
                )}

                {/* 加入表單（尚未加入時顯示） */}
                {!detail && (
                    <div className="group-join">
                        <div className="group-join__form">
                            <input
                                className="group-join__input"
                                type="text"
                                placeholder="輸入分享代碼"
                                value={code}
                                onChange={(e) => setCode(e.target.value.toUpperCase())}
                            />
                            <button
                                className="group-join__btn"
                                onClick={() => handleJoin()}
                                disabled={!code.trim() || isJoining}
                            >
                                {isJoining ? '加入中...' : '加入'}
                            </button>
                        </div>
                    </div>
                )}

                {/* 群組詳情 */}
                {detail && (
                    <div className="group-detail">
                        {/* 標題與狀態 */}
                        <div className="group-detail__header">
                            <h2 className="group-detail__title">{detail.title}</h2>
                            <div className="group-detail__meta">
                                <span className={`group-card__status group-card__status--${detail.status}`}>
                                    {STATUS_TEXT[detail.status] || detail.status}
                                </span>
                                <span>代碼：<span className="group-card__code">{detail.share_code}</span></span>
                                <span>{detail.participants.length} 人參與</span>
                            </div>
                        </div>

                        {/* 商品選擇（開放中才可編輯） */}
                        {canEdit && products.length > 0 && (
                            <div className="group-products">
                                <h3 className="group-products__title">選擇品項</h3>
                                <div className="group-products__list">
                                    {products.map((product) => (
                                        <div key={product.id} className="group-product-item">
                                            <div className="group-product-item__info">
                                                <span className="group-product-item__name">{product.name}</span>
                                                <span className="group-product-item__price">${product.price}</span>
                                            </div>
                                            <div className="group-product-item__controls">
                                                <button
                                                    className="group-product-item__qty-btn"
                                                    onClick={() => handleQuantityChange(product.id, -1)}
                                                    disabled={!selectedItems[product.id]}
                                                >
                                                    -
                                                </button>
                                                <span className="group-product-item__qty">
                                                    {selectedItems[product.id] || 0}
                                                </span>
                                                <button
                                                    className="group-product-item__qty-btn"
                                                    onClick={() => handleQuantityChange(product.id, 1)}
                                                >
                                                    +
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                <div className="group-actions" style={{ marginTop: 'var(--spacing-md)' }}>
                                    <button
                                        className="group-actions__btn group-actions__btn--save"
                                        onClick={handleSaveItems}
                                        disabled={isSaving || Object.keys(selectedItems).length === 0}
                                    >
                                        {isSaving ? '儲存中...' : '儲存我的品項'}
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* 參與者列表 */}
                        <div className="group-participants">
                            <h3 className="group-participants__title">參與者</h3>
                            {detail.participants.length > 0 ? (
                                detail.participants.map((p) => (
                                    <div key={p.user_id} className="group-participant">
                                        <div className="group-participant__header">
                                            <span className={`group-participant__name ${p.is_creator ? 'group-participant__name--creator' : ''}`}>
                                                {p.display_name}
                                            </span>
                                            <span className="group-participant__subtotal">
                                                ${p.subtotal}
                                            </span>
                                        </div>
                                        {p.items.length > 0 && (
                                            <div className="group-participant__items">
                                                {p.items.map((item, idx) => (
                                                    <div key={idx}>
                                                        {item.product_name} x{item.quantity} (${item.subtotal})
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ))
                            ) : (
                                <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-tertiary)' }}>
                                    尚無參與者
                                </p>
                            )}
                        </div>

                        {/* 總金額 */}
                        <div className="group-total">
                            <span className="group-total__label">總計</span>
                            <span className="group-total__amount">${detail.total_amount}</span>
                        </div>

                        {/* 建立者操作 */}
                        {isCreator && (
                            <div className="group-actions">
                                {detail.status === 'open' && (
                                    <button
                                        className="group-actions__btn group-actions__btn--secondary"
                                        onClick={handleLock}
                                        disabled={isLocking}
                                    >
                                        {isLocking ? '鎖定中...' : '鎖定訂單'}
                                    </button>
                                )}
                                {detail.status === 'locked' && (
                                    <button
                                        className="group-actions__btn group-actions__btn--primary"
                                        onClick={handleSubmit}
                                        disabled={isSubmitting}
                                    >
                                        {isSubmitting ? '送出中...' : '送出訂單'}
                                    </button>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </main>

            <BottomNav />
        </div>
    );
}

export default JoinGroupPage;
