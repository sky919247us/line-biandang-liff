/**
 * API 服務
 * 
 * 封裝所有後端 API 呼叫
 */
import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';
import type {
    User,
    Product,
    Category,
    Order,
    PaginatedResponse,
    CreateOrderRequest,
    LoyaltyAccount,
    PointTransaction,
} from '../types';

// API 基礎路徑
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// 建立 Axios 實例
const apiClient: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// 請求攔截器：加入認證 Token
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// 回應攔截器：處理錯誤
apiClient.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
        if (error.response?.status === 401) {
            // Token 失效，清除並重新導向登入
            localStorage.removeItem('access_token');
            // 可在此觸發重新登入邏輯
        }
        return Promise.reject(error);
    }
);

// ==================== 認證 API ====================

export const authApi = {
    /**
     * LINE Login 認證
     * @param lineAccessToken LINE Access Token
     */
    async login(lineAccessToken: string): Promise<{ accessToken: string; user: User }> {
        const response = await apiClient.post('/auth/login', {
            access_token: lineAccessToken,
        });
        return {
            accessToken: response.data.access_token,
            user: {
                id: response.data.user.id,
                lineUserId: response.data.user.line_user_id,
                displayName: response.data.user.display_name,
                pictureUrl: response.data.user.picture_url,
                phone: response.data.user.phone,
                defaultAddress: response.data.user.default_address,
            },
        };
    },

    /**
     * 取得當前使用者資訊
     */
    async getMe(): Promise<User> {
        const response = await apiClient.get('/auth/me');
        return {
            id: response.data.id,
            lineUserId: response.data.line_user_id,
            displayName: response.data.display_name,
            pictureUrl: response.data.picture_url,
            phone: response.data.phone,
            defaultAddress: response.data.default_address,
        };
    },

    /**
     * 更新個人資料
     */
    async updateProfile(data: { phone?: string; defaultAddress?: string }): Promise<User> {
        const response = await apiClient.patch('/auth/me', {
            phone: data.phone,
            default_address: data.defaultAddress,
        });
        return {
            id: response.data.id,
            lineUserId: response.data.line_user_id,
            displayName: response.data.display_name,
            pictureUrl: response.data.picture_url,
            phone: response.data.phone,
            defaultAddress: response.data.default_address,
        };
    },
};

/**
 * 轉換商品 API 回應格式
 */
function mapProductResponse(item: any): Product {
    return {
        id: item.id,
        name: item.name,
        description: item.description,
        price: item.price,
        salePrice: item.sale_price ?? null,
        effectivePrice: item.effective_price ?? item.price,
        imageUrl: item.image_url,
        categoryId: item.category_id,
        isAvailable: item.is_available,
        canOrder: item.can_order,
        dailyLimit: item.daily_limit,
        todaySold: item.today_sold,
        isCombo: item.is_combo ?? false,
        availablePeriods: item.available_periods ?? null,
        saleStart: item.sale_start ?? null,
        saleEnd: item.sale_end ?? null,
        customizationOptions: (item.customization_options || []).map((opt: any) => ({
            id: opt.id,
            name: opt.name,
            optionType: opt.option_type,
            priceAdjustment: opt.price_adjustment,
            isDefault: opt.is_default,
            groupId: opt.group_id ?? null,
        })),
        customizationGroups: (item.customization_groups || []).map((g: any) => ({
            id: g.id,
            name: g.name,
            groupType: g.group_type,
            minSelect: g.min_select,
            maxSelect: g.max_select,
            isRequired: g.is_required,
            options: (g.options || []).map((opt: any) => ({
                id: opt.id,
                name: opt.name,
                optionType: opt.option_type,
                priceAdjustment: opt.price_adjustment,
                isDefault: opt.is_default,
                groupId: g.id,
            })),
        })),
    };
}

// ==================== 商品 API ====================

export const productApi = {
    /**
     * 取得商品列表
     */
    async getProducts(params?: {
        categoryId?: string;
        search?: string;
        availableOnly?: boolean;
        skip?: number;
        limit?: number;
    }): Promise<PaginatedResponse<Product>> {
        const response = await apiClient.get('/products', {
            params: {
                category_id: params?.categoryId,
                search: params?.search,
                available_only: params?.availableOnly ?? true,
                skip: params?.skip ?? 0,
                limit: params?.limit ?? 20,
            },
        });
        return {
            items: response.data.items.map(mapProductResponse),
            total: response.data.total,
        };
    },

    /**
     * 取得熱銷商品
     */
    async getPopularProducts(limit: number = 6): Promise<Product[]> {
        const response = await apiClient.get('/products/popular', {
            params: { limit },
        });
        return response.data.items.map(mapProductResponse);
    },

    /**
     * 取得商品詳情
     */
    async getProduct(productId: string): Promise<Product> {
        const response = await apiClient.get(`/products/${productId}`);
        return mapProductResponse(response.data);
    },

    /**
     * 取得分類列表
     */
    async getCategories(): Promise<Category[]> {
        const response = await apiClient.get('/products/categories');
        return response.data.items.map((item: any) => ({
            id: item.id,
            name: item.name,
            description: item.description,
            imageUrl: item.image_url,
            productCount: item.product_count,
        }));
    },
};

// ==================== 優惠券 API ====================

export const couponApi = {
    /**
     * 驗證優惠碼
     */
    async validate(code: string, orderAmount: number): Promise<{ discountAmount: number; couponId: string }> {
        const response = await apiClient.post('/coupons/validate', {
            code,
            order_amount: orderAmount,
        });
        return {
            discountAmount: response.data.discount_amount,
            couponId: response.data.coupon_id,
        };
    },
};

// ==================== 訂單 API ====================

export const orderApi = {
    /**
     * 建立訂單
     */
    async createOrder(data: CreateOrderRequest): Promise<Order> {
        const response = await apiClient.post('/orders', {
            order_type: data.orderType,
            items: data.items.map((item) => ({
                product_id: item.productId,
                quantity: item.quantity,
                customizations: item.customizations,
                notes: item.notes,
            })),
            delivery_address: data.deliveryAddress,
            contact_name: data.contactName,
            contact_phone: data.contactPhone,
            pickup_time: data.pickupTime,
            notes: data.notes,
            table_number: data.tableNumber,
            coupon_code: data.couponCode,
        });
        return mapOrderResponse(response.data);
    },

    /**
     * 取得訂單列表
     */
    async getOrders(params?: {
        status?: string;
        skip?: number;
        limit?: number;
    }): Promise<PaginatedResponse<Order>> {
        const response = await apiClient.get('/orders', {
            params: {
                status_filter: params?.status,
                skip: params?.skip ?? 0,
                limit: params?.limit ?? 20,
            },
        });
        return {
            items: response.data.items.map(mapOrderResponse),
            total: response.data.total,
        };
    },

    /**
     * 取得訂單詳情
     */
    async getOrder(orderId: string): Promise<Order> {
        const response = await apiClient.get(`/orders/${orderId}`);
        return mapOrderResponse(response.data);
    },

    /**
     * 取消訂單
     */
    async cancelOrder(orderId: string, reason?: string): Promise<void> {
        await apiClient.patch(`/orders/${orderId}/cancel`, null, {
            params: { reason },
        });
    },
};

// ==================== 忠誠度 API ====================

export const loyaltyApi = {
    /** 取得忠誠度帳戶 */
    async getAccount(): Promise<LoyaltyAccount> {
        const response = await apiClient.get('/loyalty/account');
        return {
            id: response.data.id,
            userId: response.data.user_id,
            pointsBalance: response.data.points_balance,
            totalEarned: response.data.total_earned,
            totalRedeemed: response.data.total_redeemed,
            tier: response.data.tier,
        };
    },

    /** 取得點數交易紀錄 */
    async getTransactions(params?: { skip?: number; limit?: number }): Promise<PaginatedResponse<PointTransaction>> {
        const response = await apiClient.get('/loyalty/transactions', {
            params: {
                skip: params?.skip ?? 0,
                limit: params?.limit ?? 20,
            },
        });
        return {
            items: response.data.items.map((t: any) => ({
                id: t.id,
                points: t.points,
                transactionType: t.transaction_type,
                description: t.description,
                createdAt: t.created_at,
            })),
            total: response.data.total,
        };
    },

    /** 兌換點數 */
    async redeemPoints(points: number): Promise<{ discountAmount: number }> {
        const response = await apiClient.post('/loyalty/redeem', { points });
        return { discountAmount: response.data.discount_amount };
    },
};

/**
 * 轉換訂單 API 回應格式
 */
function mapOrderResponse(data: any): Order {
    return {
        id: data.id,
        orderNumber: data.order_number,
        orderType: data.order_type,
        status: data.status,
        subtotal: data.subtotal,
        deliveryFee: data.delivery_fee,
        discount: data.discount,
        total: data.total,
        deliveryAddress: data.delivery_address,
        contactName: data.contact_name,
        contactPhone: data.contact_phone,
        pickupTime: data.pickup_time,
        pickupNumber: data.pickup_number ?? null,
        notes: data.notes,
        tableNumber: data.table_number || null,
        items: data.items.map((item: any) => ({
            id: item.id,
            productId: item.product_id,
            productName: item.product_name,
            quantity: item.quantity,
            unitPrice: item.unit_price,
            subtotal: item.subtotal,
            customizations: item.customizations,
            notes: item.notes,
        })),
        createdAt: data.created_at,
        updatedAt: data.updated_at,
    };
}

// ==================== 管理後台 API ====================

export const adminApi = {
    /** 取得今日訂單列表 */
    async getOrders(params?: {
        status?: string;
        search?: string;
        skip?: number;
        limit?: number;
    }): Promise<{ items: Order[]; total: number }> {
        const response = await apiClient.get('/admin/orders', { params });
        return {
            items: response.data.items.map(mapOrderResponse),
            total: response.data.total,
        };
    },

    /** 更新訂單狀態 */
    async updateOrderStatus(orderId: string, status: string): Promise<void> {
        await apiClient.patch(`/admin/orders/${orderId}/status`, { status });
    },
};

// ==================== 群組點餐 API ====================

export const groupOrderApi = {
    /** 取得我的群組點餐 */
    async getMyGroupOrders(): Promise<{ items: any[]; total: number }> {
        const response = await apiClient.get('/group-orders/my');
        return response.data;
    },

    /** 建立群組點餐 */
    async create(data: { title: string; max_participants?: number }): Promise<any> {
        const response = await apiClient.post('/group-orders', data);
        return response.data;
    },

    /** 取得群組點餐詳情 */
    async getByCode(shareCode: string): Promise<any> {
        const response = await apiClient.get(`/group-orders/${shareCode}`);
        return response.data;
    },

    /** 加入群組點餐 */
    async join(shareCode: string): Promise<any> {
        const response = await apiClient.post(`/group-orders/${shareCode}/join`);
        return response.data;
    },

    /** 更新品項 */
    async updateItems(shareCode: string, items: any[]): Promise<any> {
        const response = await apiClient.put(`/group-orders/${shareCode}/items`, { items });
        return response.data;
    },

    /** 鎖定群組點餐 */
    async lock(shareCode: string): Promise<any> {
        const response = await apiClient.post(`/group-orders/${shareCode}/lock`);
        return response.data;
    },

    /** 送出群組點餐 */
    async submit(shareCode: string): Promise<any> {
        const response = await apiClient.post(`/group-orders/${shareCode}/submit`);
        return response.data;
    },
};

// ==================== 集點卡 API ====================

export const stampCardApi = {
    async getTemplates(): Promise<any[]> {
        const response = await apiClient.get('/stamp-cards/templates');
        return response.data;
    },
    async getMyCards(): Promise<any[]> {
        const response = await apiClient.get('/stamp-cards/my');
        return response.data;
    },
    async startCard(templateId: string): Promise<any> {
        const response = await apiClient.post('/stamp-cards/start', { template_id: templateId });
        return response.data;
    },
    async claimReward(cardId: string): Promise<any> {
        const response = await apiClient.post(`/stamp-cards/${cardId}/claim`);
        return response.data;
    },
};

// ==================== 推薦好友 API ====================

export const referralApi = {
    async getMyCode(): Promise<{ referral_code: string; total_referrals: number; completed_referrals: number }> {
        const response = await apiClient.get('/referrals/my-code');
        return response.data;
    },
    async getMyReferrals(): Promise<any[]> {
        const response = await apiClient.get('/referrals/my-referrals');
        return response.data;
    },
    async applyCode(code: string): Promise<any> {
        const response = await apiClient.post('/referrals/apply', { code });
        return response.data;
    },
};

export default apiClient;
