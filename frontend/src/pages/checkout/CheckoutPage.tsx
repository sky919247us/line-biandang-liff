/**
 * 結帳頁面
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '../../components/layout/Header';
import { useCartStore } from '../../stores/cartStore';
import { useAuthStore } from '../../stores/authStore';
import { orderApi, couponApi } from '../../services/api';
import './CheckoutPage.css';

export function CheckoutPage() {
    const navigate = useNavigate();
    const {
        items,
        orderType,
        deliveryAddress,
        contactName,
        contactPhone,
        pickupTime,
        notes,
        tableNumber,
        couponCode,
        appliedDiscount,
        setDeliveryAddress,
        setContactInfo,
        setNotes,
        setTableNumber,
        setCouponCode,
        setAppliedDiscount,
        subtotal,
        clearCart,
        resetCheckoutInfo
    } = useCartStore();

    const user = useAuthStore((state) => state.user);

    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isApplyingCoupon, setIsApplyingCoupon] = useState(false);
    const [couponInput, setCouponInput] = useState(couponCode);
    const [couponMessage, setCouponMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const totalSubtotal = subtotal();
    const deliveryFee = orderType === 'delivery' ? 30 : 0;
    const total = totalSubtotal + deliveryFee - appliedDiscount;

    // 套用優惠碼
    const handleApplyCoupon = async () => {
        if (!couponInput.trim()) return;
        setIsApplyingCoupon(true);
        setCouponMessage(null);
        try {
            const result = await couponApi.validate(couponInput.trim(), totalSubtotal);
            setCouponCode(couponInput.trim());
            setAppliedDiscount(result.discountAmount);
            setCouponMessage(`已套用優惠：折抵 $${result.discountAmount}`);
        } catch (err: any) {
            setCouponMessage(err.response?.data?.detail || '優惠碼無效');
            setCouponCode('');
            setAppliedDiscount(0);
        } finally {
            setIsApplyingCoupon(false);
        }
    };

    // 移除優惠碼
    const handleRemoveCoupon = () => {
        setCouponInput('');
        setCouponCode('');
        setAppliedDiscount(0);
        setCouponMessage(null);
    };

    // 驗證表單
    const validateForm = () => {
        if (orderType === 'delivery') {
            if (!deliveryAddress.trim()) {
                setError('請填寫配送地址');
                return false;
            }
            if (!contactPhone.trim()) {
                setError('請填寫聯絡電話');
                return false;
            }
            if (totalSubtotal < 150) {
                setError('外送訂單最低消費 $150');
                return false;
            }
        }
        return true;
    };

    // 提交訂單
    const handleSubmit = async () => {
        if (!validateForm()) return;

        setIsSubmitting(true);
        setError(null);

        try {
            const orderData = {
                orderType,
                items: items.map((item) => ({
                    productId: item.product.id,
                    quantity: item.quantity,
                    customizations: item.customizations,
                    notes: item.notes || undefined,
                })),
                deliveryAddress: orderType === 'delivery' ? deliveryAddress : undefined,
                contactName: contactName || user?.displayName || undefined,
                contactPhone: contactPhone || undefined,
                pickupTime: pickupTime || undefined,
                notes: notes || undefined,
                tableNumber: orderType === 'dine_in' ? tableNumber || undefined : undefined,
                couponCode: couponCode || undefined,
            };

            const order = await orderApi.createOrder(orderData);

            // 清空購物車和結帳資訊
            clearCart();
            resetCheckoutInfo();

            // 導向成功頁面或訂單詳情
            navigate('/orders', {
                state: {
                    success: true,
                    orderNumber: order.orderNumber
                }
            });

        } catch (err: any) {
            console.error('訂單建立失敗:', err);
            setError(err.response?.data?.detail || '訂單建立失敗，請稍後再試');
        } finally {
            setIsSubmitting(false);
        }
    };

    // 如果購物車為空，導回購物車頁
    if (items.length === 0) {
        navigate('/cart');
        return null;
    }

    return (
        <div className="page checkout-page">
            <Header title="確認訂單" showBack />

            <main className="page-content">
                {/* 取餐方式顯示 */}
                <div className="checkout-section">
                    <h3 className="checkout-section__title">取餐方式</h3>
                    <div className="checkout-order-type">
                        <div>
                            <strong>
                                {orderType === 'pickup' && '到店自取'}
                                {orderType === 'dine_in' && '內用'}
                                {orderType === 'delivery' && '外送服務'}
                            </strong>
                            <p>
                                {orderType === 'pickup' && '台中市中區興中街20號'}
                                {orderType === 'dine_in' && '店內用餐'}
                                {orderType === 'delivery' && `配送費 $${deliveryFee}`}
                            </p>
                        </div>
                    </div>
                </div>

                {/* 內用桌號 */}
                {orderType === 'dine_in' && (
                    <div className="checkout-section">
                        <h3 className="checkout-section__title">桌號</h3>
                        <div className="checkout-form">
                            <div className="input-group">
                                <input
                                    type="text"
                                    className="input"
                                    placeholder="請輸入桌號（選填）"
                                    value={tableNumber}
                                    onChange={(e) => setTableNumber(e.target.value)}
                                />
                            </div>
                        </div>
                    </div>
                )}

                {/* 外送地址（外送時顯示） */}
                {orderType === 'delivery' && (
                    <div className="checkout-section">
                        <h3 className="checkout-section__title">配送資訊</h3>

                        <div className="checkout-form">
                            <div className="input-group">
                                <label className="input-label required">配送地址</label>
                                <input
                                    type="text"
                                    className="input"
                                    placeholder="請輸入完整配送地址"
                                    value={deliveryAddress}
                                    onChange={(e) => setDeliveryAddress(e.target.value)}
                                />
                            </div>

                            <div className="input-group">
                                <label className="input-label required">聯絡電話</label>
                                <input
                                    type="tel"
                                    className="input"
                                    placeholder="請輸入聯絡電話"
                                    value={contactPhone}
                                    onChange={(e) => setContactInfo(contactName, e.target.value)}
                                />
                            </div>

                            <div className="input-group">
                                <label className="input-label">收件人姓名</label>
                                <input
                                    type="text"
                                    className="input"
                                    placeholder={user?.displayName || '請輸入收件人姓名'}
                                    value={contactName}
                                    onChange={(e) => setContactInfo(e.target.value, contactPhone)}
                                />
                            </div>
                        </div>
                    </div>
                )}

                {/* 訂單備註 */}
                <div className="checkout-section">
                    <h3 className="checkout-section__title">訂單備註</h3>
                    <textarea
                        className="input textarea"
                        placeholder="如有特殊需求請在此填寫..."
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        rows={3}
                    />
                </div>

                {/* 訂單明細 */}
                <div className="checkout-section">
                    <h3 className="checkout-section__title">訂單明細</h3>

                    <div className="checkout-items">
                        {items.map((item, index) => (
                            <div key={index} className="checkout-item">
                                <div className="checkout-item__info">
                                    <span className="checkout-item__name">{item.product.name}</span>
                                    <span className="checkout-item__qty">x{item.quantity}</span>
                                </div>
                                {item.customizations.length > 0 && (
                                    <p className="checkout-item__customizations">
                                        {item.customizations.map(c => c.name).join('、')}
                                    </p>
                                )}
                                <span className="checkout-item__price">${item.subtotal}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 優惠碼 */}
                <div className="checkout-section">
                    <h3 className="checkout-section__title">優惠碼</h3>
                    {couponCode && appliedDiscount > 0 ? (
                        <div className="checkout-coupon-applied">
                            <div className="checkout-coupon-applied__info">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <polyline points="20 6 9 17 4 12" />
                                </svg>
                                <span>{couponMessage}</span>
                            </div>
                            <button className="checkout-coupon-remove" onClick={handleRemoveCoupon}>
                                移除
                            </button>
                        </div>
                    ) : (
                        <div className="checkout-coupon-input">
                            <input
                                type="text"
                                className="input"
                                placeholder="請輸入優惠碼"
                                value={couponInput}
                                onChange={(e) => setCouponInput(e.target.value)}
                            />
                            <button
                                className="btn btn-primary"
                                onClick={handleApplyCoupon}
                                disabled={isApplyingCoupon || !couponInput.trim()}
                            >
                                {isApplyingCoupon ? '驗證中...' : '套用'}
                            </button>
                        </div>
                    )}
                    {couponMessage && !appliedDiscount && (
                        <p className="checkout-coupon-error">{couponMessage}</p>
                    )}
                </div>

                {/* 金額明細 */}
                <div className="checkout-section">
                    <h3 className="checkout-section__title">金額明細</h3>
                    <div className="checkout-summary">
                        <div className="checkout-summary__row">
                            <span>商品小計</span>
                            <span>${totalSubtotal}</span>
                        </div>
                        {orderType === 'delivery' && (
                            <div className="checkout-summary__row">
                                <span>運費</span>
                                <span>${deliveryFee}</span>
                            </div>
                        )}
                        {appliedDiscount > 0 && (
                            <div className="checkout-summary__row" style={{ color: 'var(--color-success)' }}>
                                <span>優惠折抵</span>
                                <span>-${appliedDiscount}</span>
                            </div>
                        )}
                        <div className="checkout-summary__row checkout-summary__row--total">
                            <span>應付金額</span>
                            <span className="checkout-summary__total">${Math.max(0, total)}</span>
                        </div>
                    </div>
                </div>

                {/* 錯誤訊息 */}
                {error && (
                    <div className="checkout-error">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10" />
                            <line x1="12" y1="8" x2="12" y2="12" />
                            <line x1="12" y1="16" x2="12.01" y2="16" />
                        </svg>
                        {error}
                    </div>
                )}
            </main>

            {/* 提交按鈕 */}
            <div className="checkout-footer">
                <button
                    className="btn btn-primary btn-lg btn-full"
                    onClick={handleSubmit}
                    disabled={isSubmitting}
                >
                    {isSubmitting ? (
                        <>
                            <span className="animate-spin">⏳</span>
                            處理中...
                        </>
                    ) : (
                        `確認訂購 - $${total}`
                    )}
                </button>
            </div>
        </div>
    );
}

export default CheckoutPage;
