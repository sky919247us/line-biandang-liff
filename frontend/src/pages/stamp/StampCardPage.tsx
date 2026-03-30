/**
 * 虛擬集點卡頁面
 *
 * 顯示集點卡模板、使用者集點進度、兌換獎勵
 */
import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Header } from '../../components/layout/Header';
import { BottomNav } from '../../components/layout/BottomNav';
import './StampCard.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
}

interface StampCardTemplate {
    id: string;
    name: string;
    description: string | null;
    stamps_required: number;
    reward_type: string;
    reward_value: string;
    min_order_amount: number;
    is_active: boolean;
}

interface StampCard {
    id: string;
    user_id: string;
    template_id: string;
    stamps_collected: number;
    is_completed: boolean;
    is_reward_claimed: boolean;
    completed_at: string | null;
    created_at: string;
    template: StampCardTemplate;
}

const rewardTypeLabel: Record<string, string> = {
    coupon: '優惠券',
    free_item: '免費商品',
    points: '點數',
};

export function StampCardPage() {
    const [templates, setTemplates] = useState<StampCardTemplate[]>([]);
    const [cards, setCards] = useState<StampCard[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const loadData = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const [templatesRes, cardsRes] = await Promise.all([
                axios.get<StampCardTemplate[]>(`${API_BASE}/stamp-cards/templates`),
                axios.get<StampCard[]>(`${API_BASE}/stamp-cards/my`, {
                    headers: getAuthHeaders(),
                }),
            ]);
            setTemplates(templatesRes.data);
            setCards(cardsRes.data);
        } catch (err) {
            console.error('載入集點卡資料失敗:', err);
            setError('載入集點卡資料失敗，請稍後再試');
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleStart = async (templateId: string) => {
        setActionLoading(templateId);
        try {
            await axios.post(
                `${API_BASE}/stamp-cards/start`,
                { template_id: templateId },
                { headers: getAuthHeaders() }
            );
            await loadData();
        } catch (err: unknown) {
            const message =
                axios.isAxiosError(err) && err.response?.data?.detail
                    ? err.response.data.detail
                    : '開始集點失敗';
            alert(message);
        } finally {
            setActionLoading(null);
        }
    };

    const handleClaim = async (cardId: string) => {
        setActionLoading(cardId);
        try {
            const res = await axios.post<{ message: string }>(
                `${API_BASE}/stamp-cards/${cardId}/claim`,
                {},
                { headers: getAuthHeaders() }
            );
            alert(res.data.message);
            await loadData();
        } catch (err: unknown) {
            const message =
                axios.isAxiosError(err) && err.response?.data?.detail
                    ? err.response.data.detail
                    : '兌換失敗';
            alert(message);
        } finally {
            setActionLoading(null);
        }
    };

    // Check which templates the user already has an active card for
    const activeTemplateIds = new Set(
        cards.filter((c) => !c.is_completed).map((c) => c.template_id)
    );

    return (
        <div className="page stamp-page">
            <Header title="集點卡" showBack />

            <main className="page-content">
                {isLoading ? (
                    <div className="stamp-skeleton">
                        <div className="skeleton" style={{ height: 120, borderRadius: 16 }} />
                        <div className="skeleton" style={{ height: 200, marginTop: 16 }} />
                    </div>
                ) : (
                    <>
                        {/* Available templates */}
                        {templates.length > 0 && (
                            <div className="stamp-section">
                                <h3>可參加的集點活動</h3>
                                {templates.map((tpl) => (
                                    <div key={tpl.id} className="stamp-template">
                                        <div className="stamp-template__info">
                                            <span className="stamp-template__name">{tpl.name}</span>
                                            {tpl.description && (
                                                <span className="stamp-template__desc">
                                                    {tpl.description}
                                                </span>
                                            )}
                                            <span className="stamp-template__meta">
                                                集滿 {tpl.stamps_required} 點 | 獎勵：
                                                {rewardTypeLabel[tpl.reward_type] || tpl.reward_type} - {tpl.reward_value}
                                            </span>
                                        </div>
                                        <button
                                            className="stamp-template__btn"
                                            disabled={
                                                activeTemplateIds.has(tpl.id) ||
                                                actionLoading === tpl.id
                                            }
                                            onClick={() => handleStart(tpl.id)}
                                        >
                                            {activeTemplateIds.has(tpl.id)
                                                ? '進行中'
                                                : '開始集點'}
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* User's stamp cards */}
                        {cards.length > 0 ? (
                            <div className="stamp-section">
                                <h3>我的集點卡</h3>
                                {cards.map((card) => {
                                    const progress =
                                        (card.stamps_collected / card.template.stamps_required) * 100;
                                    const statusBadge = card.is_reward_claimed
                                        ? { text: '已兌換', cls: 'claimed' }
                                        : card.is_completed
                                          ? { text: '已集滿', cls: 'completed' }
                                          : { text: '集點中', cls: 'active' };

                                    return (
                                        <div
                                            key={card.id}
                                            className={`stamp-card ${
                                                card.is_completed
                                                    ? card.is_reward_claimed
                                                        ? 'stamp-card--claimed'
                                                        : 'stamp-card--completed'
                                                    : ''
                                            }`}
                                        >
                                            <div className="stamp-card__header">
                                                <span className="stamp-card__name">
                                                    {card.template.name}
                                                </span>
                                                <span
                                                    className={`stamp-card__badge stamp-card__badge--${statusBadge.cls}`}
                                                >
                                                    {statusBadge.text}
                                                </span>
                                            </div>

                                            {/* Stamp grid */}
                                            <div className="stamp-grid">
                                                {Array.from(
                                                    { length: card.template.stamps_required },
                                                    (_, i) => (
                                                        <div
                                                            key={i}
                                                            className={`stamp-circle ${
                                                                i < card.stamps_collected
                                                                    ? 'stamp-circle--filled'
                                                                    : 'stamp-circle--empty'
                                                            }`}
                                                        >
                                                            {i < card.stamps_collected ? '\u2713' : i + 1}
                                                        </div>
                                                    )
                                                )}
                                            </div>

                                            {/* Progress bar */}
                                            <div className="stamp-progress">
                                                <div className="stamp-progress__text">
                                                    <span>
                                                        {card.stamps_collected} / {card.template.stamps_required}
                                                    </span>
                                                    <span>{Math.round(progress)}%</span>
                                                </div>
                                                <div className="stamp-progress__bar">
                                                    <div
                                                        className={`stamp-progress__fill ${
                                                            card.is_completed
                                                                ? 'stamp-progress__fill--completed'
                                                                : ''
                                                        }`}
                                                        style={{ width: `${Math.min(100, progress)}%` }}
                                                    />
                                                </div>
                                            </div>

                                            {/* Reward info */}
                                            <div className="stamp-card__reward">
                                                <span className="stamp-card__reward-icon">
                                                    {card.is_completed ? '\u{1F381}' : '\u{1F3AF}'}
                                                </span>
                                                <span>
                                                    {rewardTypeLabel[card.template.reward_type] || card.template.reward_type}
                                                    ：{card.template.reward_value}
                                                </span>
                                            </div>

                                            {/* Claim button */}
                                            {card.is_completed && !card.is_reward_claimed && (
                                                <button
                                                    className="stamp-card__claim-btn"
                                                    disabled={actionLoading === card.id}
                                                    onClick={() => handleClaim(card.id)}
                                                >
                                                    兌換獎勵
                                                </button>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <div className="stamp-empty">
                                <p>您尚未擁有任何集點卡</p>
                                <p>選擇上方活動開始集點吧！</p>
                            </div>
                        )}
                    </>
                )}
            </main>

            <BottomNav />
        </div>
    );
}

export default StampCardPage;
