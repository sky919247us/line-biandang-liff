/**
 * 訂單預覽確認頁
 *
 * 送出訂單前的最終確認頁面
 */
import { useNavigate } from 'react-router-dom';
import { Header } from '../../components/layout/Header';
import { useCartStore } from '../../stores/cartStore';
import './CheckoutPage.css';

export function OrderPreviewPage() {
    const navigate = useNavigate();
    const {
        items,
        orderType,
        subtotal,
    } = useCartStore();

    const totalSubtotal = subtotal();
    const deliveryFee = orderType === 'delivery' ? 30 : 0;
    const total = totalSubtotal + deliveryFee;

    const orderTypeLabels: Record<string, string> = {
        pickup: '到店自取',
        delivery: '外送服務',
        dine_in: '內用',
    };

    // 如果購物車為空，導回購物車頁
    if (items.length === 0) {
        navigate('/cart');
        return null;
    }

    return (
        <div className="page checkout-page">
            <Header title="訂單預覽" showBack />

            <main className="page-content">
                {/* 取餐方式 */}
                <div className="checkout-section">
                    <h3 className="checkout-section__title">取餐方式</h3>
                    <div className="checkout-order-type">
                        <div>
                            <strong>{orderTypeLabels[orderType] || orderType}</strong>
                            {orderType === 'delivery' && <p>配送費 ${deliveryFee}</p>}
                            {orderType === 'pickup' && <p>台中市中區興中街20號</p>}
                            {orderType === 'dine_in' && <p>店內用餐</p>}
                        </div>
                    </div>
                </div>

                {/* 訂單明細 */}
                <div className="checkout-section">
                    <h3 className="checkout-section__title">訂單明細（{items.length} 項）</h3>

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
                                {item.notes && (
                                    <p className="checkout-item__customizations">
                                        備註：{item.notes}
                                    </p>
                                )}
                                <span className="checkout-item__price">${item.subtotal}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 金額明細 */}
                <div className="checkout-section">
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
                        <div className="checkout-summary__row checkout-summary__row--total">
                            <span>預估金額</span>
                            <span className="checkout-summary__total">${total}</span>
                        </div>
                    </div>
                </div>

                {/* 提示 */}
                <div className="checkout-section">
                    <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', textAlign: 'center' }}>
                        請確認訂單內容，下一步將填寫聯絡資訊並送出訂單
                    </p>
                </div>
            </main>

            {/* 底部按鈕 */}
            <div className="checkout-footer" style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
                <button
                    className="btn btn-lg"
                    onClick={() => navigate('/cart')}
                    style={{ flex: '0 0 auto', padding: '0 var(--spacing-lg)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
                >
                    修改
                </button>
                <button
                    className="btn btn-primary btn-lg btn-full"
                    onClick={() => navigate('/checkout')}
                >
                    確認無誤，前往結帳
                </button>
            </div>
        </div>
    );
}

export default OrderPreviewPage;
