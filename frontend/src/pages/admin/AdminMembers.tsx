/**
 * 管理後台 - 會員管理頁面 (CRM)
 */
import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import '../admin/AdminLayout.css';
import './AdminMembers.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

interface Member {
    id: string;
    display_name: string;
    picture_url: string | null;
    phone: string | null;
    role: 'admin' | 'user';
    order_count: number;
    total_spent: number;
    last_order_at: string | null;
    created_at: string;
}

interface MemberDetail extends Member {
    recent_orders: RecentOrder[];
}

interface RecentOrder {
    id: string;
    order_number: string;
    total: number;
    status: string;
    created_at: string;
}

interface MemberStats {
    total_members: number;
    new_members_this_month: number;
    active_members: number;
    avg_order_value: number;
}

type SortBy = 'created_at' | 'order_count' | 'total_spent' | 'last_order_at';

function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
}

export function AdminMembers() {
    const [members, setMembers] = useState<Member[]>([]);
    const [total, setTotal] = useState(0);
    const [stats, setStats] = useState<MemberStats | null>(null);
    const [search, setSearch] = useState('');
    const [sortBy, setSortBy] = useState<SortBy>('created_at');
    const [skip, setSkip] = useState(0);
    const [loading, setLoading] = useState(false);
    const [statsLoading, setStatsLoading] = useState(false);
    const [selectedMember, setSelectedMember] = useState<MemberDetail | null>(null);
    const [detailLoading, setDetailLoading] = useState(false);
    const [roleUpdating, setRoleUpdating] = useState<string | null>(null);

    const limit = 20;

    const fetchMembers = useCallback(async () => {
        setLoading(true);
        try {
            const res = await axios.get(`${API_BASE}/admin/members`, {
                headers: getAuthHeaders(),
                params: { search, skip, limit, sort_by: sortBy },
            });
            setMembers(res.data.items);
            setTotal(res.data.total);
        } catch (err) {
            console.error('Failed to fetch members:', err);
        } finally {
            setLoading(false);
        }
    }, [search, skip, sortBy]);

    const fetchStats = useCallback(async () => {
        setStatsLoading(true);
        try {
            const res = await axios.get(`${API_BASE}/admin/members/stats`, {
                headers: getAuthHeaders(),
            });
            setStats(res.data);
        } catch (err) {
            console.error('Failed to fetch member stats:', err);
        } finally {
            setStatsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchMembers();
    }, [fetchMembers]);

    useEffect(() => {
        fetchStats();
    }, [fetchStats]);

    // Reset pagination when search or sort changes
    useEffect(() => {
        setSkip(0);
    }, [search, sortBy]);

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearch(e.target.value);
    };

    const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setSortBy(e.target.value as SortBy);
    };

    const handleMemberClick = async (memberId: string) => {
        setDetailLoading(true);
        try {
            const res = await axios.get(`${API_BASE}/admin/members/${memberId}`, {
                headers: getAuthHeaders(),
            });
            setSelectedMember(res.data);
        } catch (err) {
            console.error('Failed to fetch member detail:', err);
        } finally {
            setDetailLoading(false);
        }
    };

    const handleRoleToggle = async (memberId: string, currentRole: 'admin' | 'user') => {
        const newRole = currentRole === 'admin' ? 'user' : 'admin';
        const confirmMsg = newRole === 'admin'
            ? '確定要將此會員設為管理員？'
            : '確定要將此管理員降為一般會員？';

        if (!window.confirm(confirmMsg)) return;

        setRoleUpdating(memberId);
        try {
            await axios.patch(
                `${API_BASE}/admin/members/${memberId}/role`,
                { role: newRole },
                { headers: getAuthHeaders() },
            );
            // Update local state
            setMembers(prev =>
                prev.map(m => (m.id === memberId ? { ...m, role: newRole } : m)),
            );
            if (selectedMember?.id === memberId) {
                setSelectedMember(prev => (prev ? { ...prev, role: newRole } : null));
            }
        } catch (err) {
            console.error('Failed to update role:', err);
            alert('角色更新失敗，請重試');
        } finally {
            setRoleUpdating(null);
        }
    };

    const handleExport = () => {
        const token = localStorage.getItem('access_token');
        window.open(`${API_BASE}/admin/members/export?token=${token}`, '_blank');
    };

    const handlePrev = () => {
        setSkip(prev => Math.max(0, prev - limit));
    };

    const handleNext = () => {
        if (skip + limit < total) {
            setSkip(prev => prev + limit);
        }
    };

    const formatDate = (dateString: string | null) => {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('zh-TW', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
        });
    };

    const formatDateTime = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleString('zh-TW', {
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    const formatCurrency = (value: number) => {
        return `$${value.toLocaleString()}`;
    };

    const currentPage = Math.floor(skip / limit) + 1;
    const totalPages = Math.ceil(total / limit);

    const statusText: Record<string, string> = {
        pending: '待確認',
        confirmed: '已確認',
        preparing: '備餐中',
        ready: '待取餐',
        delivering: '配送中',
        completed: '已完成',
        cancelled: '已取消',
    };

    return (
        <div className="admin-members">
            <div className="admin-page-header">
                <h1 className="admin-page-title">會員管理</h1>
                <div className="admin-actions">
                    <button className="admin-action-btn" onClick={handleExport}>
                        匯出 CSV
                    </button>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="admin-stats">
                <div className="admin-stat-card">
                    <span className="admin-stat-card__label">總會員數</span>
                    <span className="admin-stat-card__value">
                        {statsLoading ? '...' : stats?.total_members ?? '-'}
                    </span>
                </div>
                <div className="admin-stat-card">
                    <span className="admin-stat-card__label">本月新增</span>
                    <span className="admin-stat-card__value">
                        {statsLoading ? '...' : stats?.new_members_this_month ?? '-'}
                    </span>
                </div>
                <div className="admin-stat-card">
                    <span className="admin-stat-card__label">活躍會員</span>
                    <span className="admin-stat-card__value">
                        {statsLoading ? '...' : stats?.active_members ?? '-'}
                    </span>
                </div>
                <div className="admin-stat-card">
                    <span className="admin-stat-card__label">平均客單價</span>
                    <span className="admin-stat-card__value">
                        {statsLoading ? '...' : stats ? formatCurrency(stats.avg_order_value) : '-'}
                    </span>
                </div>
            </div>

            {/* Search & Sort */}
            <div className="admin-members__toolbar">
                <input
                    type="text"
                    className="form-input admin-members__search-input"
                    placeholder="搜尋會員名稱、電話..."
                    value={search}
                    onChange={handleSearchChange}
                />
                <select
                    className="form-input admin-members__sort-select"
                    value={sortBy}
                    onChange={handleSortChange}
                >
                    <option value="created_at">加入時間</option>
                    <option value="order_count">訂單數</option>
                    <option value="total_spent">消費總額</option>
                    <option value="last_order_at">最近消費</option>
                </select>
            </div>

            {/* Members Table */}
            <div className="admin-card">
                <div className="admin-table-responsive">
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>會員</th>
                                <th>電話</th>
                                <th>訂單數</th>
                                <th>消費總額</th>
                                <th>最近消費</th>
                                <th>角色</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr>
                                    <td colSpan={7}>
                                        <div className="admin-empty">
                                            <p>載入中...</p>
                                        </div>
                                    </td>
                                </tr>
                            ) : members.length > 0 ? (
                                members.map(member => (
                                    <tr
                                        key={member.id}
                                        className={`admin-members__row ${selectedMember?.id === member.id ? 'selected' : ''}`}
                                        onClick={() => handleMemberClick(member.id)}
                                    >
                                        <td>
                                            <div className="admin-members__user">
                                                <div className="admin-members__avatar">
                                                    {member.picture_url ? (
                                                        <img
                                                            src={member.picture_url}
                                                            alt={member.display_name}
                                                        />
                                                    ) : (
                                                        <span className="admin-members__avatar-placeholder">
                                                            {member.display_name?.charAt(0) || '?'}
                                                        </span>
                                                    )}
                                                </div>
                                                <span className="admin-members__name">
                                                    {member.display_name}
                                                </span>
                                            </div>
                                        </td>
                                        <td>{member.phone || '-'}</td>
                                        <td>{member.order_count}</td>
                                        <td><strong>{formatCurrency(member.total_spent)}</strong></td>
                                        <td>{formatDate(member.last_order_at)}</td>
                                        <td>
                                            <span className={`admin-status admin-status--${member.role}`}>
                                                {member.role === 'admin' ? '管理員' : '會員'}
                                            </span>
                                        </td>
                                        <td>
                                            <div className="admin-actions">
                                                <button
                                                    className={`admin-action-btn ${member.role === 'admin' ? '' : 'admin-action-btn--primary'}`}
                                                    disabled={roleUpdating === member.id}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleRoleToggle(member.id, member.role);
                                                    }}
                                                >
                                                    {roleUpdating === member.id
                                                        ? '...'
                                                        : member.role === 'admin'
                                                            ? '降為會員'
                                                            : '設為管理員'}
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={7}>
                                        <div className="admin-empty">
                                            <p>沒有符合條件的會員</p>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="admin-members__pagination">
                        <button
                            className="admin-action-btn"
                            disabled={skip === 0}
                            onClick={handlePrev}
                        >
                            上一頁
                        </button>
                        <span className="admin-members__pagination-info">
                            第 {currentPage} / {totalPages} 頁（共 {total} 筆）
                        </span>
                        <button
                            className="admin-action-btn"
                            disabled={skip + limit >= total}
                            onClick={handleNext}
                        >
                            下一頁
                        </button>
                    </div>
                )}
            </div>

            {/* Member Detail Modal */}
            {(selectedMember || detailLoading) && (
                <div
                    className="admin-members__overlay"
                    onClick={() => setSelectedMember(null)}
                >
                    <div
                        className="admin-card admin-members__detail"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="admin-card__header">
                            <h3 className="admin-card__title">會員詳情</h3>
                            <button
                                className="admin-members__close-btn"
                                onClick={() => setSelectedMember(null)}
                            >
                                ✕
                            </button>
                        </div>

                        {detailLoading ? (
                            <div className="admin-members__detail-loading">載入中...</div>
                        ) : selectedMember ? (
                            <div className="admin-members__detail-body">
                                {/* Profile */}
                                <div className="admin-members__detail-profile">
                                    <div className="admin-members__detail-avatar">
                                        {selectedMember.picture_url ? (
                                            <img
                                                src={selectedMember.picture_url}
                                                alt={selectedMember.display_name}
                                            />
                                        ) : (
                                            <span className="admin-members__avatar-placeholder admin-members__avatar-placeholder--lg">
                                                {selectedMember.display_name?.charAt(0) || '?'}
                                            </span>
                                        )}
                                    </div>
                                    <div className="admin-members__detail-info">
                                        <h4 className="admin-members__detail-name">
                                            {selectedMember.display_name}
                                        </h4>
                                        <span className={`admin-status admin-status--${selectedMember.role}`}>
                                            {selectedMember.role === 'admin' ? '管理員' : '會員'}
                                        </span>
                                    </div>
                                </div>

                                {/* Info rows */}
                                <div className="admin-members__detail-section">
                                    <div className="admin-members__detail-row">
                                        <span>電話</span>
                                        <span>{selectedMember.phone || '-'}</span>
                                    </div>
                                    <div className="admin-members__detail-row">
                                        <span>訂單數</span>
                                        <span>{selectedMember.order_count}</span>
                                    </div>
                                    <div className="admin-members__detail-row">
                                        <span>消費總額</span>
                                        <strong>{formatCurrency(selectedMember.total_spent)}</strong>
                                    </div>
                                    <div className="admin-members__detail-row">
                                        <span>加入時間</span>
                                        <span>{formatDate(selectedMember.created_at)}</span>
                                    </div>
                                    <div className="admin-members__detail-row">
                                        <span>最近消費</span>
                                        <span>{formatDate(selectedMember.last_order_at)}</span>
                                    </div>
                                </div>

                                {/* Recent Orders */}
                                <div className="admin-members__detail-section">
                                    <h4 className="admin-members__detail-section-title">近期訂單</h4>
                                    {selectedMember.recent_orders.length > 0 ? (
                                        <div className="admin-members__recent-orders">
                                            {selectedMember.recent_orders.map(order => (
                                                <div
                                                    key={order.id}
                                                    className="admin-members__recent-order"
                                                >
                                                    <div className="admin-members__recent-order-header">
                                                        <span className="admin-members__recent-order-number">
                                                            {order.order_number}
                                                        </span>
                                                        <span className={`admin-status admin-status--${order.status}`}>
                                                            {statusText[order.status] || order.status}
                                                        </span>
                                                    </div>
                                                    <div className="admin-members__recent-order-footer">
                                                        <span>{formatDateTime(order.created_at)}</span>
                                                        <strong>{formatCurrency(order.total)}</strong>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="admin-members__no-orders">尚無訂單紀錄</p>
                                    )}
                                </div>

                                {/* Role toggle */}
                                <button
                                    className={`btn btn-full ${selectedMember.role === 'admin' ? 'btn-secondary' : 'btn-primary'}`}
                                    disabled={roleUpdating === selectedMember.id}
                                    onClick={() => handleRoleToggle(selectedMember.id, selectedMember.role)}
                                >
                                    {roleUpdating === selectedMember.id
                                        ? '更新中...'
                                        : selectedMember.role === 'admin'
                                            ? '降為一般會員'
                                            : '設為管理員'}
                                </button>
                            </div>
                        ) : null}
                    </div>
                </div>
            )}
        </div>
    );
}

export default AdminMembers;
