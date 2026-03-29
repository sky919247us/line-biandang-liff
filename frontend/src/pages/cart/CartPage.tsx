/**
 * 購物車頁面
 */
import { useNavigate } from 'react-router-dom';
import { Header } from '../../components/layout/Header';
import { BottomNav } from '../../components/layout/BottomNav';
import { useCartStore } from '../../stores/cartStore';
import './CartPage.css';

export function CartPage() {
    const navigate = useNavigate();
    const {
        items,
        orderType,
        updateQuantity,
        removeItem,
        clearCart,
        setOrderType,
        subtotal
    } = useCartStore();

    const totalSubtotal = subtotal();
    const deliveryFee = orderType === 'delivery' ? 30 : 0;
    const total = totalSubtotal + deliveryFee;

    const handleCheckout = () => {
        if (items.length === 0) return;
        navigate('/checkout/preview');
    };

    if (items.length === 0) {
        return (
            <div className="page cart-page">
                <Header title="購物車" showBack={false} showCart={false} />

                <main className="page-content">
                    <div className="cart-empty">
                        <div className="cart-empty__icon">
                            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <circle cx="9" cy="21" r="1" />
                                <circle cx="20" cy="21" r="1" />
                                <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
                            </svg>
                        </div>
                        <h3 className="cart-empty__title">購物車是空的</h3>
                        <p className="cart-empty__description">快去挑選美味的便當吧！</p>
                        <button
                            className="btn btn-primary btn-lg"
                            onClick={() => navigate('/menu')}
                        >
                            立即點餐
                        </button>
                    </div>
                </main>

                <BottomNav />
            </div>
        );
    }

    return (
        <div className="page cart-page">
            <Header title="購物車" showBack={false} showCart={false} />

            <main className="page-content">
                {/* 取餐方式切換 */}
                <div className="cart-section">
                    <h3 className="cart-section__title">取餐方式</h3>
                    <div className="order-type-toggle">
                        <button
                            className={`order-type-toggle__btn ${orderType === 'pickup' ? 'active' : ''}`}
                            onClick={() => setOrderType('pickup')}
                        >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                <circle cx="12" cy="7" r="4" />
                            </svg>
                            到店自取
                        </button>
                        <button
                            className={`order-type-toggle__btn ${orderType === 'dine_in' ? 'active' : ''}`}
                            onClick={() => setOrderType('dine_in')}
                        >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M3 2l2 18h14l2-18" />
                                <path d="M8 2v4c0 2 2 3 4 3s4-1 4-3V2" />
                            </svg>
                            內用
                        </button>
                        <button
                            className={`order-type-toggle__btn ${orderType === 'delivery' ? 'active' : ''}`}
                            onClick={() => setOrderType('delivery')}
                        >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <rect x="1" y="3" width="15" height="13" />
                                <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
                                <circle cx="5.5" cy="18.5" r="2.5" />
                                <circle cx="18.5" cy="18.5" r="2.5" />
                            </svg>
                            外送
                        </button>
                    </div>
                </div>

                {/* 購物車項目 */}
                <div className="cart-section">
                    <div className="cart-section__header">
                        <h3 className="cart-section__title">已選商品</h3>
                        <button className="cart-clear-btn" onClick={clearCart}>
                            清空購物車
                        </button>
                    </div>

                    <div className="cart-items">
                        {items.map((item, index) => (
                            <div key={index} className="cart-item">
                                <div className="cart-item__info">
                                    <h4 className="cart-item__name">{item.product.name}</h4>
                                    {item.customizations.length > 0 && (
                                        <p className="cart-item__customizations">
                                            {item.customizations.map((c) => c.name).join('、')}
                                        </p>
                                    )}
                                    {item.notes && (
                                        <p className="cart-item__notes">備註：{item.notes}</p>
                                    )}
                                    <span className="cart-item__price">${item.unitPrice}</span>
                                </div>

                                <div className="cart-item__actions">
                                    <div className="quantity-selector">
                                        <button
                                            className="quantity-selector__btn"
                                            onClick={() => updateQuantity(index, item.quantity - 1)}
                                        >
                                            −
                                        </button>
                                        <span className="quantity-selector__value">{item.quantity}</span>
                                        <button
                                            className="quantity-selector__btn"
                                            onClick={() => updateQuantity(index, item.quantity + 1)}
                                        >
                                            +
                                        </button>
                                    </div>
                                    <button
                                        className="cart-item__remove"
                                        onClick={() => removeItem(index)}
                                    >
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <polyline points="3 6 5 6 21 6" />
                                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                                        </svg>
                                    </button>
                                </div>

                                <span className="cart-item__subtotal">${item.subtotal}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </main>

            {/* 結帳區塊 */}
            <div className="cart-checkout">
                <div className="cart-checkout__summary">
                    <div className="cart-checkout__row">
                        <span>商品小計</span>
                        <span>${totalSubtotal}</span>
                    </div>
                    {orderType === 'delivery' && (
                        <div className="cart-checkout__row">
                            <span>運費</span>
                            <span>${deliveryFee}</span>
                        </div>
                    )}
                    <div className="cart-checkout__row cart-checkout__row--total">
                        <span>合計</span>
                        <span className="cart-checkout__total">${total}</span>
                    </div>
                </div>

                <button
                    className="btn btn-primary btn-lg btn-full"
                    onClick={handleCheckout}
                >
                    前往結帳
                </button>
            </div>

            <BottomNav />
        </div>
    );
}

export default CartPage;
