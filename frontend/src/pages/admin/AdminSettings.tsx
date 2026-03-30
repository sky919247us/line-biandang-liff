/**
 * 管理後台 - 系統設定頁面
 */
import { useState } from 'react';
import '../admin/AdminLayout.css';
import './AdminSettings.css';

interface StoreSettings {
    storeName: string;
    phone: string;
    address: string;
    openTime: string;
    closeTime: string;
    closedDays: string[];
    deliveryEnabled: boolean;
    deliveryFee: number;
    freeDeliveryMinimum: number;
    deliveryRadius: number;
    autoAcceptOrders: boolean;
}

const initialSettings: StoreSettings = {
    storeName: '一米粒 弁当専門店',
    phone: '0909-998-952',
    address: '台中市中區興中街20號',
    openTime: '10:00',
    closeTime: '16:30',
    closedDays: ['saturday', 'sunday'],
    deliveryEnabled: true,
    deliveryFee: 30,
    freeDeliveryMinimum: 300,
    deliveryRadius: 3,
    autoAcceptOrders: false,
};

const dayOptions = [
    { value: 'monday', label: '週一' },
    { value: 'tuesday', label: '週二' },
    { value: 'wednesday', label: '週三' },
    { value: 'thursday', label: '週四' },
    { value: 'friday', label: '週五' },
    { value: 'saturday', label: '週六' },
    { value: 'sunday', label: '週日' },
];

export function AdminSettings() {
    const [settings, setSettings] = useState<StoreSettings>(initialSettings);
    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);

    const handleChange = (field: keyof StoreSettings, value: any) => {
        setSettings(prev => ({ ...prev, [field]: value }));
        setSaveSuccess(false);
    };

    const handleClosedDayToggle = (day: string) => {
        setSettings(prev => {
            const newDays = prev.closedDays.includes(day)
                ? prev.closedDays.filter(d => d !== day)
                : [...prev.closedDays, day];
            return { ...prev, closedDays: newDays };
        });
        setSaveSuccess(false);
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            const { updateSettings } = await import('../../services/adminApi');
            await updateSettings(settings);
            setSaveSuccess(true);
        } catch (err) {
            console.error('儲存設定失敗:', err);
            alert('儲存設定失敗，請稍後再試');
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className="admin-settings">
            <div className="admin-page-header">
                <h1 className="admin-page-title">系統設定</h1>
            </div>

            {/* 基本資訊 */}
            <div className="admin-card admin-settings__section">
                <div className="admin-card__header">
                    <h3 className="admin-card__title">店家資訊</h3>
                </div>
                <div className="admin-card__body">
                    <div className="admin-settings__form-grid">
                        <div className="form-group">
                            <label className="form-label">店名</label>
                            <input
                                type="text"
                                className="form-input"
                                value={settings.storeName}
                                onChange={(e) => handleChange('storeName', e.target.value)}
                            />
                        </div>
                        <div className="form-group">
                            <label className="form-label">聯絡電話</label>
                            <input
                                type="tel"
                                className="form-input"
                                value={settings.phone}
                                onChange={(e) => handleChange('phone', e.target.value)}
                            />
                        </div>
                        <div className="form-group form-group--full">
                            <label className="form-label">地址</label>
                            <input
                                type="text"
                                className="form-input"
                                value={settings.address}
                                onChange={(e) => handleChange('address', e.target.value)}
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* 營業時間 */}
            <div className="admin-card admin-settings__section">
                <div className="admin-card__header">
                    <h3 className="admin-card__title">營業時間</h3>
                </div>
                <div className="admin-card__body">
                    <div className="admin-settings__form-grid">
                        <div className="form-group">
                            <label className="form-label">開始營業</label>
                            <input
                                type="time"
                                className="form-input"
                                value={settings.openTime}
                                onChange={(e) => handleChange('openTime', e.target.value)}
                            />
                        </div>
                        <div className="form-group">
                            <label className="form-label">結束營業</label>
                            <input
                                type="time"
                                className="form-input"
                                value={settings.closeTime}
                                onChange={(e) => handleChange('closeTime', e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">公休日</label>
                        <div className="admin-settings__day-selector">
                            {dayOptions.map(day => (
                                <label
                                    key={day.value}
                                    className={`admin-settings__day-option ${settings.closedDays.includes(day.value) ? 'active' : ''}`}
                                >
                                    <input
                                        type="checkbox"
                                        checked={settings.closedDays.includes(day.value)}
                                        onChange={() => handleClosedDayToggle(day.value)}
                                    />
                                    {day.label}
                                </label>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* 外送設定 */}
            <div className="admin-card admin-settings__section">
                <div className="admin-card__header">
                    <h3 className="admin-card__title">外送設定</h3>
                </div>
                <div className="admin-card__body">
                    <div className="form-group">
                        <label className="admin-settings__toggle">
                            <input
                                type="checkbox"
                                checked={settings.deliveryEnabled}
                                onChange={(e) => handleChange('deliveryEnabled', e.target.checked)}
                            />
                            <span className="admin-settings__toggle-slider"></span>
                            <span>啟用外送服務</span>
                        </label>
                    </div>

                    {settings.deliveryEnabled && (
                        <div className="admin-settings__form-grid">
                            <div className="form-group">
                                <label className="form-label">外送費用 (元)</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    value={settings.deliveryFee}
                                    min={0}
                                    onChange={(e) => handleChange('deliveryFee', parseInt(e.target.value) || 0)}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">滿額免運 (元)</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    value={settings.freeDeliveryMinimum}
                                    min={0}
                                    onChange={(e) => handleChange('freeDeliveryMinimum', parseInt(e.target.value) || 0)}
                                />
                                <span className="form-hint">設為 0 表示無免運門檻</span>
                            </div>
                            <div className="form-group">
                                <label className="form-label">外送範圍 (公里)</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    value={settings.deliveryRadius}
                                    min={0}
                                    step={0.5}
                                    onChange={(e) => handleChange('deliveryRadius', parseFloat(e.target.value) || 0)}
                                />
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* 訂單設定 */}
            <div className="admin-card admin-settings__section">
                <div className="admin-card__header">
                    <h3 className="admin-card__title">訂單設定</h3>
                </div>
                <div className="admin-card__body">
                    <div className="form-group">
                        <label className="admin-settings__toggle">
                            <input
                                type="checkbox"
                                checked={settings.autoAcceptOrders}
                                onChange={(e) => handleChange('autoAcceptOrders', e.target.checked)}
                            />
                            <span className="admin-settings__toggle-slider"></span>
                            <span>自動接單</span>
                        </label>
                        <span className="form-hint">啟用後，新訂單將自動確認，無需手動接單</span>
                    </div>
                </div>
            </div>

            {/* 儲存按鈕 */}
            <div className="admin-settings__actions">
                {saveSuccess && (
                    <span className="admin-settings__success">✓ 設定已儲存</span>
                )}
                <button
                    className="btn btn-primary btn-lg"
                    onClick={handleSave}
                    disabled={isSaving}
                >
                    {isSaving ? '儲存中...' : '儲存設定'}
                </button>
            </div>
        </div>
    );
}

export default AdminSettings;
