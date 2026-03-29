/**
 * TypeScript 型別定義
 * 
 * 定義應用程式中使用的所有資料型別
 */

// ==================== 使用者相關 ====================

/** 使用者資料 */
export interface User {
  id: string;
  lineUserId: string;
  displayName: string | null;
  pictureUrl: string | null;
  phone: string | null;
  defaultAddress: string | null;
}

// ==================== 商品相關 ====================

/** 商品分類 */
export interface Category {
  id: string;
  name: string;
  description: string | null;
  imageUrl: string | null;
  productCount: number;
}

/** 客製化群組 */
export interface CustomizationGroup {
  id: string;
  name: string;
  groupType: 'single_select' | 'multi_select' | 'quantity_select';
  minSelect: number;
  maxSelect: number;
  isRequired: boolean;
  options: CustomizationOption[];
}

/** 客製化選項 */
export interface CustomizationOption {
  id: string;
  name: string;
  optionType: 'addon' | 'modifier';
  priceAdjustment: number;
  isDefault: boolean;
  groupId?: string | null;
}

/** 商品 */
export interface Product {
  id: string;
  name: string;
  description: string | null;
  price: number;
  salePrice: number | null;
  effectivePrice: number;
  imageUrl: string | null;
  categoryId: string | null;
  isAvailable: boolean;
  canOrder: boolean;
  dailyLimit: number;
  todaySold: number;
  isCombo: boolean;
  availablePeriods: { start: string; end: string; label: string }[] | null;
  saleStart: string | null;
  saleEnd: string | null;
  customizationOptions: CustomizationOption[];
  customizationGroups: CustomizationGroup[];
}

// ==================== 購物車相關 ====================

/** 購物車項目選中的客製化 */
export interface SelectedCustomization {
  id: string;
  name: string;
  price: number;
}

/** 購物車項目 */
export interface CartItem {
  product: Product;
  quantity: number;
  customizations: SelectedCustomization[];
  notes: string;
  /** 計算後的單價（含客製化加價） */
  unitPrice: number;
  /** 小計 */
  subtotal: number;
}

// ==================== 訂單相關 ====================

/** 訂單類型 */
export type OrderType = 'pickup' | 'delivery' | 'dine_in';

/** 訂單狀態 */
export type OrderStatus = 
  | 'pending'     // 待確認
  | 'confirmed'   // 已確認
  | 'preparing'   // 備餐中
  | 'ready'       // 待取餐
  | 'delivering'  // 配送中
  | 'completed'   // 已完成
  | 'cancelled';  // 已取消

/** 訂單狀態顯示文字對應 */
export const OrderStatusText: Record<OrderStatus, string> = {
  pending: '待確認',
  confirmed: '已確認',
  preparing: '備餐中',
  ready: '待取餐',
  delivering: '配送中',
  completed: '已完成',
  cancelled: '已取消',
};

/** 訂單狀態顏色對應 */
export const OrderStatusColor: Record<OrderStatus, string> = {
  pending: '#f59e0b',
  confirmed: '#3b82f6',
  preparing: '#8b5cf6',
  ready: '#10b981',
  delivering: '#06b6d4',
  completed: '#22c55e',
  cancelled: '#ef4444',
};

/** 訂單明細 */
export interface OrderItem {
  id: string;
  productId: string;
  productName: string;
  quantity: number;
  unitPrice: number;
  subtotal: number;
  customizations: SelectedCustomization[] | null;
  notes: string | null;
}

/** 訂單 */
export interface Order {
  id: string;
  orderNumber: string;
  orderType: OrderType;
  status: OrderStatus;
  subtotal: number;
  deliveryFee: number;
  discount: number;
  total: number;
  deliveryAddress: string | null;
  contactName: string | null;
  contactPhone: string | null;
  pickupTime: string | null;
  pickupNumber: number | null;
  notes: string | null;
  tableNumber: string | null;
  items: OrderItem[];
  createdAt: string;
  updatedAt: string;
}

// ==================== API 相關 ====================

/** API 回應基礎格式 */
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

/** 分頁列表回應 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

/** 建立訂單請求 */
export interface CreateOrderRequest {
  orderType: OrderType;
  items: {
    productId: string;
    quantity: number;
    customizations?: SelectedCustomization[];
    notes?: string;
  }[];
  deliveryAddress?: string;
  contactName?: string;
  contactPhone?: string;
  pickupTime?: string;
  notes?: string;
  tableNumber?: string;
  couponCode?: string;
  redeemPoints?: number;
}

// ==================== 忠誠度相關 ====================

/** 會員等級 */
export type LoyaltyTier = 'normal' | 'silver' | 'gold' | 'vip';

/** 忠誠度帳戶 */
export interface LoyaltyAccount {
  id: string;
  userId: string;
  pointsBalance: number;
  totalEarned: number;
  totalRedeemed: number;
  tier: LoyaltyTier;
}

/** 點數交易紀錄 */
export interface PointTransaction {
  id: string;
  points: number;
  transactionType: 'earn' | 'redeem' | 'bonus' | 'expire' | 'adjust';
  description: string | null;
  createdAt: string;
}

/** 等級名稱對應 */
export const LoyaltyTierText: Record<LoyaltyTier, string> = {
  normal: '一般會員',
  silver: '銀卡會員',
  gold: '金卡會員',
  vip: 'VIP 會員',
};

/** 等級顏色 */
export const LoyaltyTierColor: Record<LoyaltyTier, string> = {
  normal: '#6b7280',
  silver: '#9ca3af',
  gold: '#f59e0b',
  vip: '#8b5cf6',
};
