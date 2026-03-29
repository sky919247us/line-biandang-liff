/**
 * 會員忠誠度頁面
 *
 * 顯示點數餘額、等級、交易紀錄
 */
import { useState, useEffect } from 'react';
import { Header } from '../../components/layout/Header';
import { BottomNav } from '../../components/layout/BottomNav';
import { loyaltyApi } from '../../services/api';
import type { LoyaltyAccount, PointTransaction, LoyaltyTier } from '../../types';
import { LoyaltyTierText, LoyaltyTierColor } from '../../types';
import './LoyaltyPage.css';

const tierThresholds: { tier: LoyaltyTier; min: number; label: string }[] = [
    { tier: 'normal', min: 0, label: '一般' },
    { tier: 'silver', min: 500, label: '銀卡' },
    { tier: 'gold', min: 1500, label: '金卡' },
    { tier: 'vip', min: 5000, label: 'VIP' },
];

export function LoyaltyPage() {
    const [account, setAccount] = useState<LoyaltyAccount | null>(null);
    const [transactions, setTransactions] = useState<PointTransaction[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            setIsLoading(true);
            try {
                const [acc, txns] = await Promise.all([
                    loyaltyApi.getAccount(),
                    loyaltyApi.getTransactions({ limit: 30 }),
                ]);
                setAccount(acc);
                setTransactions(txns.items);
            } catch (err) {
                console.error('載入忠誠度資料失敗:', err);
                // Mock data
                setAccount({
                    id: '1',
                    userId: '1',
                    pointsBalance: 320,
                    totalEarned: 520,
                    totalRedeemed: 200,
                    tier: 'silver',
                });
                setTransactions([
                    { id: '1', points: 24, transactionType: 'earn', description: '訂單 BD202603200001', createdAt: new Date().toISOString() },
                    { id: '2', points: -100, transactionType: 'redeem', description: '點數折抵', createdAt: new Date(Date.now() - 86400000).toISOString() },
                    { id: '3', points: 16, transactionType: 'earn', description: '訂單 BD202603180002', createdAt: new Date(Date.now() - 2 * 86400000).toISOString() },
                    { id: '4', points: 50, transactionType: 'bonus', description: '首購獎勵', createdAt: new Date(Date.now() - 7 * 86400000).toISOString() },
                ]);
            } finally {
                setIsLoading(false);
            }
        };
        loadData();
    }, []);

    const getNextTier = () => {
        if (!account) return null;
        const currentIdx = tierThresholds.findIndex(t => t.tier === account.tier);
        if (currentIdx < tierThresholds.length - 1) {
            const next = tierThresholds[currentIdx + 1];
            return { ...next, remaining: next.min - account.totalEarned };
        }
        return null;
    };

    const nextTier = getNextTier();
    const tierProgress = account
        ? (() => {
            const currentIdx = tierThresholds.findIndex(t => t.tier === account.tier);
            const currentMin = tierThresholds[currentIdx].min;
            const nextMin = currentIdx < tierThresholds.length - 1 ? tierThresholds[currentIdx + 1].min : account.totalEarned;
            return Math.min(100, ((account.totalEarned - currentMin) / (nextMin - currentMin)) * 100);
        })()
        : 0;

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('zh-TW', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    };

    const txnTypeText: Record<string, string> = {
        earn: '消費獲得',
        redeem: '點數折抵',
        bonus: '獎勵',
        expire: '過期',
        adjust: '調整',
    };

    return (
        <div className="page loyalty-page">
            <Header title="會員點數" showBack />

            <main className="page-content">
                {isLoading ? (
                    <div className="loyalty-skeleton">
                        <div className="skeleton" style={{ height: 160, borderRadius: 16 }} />
                        <div className="skeleton" style={{ height: 40, marginTop: 16 }} />
                        <div className="skeleton" style={{ height: 200, marginTop: 16 }} />
                    </div>
                ) : account ? (
                    <>
                        {/* 點數卡片 */}
                        <div className="loyalty-card" style={{ borderColor: LoyaltyTierColor[account.tier] }}>
                            <div className="loyalty-card__tier">
                                <span
                                    className="loyalty-card__tier-badge"
                                    style={{ background: LoyaltyTierColor[account.tier] }}
                                >
                                    {LoyaltyTierText[account.tier]}
                                </span>
                            </div>
                            <div className="loyalty-card__balance">
                                <span className="loyalty-card__balance-label">可用點數</span>
                                <span className="loyalty-card__balance-value">{account.pointsBalance}</span>
                                <span className="loyalty-card__balance-unit">點</span>
                            </div>
                            <div className="loyalty-card__stats">
                                <div>
                                    <span className="loyalty-card__stat-label">累計獲得</span>
                                    <span className="loyalty-card__stat-value">{account.totalEarned}</span>
                                </div>
                                <div>
                                    <span className="loyalty-card__stat-label">已兌換</span>
                                    <span className="loyalty-card__stat-value">{account.totalRedeemed}</span>
                                </div>
                            </div>
                        </div>

                        {/* 等級進度 */}
                        {nextTier && (
                            <div className="loyalty-progress">
                                <div className="loyalty-progress__header">
                                    <span>距離 {nextTier.label} 還需 {nextTier.remaining} 點</span>
                                </div>
                                <div className="loyalty-progress__bar">
                                    <div
                                        className="loyalty-progress__fill"
                                        style={{
                                            width: `${tierProgress}%`,
                                            background: LoyaltyTierColor[account.tier],
                                        }}
                                    />
                                </div>
                            </div>
                        )}

                        {/* 點數規則 */}
                        <div className="loyalty-rules">
                            <h3>點數規則</h3>
                            <ul>
                                <li>每消費 NT$10 可獲得 1 點</li>
                                <li>銀卡 1.2x / 金卡 1.5x / VIP 2x 點數加成</li>
                                <li>1 點 = NT$1 折抵</li>
                            </ul>
                        </div>

                        {/* 交易紀錄 */}
                        <div className="loyalty-history">
                            <h3>點數紀錄</h3>
                            {transactions.length > 0 ? (
                                <div className="loyalty-history__list">
                                    {transactions.map(txn => (
                                        <div key={txn.id} className="loyalty-history__item">
                                            <div className="loyalty-history__info">
                                                <span className="loyalty-history__type">
                                                    {txnTypeText[txn.transactionType] || txn.transactionType}
                                                </span>
                                                <span className="loyalty-history__desc">{txn.description}</span>
                                            </div>
                                            <div className="loyalty-history__right">
                                                <span className={`loyalty-history__points ${txn.points > 0 ? 'positive' : 'negative'}`}>
                                                    {txn.points > 0 ? '+' : ''}{txn.points}
                                                </span>
                                                <span className="loyalty-history__date">{formatDate(txn.createdAt)}</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="loyalty-history__empty">尚無點數紀錄</p>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="loyalty-empty">
                        <p>無法載入會員資料</p>
                    </div>
                )}
            </main>

            <BottomNav />
        </div>
    );
}

export default LoyaltyPage;
