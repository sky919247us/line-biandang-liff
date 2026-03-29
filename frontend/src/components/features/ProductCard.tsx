/**
 * ProductCard 商品卡片元件
 * 
 * 顯示單個商品資訊，支援加入購物車
 */
import { useState } from 'react';
import { useCartStore } from '../../stores/cartStore';
import { CustomizationSelector } from './CustomizationSelector';
import type { Product, SelectedCustomization } from '../../types';
import './ProductCard.css';

interface ProductCardProps {
    product: Product;
}

/**
 * 商品卡片元件
 */
export function ProductCard({ product }: ProductCardProps) {
    const [showModal, setShowModal] = useState(false);
    const [quantity, setQuantity] = useState(1);
    const [selectedCustomizations, setSelectedCustomizations] = useState<SelectedCustomization[]>([]);
    const [notes, setNotes] = useState('');

    const addItem = useCartStore((state) => state.addItem);

    // 計算單價（含客製化加價）
    const basePrice = product.effectivePrice ?? product.price;
    const customizationTotal = selectedCustomizations.reduce((sum, c) => sum + c.price, 0);
    const unitPrice = basePrice + customizationTotal;
    const subtotal = unitPrice * quantity;

    // Has customization groups or legacy options
    const hasGroups = product.customizationGroups && product.customizationGroups.length > 0;
    const ungroupedOptions = product.customizationOptions.filter(o => !o.groupId);
    const hasCustomizations = hasGroups || ungroupedOptions.length > 0;

    // 加入購物車
    const handleAddToCart = () => {
        addItem(product, quantity, selectedCustomizations, notes);
        setShowModal(false);
        // 重置狀態
        setQuantity(1);
        setSelectedCustomizations([]);
        setNotes('');
    };

    // 點擊卡片
    const handleCardClick = () => {
        if (product.canOrder) {
            setShowModal(true);
        }
    };

    return (
        <>
            <div
                className={`product-card ${!product.canOrder ? 'product-card--disabled' : ''}`}
                onClick={handleCardClick}
            >
                <div className="product-card__image">
                    {product.imageUrl ? (
                        <img src={product.imageUrl} alt={product.name} />
                    ) : (
                        <div className="product-card__image-placeholder">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <path d="M18 8h1a4 4 0 0 1 0 8h-1" />
                                <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z" />
                            </svg>
                        </div>
                    )}

                    {product.dailyLimit > 0 && (
                        <span className="product-card__badge">
                            限量 {product.dailyLimit - product.todaySold} 份
                        </span>
                    )}

                    {!product.canOrder && (
                        <div className="product-card__soldout">已售完</div>
                    )}
                </div>

                <div className="product-card__content">
                    <h3 className="product-card__name">{product.name}</h3>
                    {product.description && (
                        <p className="product-card__description">{product.description}</p>
                    )}
                    <div className="product-card__footer">
                        <span className="product-card__price">
                            {product.salePrice != null && product.salePrice < product.price ? (
                                <>
                                    <span className="product-card__original-price">${product.price}</span>
                                    ${product.effectivePrice}
                                </>
                            ) : (
                                `$${product.price}`
                            )}
                        </span>
                        <button
                            className="product-card__add-btn"
                            disabled={!product.canOrder}
                            onClick={(e) => {
                                e.stopPropagation();
                                if (hasCustomizations) {
                                    setShowModal(true);
                                } else {
                                    addItem(product, 1, [], '');
                                }
                            }}
                        >
                            +
                        </button>
                    </div>
                </div>
            </div>

            {/* 商品詳情 Modal */}
            {showModal && (
                <div className="product-modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="product-modal" onClick={(e) => e.stopPropagation()}>
                        {/* Modal Header */}
                        <div className="product-modal__header">
                            <h2 className="product-modal__title">{product.name}</h2>
                            <button
                                className="product-modal__close"
                                onClick={() => setShowModal(false)}
                            >
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <line x1="18" y1="6" x2="6" y2="18" />
                                    <line x1="6" y1="6" x2="18" y2="18" />
                                </svg>
                            </button>
                        </div>

                        {/* 商品資訊 */}
                        <div className="product-modal__info">
                            <p className="product-modal__description">{product.description}</p>
                            <span className="product-modal__price">
                                {product.salePrice != null && product.salePrice < product.price ? (
                                    <>
                                        <span className="product-card__original-price">${product.price}</span>
                                        ${product.effectivePrice}
                                    </>
                                ) : (
                                    `$${product.price}`
                                )}
                            </span>
                        </div>

                        {/* 客製化選項 */}
                        {hasCustomizations && (
                            <div className="product-modal__section">
                                <CustomizationSelector
                                    groups={product.customizationGroups || []}
                                    ungroupedOptions={ungroupedOptions}
                                    selectedCustomizations={selectedCustomizations}
                                    onChange={setSelectedCustomizations}
                                />
                            </div>
                        )}

                        {/* 備註 */}
                        <div className="product-modal__section">
                            <h4 className="product-modal__section-title">備註</h4>
                            <textarea
                                className="product-modal__notes"
                                placeholder="請輸入特殊需求..."
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                rows={2}
                            />
                        </div>

                        {/* 數量選擇 */}
                        <div className="product-modal__quantity">
                            <span className="product-modal__quantity-label">數量</span>
                            <div className="quantity-selector">
                                <button
                                    className="quantity-selector__btn"
                                    disabled={quantity <= 1}
                                    onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                                >
                                    −
                                </button>
                                <span className="quantity-selector__value">{quantity}</span>
                                <button
                                    className="quantity-selector__btn"
                                    onClick={() => setQuantity((q) => q + 1)}
                                >
                                    +
                                </button>
                            </div>
                        </div>

                        {/* 加入購物車按鈕 */}
                        <button
                            className="product-modal__add-btn btn btn-primary btn-lg btn-full"
                            onClick={handleAddToCart}
                        >
                            加入購物車 - ${subtotal}
                        </button>
                    </div>
                </div>
            )}
        </>
    );
}

export default ProductCard;
