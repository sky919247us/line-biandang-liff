/**
 * 管理後台 - 報表分析頁面
 */
import { useState, useEffect } from 'react';
import axios from 'axios';
import '../admin/AdminLayout.css';
import './AdminReports.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// ==================== 型別定義 ====================

interface SalesOverview {
    total_orders: number;
    total_revenue: number;
    avg_order_value: number;
    completed_orders: number;
    cancelled_orders: number;
}

interface DailySale {
    date: string;
    order_count: number;
    total_revenue: number;
    avg_order_value: number;
    pickup_count: number;
    delivery_count: number;
}

interface TopProduct {
    product_id: string;
    product_name: string;
    category_name: string;
    quantity_sold: number;
    total_revenue: number;
    order_count: number;
}

interface CategorySale {
    category_id: string;
    category_name: string;
    product_count: number;
    quantity_sold: number;
    total_revenue: number;
}

interface HourlySale {
    hour: number;
    order_count: number;
    total_revenue: number;
}

// ==================== 工具函式 ====================

function formatDate(date: Date): string {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

function formatCurrency(value: number): string {
    return `NT$ ${value.toLocaleString()}`;
}

function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
}

// ==================== 元件 ====================

export function AdminReports() {
    const today = new Date();
    const sevenDaysAgo = new Date(today);
    sevenDaysAgo.setDate(today.getDate() - 6);

    const [startDate, setStartDate] = useState(formatDate(sevenDaysAgo));
    const [endDate, setEndDate] = useState(formatDate(today));
    const [hourlyDate, setHourlyDate] = useState(formatDate(today));

    const [overview, setOverview] = useState<SalesOverview | null>(null);
    const [dailySales, setDailySales] = useState<DailySale[]>([]);
    const [topProducts, setTopProducts] = useState<TopProduct[]>([]);
    const [categorySales, setCategorySales] = useState<CategorySale[]>([]);
    const [hourlySales, setHourlySales] = useState<HourlySale[]>([]);

    const [loading, setLoading] = useState(false);
    const [hourlyLoading, setHourlyLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // 載入主要報表資料
    const fetchReports = async () => {
        setLoading(true);
        setError(null);
        const headers = getAuthHeaders();
        const params = { start_date: startDate, end_date: endDate };

        try {
            const [overviewRes, dailyRes, topRes, categoryRes] = await Promise.all([
                axios.get<SalesOverview>(`${API_BASE}/admin/reports/sales-overview`, { headers, params }),
                axios.get<DailySale[]>(`${API_BASE}/admin/reports/daily-sales`, { headers, params }),
                axios.get<TopProduct[]>(`${API_BASE}/admin/reports/top-products`, { headers, params: { ...params, limit: 10 } }),
                axios.get<CategorySale[]>(`${API_BASE}/admin/reports/category-sales`, { headers, params }),
            ]);
            setOverview(overviewRes.data);
            setDailySales(dailyRes.data);
            setTopProducts(topRes.data);
            setCategorySales(categoryRes.data);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : '載入報表資料失敗';
            setError(message);
        } finally {
            setLoading(false);
        }
    };

    // 載入每時銷售資料
    const fetchHourlySales = async () => {
        setHourlyLoading(true);
        const headers = getAuthHeaders();
        try {
            const res = await axios.get<HourlySale[]>(`${API_BASE}/admin/reports/hourly-sales`, {
                headers,
                params: { date: hourlyDate },
            });
            setHourlySales(res.data);
        } catch {
            setHourlySales([]);
        } finally {
            setHourlyLoading(false);
        }
    };

    useEffect(() => {
        fetchReports();
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        fetchHourlySales();
    }, [hourlyDate]); // eslint-disable-line react-hooks/exhaustive-deps

    // 計算長條圖最大值
    const maxHourlyOrders = Math.max(...hourlySales.map(h => h.order_count), 1);

    // 完成率
    const completionRate = overview && overview.total_orders > 0
        ? ((overview.completed_orders / overview.total_orders) * 100).toFixed(1)
        : '0.0';

    return (
        <div className="admin-reports">
            {/* 頁面標題 & 日期篩選 */}
            <div className="admin-page-header">
                <h1 className="admin-page-title">報表分析</h1>
                <div className="admin-reports__filters">
                    <div className="admin-reports__date-group">
                        <span className="admin-reports__date-label">起始</span>
                        <input
                            type="date"
                            className="admin-reports__date-input"
                            value={startDate}
                            onChange={e => setStartDate(e.target.value)}
                        />
                    </div>
                    <div className="admin-reports__date-group">
                        <span className="admin-reports__date-label">結束</span>
                        <input
                            type="date"
                            className="admin-reports__date-input"
                            value={endDate}
                            onChange={e => setEndDate(e.target.value)}
                        />
                    </div>
                    <button
                        className="admin-reports__query-btn"
                        onClick={fetchReports}
                        disabled={loading}
                    >
                        {loading ? '查詢中...' : '查詢'}
                    </button>
                </div>
            </div>

            {/* 錯誤訊息 */}
            {error && <div className="admin-reports__error">{error}</div>}

            {/* 銷售總覽 */}
            {loading ? (
                <div className="admin-reports__loading">載入中...</div>
            ) : overview ? (
                <>
                    <div className="admin-reports__overview">
                        <div className="admin-reports__stat-card">
                            <div className="admin-reports__stat-label">總訂單數</div>
                            <div className="admin-reports__stat-value">{overview.total_orders}</div>
                            <div className="admin-reports__stat-sub">
                                完成 {overview.completed_orders} / 取消 {overview.cancelled_orders}
                            </div>
                        </div>
                        <div className="admin-reports__stat-card">
                            <div className="admin-reports__stat-label">總營收</div>
                            <div className="admin-reports__stat-value admin-reports__stat-value--revenue">
                                {formatCurrency(overview.total_revenue)}
                            </div>
                        </div>
                        <div className="admin-reports__stat-card">
                            <div className="admin-reports__stat-label">平均客單價</div>
                            <div className="admin-reports__stat-value">
                                {formatCurrency(overview.avg_order_value)}
                            </div>
                        </div>
                        <div className="admin-reports__stat-card">
                            <div className="admin-reports__stat-label">完成率</div>
                            <div className="admin-reports__stat-value admin-reports__stat-value--success">
                                {completionRate}%
                            </div>
                        </div>
                    </div>

                    {/* 每日銷售 */}
                    <div className="admin-reports__section">
                        <div className="admin-reports__section-header">
                            <h2 className="admin-reports__section-title">每日銷售</h2>
                        </div>
                        <div className="admin-reports__table-wrap">
                            {dailySales.length > 0 ? (
                                <table className="admin-reports__table">
                                    <thead>
                                        <tr>
                                            <th>日期</th>
                                            <th className="admin-reports__cell--number">訂單數</th>
                                            <th className="admin-reports__cell--number">營收</th>
                                            <th className="admin-reports__cell--number">平均客單價</th>
                                            <th className="admin-reports__cell--number">自取</th>
                                            <th className="admin-reports__cell--number">外送</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {dailySales.map(day => (
                                            <tr key={day.date}>
                                                <td>{day.date}</td>
                                                <td className="admin-reports__cell--number">{day.order_count}</td>
                                                <td className="admin-reports__cell--number">{formatCurrency(day.total_revenue)}</td>
                                                <td className="admin-reports__cell--number">{formatCurrency(day.avg_order_value)}</td>
                                                <td className="admin-reports__cell--number">{day.pickup_count}</td>
                                                <td className="admin-reports__cell--number">{day.delivery_count}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            ) : (
                                <div className="admin-reports__empty">此區間無銷售資料</div>
                            )}
                        </div>
                    </div>

                    {/* 熱銷商品 */}
                    <div className="admin-reports__section">
                        <div className="admin-reports__section-header">
                            <h2 className="admin-reports__section-title">熱銷商品 TOP 10</h2>
                        </div>
                        <div className="admin-reports__table-wrap">
                            {topProducts.length > 0 ? (
                                <table className="admin-reports__table">
                                    <thead>
                                        <tr>
                                            <th>排名</th>
                                            <th>商品名稱</th>
                                            <th>分類</th>
                                            <th className="admin-reports__cell--number">銷售數量</th>
                                            <th className="admin-reports__cell--number">營收</th>
                                            <th className="admin-reports__cell--number">訂單數</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {topProducts.map((product, idx) => (
                                            <tr key={product.product_id}>
                                                <td>
                                                    <span className={`admin-reports__rank${idx < 3 ? ` admin-reports__rank--${idx + 1}` : ''}`}>
                                                        {idx + 1}
                                                    </span>
                                                </td>
                                                <td>{product.product_name}</td>
                                                <td>{product.category_name}</td>
                                                <td className="admin-reports__cell--number">{product.quantity_sold}</td>
                                                <td className="admin-reports__cell--number">{formatCurrency(product.total_revenue)}</td>
                                                <td className="admin-reports__cell--number">{product.order_count}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            ) : (
                                <div className="admin-reports__empty">此區間無商品銷售資料</div>
                            )}
                        </div>
                    </div>

                    {/* 分類銷售 */}
                    <div className="admin-reports__section">
                        <div className="admin-reports__section-header">
                            <h2 className="admin-reports__section-title">分類銷售</h2>
                        </div>
                        <div className="admin-reports__table-wrap">
                            {categorySales.length > 0 ? (
                                <table className="admin-reports__table">
                                    <thead>
                                        <tr>
                                            <th>分類名稱</th>
                                            <th className="admin-reports__cell--number">商品數</th>
                                            <th className="admin-reports__cell--number">銷售數量</th>
                                            <th className="admin-reports__cell--number">營收</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {categorySales.map(cat => (
                                            <tr key={cat.category_id}>
                                                <td>{cat.category_name}</td>
                                                <td className="admin-reports__cell--number">{cat.product_count}</td>
                                                <td className="admin-reports__cell--number">{cat.quantity_sold}</td>
                                                <td className="admin-reports__cell--number">{formatCurrency(cat.total_revenue)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            ) : (
                                <div className="admin-reports__empty">此區間無分類銷售資料</div>
                            )}
                        </div>
                    </div>
                </>
            ) : null}

            {/* 每時銷售長條圖 */}
            <div className="admin-reports__section">
                <div className="admin-reports__hourly">
                    <div className="admin-reports__hourly-header">
                        <h2 className="admin-reports__section-title">每時銷售分佈</h2>
                        <div className="admin-reports__hourly-date">
                            <span className="admin-reports__date-label">日期</span>
                            <input
                                type="date"
                                className="admin-reports__hourly-date-input"
                                value={hourlyDate}
                                onChange={e => setHourlyDate(e.target.value)}
                            />
                        </div>
                    </div>
                    {hourlyLoading ? (
                        <div className="admin-reports__loading">載入中...</div>
                    ) : hourlySales.length > 0 ? (
                        <div className="admin-reports__chart">
                            {hourlySales.map(h => (
                                <div className="admin-reports__bar-group" key={h.hour}>
                                    <div
                                        className="admin-reports__bar"
                                        style={{ height: `${(h.order_count / maxHourlyOrders) * 100}%` }}
                                    >
                                        <span className="admin-reports__bar-tooltip">
                                            {h.order_count} 單 / {formatCurrency(h.total_revenue)}
                                        </span>
                                    </div>
                                    <span className="admin-reports__bar-label">{String(h.hour).padStart(2, '0')}</span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="admin-reports__empty">該日無銷售資料</div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default AdminReports;
