/**
 * 管理後台 API 服務
 * 
 * 封裝所有管理後台相關的 API 呼叫
 */
import axios from 'axios';
import type { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// 建立 Admin API 客戶端
const adminClient: AxiosInstance = axios.create({
    baseURL: `${API_BASE_URL}/admin`,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// 請求攔截器 - 加入認證 Token
adminClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('admin_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// 回應攔截器 - 處理錯誤
adminClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // 未授權，可能需要重新登入
            localStorage.removeItem('admin_token');
            window.location.href = '/admin/login';
        }
        return Promise.reject(error);
    }
);

// ==================== 統計 API ====================

export interface DashboardStats {
    todayOrderCount: number;
    todayRevenue: number;
    pendingOrders: number;
    preparingOrders: number;
}

export async function getDashboardStats(): Promise<DashboardStats> {
    const response = await adminClient.get('/orders/stats');
    return {
        todayOrderCount: response.data.today_order_count,
        todayRevenue: response.data.today_revenue,
        pendingOrders: response.data.pending_orders,
        preparingOrders: response.data.preparing_orders,
    };
}

// ==================== 訂單 API ====================

export interface OrderItem {
    id: string;
    productId: string;
    productName: string;
    quantity: number;
    unitPrice: number;
    subtotal: number;
    customizations: { name: string; price: number }[] | null;
    notes: string | null;
}

export interface Order {
    id: string;
    orderNumber: string;
    orderType: 'pickup' | 'delivery';
    status: string;
    subtotal: number;
    deliveryFee: number;
    discount: number;
    total: number;
    deliveryAddress: string | null;
    contactName: string | null;
    contactPhone: string | null;
    pickupTime: string | null;
    notes: string | null;
    items: OrderItem[];
    createdAt: string;
    updatedAt: string;
}

export interface OrderListResponse {
    orders: Order[];
    total: number;
    page: number;
    pageSize: number;
}

export interface GetOrdersParams {
    status?: string;
    dateFrom?: string;
    dateTo?: string;
    page?: number;
    pageSize?: number;
}

export async function getOrders(params: GetOrdersParams = {}): Promise<OrderListResponse> {
    const response = await adminClient.get('/orders', {
        params: {
            status: params.status,
            date_from: params.dateFrom,
            date_to: params.dateTo,
            page: params.page || 1,
            page_size: params.pageSize || 20,
        },
    });

    return {
        orders: response.data.orders.map(mapOrderFromApi),
        total: response.data.total,
        page: response.data.page,
        pageSize: response.data.page_size,
    };
}

export async function getOrder(orderId: string): Promise<Order> {
    const response = await adminClient.get(`/orders/${orderId}`);
    return mapOrderFromApi(response.data);
}

export async function updateOrderStatus(orderId: string, status: string): Promise<void> {
    await adminClient.patch(`/orders/${orderId}/status`, { status });
}

export async function cancelOrder(orderId: string, reason?: string): Promise<void> {
    await adminClient.post(`/orders/${orderId}/cancel`, { reason });
}

// ==================== 商品 API ====================

export interface CustomizationOption {
    id: string;
    name: string;
    optionType: string;
    priceAdjustment: number;
}

export interface Product {
    id: string;
    categoryId: string | null;
    name: string;
    description: string | null;
    price: number;
    imageUrl: string | null;
    dailyLimit: number;
    todaySold: number;
    isAvailable: boolean;
    customizationOptions: CustomizationOption[];
}

export interface Category {
    id: string;
    name: string;
    description: string | null;
    imageUrl: string | null;
    productCount: number;
}

export async function getCategories(): Promise<Category[]> {
    const response = await adminClient.get('/products/categories');
    return response.data.map((cat: any) => ({
        id: cat.id,
        name: cat.name,
        description: cat.description,
        imageUrl: cat.image_url,
        productCount: cat.product_count,
    }));
}

export async function getProducts(categoryId?: string): Promise<Product[]> {
    const response = await adminClient.get('/products', {
        params: categoryId ? { category_id: categoryId } : undefined,
    });
    return response.data.map(mapProductFromApi);
}

export async function getProduct(productId: string): Promise<Product> {
    const response = await adminClient.get(`/products/${productId}`);
    return mapProductFromApi(response.data);
}

export async function toggleProductAvailability(productId: string): Promise<boolean> {
    const response = await adminClient.patch(`/products/${productId}/toggle-availability`);
    return response.data.is_available;
}

export async function resetProductSold(productId: string): Promise<void> {
    await adminClient.post(`/products/${productId}/reset-sold`);
}

export async function updateProduct(productId: string, data: Partial<Product>): Promise<Product> {
    const response = await adminClient.patch(`/products/${productId}`, {
        category_id: data.categoryId,
        name: data.name,
        description: data.description,
        price: data.price,
        image_url: data.imageUrl,
        daily_limit: data.dailyLimit,
        is_available: data.isAvailable,
    });
    return mapProductFromApi(response.data);
}

// ==================== 庫存 API ====================

export interface Material {
    id: string;
    name: string;
    unit: string;
    currentStock: number;
    safetyStock: number;
    isActive: boolean;
}

export interface InventoryStats {
    totalMaterials: number;
    lowStockCount: number;
    outOfStockCount: number;
}

export async function getInventoryStats(): Promise<InventoryStats> {
    const response = await adminClient.get('/inventory/stats');
    return {
        totalMaterials: response.data.total_materials,
        lowStockCount: response.data.low_stock_count,
        outOfStockCount: response.data.out_of_stock_count,
    };
}

export async function getMaterials(lowStockOnly = false): Promise<Material[]> {
    const response = await adminClient.get('/inventory', {
        params: { low_stock_only: lowStockOnly },
    });
    return response.data.map((mat: any) => ({
        id: mat.id,
        name: mat.name,
        unit: mat.unit,
        currentStock: mat.current_stock,
        safetyStock: mat.safety_stock,
        isActive: mat.is_active,
    }));
}

export async function adjustStock(materialId: string, quantity: number, notes?: string): Promise<Material> {
    const response = await adminClient.post(`/inventory/${materialId}/adjust`, {
        quantity,
        notes,
    });
    return {
        id: response.data.id,
        name: response.data.name,
        unit: response.data.unit,
        currentStock: response.data.current_stock,
        safetyStock: response.data.safety_stock,
        isActive: response.data.is_active,
    };
}

// ==================== 設定 API ====================

export interface StoreSettings {
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
}

export async function getSettings(): Promise<StoreSettings> {
    const response = await adminClient.get('/settings');
    return {
        storeName: response.data.store_name,
        phone: response.data.phone,
        address: response.data.address,
        openTime: response.data.open_time,
        closeTime: response.data.close_time,
        closedDays: response.data.closed_days,
        deliveryEnabled: response.data.delivery_enabled,
        deliveryFee: response.data.delivery_fee,
        freeDeliveryMinimum: response.data.free_delivery_minimum,
        deliveryRadius: response.data.delivery_radius,
    };
}

export async function updateSettings(settings: Partial<StoreSettings>): Promise<StoreSettings> {
    const response = await adminClient.patch('/settings', {
        store_name: settings.storeName,
        phone: settings.phone,
        address: settings.address,
        open_time: settings.openTime,
        close_time: settings.closeTime,
        closed_days: settings.closedDays,
        delivery_enabled: settings.deliveryEnabled,
        delivery_fee: settings.deliveryFee,
        free_delivery_minimum: settings.freeDeliveryMinimum,
        delivery_radius: settings.deliveryRadius,
    });
    return {
        storeName: response.data.store_name,
        phone: response.data.phone,
        address: response.data.address,
        openTime: response.data.open_time,
        closeTime: response.data.close_time,
        closedDays: response.data.closed_days,
        deliveryEnabled: response.data.delivery_enabled,
        deliveryFee: response.data.delivery_fee,
        freeDeliveryMinimum: response.data.free_delivery_minimum,
        deliveryRadius: response.data.delivery_radius,
    };
}

// ==================== Helper Functions ====================

function mapOrderFromApi(data: any): Order {
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
        notes: data.notes,
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

function mapProductFromApi(data: any): Product {
    return {
        id: data.id,
        categoryId: data.category_id,
        name: data.name,
        description: data.description,
        price: data.price,
        imageUrl: data.image_url,
        dailyLimit: data.daily_limit,
        todaySold: data.today_sold,
        isAvailable: data.is_available,
        customizationOptions: (data.customization_options || []).map((opt: any) => ({
            id: opt.id,
            name: opt.name,
            optionType: opt.option_type,
            priceAdjustment: opt.price_adjustment,
        })),
    };
}

export default adminClient;
