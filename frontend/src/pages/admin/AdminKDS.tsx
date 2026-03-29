/**
 * 管理後台 - KDS 廚房顯示系統
 * Kitchen Display System for real-time order management
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import './AdminKDS.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

interface KDSOrderItem {
    product_name: string;
    quantity: number;
    notes?: string | null;
}

interface KDSOrder {
    id: string;
    order_number: string;
    order_type: string;
    status: string;
    pickup_number: string | null;
    items: KDSOrderItem[];
    notes: string | null;
    created_at: string;
    elapsed_minutes: number;
}

const REFRESH_INTERVAL = 15_000;

function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
}

function getElapsedColor(minutes: number): 'green' | 'yellow' | 'red' {
    if (minutes < 10) return 'green';
    if (minutes <= 20) return 'yellow';
    return 'red';
}

function formatElapsed(minutes: number): string {
    if (minutes < 1) return '< 1 分鐘';
    return `${minutes} 分鐘`;
}

function playBeep() {
    try {
        const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
        const oscillator = ctx.createOscillator();
        const gain = ctx.createGain();
        oscillator.connect(gain);
        gain.connect(ctx.destination);
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(880, ctx.currentTime);
        gain.gain.setValueAtTime(0.3, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
        oscillator.start(ctx.currentTime);
        oscillator.stop(ctx.currentTime + 0.5);
    } catch {
        // Audio not supported — silent fallback
    }
}

function getOrderTypeLabel(type: string): string {
    switch (type) {
        case 'pickup': return '自取';
        case 'delivery': return '外送';
        case 'dine_in': return '內用';
        default: return type;
    }
}

function getStatusLabel(status: string): string {
    switch (status) {
        case 'confirmed': return '已確認';
        case 'preparing': return '備餐中';
        default: return status;
    }
}

export function AdminKDS() {
    const [orders, setOrders] = useState<KDSOrder[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
    const [soundEnabled, setSoundEnabled] = useState(false);
    const previousOrderIdsRef = useRef<Set<string>>(new Set());

    const fetchOrders = useCallback(async () => {
        try {
            const res = await axios.get<KDSOrder[]>(`${API_BASE}/admin/kds/orders`, {
                headers: getAuthHeaders(),
            });
            const fetched = res.data;

            // Detect new orders for sound notification
            if (soundEnabled && previousOrderIdsRef.current.size > 0) {
                const hasNew = fetched.some(
                    (o) => !previousOrderIdsRef.current.has(o.id)
                );
                if (hasNew) {
                    playBeep();
                }
            }

            previousOrderIdsRef.current = new Set(fetched.map((o) => o.id));
            setOrders(fetched);
            setError(null);
        } catch (err: any) {
            const msg =
                err?.response?.data?.detail ||
                err?.message ||
                '無法載入訂單資料';
            setError(msg);
        } finally {
            setLoading(false);
        }
    }, [soundEnabled]);

    // Initial fetch + auto-refresh
    useEffect(() => {
        fetchOrders();
        const interval = setInterval(fetchOrders, REFRESH_INTERVAL);
        return () => clearInterval(interval);
    }, [fetchOrders]);

    const handleStart = useCallback(
        async (orderId: string) => {
            setActionLoading((prev) => ({ ...prev, [orderId]: true }));
            try {
                await axios.patch(
                    `${API_BASE}/admin/kds/orders/${orderId}/start`,
                    null,
                    { headers: getAuthHeaders() }
                );
                await fetchOrders();
            } catch (err: any) {
                const msg =
                    err?.response?.data?.detail || '操作失敗，請重試';
                alert(msg);
            } finally {
                setActionLoading((prev) => ({ ...prev, [orderId]: false }));
            }
        },
        [fetchOrders]
    );

    const handleReady = useCallback(
        async (orderId: string) => {
            setActionLoading((prev) => ({ ...prev, [orderId]: true }));
            try {
                await axios.patch(
                    `${API_BASE}/admin/kds/orders/${orderId}/ready`,
                    null,
                    { headers: getAuthHeaders() }
                );
                await fetchOrders();
            } catch (err: any) {
                const msg =
                    err?.response?.data?.detail || '操作失敗，請重試';
                alert(msg);
            } finally {
                setActionLoading((prev) => ({ ...prev, [orderId]: false }));
            }
        },
        [fetchOrders]
    );

    return (
        <div className="admin-kds">
            <header className="admin-kds__header">
                <h1 className="admin-kds__title">廚房顯示系統 (KDS)</h1>
                <div className="admin-kds__header-actions">
                    <span className="admin-kds__order-count">
                        待處理：{orders.length} 筆
                    </span>
                    <button
                        className={`admin-kds__sound-toggle ${soundEnabled ? 'admin-kds__sound-toggle--active' : ''}`}
                        onClick={() => setSoundEnabled((v) => !v)}
                        type="button"
                    >
                        {soundEnabled ? '🔔 音效開' : '🔕 音效關'}
                    </button>
                    <span className="admin-kds__refresh-indicator">
                        每 15 秒自動更新
                    </span>
                </div>
            </header>

            <div className="admin-kds__grid">
                {loading && orders.length === 0 && (
                    <div className="admin-kds__loading">載入中...</div>
                )}

                {error && (
                    <div className="admin-kds__error">
                        <div>{error}</div>
                        <button
                            className="admin-kds__error-retry"
                            onClick={fetchOrders}
                            type="button"
                        >
                            重試
                        </button>
                    </div>
                )}

                {!loading && !error && orders.length === 0 && (
                    <div className="admin-kds__empty">目前沒有待處理訂單</div>
                )}

                {orders.map((order) => {
                    const elapsedColor = getElapsedColor(order.elapsed_minutes);
                    const isConfirmed = order.status === 'confirmed';
                    const isPreparing = order.status === 'preparing';
                    const busy = !!actionLoading[order.id];

                    return (
                        <div
                            key={order.id}
                            className={`admin-kds__card admin-kds__card--${order.status}`}
                        >
                            {/* Header: order number + pickup number */}
                            <div className="admin-kds__card-header">
                                <div className="admin-kds__order-info">
                                    <span className="admin-kds__order-number">
                                        {order.order_number}
                                    </span>
                                    <span className="admin-kds__order-type">
                                        {getOrderTypeLabel(order.order_type)}
                                    </span>
                                    <span
                                        className={`admin-kds__status admin-kds__status--${order.status}`}
                                    >
                                        {getStatusLabel(order.status)}
                                    </span>
                                </div>
                                {order.pickup_number && (
                                    <div className="admin-kds__pickup-number">
                                        {order.pickup_number}
                                    </div>
                                )}
                            </div>

                            {/* Elapsed time */}
                            <div
                                className={`admin-kds__elapsed admin-kds__elapsed--${elapsedColor}`}
                            >
                                {formatElapsed(order.elapsed_minutes)}
                            </div>

                            {/* Items list */}
                            <div className="admin-kds__items">
                                {order.items.map((item, idx) => (
                                    <div key={idx}>
                                        <div className="admin-kds__item">
                                            <span className="admin-kds__item-quantity">
                                                x{item.quantity}
                                            </span>
                                            <span className="admin-kds__item-name">
                                                {item.product_name}
                                            </span>
                                        </div>
                                        {item.notes && (
                                            <div className="admin-kds__item-notes">
                                                {item.notes}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>

                            {/* Order-level notes */}
                            {order.notes && (
                                <div className="admin-kds__notes">
                                    {order.notes}
                                </div>
                            )}

                            {/* Action buttons */}
                            <div className="admin-kds__actions">
                                {isConfirmed && (
                                    <button
                                        className="admin-kds__action-btn admin-kds__action-btn--start"
                                        onClick={() => handleStart(order.id)}
                                        disabled={busy}
                                        type="button"
                                    >
                                        {busy ? '處理中...' : '開始備餐'}
                                    </button>
                                )}
                                {isPreparing && (
                                    <button
                                        className="admin-kds__action-btn admin-kds__action-btn--ready"
                                        onClick={() => handleReady(order.id)}
                                        disabled={busy}
                                        type="button"
                                    >
                                        {busy ? '處理中...' : '備餐完成'}
                                    </button>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

export default AdminKDS;
