"""
管理後台 - 統計報表 API

提供訂單統計、銷售分析、熱門商品等報表功能
"""
from typing import List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.api.deps import DbSession, CurrentAdmin
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product, Category
from app.models.material import Material


router = APIRouter(prefix="/reports", tags=["Admin - Reports"])


# ==================== Schemas ====================

class DailySalesSchema(BaseModel):
    """每日銷售統計"""
    date: date
    order_count: int
    total_revenue: float
    avg_order_value: float
    pickup_count: int
    delivery_count: int


class ProductSalesSchema(BaseModel):
    """商品銷售統計"""
    product_id: str
    product_name: str
    category_name: Optional[str] = None
    quantity_sold: int
    total_revenue: float
    order_count: int


class CategorySalesSchema(BaseModel):
    """分類銷售統計"""
    category_id: str
    category_name: str
    product_count: int
    quantity_sold: int
    total_revenue: float


class HourlySalesSchema(BaseModel):
    """時段銷售統計"""
    hour: int
    order_count: int
    total_revenue: float


class OrderStatusSummarySchema(BaseModel):
    """訂單狀態統計"""
    status: str
    status_label: str
    count: int
    percentage: float


class SalesOverviewSchema(BaseModel):
    """銷售總覽"""
    period: str
    total_orders: int
    total_revenue: float
    avg_order_value: float
    completed_orders: int
    cancelled_orders: int
    completion_rate: float
    pickup_orders: int
    delivery_orders: int
    total_items_sold: int


class MaterialUsageSchema(BaseModel):
    """物料使用統計"""
    material_id: str
    material_name: str
    unit: str
    total_used: float
    estimated_cost: float
    related_products: int


# ==================== 輔助函式 ====================

STATUS_LABELS = {
    "pending": "待確認",
    "confirmed": "已確認",
    "preparing": "製作中",
    "ready": "可取餐",
    "delivering": "外送中",
    "completed": "已完成",
    "cancelled": "已取消"
}


def get_date_range(period: str) -> tuple[datetime, datetime]:
    """
    根據期間類型取得日期範圍
    
    Args:
        period: today, yesterday, week, month, year
        
    Returns:
        (start_datetime, end_datetime)
    """
    today = datetime.now().date()
    
    if period == "today":
        start_date = today
        end_date = today
    elif period == "yesterday":
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
    elif period == "week":
        start_date = today - timedelta(days=6)
        end_date = today
    elif period == "month":
        start_date = today - timedelta(days=29)
        end_date = today
    elif period == "year":
        start_date = today - timedelta(days=364)
        end_date = today
    else:
        start_date = today
        end_date = today
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    return start_datetime, end_datetime


# ==================== API 端點 ====================

@router.get("/overview", response_model=SalesOverviewSchema)
async def get_sales_overview(
    db: DbSession,
    admin: CurrentAdmin,
    period: str = Query("today", description="期間: today, yesterday, week, month, year"),
):
    """
    取得銷售總覽
    """
    start_dt, end_dt = get_date_range(period)
    
    orders = db.query(Order).filter(
        Order.created_at >= start_dt,
        Order.created_at <= end_dt
    ).all()
    
    total_orders = len(orders)
    completed = [o for o in orders if o.status == OrderStatus.COMPLETED.value]
    cancelled = [o for o in orders if o.status == OrderStatus.CANCELLED.value]
    pickup = [o for o in orders if o.order_type == "pickup"]
    delivery = [o for o in orders if o.order_type == "delivery"]
    
    # 計算營收（排除取消訂單）
    valid_orders = [o for o in orders if o.status != OrderStatus.CANCELLED.value]
    total_revenue = sum(float(o.total) for o in valid_orders)
    avg_order_value = total_revenue / len(valid_orders) if valid_orders else 0
    
    # 計算完成率
    completion_rate = len(completed) / total_orders * 100 if total_orders > 0 else 0
    
    # 計算總銷售數量
    total_items = 0
    for order in valid_orders:
        for item in order.items:
            total_items += item.quantity
    
    return SalesOverviewSchema(
        period=period,
        total_orders=total_orders,
        total_revenue=round(total_revenue, 2),
        avg_order_value=round(avg_order_value, 2),
        completed_orders=len(completed),
        cancelled_orders=len(cancelled),
        completion_rate=round(completion_rate, 1),
        pickup_orders=len(pickup),
        delivery_orders=len(delivery),
        total_items_sold=total_items
    )


@router.get("/daily-sales", response_model=List[DailySalesSchema])
async def get_daily_sales(
    db: DbSession,
    admin: CurrentAdmin,
    days: int = Query(7, ge=1, le=90, description="天數"),
):
    """
    取得每日銷售統計
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    result = []
    
    current_date = start_date
    while current_date <= end_date:
        start_dt = datetime.combine(current_date, datetime.min.time())
        end_dt = datetime.combine(current_date, datetime.max.time())
        
        orders = db.query(Order).filter(
            Order.created_at >= start_dt,
            Order.created_at <= end_dt,
            Order.status != OrderStatus.CANCELLED.value
        ).all()
        
        order_count = len(orders)
        total_revenue = sum(float(o.total) for o in orders)
        avg_order_value = total_revenue / order_count if order_count > 0 else 0
        pickup_count = len([o for o in orders if o.order_type == "pickup"])
        delivery_count = len([o for o in orders if o.order_type == "delivery"])
        
        result.append(DailySalesSchema(
            date=current_date,
            order_count=order_count,
            total_revenue=round(total_revenue, 2),
            avg_order_value=round(avg_order_value, 2),
            pickup_count=pickup_count,
            delivery_count=delivery_count
        ))
        
        current_date += timedelta(days=1)
    
    return result


@router.get("/hourly-sales", response_model=List[HourlySalesSchema])
async def get_hourly_sales(
    db: DbSession,
    admin: CurrentAdmin,
    target_date: Optional[date] = Query(None, description="目標日期，預設今日"),
):
    """
    取得時段銷售統計（按小時）
    """
    if target_date is None:
        target_date = datetime.now().date()
    
    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = datetime.combine(target_date, datetime.max.time())
    
    orders = db.query(Order).filter(
        Order.created_at >= start_dt,
        Order.created_at <= end_dt,
        Order.status != OrderStatus.CANCELLED.value
    ).all()
    
    # 按小時分組
    hourly_data = {}
    for hour in range(24):
        hourly_data[hour] = {"order_count": 0, "total_revenue": 0}
    
    for order in orders:
        hour = order.created_at.hour
        hourly_data[hour]["order_count"] += 1
        hourly_data[hour]["total_revenue"] += float(order.total)
    
    result = [
        HourlySalesSchema(
            hour=hour,
            order_count=data["order_count"],
            total_revenue=round(data["total_revenue"], 2)
        )
        for hour, data in hourly_data.items()
    ]
    
    return result


@router.get("/top-products", response_model=List[ProductSalesSchema])
async def get_top_products(
    db: DbSession,
    admin: CurrentAdmin,
    period: str = Query("week", description="期間: today, week, month"),
    limit: int = Query(10, ge=1, le=50, description="返回數量"),
):
    """
    取得熱門商品排行
    """
    start_dt, end_dt = get_date_range(period)
    
    # 查詢期間內的有效訂單項目
    order_items = db.query(OrderItem).join(Order).filter(
        Order.created_at >= start_dt,
        Order.created_at <= end_dt,
        Order.status != OrderStatus.CANCELLED.value
    ).all()
    
    # 按商品彙整
    product_stats = {}
    for item in order_items:
        pid = item.product_id
        if pid not in product_stats:
            product_stats[pid] = {
                "quantity_sold": 0,
                "total_revenue": 0,
                "order_count": 0,
                "order_ids": set()
            }
        product_stats[pid]["quantity_sold"] += item.quantity
        product_stats[pid]["total_revenue"] += float(item.subtotal)
        if item.order_id not in product_stats[pid]["order_ids"]:
            product_stats[pid]["order_ids"].add(item.order_id)
            product_stats[pid]["order_count"] += 1
    
    # 排序並取前 N
    sorted_products = sorted(
        product_stats.items(),
        key=lambda x: x[1]["quantity_sold"],
        reverse=True
    )[:limit]
    
    result = []
    for pid, stats in sorted_products:
        product = db.query(Product).filter(Product.id == pid).first()
        if product:
            result.append(ProductSalesSchema(
                product_id=pid,
                product_name=product.name,
                category_name=product.category.name if product.category else None,
                quantity_sold=stats["quantity_sold"],
                total_revenue=round(stats["total_revenue"], 2),
                order_count=stats["order_count"]
            ))
    
    return result


@router.get("/category-sales", response_model=List[CategorySalesSchema])
async def get_category_sales(
    db: DbSession,
    admin: CurrentAdmin,
    period: str = Query("week", description="期間: today, week, month"),
):
    """
    取得分類銷售統計
    """
    start_dt, end_dt = get_date_range(period)
    
    # 取得所有分類
    categories = db.query(Category).filter(Category.is_active == True).all()
    
    # 查詢期間內的有效訂單項目
    order_items = db.query(OrderItem).join(Order).filter(
        Order.created_at >= start_dt,
        Order.created_at <= end_dt,
        Order.status != OrderStatus.CANCELLED.value
    ).all()
    
    # 按分類彙整
    category_stats = {}
    for cat in categories:
        category_stats[cat.id] = {
            "category_name": cat.name,
            "product_count": 0,
            "quantity_sold": 0,
            "total_revenue": 0
        }
    
    # 計算各分類的商品數
    products = db.query(Product).filter(Product.is_active == True).all()
    for product in products:
        if product.category_id in category_stats:
            category_stats[product.category_id]["product_count"] += 1
    
    # 統計銷售
    for item in order_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product and product.category_id in category_stats:
            category_stats[product.category_id]["quantity_sold"] += item.quantity
            category_stats[product.category_id]["total_revenue"] += float(item.subtotal)
    
    result = [
        CategorySalesSchema(
            category_id=cid,
            category_name=stats["category_name"],
            product_count=stats["product_count"],
            quantity_sold=stats["quantity_sold"],
            total_revenue=round(stats["total_revenue"], 2)
        )
        for cid, stats in category_stats.items()
    ]
    
    # 按銷售量排序
    result.sort(key=lambda x: x.quantity_sold, reverse=True)
    
    return result


@router.get("/order-status", response_model=List[OrderStatusSummarySchema])
async def get_order_status_summary(
    db: DbSession,
    admin: CurrentAdmin,
    period: str = Query("today", description="期間: today, week, month"),
):
    """
    取得訂單狀態分布
    """
    start_dt, end_dt = get_date_range(period)
    
    orders = db.query(Order).filter(
        Order.created_at >= start_dt,
        Order.created_at <= end_dt
    ).all()
    
    total = len(orders)
    
    # 按狀態分組
    status_counts = {}
    for status in OrderStatus:
        status_counts[status.value] = 0
    
    for order in orders:
        status_counts[order.status] = status_counts.get(order.status, 0) + 1
    
    result = [
        OrderStatusSummarySchema(
            status=status,
            status_label=STATUS_LABELS.get(status, status),
            count=count,
            percentage=round(count / total * 100, 1) if total > 0 else 0
        )
        for status, count in status_counts.items()
        if count > 0  # 只顯示有訂單的狀態
    ]
    
    # 按數量排序
    result.sort(key=lambda x: x.count, reverse=True)
    
    return result


@router.get("/material-usage", response_model=List[MaterialUsageSchema])
async def get_material_usage(
    db: DbSession,
    admin: CurrentAdmin,
    period: str = Query("week", description="期間: today, week, month"),
):
    """
    取得物料使用統計
    """
    start_dt, end_dt = get_date_range(period)
    
    # 取得所有物料
    materials = db.query(Material).all()
    
    # 查詢期間內的有效訂單項目
    order_items = db.query(OrderItem).join(Order).filter(
        Order.created_at >= start_dt,
        Order.created_at <= end_dt,
        Order.status != OrderStatus.CANCELLED.value
    ).all()
    
    # 計算物料使用量
    material_usage = {}
    for mat in materials:
        material_usage[mat.id] = {
            "material_name": mat.name,
            "unit": mat.unit,
            "unit_cost": float(mat.unit_cost),
            "total_used": 0,
            "related_products": set()
        }
    
    from app.models.material import ProductMaterial
    
    for item in order_items:
        # 取得商品的 BOM
        bom_list = db.query(ProductMaterial).filter(
            ProductMaterial.product_id == item.product_id
        ).all()
        
        for bom in bom_list:
            if bom.material_id in material_usage:
                material_usage[bom.material_id]["total_used"] += float(bom.quantity) * item.quantity
                material_usage[bom.material_id]["related_products"].add(item.product_id)
    
    result = [
        MaterialUsageSchema(
            material_id=mid,
            material_name=stats["material_name"],
            unit=stats["unit"],
            total_used=round(stats["total_used"], 2),
            estimated_cost=round(stats["total_used"] * stats["unit_cost"], 2),
            related_products=len(stats["related_products"])
        )
        for mid, stats in material_usage.items()
        if stats["total_used"] > 0  # 只顯示有使用的物料
    ]
    
    # 按使用量排序
    result.sort(key=lambda x: x.total_used, reverse=True)
    
    return result


@router.get("/revenue-summary")
async def get_revenue_summary(
    db: DbSession,
    admin: CurrentAdmin,
):
    """
    取得營收摘要
    
    提供今日、本週、本月的營收對比
    """
    today = datetime.now().date()
    
    # 今日
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    today_orders = db.query(Order).filter(
        Order.created_at >= today_start,
        Order.created_at <= today_end,
        Order.status != OrderStatus.CANCELLED.value
    ).all()
    today_revenue = sum(float(o.total) for o in today_orders)
    
    # 本週
    week_start = datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time())
    week_orders = db.query(Order).filter(
        Order.created_at >= week_start,
        Order.created_at <= today_end,
        Order.status != OrderStatus.CANCELLED.value
    ).all()
    week_revenue = sum(float(o.total) for o in week_orders)
    
    # 本月
    month_start = datetime.combine(today.replace(day=1), datetime.min.time())
    month_orders = db.query(Order).filter(
        Order.created_at >= month_start,
        Order.created_at <= today_end,
        Order.status != OrderStatus.CANCELLED.value
    ).all()
    month_revenue = sum(float(o.total) for o in month_orders)
    
    # 昨日（用於對比）
    yesterday = today - timedelta(days=1)
    yesterday_start = datetime.combine(yesterday, datetime.min.time())
    yesterday_end = datetime.combine(yesterday, datetime.max.time())
    yesterday_orders = db.query(Order).filter(
        Order.created_at >= yesterday_start,
        Order.created_at <= yesterday_end,
        Order.status != OrderStatus.CANCELLED.value
    ).all()
    yesterday_revenue = sum(float(o.total) for o in yesterday_orders)
    
    # 計算成長率
    today_growth = ((today_revenue - yesterday_revenue) / yesterday_revenue * 100) if yesterday_revenue > 0 else 0
    
    return {
        "today": {
            "revenue": round(today_revenue, 2),
            "order_count": len(today_orders),
            "growth_rate": round(today_growth, 1)
        },
        "this_week": {
            "revenue": round(week_revenue, 2),
            "order_count": len(week_orders),
            "avg_daily": round(week_revenue / (today.weekday() + 1), 2)
        },
        "this_month": {
            "revenue": round(month_revenue, 2),
            "order_count": len(month_orders),
            "avg_daily": round(month_revenue / today.day, 2)
        }
    }
