/**
 * 訂單頁面
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '../../components/layout/Header';
import { BottomNav } from '../../components/layout/BottomNav';
import { orderApi, productApi } from '../../services/api';
import { useCartStore } from '../../stores/cartStore';
import type { Order } from '../../types';
import { OrderStatusText, OrderStatusColor } from '../../types';
import './OrdersPage.css';

export function OrdersPage() {
    const navigate = useNavigate();
    const addItem = useCartStore((state) => state.addItem);
    const [orders, setOrders] = useState<Order[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedStatus, setSelectedStatus] = useState<string | null>(null);
    const [reorderingId, setReorderingId] = useState<string | null>(null);

    useEffect(() => {
        const loadOrders = async () => {
            setIsLoading(true);
            try {
                const result = await orderApi.getOrders({
                    status: selectedStatus || undefined,
                    limit: 50
                });
                setOrders(result.items);
            } catch (error) {
                console.error('載入訂單失敗:', error);
                setOrders([]);
            } finally {
                setIsLoading(false);
            }
        };

        loadOrders();
    }, [selectedStatus]);

    const statusFilters = [
        { value: null, label: '全部' },
        { value: 'pending', label: '待確認' },
        { value: 'preparing', label: '備餐中' },
        { value: 'completed', label: '已完成' },
        { value: 'cancelled', label: '已取消' },
    ];

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('zh-TW', {
            month: 'numeric',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    // 重複下單
    const handleReorder = async (order: Order) => {
        setReorderingId(order.id);
        try {
            for (const item of order.items) {
                const product = await productApi.getProduct(item.productId);
                if (product && product.canOrder) {
                    const customizations = (item.customizations || []).map(c => ({
                        id: c.id,
                        name: c.name,
                        price: c.price,
                    }));
                    addItem(product, item.quantity, customizations, item.notes || '');
                }
            }
            navigate('/cart');
        } catch (err) {
            console.error('重複下單失敗:', err);
        } finally {
            setReorderingId(null);
        }
    };

    return (
        <div className="page orders-page">
            <Header title="訂單記錄" showBack={false} />

            <main className="page-content">
                {/* 狀態篩選 */}
                <div className="orders-filter hide-scrollbar">
                    {statusFilters.map((filter) => (
                        <button
                            key={filter.value || 'all'}
                            className={`orders-filter__btn ${selectedStatus === filter.value ? 'active' : ''}`}
                            onClick={() => setSelectedStatus(filter.value)}
                        >
                            {filter.label}
                        </button>
                    ))}
                </div>

                {/* 訂單列表 */}
                <div className="orders-list">
                    {isLoading ? (
                        // 載入中骨架
                        Array.from({ length: 3 }).map((_, index) => (
                            <div key={index} className="order-card order-card--skeleton">
                                <div className="skeleton" style={{ width: '40%', height: 16 }} />
                                <div className="skeleton" style={{ width: '60%', height: 20, marginTop: 8 }} />
                                <div className="skeleton" style={{ width: '30%', height: 16, marginTop: 8 }} />
                            </div>
                        ))
                    ) : orders.length > 0 ? (
                        orders.map((order) => (
                            <div key={order.id} className="order-card">
                                <div className="order-card__header">
                                    <span className="order-card__number">{order.orderNumber}</span>
                                    <span
                                        className="order-card__status"
                                        style={{
                                            background: `${OrderStatusColor[order.status]}20`,
                                            color: OrderStatusColor[order.status]
                                        }}
                                    >
                                        {OrderStatusText[order.status]}
                                    </span>
                                </div>

                                <div className="order-card__items">
                                    {order.items.slice(0, 2).map((item) => (
                                        <span key={item.id} className="order-card__item">
                                            {item.productName} x{item.quantity}
                                        </span>
                                    ))}
                                    {order.items.length > 2 && (
                                        <span className="order-card__more">
                                            ...還有 {order.items.length - 2} 項
                                        </span>
                                    )}
                                </div>

                                <div className="order-card__footer">
                                    <span className="order-card__date">{formatDate(order.createdAt)}</span>
                                    <span className="order-card__total">${order.total}</span>
                                </div>

                                <div className="order-card__bottom">
                                    <div className="order-card__type">
                                        {order.orderType === 'delivery' && '外送'}
                                        {order.orderType === 'pickup' && '自取'}
                                        {order.orderType === 'dine_in' && '內用'}
                                        {order.pickupNumber && (
                                            <span className="order-card__pickup-number">
                                                取餐號 #{order.pickupNumber}
                                            </span>
                                        )}
                                    </div>
                                    {(order.status === 'completed' || order.status === 'cancelled') && (
                                        <button
                                            className="order-card__reorder"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleReorder(order);
                                            }}
                                            disabled={reorderingId === order.id}
                                        >
                                            {reorderingId === order.id ? '加入中...' : '再次訂購'}
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="orders-empty">
                            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                <polyline points="14 2 14 8 20 8" />
                            </svg>
                            <p>還沒有訂單記錄</p>
                        </div>
                    )}
                </div>
            </main>

            <BottomNav />
        </div>
    );
}

export default OrdersPage;
