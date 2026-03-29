/**
 * 管理後台 - 總覽頁面
 *
 * 使用 SSE 即時更新儀表板統計數據，
 * 並從 API 載入最新訂單列表。
 */
import { useState, useEffect, useRef } from 'react';
import type { Order } from '../../types';
import '../admin/AdminLayout.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const statusText: Record<string, string> = {
    pending: '待確認',
    confirmed: '已確認',
    preparing: '備餐中',
    ready: '待取餐',
    delivering: '配送中',
    completed: '已完成',
    cancelled: '已取消',
};

export function AdminDashboard() {
    const [todayOrders, setTodayOrders] = useState<Order[]>([]);
    const [stats, setStats] = useState({
        todayOrderCount: 0,
        todayRevenue: 0,
        pendingOrders: 0,
        preparingOrders: 0,
    });
    const eventSourceRef = useRef<EventSource | null>(null);

    // Fetch today's latest orders from API
    useEffect(() => {
        const fetchOrders = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/admin/orders?status=all&limit=10`);
                if (res.ok) {
                    const data = await res.json();
                    // API may return { items: [...] } or an array directly
                    const orders: Order[] = Array.isArray(data) ? data : (data.items ?? data.data ?? []);
                    setTodayOrders(orders);
                }
            } catch (err) {
                console.error('Failed to fetch orders:', err);
            }
        };

        fetchOrders();
    }, []);

    // Connect to SSE for live dashboard stats
    useEffect(() => {
        const sseUrl = `${API_BASE_URL}/admin/sse/dashboard`;
        const es = new EventSource(sseUrl);
        eventSourceRef.current = es;

        es.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (!data.error) {
                    setStats({
                        todayOrderCount: data.todayOrderCount ?? 0,
                        todayRevenue: data.todayRevenue ?? 0,
                        pendingOrders: data.pendingOrders ?? 0,
                        preparingOrders: data.preparingOrders ?? 0,
                    });
                }
            } catch (err) {
                console.error('SSE parse error:', err);
            }
        };

        es.onerror = () => {
            console.warn('SSE connection error, will auto-reconnect');
        };

        return () => {
            es.close();
            eventSourceRef.current = null;
        };
    }, []);

    const formatTime = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });
    };

    return (
        <div className="admin-dashboard">
            <div className="admin-page-header">
                <h1 className="admin-page-title">總覽</h1>
                <span style={{ color: 'var(--text-secondary)' }}>
                    {new Date().toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })}
                </span>
            </div>

            {/* 統計卡片 */}
            <div className="admin-stats">
                <div className="admin-stat-card">
                    <div className="admin-stat-card__label">今日訂單</div>
                    <div className="admin-stat-card__value">{stats.todayOrderCount}</div>
                </div>
                <div className="admin-stat-card">
                    <div className="admin-stat-card__label">今日營收</div>
                    <div className="admin-stat-card__value">${stats.todayRevenue}</div>
                </div>
                <div className="admin-stat-card">
                    <div className="admin-stat-card__label">待確認</div>
                    <div className="admin-stat-card__value" style={{ color: 'var(--color-warning)' }}>
                        {stats.pendingOrders}
                    </div>
                </div>
                <div className="admin-stat-card">
                    <div className="admin-stat-card__label">備餐中</div>
                    <div className="admin-stat-card__value" style={{ color: 'var(--color-info)' }}>
                        {stats.preparingOrders}
                    </div>
                </div>
            </div>

            {/* 最新訂單 */}
            <div className="admin-card">
                <div className="admin-card__header">
                    <h3 className="admin-card__title">最新訂單</h3>
                </div>
                <div className="admin-table-responsive">
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>訂單編號</th>
                                <th>時間</th>
                                <th>顧客</th>
                                <th>取餐方式</th>
                                <th>金額</th>
                                <th>狀態</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            {todayOrders.length > 0 ? (
                                todayOrders.map((order) => (
                                    <tr key={order.id}>
                                        <td><strong>{order.orderNumber}</strong></td>
                                        <td>{formatTime(order.createdAt)}</td>
                                        <td>{order.contactName}</td>
                                        <td>{order.orderType === 'pickup' ? '自取' : '外送'}</td>
                                        <td><strong>${order.total}</strong></td>
                                        <td>
                                            <span className={`admin-status admin-status--${order.status}`}>
                                                {statusText[order.status]}
                                            </span>
                                        </td>
                                        <td>
                                            <div className="admin-actions">
                                                <button className="admin-action-btn admin-action-btn--primary">
                                                    查看
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={7}>
                                        <div className="admin-empty">
                                            <p>今日尚無訂單</p>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

export default AdminDashboard;
