/**
 * 推薦好友頁面
 *
 * 顯示推薦碼、分享連結、推薦統計與推薦紀錄
 */
import { useState, useEffect } from 'react';
import axios from 'axios';
import { Header } from '../../components/layout/Header';
import { BottomNav } from '../../components/layout/BottomNav';
import './Referral.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
}

interface ReferralCode {
    referral_code: string;
    share_link: string;
}

interface ReferredUser {
    id: string;
    referred_name: string | null;
    status: string;
    referrer_reward_type: string | null;
    referrer_reward_value: string | null;
    created_at: string;
    completed_at: string | null;
}

interface MyReferrals {
    total: number;
    completed: number;
    rewarded: number;
    referrals: ReferredUser[];
}

const statusText: Record<string, string> = {
    pending: '等待中',
    completed: '已完成',
    rewarded: '已獲獎勵',
};

const statusClass: Record<string, string> = {
    pending: 'status--pending',
    completed: 'status--completed',
    rewarded: 'status--rewarded',
};

export function ReferralPage() {
    const [codeData, setCodeData] = useState<ReferralCode | null>(null);
    const [referrals, setReferrals] = useState<MyReferrals | null>(null);
    const [applyCode, setApplyCode] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [applyLoading, setApplyLoading] = useState(false);
    const [copySuccess, setCopySuccess] = useState(false);
    const [copyLinkSuccess, setCopyLinkSuccess] = useState(false);
    const [applyMessage, setApplyMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setIsLoading(true);
        try {
            const headers = getAuthHeaders();
            const [codeRes, referralsRes] = await Promise.all([
                axios.get<ReferralCode>(`${API_BASE}/referrals/my-code`, { headers }),
                axios.get<MyReferrals>(`${API_BASE}/referrals/my-referrals`, { headers }),
            ]);
            setCodeData(codeRes.data);
            setReferrals(referralsRes.data);
        } catch (err) {
            console.error('載入推薦資料失敗:', err);
            setError('載入推薦資料失敗，請稍後再試');
        } finally {
            setIsLoading(false);
        }
    };

    const handleCopyCode = async () => {
        if (!codeData) return;
        try {
            await navigator.clipboard.writeText(codeData.referral_code);
            setCopySuccess(true);
            setTimeout(() => setCopySuccess(false), 2000);
        } catch {
            console.error('複製失敗');
        }
    };

    const handleCopyLink = async () => {
        if (!codeData) return;
        try {
            await navigator.clipboard.writeText(codeData.share_link);
            setCopyLinkSuccess(true);
            setTimeout(() => setCopyLinkSuccess(false), 2000);
        } catch {
            console.error('複製失敗');
        }
    };

    const handleApplyCode = async () => {
        if (!applyCode.trim()) return;
        setApplyLoading(true);
        setApplyMessage(null);
        try {
            const headers = getAuthHeaders();
            await axios.post(`${API_BASE}/referrals/apply`, { code: applyCode.trim() }, { headers });
            setApplyMessage({ type: 'success', text: '推薦碼套用成功！' });
            setApplyCode('');
            loadData();
        } catch (err: any) {
            const detail = err?.response?.data?.detail || '套用失敗，請確認推薦碼是否正確';
            setApplyMessage({ type: 'error', text: detail });
        } finally {
            setApplyLoading(false);
        }
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('zh-TW', { month: 'numeric', day: 'numeric' });
    };

    const totalRewardPoints = referrals
        ? referrals.referrals
            .filter(r => r.referrer_reward_type === 'points' && r.referrer_reward_value)
            .reduce((sum, r) => sum + parseInt(r.referrer_reward_value || '0', 10), 0)
        : 0;

    return (
        <div className="page referral-page">
            <Header title="推薦好友" showBack />

            <main className="page-content">
                {error && (
                    <div className="error-message" style={{ color: '#e53e3e', textAlign: 'center', padding: '2rem 1rem' }}>
                        {error}
                    </div>
                )}
                {isLoading ? (
                    <div className="referral-skeleton">
                        <div className="skeleton" style={{ height: 140, borderRadius: 16 }} />
                        <div className="skeleton" style={{ height: 80, marginTop: 16 }} />
                        <div className="skeleton" style={{ height: 200, marginTop: 16 }} />
                    </div>
                ) : (
                    <>
                        {/* 推薦碼區塊 */}
                        <div className="referral-code-card">
                            <h3 className="referral-code-card__title">我的推薦碼</h3>
                            <div className="referral-code-card__code-row">
                                <span className="referral-code-card__code">
                                    {codeData?.referral_code || '---'}
                                </span>
                                <button
                                    className="referral-code-card__copy-btn"
                                    onClick={handleCopyCode}
                                >
                                    {copySuccess ? '已複製' : '複製'}
                                </button>
                            </div>
                            <div className="referral-code-card__share-row">
                                <span className="referral-code-card__share-label">分享連結</span>
                                <button
                                    className="referral-code-card__share-btn"
                                    onClick={handleCopyLink}
                                >
                                    {copyLinkSuccess ? '已複製連結' : '複製連結'}
                                </button>
                            </div>
                            <p className="referral-code-card__hint">
                                分享推薦碼給好友，雙方完成首筆訂單後皆可獲得 50 點獎勵！
                            </p>
                        </div>

                        {/* 統計區塊 */}
                        <div className="referral-stats">
                            <div className="referral-stats__item">
                                <span className="referral-stats__value">{referrals?.total ?? 0}</span>
                                <span className="referral-stats__label">已推薦</span>
                            </div>
                            <div className="referral-stats__item">
                                <span className="referral-stats__value">{referrals?.completed ?? 0}</span>
                                <span className="referral-stats__label">已完成</span>
                            </div>
                            <div className="referral-stats__item">
                                <span className="referral-stats__value">{totalRewardPoints}</span>
                                <span className="referral-stats__label">獲得點數</span>
                            </div>
                        </div>

                        {/* 套用推薦碼 */}
                        <div className="referral-apply">
                            <h3 className="referral-apply__title">輸入推薦碼</h3>
                            <div className="referral-apply__row">
                                <input
                                    className="referral-apply__input"
                                    type="text"
                                    placeholder="請輸入好友的推薦碼"
                                    value={applyCode}
                                    onChange={(e) => setApplyCode(e.target.value)}
                                    maxLength={20}
                                />
                                <button
                                    className="referral-apply__btn"
                                    onClick={handleApplyCode}
                                    disabled={applyLoading || !applyCode.trim()}
                                >
                                    {applyLoading ? '送出中...' : '套用'}
                                </button>
                            </div>
                            {applyMessage && (
                                <p className={`referral-apply__message referral-apply__message--${applyMessage.type}`}>
                                    {applyMessage.text}
                                </p>
                            )}
                        </div>

                        {/* 推薦紀錄 */}
                        <div className="referral-list">
                            <h3 className="referral-list__title">推薦紀錄</h3>
                            {referrals && referrals.referrals.length > 0 ? (
                                <div className="referral-list__items">
                                    {referrals.referrals.map((r) => (
                                        <div key={r.id} className="referral-list__item">
                                            <div className="referral-list__info">
                                                <span className="referral-list__name">
                                                    {r.referred_name || '未知使用者'}
                                                </span>
                                                <span className="referral-list__date">
                                                    {formatDate(r.created_at)}
                                                </span>
                                            </div>
                                            <div className="referral-list__right">
                                                <span className={`referral-list__status ${statusClass[r.status] || ''}`}>
                                                    {statusText[r.status] || r.status}
                                                </span>
                                                {r.referrer_reward_type === 'points' && r.referrer_reward_value && (
                                                    <span className="referral-list__reward">
                                                        +{r.referrer_reward_value} 點
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="referral-list__empty">尚無推薦紀錄</p>
                            )}
                        </div>
                    </>
                )}
            </main>

            <BottomNav />
        </div>
    );
}

export default ReferralPage;
