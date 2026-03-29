/**
 * Header 頂部導航元件
 */
import { useNavigate, useLocation } from 'react-router-dom';
import { useCartStore } from '../../stores/cartStore';
import './Header.css';

interface HeaderProps {
    /** 頁面標題 */
    title?: string;
    /** 是否顯示返回按鈕 */
    showBack?: boolean;
    /** 是否顯示購物車按鈕 */
    showCart?: boolean;
    /** 自訂返回處理 */
    onBack?: () => void;
}

/**
 * 頂部導航元件
 * 
 * 提供頁面標題、返回按鈕和購物車入口
 */
export function Header({
    title = '便當訂購',
    showBack = false,
    showCart = true,
    onBack
}: HeaderProps) {
    const navigate = useNavigate();
    const location = useLocation();
    const totalQuantity = useCartStore((state) => state.totalQuantity());

    const handleBack = () => {
        if (onBack) {
            onBack();
        } else {
            navigate(-1);
        }
    };

    const handleCartClick = () => {
        navigate('/cart');
    };

    const isCartPage = location.pathname === '/cart';

    return (
        <header className="header">
            <div className="header__left">
                {showBack && (
                    <button className="header__back-btn" onClick={handleBack} aria-label="返回">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M19 12H5M12 19l-7-7 7-7" />
                        </svg>
                    </button>
                )}
            </div>

            <h1 className="header__title">{title}</h1>

            <div className="header__right">
                {showCart && !isCartPage && (
                    <button className="header__cart-btn" onClick={handleCartClick} aria-label="購物車">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="9" cy="21" r="1" />
                            <circle cx="20" cy="21" r="1" />
                            <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
                        </svg>
                        {totalQuantity > 0 && (
                            <span className="header__cart-badge">{totalQuantity}</span>
                        )}
                    </button>
                )}
            </div>
        </header>
    );
}

export default Header;
