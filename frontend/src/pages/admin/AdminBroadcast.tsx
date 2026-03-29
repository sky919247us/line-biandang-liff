/**
 * 管理後台 - 群發訊息頁面
 */
import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import '../admin/AdminLayout.css';
import './AdminBroadcast.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

interface SegmentInfo {
    all_users: number;
    active_users: number;
    inactive_users: number;
    new_users: number;
}

interface PreviewResult {
    target: string;
    target_count: number;
    messages: Record<string, unknown>[];
    preview_text: string;
}

type TargetType = 'all' | 'active' | 'inactive' | 'custom';

function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
}

const TARGET_LABELS: Record<TargetType, string> = {
    all: '所有使用者',
    active: '活躍使用者 (30天內有訂單)',
    inactive: '不活躍使用者',
    custom: '自訂使用者',
};

export function AdminBroadcast() {
    // Segments
    const [segments, setSegments] = useState<SegmentInfo | null>(null);
    const [segmentsLoading, setSegmentsLoading] = useState(false);

    // Form state
    const [target, setTarget] = useState<TargetType>('all');
    const [daysInactive, setDaysInactive] = useState(30);
    const [customIds, setCustomIds] = useState('');
    const [messageType, setMessageType] = useState<'text' | 'flex'>('text');
    const [text, setText] = useState('');
    const [altText, setAltText] = useState('');
    const [flexContents, setFlexContents] = useState('');

    // Preview & Send
    const [preview, setPreview] = useState<PreviewResult | null>(null);
    const [previewLoading, setPreviewLoading] = useState(false);
    const [sending, setSending] = useState(false);
    const [sendResult, setSendResult] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Confirmation dialog
    const [showConfirm, setShowConfirm] = useState(false);

    const fetchSegments = useCallback(async () => {
        setSegmentsLoading(true);
        try {
            const res = await axios.get(`${API_BASE}/admin/broadcast/segments`, {
                headers: getAuthHeaders(),
            });
            setSegments(res.data);
        } catch (err) {
            console.error('Failed to fetch segments:', err);
        } finally {
            setSegmentsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchSegments();
    }, [fetchSegments]);

    function buildRequest() {
        const message: Record<string, unknown> = { message_type: messageType };
        if (messageType === 'text') {
            message.text = text;
        } else {
            message.alt_text = altText;
            try {
                message.flex_contents = JSON.parse(flexContents);
            } catch {
                setError('Flex 訊息 JSON 格式錯誤');
                return null;
            }
        }

        const body: Record<string, unknown> = {
            target,
            message,
        };
        if (target === 'inactive') {
            body.days_inactive = daysInactive;
        }
        if (target === 'custom') {
            body.user_ids = customIds.split(/[\n,]+/).map(s => s.trim()).filter(Boolean);
        }
        return body;
    }

    async function handlePreview() {
        setError(null);
        setSendResult(null);
        const body = buildRequest();
        if (!body) return;

        setPreviewLoading(true);
        try {
            const res = await axios.post(`${API_BASE}/admin/broadcast/preview`, body, {
                headers: getAuthHeaders(),
            });
            setPreview(res.data);
        } catch (err: unknown) {
            const axErr = err as { response?: { data?: { detail?: string } } };
            setError(axErr.response?.data?.detail || '預覽失敗');
        } finally {
            setPreviewLoading(false);
        }
    }

    async function handleSend() {
        setError(null);
        setSendResult(null);
        const body = buildRequest();
        if (!body) return;

        setSending(true);
        setShowConfirm(false);
        try {
            const res = await axios.post(`${API_BASE}/admin/broadcast/send`, body, {
                headers: getAuthHeaders(),
            });
            setSendResult(
                `已發送給 ${res.data.success_count} 位使用者` +
                (res.data.fail_count > 0 ? `，${res.data.fail_count} 位失敗` : '')
            );
            setPreview(null);
        } catch (err: unknown) {
            const axErr = err as { response?: { data?: { detail?: string } } };
            setError(axErr.response?.data?.detail || '發送失敗');
        } finally {
            setSending(false);
        }
    }

    function getTargetCount(): number {
        if (!segments) return 0;
        switch (target) {
            case 'all': return segments.all_users;
            case 'active': return segments.active_users;
            case 'inactive': return segments.inactive_users;
            case 'custom': return customIds.split(/[\n,]+/).filter(s => s.trim()).length;
        }
    }

    const isValid = messageType === 'text' ? text.trim().length > 0 : flexContents.trim().length > 0;

    return (
        <div className="admin-broadcast">
            <div className="admin-page-header">
                <h1 className="admin-page-title">群發訊息</h1>
                <p className="admin-page-subtitle">向使用者推播 LINE 訊息</p>
            </div>

            {/* Segment counts */}
            <div className="admin-broadcast__segments">
                <h3 className="admin-broadcast__section-title">受眾概覽</h3>
                {segmentsLoading ? (
                    <p className="admin-broadcast__loading">載入中...</p>
                ) : segments ? (
                    <div className="admin-broadcast__segment-cards">
                        <div className={`admin-broadcast__segment-card ${target === 'all' ? 'active' : ''}`}
                             onClick={() => setTarget('all')}>
                            <div className="admin-broadcast__segment-count">{segments.all_users}</div>
                            <div className="admin-broadcast__segment-label">全部使用者</div>
                        </div>
                        <div className={`admin-broadcast__segment-card ${target === 'active' ? 'active' : ''}`}
                             onClick={() => setTarget('active')}>
                            <div className="admin-broadcast__segment-count">{segments.active_users}</div>
                            <div className="admin-broadcast__segment-label">活躍使用者</div>
                        </div>
                        <div className={`admin-broadcast__segment-card ${target === 'inactive' ? 'active' : ''}`}
                             onClick={() => setTarget('inactive')}>
                            <div className="admin-broadcast__segment-count">{segments.inactive_users}</div>
                            <div className="admin-broadcast__segment-label">不活躍使用者</div>
                        </div>
                        <div className={`admin-broadcast__segment-card ${target === 'custom' ? 'active' : ''}`}
                             onClick={() => setTarget('custom')}>
                            <div className="admin-broadcast__segment-count">{segments.new_users}</div>
                            <div className="admin-broadcast__segment-label">本月新加入</div>
                        </div>
                    </div>
                ) : null}
            </div>

            <div className="admin-broadcast__main">
                {/* Composer */}
                <div className="admin-broadcast__composer">
                    <h3 className="admin-broadcast__section-title">訊息編輯</h3>

                    {/* Target selector */}
                    <div className="admin-broadcast__field">
                        <label className="admin-broadcast__label">發送對象</label>
                        <select
                            className="admin-broadcast__select"
                            value={target}
                            onChange={e => setTarget(e.target.value as TargetType)}
                        >
                            {Object.entries(TARGET_LABELS).map(([key, label]) => (
                                <option key={key} value={key}>{label}</option>
                            ))}
                        </select>
                    </div>

                    {target === 'inactive' && (
                        <div className="admin-broadcast__field">
                            <label className="admin-broadcast__label">未活躍天數</label>
                            <input
                                type="number"
                                className="admin-broadcast__input"
                                value={daysInactive}
                                onChange={e => setDaysInactive(Number(e.target.value))}
                                min={1}
                            />
                        </div>
                    )}

                    {target === 'custom' && (
                        <div className="admin-broadcast__field">
                            <label className="admin-broadcast__label">使用者 ID（每行一個或用逗號分隔）</label>
                            <textarea
                                className="admin-broadcast__textarea"
                                value={customIds}
                                onChange={e => setCustomIds(e.target.value)}
                                rows={3}
                                placeholder="user-id-1&#10;user-id-2"
                            />
                        </div>
                    )}

                    {/* Message type */}
                    <div className="admin-broadcast__field">
                        <label className="admin-broadcast__label">訊息類型</label>
                        <div className="admin-broadcast__radio-group">
                            <label className="admin-broadcast__radio">
                                <input
                                    type="radio"
                                    name="messageType"
                                    value="text"
                                    checked={messageType === 'text'}
                                    onChange={() => setMessageType('text')}
                                />
                                文字訊息
                            </label>
                            <label className="admin-broadcast__radio">
                                <input
                                    type="radio"
                                    name="messageType"
                                    value="flex"
                                    checked={messageType === 'flex'}
                                    onChange={() => setMessageType('flex')}
                                />
                                Flex 訊息
                            </label>
                        </div>
                    </div>

                    {/* Message content */}
                    {messageType === 'text' ? (
                        <div className="admin-broadcast__field">
                            <label className="admin-broadcast__label">訊息內容</label>
                            <textarea
                                className="admin-broadcast__textarea admin-broadcast__textarea--large"
                                value={text}
                                onChange={e => setText(e.target.value)}
                                rows={6}
                                placeholder="輸入要推播的訊息..."
                                maxLength={5000}
                            />
                            <span className="admin-broadcast__char-count">{text.length} / 5000</span>
                        </div>
                    ) : (
                        <>
                            <div className="admin-broadcast__field">
                                <label className="admin-broadcast__label">替代文字（推播通知顯示）</label>
                                <input
                                    type="text"
                                    className="admin-broadcast__input"
                                    value={altText}
                                    onChange={e => setAltText(e.target.value)}
                                    placeholder="Flex 訊息替代文字"
                                />
                            </div>
                            <div className="admin-broadcast__field">
                                <label className="admin-broadcast__label">Flex 訊息 JSON</label>
                                <textarea
                                    className="admin-broadcast__textarea admin-broadcast__textarea--large admin-broadcast__textarea--code"
                                    value={flexContents}
                                    onChange={e => setFlexContents(e.target.value)}
                                    rows={10}
                                    placeholder='{"type": "bubble", "body": { ... }}'
                                />
                            </div>
                        </>
                    )}

                    {/* Action buttons */}
                    <div className="admin-broadcast__actions">
                        <button
                            className="admin-broadcast__btn admin-broadcast__btn--preview"
                            onClick={handlePreview}
                            disabled={!isValid || previewLoading}
                        >
                            {previewLoading ? '預覽中...' : '預覽訊息'}
                        </button>
                        <button
                            className="admin-broadcast__btn admin-broadcast__btn--send"
                            onClick={() => setShowConfirm(true)}
                            disabled={!isValid || sending}
                        >
                            {sending ? '發送中...' : '發送訊息'}
                        </button>
                    </div>
                </div>

                {/* Preview panel */}
                <div className="admin-broadcast__preview-panel">
                    <h3 className="admin-broadcast__section-title">預覽</h3>

                    {error && (
                        <div className="admin-broadcast__alert admin-broadcast__alert--error">
                            {error}
                        </div>
                    )}

                    {sendResult && (
                        <div className="admin-broadcast__alert admin-broadcast__alert--success">
                            {sendResult}
                        </div>
                    )}

                    {preview ? (
                        <div className="admin-broadcast__preview-content">
                            <div className="admin-broadcast__preview-meta">
                                <span>目標: {TARGET_LABELS[preview.target as TargetType] || preview.target}</span>
                                <span>人數: {preview.target_count}</span>
                            </div>
                            <div className="admin-broadcast__preview-bubble">
                                <div className="admin-broadcast__preview-text">
                                    {preview.preview_text}
                                </div>
                                {preview.messages.length > 0 && messageType === 'flex' && (
                                    <pre className="admin-broadcast__preview-json">
                                        {JSON.stringify(preview.messages[0], null, 2)}
                                    </pre>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="admin-broadcast__preview-empty">
                            <p>點擊「預覽訊息」查看訊息內容</p>
                            <p className="admin-broadcast__preview-hint">
                                預計發送給 <strong>{getTargetCount()}</strong> 位使用者
                            </p>
                        </div>
                    )}
                </div>
            </div>

            {/* Confirmation dialog */}
            {showConfirm && (
                <div className="admin-broadcast__overlay" onClick={() => setShowConfirm(false)}>
                    <div className="admin-broadcast__dialog" onClick={e => e.stopPropagation()}>
                        <h3 className="admin-broadcast__dialog-title">確認發送</h3>
                        <p className="admin-broadcast__dialog-text">
                            確定要向 <strong>{getTargetCount()}</strong> 位
                            {TARGET_LABELS[target]}發送訊息嗎？
                        </p>
                        <p className="admin-broadcast__dialog-warning">
                            此操作無法復原，訊息將立即推播至使用者的 LINE。
                        </p>
                        <div className="admin-broadcast__dialog-actions">
                            <button
                                className="admin-broadcast__btn admin-broadcast__btn--cancel"
                                onClick={() => setShowConfirm(false)}
                            >
                                取消
                            </button>
                            <button
                                className="admin-broadcast__btn admin-broadcast__btn--confirm"
                                onClick={handleSend}
                                disabled={sending}
                            >
                                {sending ? '發送中...' : '確認發送'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default AdminBroadcast;
