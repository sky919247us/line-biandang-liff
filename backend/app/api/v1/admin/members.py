"""
管理後台 - 會員 API

提供 CRM 會員列表、詳情、統計、角色管理及匯出功能
"""
import io
import csv
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, status
from starlette.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, case, desc

from app.api.deps import DbSession, CurrentAdmin
from app.models.user import User
from app.models.order import Order, OrderStatus


router = APIRouter(prefix="/members", tags=["Admin - Members"])


# ==================== Schemas ====================

class MemberListItem(BaseModel):
    """會員列表項目"""
    id: str
    display_name: Optional[str] = None
    picture_url: Optional[str] = None
    phone: Optional[str] = None
    role: str
    order_count: int
    total_spent: float
    last_order_at: Optional[datetime] = None
    created_at: datetime


class MemberListResponse(BaseModel):
    """會員列表回應"""
    members: List[MemberListItem]
    total: int
    skip: int
    limit: int


class OrderBrief(BaseModel):
    """訂單簡要資訊"""
    id: str
    order_number: str
    total: float
    status: str
    created_at: datetime


class MemberDetail(BaseModel):
    """會員詳情"""
    id: str
    line_user_id: str
    display_name: Optional[str] = None
    picture_url: Optional[str] = None
    phone: Optional[str] = None
    default_address: Optional[str] = None
    role: str
    order_count: int
    total_spent: float
    last_order_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    recent_orders: List[OrderBrief]


class MemberStats(BaseModel):
    """會員總覽統計"""
    total_members: int
    new_members_this_month: int
    active_members: int
    avg_order_value: float


class UpdateRoleRequest(BaseModel):
    """更新角色請求"""
    role: str


# ==================== API 端點 ====================

@router.get("/stats", response_model=MemberStats)
async def get_member_stats(
    db: DbSession,
    admin: CurrentAdmin,
):
    """
    取得會員總覽統計

    - total_members: 總會員數
    - new_members_this_month: 本月新增會員
    - active_members: 近 30 天有下單的會員
    - avg_order_value: 平均訂單金額
    """
    now = datetime.now()

    total_members = db.query(func.count(User.id)).scalar() or 0

    # 本月第一天
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_members_this_month = db.query(func.count(User.id)).filter(
        User.created_at >= month_start
    ).scalar() or 0

    # 近 30 天有下單（排除取消）
    thirty_days_ago = now - timedelta(days=30)
    active_members = db.query(func.count(func.distinct(Order.user_id))).filter(
        Order.created_at >= thirty_days_ago,
        Order.status != OrderStatus.CANCELLED.value,
    ).scalar() or 0

    # 平均訂單金額（排除取消）
    avg_order_value = db.query(func.avg(Order.total)).filter(
        Order.status != OrderStatus.CANCELLED.value,
    ).scalar()
    avg_order_value = float(avg_order_value) if avg_order_value else 0.0

    return MemberStats(
        total_members=total_members,
        new_members_this_month=new_members_this_month,
        active_members=active_members,
        avg_order_value=round(avg_order_value, 2),
    )


@router.get("/export")
async def export_members(
    db: DbSession,
    admin: CurrentAdmin,
):
    """
    匯出會員 CSV

    包含欄位：display_name, phone, role, order_count, total_spent, created_at
    """
    # 統計每位會員的訂單數與消費金額（排除取消）
    order_stats = (
        db.query(
            Order.user_id,
            func.count(Order.id).label("order_count"),
            func.coalesce(
                func.sum(
                    case(
                        (Order.status != OrderStatus.CANCELLED.value, Order.total),
                        else_=0,
                    )
                ),
                0,
            ).label("total_spent"),
        )
        .group_by(Order.user_id)
        .subquery()
    )

    rows = (
        db.query(
            User.display_name,
            User.phone,
            User.role,
            func.coalesce(order_stats.c.order_count, 0).label("order_count"),
            func.coalesce(order_stats.c.total_spent, 0).label("total_spent"),
            User.created_at,
        )
        .outerjoin(order_stats, User.id == order_stats.c.user_id)
        .order_by(User.created_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "display_name", "phone", "role", "order_count", "total_spent", "created_at"
    ])

    for row in rows:
        writer.writerow([
            row.display_name or "",
            row.phone or "",
            row.role,
            row.order_count,
            float(row.total_spent),
            row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else "",
        ])

    output.seek(0)

    # 加上 BOM 以便 Excel 正確顯示中文
    bom = "\ufeff"
    content = bom + output.getvalue()

    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=members_export.csv"},
    )


@router.get("/{user_id}", response_model=MemberDetail)
async def get_member_detail(
    user_id: str,
    db: DbSession,
    admin: CurrentAdmin,
):
    """
    取得單一會員詳情及最近 10 筆訂單
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="會員不存在",
        )

    # 統計（排除取消）
    stats = db.query(
        func.count(Order.id).label("order_count"),
        func.coalesce(
            func.sum(
                case(
                    (Order.status != OrderStatus.CANCELLED.value, Order.total),
                    else_=0,
                )
            ),
            0,
        ).label("total_spent"),
        func.max(Order.created_at).label("last_order_at"),
    ).filter(Order.user_id == user_id).first()

    # 最近 10 筆訂單
    recent_orders = (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )

    return MemberDetail(
        id=user.id,
        line_user_id=user.line_user_id,
        display_name=user.display_name,
        picture_url=user.picture_url,
        phone=user.phone,
        default_address=user.default_address,
        role=user.role,
        order_count=stats.order_count or 0,
        total_spent=float(stats.total_spent or 0),
        last_order_at=stats.last_order_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        recent_orders=[
            OrderBrief(
                id=o.id,
                order_number=o.order_number,
                total=float(o.total),
                status=o.status,
                created_at=o.created_at,
            )
            for o in recent_orders
        ],
    )


@router.get("", response_model=MemberListResponse)
async def list_members(
    db: DbSession,
    admin: CurrentAdmin,
    search: Optional[str] = Query(None, description="搜尋（顯示名稱或電話）"),
    sort_by: Optional[str] = Query(
        "created_at",
        description="排序欄位：created_at, order_count, total_spent",
    ),
    sort_order: Optional[str] = Query("desc", description="排序方向：asc, desc"),
    skip: int = Query(0, ge=0, description="跳過筆數"),
    limit: int = Query(20, ge=1, le=100, description="每頁數量"),
):
    """
    取得會員列表

    支援搜尋、分頁及排序（依建立時間、訂單數或消費金額）
    """
    # 子查詢：每位使用者的訂單統計（排除取消）
    order_stats = (
        db.query(
            Order.user_id,
            func.count(Order.id).label("order_count"),
            func.coalesce(
                func.sum(
                    case(
                        (Order.status != OrderStatus.CANCELLED.value, Order.total),
                        else_=0,
                    )
                ),
                0,
            ).label("total_spent"),
            func.max(Order.created_at).label("last_order_at"),
        )
        .group_by(Order.user_id)
        .subquery()
    )

    query = (
        db.query(
            User.id,
            User.display_name,
            User.picture_url,
            User.phone,
            User.role,
            func.coalesce(order_stats.c.order_count, 0).label("order_count"),
            func.coalesce(order_stats.c.total_spent, 0).label("total_spent"),
            order_stats.c.last_order_at.label("last_order_at"),
            User.created_at,
        )
        .outerjoin(order_stats, User.id == order_stats.c.user_id)
    )

    # 搜尋
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.display_name.ilike(search_term))
            | (User.phone.ilike(search_term))
        )

    # 總筆數
    total = query.count()

    # 排序
    sort_column_map = {
        "created_at": User.created_at,
        "order_count": "order_count",
        "total_spent": "total_spent",
    }
    sort_col = sort_column_map.get(sort_by, User.created_at)

    if sort_order == "asc":
        if isinstance(sort_col, str):
            query = query.order_by(sort_col)
        else:
            query = query.order_by(sort_col.asc())
    else:
        if isinstance(sort_col, str):
            query = query.order_by(desc(sort_col))
        else:
            query = query.order_by(sort_col.desc())

    rows = query.offset(skip).limit(limit).all()

    members = [
        MemberListItem(
            id=row.id,
            display_name=row.display_name,
            picture_url=row.picture_url,
            phone=row.phone,
            role=row.role,
            order_count=row.order_count,
            total_spent=float(row.total_spent),
            last_order_at=row.last_order_at,
            created_at=row.created_at,
        )
        for row in rows
    ]

    return MemberListResponse(
        members=members,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.patch("/{user_id}/role")
async def update_member_role(
    user_id: str,
    request: UpdateRoleRequest,
    db: DbSession,
    admin: CurrentAdmin,
):
    """
    更新會員角色

    有效角色：user, admin
    """
    valid_roles = ["user", "admin"]
    if request.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"無效的角色: {request.role}，有效角色為: {', '.join(valid_roles)}",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="會員不存在",
        )

    old_role = user.role
    user.role = request.role
    db.commit()

    return {
        "message": "會員角色已更新",
        "user_id": user.id,
        "old_role": old_role,
        "new_role": request.role,
    }
