/**
 * 群組點餐主頁面
 *
 * 建立新群組訂單、檢視已建立的群組訂單列表
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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

interface GroupOrder {
    id: string;
    title: string;
    status: string;
    share_code: string;
    max_participants: number | null;
    participant_count: number;
    total_amount: number;
    created_at: string;
}

function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
}

export function GroupOrderPage() {
    const navigate = useNavigate();
    const [orders, setOrders] = useState<GroupOrder[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [title, setTitle] = useState('');
    const [maxParticipants, setMaxParticipants] = useState('');
    const [isCreating, setIsCreating] = useState(false);
    const [message, setMessage] = useState<{ type: string; text: string } | null>(null);

    const loadOrders = async () => {
        setIsLoading(true);
        try {
            const res = await axios.get(`${API_BASE}/group-orders/my`, {
                headers: getAuthHeaders(),
            });
            setOrders(res.data);
        } catch (err) {
            console.error('載入群組訂單失敗:', err);
            setOrders([]);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadOrders();
    }, []);

    const handleCreate = async () => {
        if (!title.trim()) return;
        setIsCreating(true);
        setMessage(null);
        try {
            const payload: Record<string, unknown> = { title: title.trim() };
            if (maxParticipants) {
                payload.max_participants = parseInt(maxParticipants, 10);
            }
            await axios.post(`${API_BASE}/group-orders/`, payload, {
                headers: getAuthHeaders(),
            });
            setTitle('');
            setMaxParticipants('');
            setMessage({ type: 'success', text: '群組訂單已建立' });
            await loadOrders();
        } catch (err) {
            console.error('建立群組訂單失敗:', err);
            setMessage({ type: 'error', text: '建立失敗，請稍後再試' });
        } finally {
            setIsCreating(false);
        }
    };

    const handleShare = (e: React.MouseEvent, shareCode: string) => {
        e.stopPropagation();
        const url = `${window.location.origin}/group/join?code=${shareCode}`;
        navigator.clipboard.writeText(url).then(() => {
            setMessage({ type: 'success', text: '分享連結已複製' });
            setTimeout(() => setMessage(null), 2000);
        }).catch(() => {
            setMessage({ type: 'error', text: '複製失敗，請手動複製' });
        });
    };

    const handleCardClick = (shareCode: string) => {
        navigate(`/group/join?code=${shareCode}`);
    };

    return (
        <div className="page group-page">
            <Header title="群組點餐" showBack={false} />

            <main className="page-content">
                {/* 訊息提示 */}
                {message && (
                    <div className={`group-message group-message--${message.type}`}>
                        {message.text}
                    </div>
                )}

                {/* 建立群組 */}
                <div className="group-create">
                    <h2 className="group-create__title">建立群組訂單</h2>
                    <div className="group-create__form">
                        <div className="group-create__row">
                            <div className="group-create__field">
                                <label className="group-create__label">訂單標題</label>
                                <input
                                    className="group-create__input"
                                    type="text"
                                    placeholder="例：午餐團訂"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                />
                            </div>
                            <div className="group-create__field group-create__field--small">
                                <label className="group-create__label">人數上限</label>
                                <input
                                    className="group-create__input"
                                    type="number"
                                    min="2"
                                    placeholder="不限"
                                    value={maxParticipants}
                                    onChange={(e) => setMaxParticipants(e.target.value)}
                                />
                            </div>
                        </div>
                        <button
                            className="group-create__btn"
                            onClick={handleCreate}
                            disabled={!title.trim() || isCreating}
                        >
                            {isCreating ? '建立中...' : '建立群組'}
                        </button>
                    </div>
                </div>

                {/* 群組列表 */}
                <div className="group-list">
                    <h2 className="group-list__title">我的群組訂單</h2>

                    {isLoading ? (
                        Array.from({ length: 3 }).map((_, i) => (
                            <div key={i} className="group-card group-card--skeleton">
                                <div className="skeleton" style={{ width: '50%', height: 18 }} />
                                <div className="skeleton" style={{ width: '70%', height: 14, marginTop: 8 }} />
                                <div className="skeleton" style={{ width: '30%', height: 14, marginTop: 8 }} />
                            </div>
                        ))
                    ) : orders.length > 0 ? (
                        orders.map((order) => (
                            <div
                                key={order.id}
                                className="group-card"
                                onClick={() => handleCardClick(order.share_code)}
                            >
                                <div className="group-card__header">
                                    <span className="group-card__title">{order.title}</span>
                                    <span className={`group-card__status group-card__status--${order.status}`}>
                                        {STATUS_TEXT[order.status] || order.status}
                                    </span>
                                </div>
                                <div className="group-card__info">
                                    <span>
                                        代碼：<span className="group-card__code">{order.share_code}</span>
                                    </span>
                                    <span>{order.participant_count} 人參與</span>
                                </div>
                                <div className="group-card__footer">
                                    <span className="group-card__total">
                                        ${order.total_amount}
                                    </span>
                                    {order.status === 'open' && (
                                        <button
                                            className="group-card__share-btn"
                                            onClick={(e) => handleShare(e, order.share_code)}
                                        >
                                            分享連結
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="group-empty">
                            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                                <circle cx="9" cy="7" r="4" />
                                <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                            </svg>
                            <p>還沒有群組訂單</p>
                        </div>
                    )}
                </div>
            </main>

            <BottomNav />
        </div>
    );
}

export default GroupOrderPage;
