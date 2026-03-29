/**
 * 購物車狀態管理
 * 
 * 使用 Zustand 管理購物車狀態
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { CartItem, Product, SelectedCustomization, OrderType } from '../types';

interface CartState {
    /** 購物車項目 */
    items: CartItem[];

    /** 訂單類型（自取/外送） */
    orderType: OrderType;

    /** 配送地址 */
    deliveryAddress: string;

    /** 聯絡人姓名 */
    contactName: string;

    /** 聯絡電話 */
    contactPhone: string;

    /** 預計取餐時間 */
    pickupTime: string;

    /** 訂單備註 */
    notes: string;

    /** 桌號（內用） */
    tableNumber: string;

    /** 優惠碼 */
    couponCode: string;

    /** 已套用折扣金額 */
    appliedDiscount: number;

    /** 計算總數量 */
    totalQuantity: () => number;

    /** 計算小計 */
    subtotal: () => number;

    /** 新增商品到購物車 */
    addItem: (
        product: Product,
        quantity: number,
        customizations: SelectedCustomization[],
        notes: string
    ) => void;

    /** 更新購物車項目數量 */
    updateQuantity: (index: number, quantity: number) => void;

    /** 移除購物車項目 */
    removeItem: (index: number) => void;

    /** 清空購物車 */
    clearCart: () => void;

    /** 設定訂單類型 */
    setOrderType: (type: OrderType) => void;

    /** 設定配送地址 */
    setDeliveryAddress: (address: string) => void;

    /** 設定聯絡人資訊 */
    setContactInfo: (name: string, phone: string) => void;

    /** 設定取餐時間 */
    setPickupTime: (time: string) => void;

    /** 設定備註 */
    setNotes: (notes: string) => void;

    /** 設定桌號 */
    setTableNumber: (tableNumber: string) => void;

    /** 設定優惠碼 */
    setCouponCode: (code: string) => void;

    /** 設定已套用折扣 */
    setAppliedDiscount: (discount: number) => void;

    /** 重置結帳資訊 */
    resetCheckoutInfo: () => void;
}

/**
 * 計算購物車項目的單價（含客製化加價）
 */
function calculateUnitPrice(product: Product, customizations: SelectedCustomization[]): number {
    const customizationTotal = customizations.reduce((sum, c) => sum + c.price, 0);
    return product.price + customizationTotal;
}

export const useCartStore = create<CartState>()(
    persist(
        (set, get) => ({
            items: [],
            orderType: 'pickup',
            deliveryAddress: '',
            contactName: '',
            contactPhone: '',
            pickupTime: '',
            notes: '',
            tableNumber: '',
            couponCode: '',
            appliedDiscount: 0,

            totalQuantity: () => {
                return get().items.reduce((sum, item) => sum + item.quantity, 0);
            },

            subtotal: () => {
                return get().items.reduce((sum, item) => sum + item.subtotal, 0);
            },

            addItem: (product, quantity, customizations, notes) => {
                const unitPrice = calculateUnitPrice(product, customizations);
                const subtotal = unitPrice * quantity;

                set((state) => ({
                    items: [
                        ...state.items,
                        {
                            product,
                            quantity,
                            customizations,
                            notes,
                            unitPrice,
                            subtotal,
                        },
                    ],
                }));
            },

            updateQuantity: (index, quantity) => {
                if (quantity <= 0) {
                    get().removeItem(index);
                    return;
                }

                set((state) => ({
                    items: state.items.map((item, i) => {
                        if (i === index) {
                            return {
                                ...item,
                                quantity,
                                subtotal: item.unitPrice * quantity,
                            };
                        }
                        return item;
                    }),
                }));
            },

            removeItem: (index) => {
                set((state) => ({
                    items: state.items.filter((_, i) => i !== index),
                }));
            },

            clearCart: () => {
                set({ items: [] });
            },

            setOrderType: (type) => {
                set({ orderType: type });
            },

            setDeliveryAddress: (address) => {
                set({ deliveryAddress: address });
            },

            setContactInfo: (name, phone) => {
                set({ contactName: name, contactPhone: phone });
            },

            setPickupTime: (time) => {
                set({ pickupTime: time });
            },

            setNotes: (notes) => {
                set({ notes });
            },

            setTableNumber: (tableNumber) => {
                set({ tableNumber });
            },

            setCouponCode: (code) => {
                set({ couponCode: code });
            },

            setAppliedDiscount: (discount) => {
                set({ appliedDiscount: discount });
            },

            resetCheckoutInfo: () => {
                set({
                    deliveryAddress: '',
                    contactName: '',
                    contactPhone: '',
                    pickupTime: '',
                    notes: '',
                    tableNumber: '',
                    couponCode: '',
                    appliedDiscount: 0,
                });
            },
        }),
        {
            name: 'biandang-cart', // localStorage key
            partialize: (state) => ({
                items: state.items,
                orderType: state.orderType,
            }),
        }
    )
);
