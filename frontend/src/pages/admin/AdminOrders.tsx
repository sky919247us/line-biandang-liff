/**
 * 管理後台 - 訂單管理頁面
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Order, OrderStatus } from '../../types';
import '../admin/AdminLayout.css';
import './AdminOrders.css';

// 模擬訂單資料
const mockOrders: Order[] = [
    {
        id: '1',
        orderNumber: 'ORD-20260205-001',
        orderType: 'pickup',
        status: 'pending',
        subtotal: 240,
        deliveryFee: 0,
        discount: 0,
        total: 240,
        deliveryAddress: null,
        contactName: '王小明',
        contactPhone: '0912-345-678',
        pickupTime: '12:00',
        notes: '少飯',
        items: [
            { id: '1', productId: 'chicken-1', productName: '戰斧雞腿', quantity: 2, unitPrice: 120, subtotal: 240, customizations: [{ id: 'c1', name: '少飯', price: 0 }], notes: null }
        ],
        tableNumber: null,
        pickupNumber: null,
        createdAt: '2026-02-05T10:30:00Z',
        updatedAt: '2026-02-05T10:30:00Z',
    },
    {
        id: '2',
        orderNumber: 'ORD-20260205-002',
        orderType: 'delivery',
        status: 'confirmed',
        subtotal: 380,
        deliveryFee: 30,
        discount: 0,
        total: 410,
        deliveryAddress: '台中市中區某某路100號',
        contactName: '李小華',
        contactPhone: '0923-456-789',
        pickupTime: null,
        notes: null,
        items: [
            { id: '2', productId: 'pork-5', productName: '五告厚豬排', quantity: 2, unitPrice: 130, subtotal: 260, customizations: null, notes: null },
            { id: '3', productId: 'chicken-2', productName: '醬燒揚雞', quantity: 1, unitPrice: 120, subtotal: 120, customizations: null, notes: null }
        ],
        tableNumber: null,
        pickupNumber: null,
        createdAt: '2026-02-05T10:45:00Z',
        updatedAt: '2026-02-05T10:50:00Z',
    },
    {
        id: '3',
        orderNumber: 'ORD-20260205-003',
        orderType: 'pickup',
        status: 'preparing',
        subtotal: 150,
        deliveryFee: 0,
        discount: 0,
        total: 150,
        deliveryAddress: null,
        contactName: '張小花',
        contactPhone: '0934-567-890',
        pickupTime: '12:30',
        notes: '加辣',
        items: [
            { id: '4', productId: 'beef-1', productName: '牛逼菲力', quantity: 1, unitPrice: 150, subtotal: 150, customizations: [{ id: 'c2', name: '加辣', price: 0 }], notes: null }
        ],
        tableNumber: null,
        pickupNumber: null,
        createdAt: '2026-02-05T11:00:00Z',
        updatedAt: '2026-02-05T11:10:00Z',
    },
    {
        id: '4',
        orderNumber: 'ORD-20260205-004',
        orderType: 'pickup',
        status: 'ready',
        subtotal: 120,
        deliveryFee: 0,
        discount: 0,
        total: 120,
        deliveryAddress: null,
        contactName: '陳小姐',
        contactPhone: '0945-678-901',
        pickupTime: '11:30',
        notes: null,
        items: [
            { id: '5', productId: 'pork-1', productName: '相撲豬太郎', quantity: 1, unitPrice: 120, subtotal: 120, customizations: null, notes: null }
        ],
        tableNumber: null,
        pickupNumber: null,
        createdAt: '2026-02-05T09:30:00Z',
        updatedAt: '2026-02-05T11:20:00Z',
    },
    {
        id: '5',
        orderNumber: 'ORD-20260204-010',
        orderType: 'delivery',
        status: 'completed',
        subtotal: 360,
        deliveryFee: 30,
        discount: 0,
        total: 390,
        deliveryAddress: '台中市北區某某街50號',
        contactName: '林先生',
        contactPhone: '0956-789-012',
        pickupTime: null,
        notes: null,
        items: [
            { id: '6', productId: 'pork-6', productName: '藍帶豬排', quantity: 2, unitPrice: 180, subtotal: 360, customizations: null, notes: null }
        ],
        tableNumber: null,
        pickupNumber: null,
        createdAt: '2026-02-04T12:00:00Z',
        updatedAt: '2026-02-04T13:00:00Z',
    },
];

const statusOptions: { value: OrderStatus | 'all'; label: string }[] = [
    { value: 'all', label: '全部' },
    { value: 'pending', label: '待確認' },
    { value: 'confirmed', label: '已確認' },
    { value: 'preparing', label: '備餐中' },
    { value: 'ready', label: '待取餐' },
    { value: 'delivering', label: '配送中' },
    { value: 'completed', label: '已完成' },
    { value: 'cancelled', label: '已取消' },
];

const statusText: Record<string, string> = {
    pending: '待確認',
    confirmed: '已確認',
    preparing: '備餐中',
    ready: '待取餐',
    delivering: '配送中',
    completed: '已完成',
    cancelled: '已取消',
};

const nextStatusMap: Record<string, OrderStatus | null> = {
    pending: 'confirmed',
    confirmed: 'preparing',
    preparing: 'ready',
    ready: 'completed',
    delivering: 'completed',
    completed: null,
    cancelled: null,
};

const orderTypeText: Record<string, string> = {
    pickup: '自取',
    delivery: '外送',
    dine_in: '內用',
};

export function AdminOrders() {
    const navigate = useNavigate();
    const [orders, setOrders] = useState<Order[]>([]);
    const [filteredOrders, setFilteredOrders] = useState<Order[]>([]);
    const [statusFilter, setStatusFilter] = useState<OrderStatus | 'all'>('all');
    const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [orderTypeFilter, setOrderTypeFilter] = useState<string>('all');

    useEffect(() => {
        // 模擬載入資料
        setOrders(mockOrders);
    }, []);

    useEffect(() => {
        let filtered = orders;
        if (statusFilter !== 'all') {
            filtered = filtered.filter(o => o.status === statusFilter);
        }
        if (orderTypeFilter !== 'all') {
            filtered = filtered.filter(o => o.orderType === orderTypeFilter);
        }
        if (searchQuery.trim()) {
            const q = searchQuery.toLowerCase();
            filtered = filtered.filter(o =>
                o.orderNumber.toLowerCase().includes(q) ||
                (o.contactName && o.contactName.toLowerCase().includes(q)) ||
                (o.contactPhone && o.contactPhone.includes(q))
            );
        }
        setFilteredOrders(filtered);
    }, [orders, statusFilter, orderTypeFilter, searchQuery]);

    const formatDateTime = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleString('zh-TW', {
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    const handleStatusChange = (orderId: string, newStatus: OrderStatus) => {
        setOrders(prev => prev.map(order => {
            if (order.id === orderId) {
                return { ...order, status: newStatus, updatedAt: new Date().toISOString() };
            }
            return order;
        }));

        if (selectedOrder?.id === orderId) {
            setSelectedOrder(prev => prev ? { ...prev, status: newStatus } : null);
        }
    };

    return (
        <div className="admin-orders">
            <div className="admin-page-header">
                <h1 className="admin-page-title">訂單管理</h1>
                <div className="admin-actions">
                    <button
                        className="admin-action-btn"
                        onClick={() => {
                            const token = localStorage.getItem('access_token');
                            window.open(`/api/v1/admin/orders/export?token=${token}`, '_blank');
                        }}
                    >
                        匯出 CSV
                    </button>
                    <button
                        className="admin-action-btn admin-action-btn--primary"
                        onClick={() => navigate('/admin/orders/manual')}
                    >
                        + 手動新增
                    </button>
                </div>
            </div>

            {/* 搜尋與篩選 */}
            <div className="admin-orders__search">
                <input
                    type="text"
                    className="form-input"
                    placeholder="搜尋訂單編號、顧客姓名、電話..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
                <select
                    className="form-input"
                    value={orderTypeFilter}
                    onChange={(e) => setOrderTypeFilter(e.target.value)}
                    style={{ maxWidth: 120 }}
                >
                    <option value="all">全部方式</option>
                    <option value="pickup">自取</option>
                    <option value="dine_in">內用</option>
                    <option value="delivery">外送</option>
                </select>
            </div>

            {/* 狀態篩選 */}
            <div className="admin-orders__filters">
                {statusOptions.map(option => (
                    <button
                        key={option.value}
                        className={`admin-orders__filter-btn ${statusFilter === option.value ? 'active' : ''}`}
                        onClick={() => setStatusFilter(option.value)}
                    >
                        {option.label}
                        {option.value !== 'all' && (
                            <span className="admin-orders__filter-count">
                                {orders.filter(o => o.status === option.value).length}
                            </span>
                        )}
                    </button>
                ))}
            </div>

            <div className="admin-orders__content">
                {/* 訂單列表 */}
                <div className="admin-card admin-orders__list">
                    <div className="admin-table-responsive">
                        <table className="admin-table">
                            <thead>
                                <tr>
                                    <th>訂單編號</th>
                                    <th>時間</th>
                                    <th>顧客</th>
                                    <th>方式</th>
                                    <th>金額</th>
                                    <th>狀態</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredOrders.length > 0 ? (
                                    filteredOrders.map((order) => (
                                        <tr
                                            key={order.id}
                                            className={selectedOrder?.id === order.id ? 'selected' : ''}
                                            onClick={() => setSelectedOrder(order)}
                                        >
                                            <td><strong>{order.orderNumber}</strong></td>
                                            <td>{formatDateTime(order.createdAt)}</td>
                                            <td>{order.contactName}</td>
                                            <td>{orderTypeText[order.orderType] || order.orderType}</td>
                                            <td><strong>${order.total}</strong></td>
                                            <td>
                                                <span className={`admin-status admin-status--${order.status}`}>
                                                    {statusText[order.status]}
                                                </span>
                                            </td>
                                            <td>
                                                <div className="admin-actions">
                                                    {nextStatusMap[order.status] && (
                                                        <button
                                                            className="admin-action-btn admin-action-btn--primary"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                handleStatusChange(order.id, nextStatusMap[order.status]!);
                                                            }}
                                                        >
                                                            {order.status === 'pending' ? '確認' :
                                                                order.status === 'confirmed' ? '開始備餐' :
                                                                    order.status === 'preparing' ? '備餐完成' :
                                                                        order.status === 'ready' || order.status === 'delivering' ? '完成' : ''}
                                                        </button>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan={7}>
                                            <div className="admin-empty">
                                                <p>沒有符合條件的訂單</p>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* 訂單詳情 */}
                {selectedOrder && (
                    <div className="admin-card admin-orders__detail">
                        <div className="admin-card__header">
                            <h3 className="admin-card__title">訂單詳情</h3>
                            <button
                                className="admin-orders__close-btn"
                                onClick={() => setSelectedOrder(null)}
                            >
                                ✕
                            </button>
                        </div>
                        <div className="admin-card__body">
                            <div className="admin-orders__detail-section">
                                <h4>訂單資訊</h4>
                                <div className="admin-orders__detail-row">
                                    <span>訂單編號</span>
                                    <strong>{selectedOrder.orderNumber}</strong>
                                </div>
                                <div className="admin-orders__detail-row">
                                    <span>下單時間</span>
                                    <span>{new Date(selectedOrder.createdAt).toLocaleString('zh-TW')}</span>
                                </div>
                                <div className="admin-orders__detail-row">
                                    <span>取餐方式</span>
                                    <span>{orderTypeText[selectedOrder.orderType] || selectedOrder.orderType}</span>
                                </div>
                                {selectedOrder.pickupTime && (
                                    <div className="admin-orders__detail-row">
                                        <span>預計取餐</span>
                                        <span>{selectedOrder.pickupTime}</span>
                                    </div>
                                )}
                                {selectedOrder.deliveryAddress && (
                                    <div className="admin-orders__detail-row">
                                        <span>外送地址</span>
                                        <span>{selectedOrder.deliveryAddress}</span>
                                    </div>
                                )}
                            </div>

                            <div className="admin-orders__detail-section">
                                <h4>顧客資訊</h4>
                                <div className="admin-orders__detail-row">
                                    <span>姓名</span>
                                    <span>{selectedOrder.contactName}</span>
                                </div>
                                <div className="admin-orders__detail-row">
                                    <span>電話</span>
                                    <a href={`tel:${selectedOrder.contactPhone}`}>{selectedOrder.contactPhone}</a>
                                </div>
                            </div>

                            <div className="admin-orders__detail-section">
                                <h4>訂單明細</h4>
                                {selectedOrder.items.map(item => (
                                    <div key={item.id} className="admin-orders__item">
                                        <div className="admin-orders__item-info">
                                            <span className="admin-orders__item-name">{item.productName}</span>
                                            <span className="admin-orders__item-qty">x{item.quantity}</span>
                                        </div>
                                        <span className="admin-orders__item-price">${item.subtotal}</span>
                                        {item.customizations && item.customizations.length > 0 && (
                                            <div className="admin-orders__item-options">
                                                {item.customizations.map(c => c.name).join('、')}
                                            </div>
                                        )}
                                    </div>
                                ))}
                                {selectedOrder.notes && (
                                    <div className="admin-orders__notes">
                                        <span>備註：</span>
                                        {selectedOrder.notes}
                                    </div>
                                )}
                            </div>

                            <div className="admin-orders__detail-section">
                                <h4>金額</h4>
                                <div className="admin-orders__detail-row">
                                    <span>小計</span>
                                    <span>${selectedOrder.subtotal}</span>
                                </div>
                                {selectedOrder.deliveryFee > 0 && (
                                    <div className="admin-orders__detail-row">
                                        <span>運費</span>
                                        <span>${selectedOrder.deliveryFee}</span>
                                    </div>
                                )}
                                {selectedOrder.discount > 0 && (
                                    <div className="admin-orders__detail-row">
                                        <span>折扣</span>
                                        <span>-${selectedOrder.discount}</span>
                                    </div>
                                )}
                                <div className="admin-orders__detail-row admin-orders__detail-total">
                                    <span>總計</span>
                                    <strong>${selectedOrder.total}</strong>
                                </div>
                            </div>

                            {nextStatusMap[selectedOrder.status] && (
                                <button
                                    className="btn btn-primary btn-lg btn-full"
                                    onClick={() => handleStatusChange(selectedOrder.id, nextStatusMap[selectedOrder.status]!)}
                                >
                                    {selectedOrder.status === 'pending' ? '確認訂單' :
                                        selectedOrder.status === 'confirmed' ? '開始備餐' :
                                            selectedOrder.status === 'preparing' ? '備餐完成' :
                                                selectedOrder.status === 'ready' || selectedOrder.status === 'delivering' ? '完成訂單' : ''}
                                </button>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default AdminOrders;
