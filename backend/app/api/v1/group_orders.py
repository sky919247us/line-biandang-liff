"""
群組點餐 API 路由

處理群組點餐建立、加入、品項更新、鎖定與送出
"""
import logging
import random
import string
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import DbSession, CurrentUser
from app.models.group_order import GroupOrder, GroupOrderParticipant, GroupOrderStatus
from app.models.order import Order, OrderItem, OrderStatus, OrderType
from app.models.product import Product


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/group-orders", tags=["群組點餐"])


# ==================== Request / Response Schemas ====================

class GroupOrderCreate(BaseModel):
    """建立群組點餐請求"""
    title: str
    max_participants: Optional[int] = 10


class GroupOrderItemInput(BaseModel):
    """參與者品項"""
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    customizations: Optional[List[dict]] = None
    notes: Optional[str] = None


class GroupOrderItemsUpdate(BaseModel):
    """更新參與者品項請求"""
    items: List[GroupOrderItemInput]


class ParticipantResponse(BaseModel):
    """參與者回應"""
    id: str
    user_id: str
    display_name: Optional[str]
    items: Optional[list]
    subtotal: float
    is_confirmed: bool
    created_at: datetime


class GroupOrderResponse(BaseModel):
    """群組點餐回應"""
    id: str
    creator_id: str
    title: str
    status: str
    share_code: str
    max_participants: int
    total_amount: float
    expires_at: Optional[datetime]
    participants: List[ParticipantResponse]
    order_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class GroupOrderListResponse(BaseModel):
    """群組點餐列表回應"""
    items: List[GroupOrderResponse]
    total: int


# ==================== Helper Functions ====================

def generate_share_code() -> str:
    """產生 6 位英數字分享碼"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def build_group_order_response(group_order: GroupOrder) -> GroupOrderResponse:
    """將 GroupOrder ORM 物件轉為回應模型"""
    participants = [
        ParticipantResponse(
            id=p.id,
            user_id=p.user_id,
            display_name=p.display_name,
            items=p.items,
            subtotal=float(p.subtotal),
            is_confirmed=p.is_confirmed,
            created_at=p.created_at,
        )
        for p in group_order.participants
    ]
    return GroupOrderResponse(
        id=group_order.id,
        creator_id=group_order.creator_id,
        title=group_order.title,
        status=group_order.status,
        share_code=group_order.share_code,
        max_participants=group_order.max_participants,
        total_amount=float(group_order.total_amount),
        expires_at=group_order.expires_at,
        participants=participants,
        order_id=group_order.order_id,
        created_at=group_order.created_at,
        updated_at=group_order.updated_at,
    )


# ==================== Endpoints ====================

@router.get("/my", response_model=GroupOrderListResponse)
async def get_my_group_orders(
    current_user: CurrentUser,
    db: DbSession,
):
    """
    取得使用者的群組點餐列表

    包含使用者建立的和參與的群組點餐
    """
    # 使用者建立的群組點餐
    created = db.query(GroupOrder).filter(
        GroupOrder.creator_id == current_user.id
    ).all()

    # 使用者參與的群組點餐（但非建立者）
    participated_ids = db.query(GroupOrderParticipant.group_order_id).filter(
        GroupOrderParticipant.user_id == current_user.id
    ).scalar_subquery()

    participated = db.query(GroupOrder).filter(
        GroupOrder.id.in_(participated_ids),
        GroupOrder.creator_id != current_user.id,
    ).all()

    all_group_orders = created + participated
    # 依建立時間降序排列
    all_group_orders.sort(key=lambda g: g.created_at, reverse=True)

    items = [build_group_order_response(g) for g in all_group_orders]
    return GroupOrderListResponse(items=items, total=len(items))


@router.post("", response_model=GroupOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_group_order(
    request: GroupOrderCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    建立群組點餐

    建立者自動成為第一位參與者
    """
    # 產生唯一分享碼
    share_code = generate_share_code()
    while db.query(GroupOrder).filter(GroupOrder.share_code == share_code).first():
        share_code = generate_share_code()

    group_order = GroupOrder(
        creator_id=current_user.id,
        title=request.title,
        share_code=share_code,
        max_participants=request.max_participants or 10,
    )
    db.add(group_order)
    db.flush()

    # 建立者自動加入
    participant = GroupOrderParticipant(
        group_order_id=group_order.id,
        user_id=current_user.id,
        display_name=current_user.display_name,
    )
    db.add(participant)
    db.commit()
    db.refresh(group_order)

    return build_group_order_response(group_order)


@router.get("/{share_code}", response_model=GroupOrderResponse)
async def get_group_order(
    share_code: str,
    db: DbSession,
):
    """
    透過分享碼取得群組點餐詳情
    """
    group_order = db.query(GroupOrder).filter(
        GroupOrder.share_code == share_code
    ).first()

    if not group_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="群組點餐不存在",
        )

    return build_group_order_response(group_order)


@router.post("/{share_code}/join", response_model=GroupOrderResponse)
async def join_group_order(
    share_code: str,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    加入群組點餐
    """
    group_order = db.query(GroupOrder).filter(
        GroupOrder.share_code == share_code
    ).first()

    if not group_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="群組點餐不存在",
        )

    if group_order.status != GroupOrderStatus.OPEN.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="群組點餐已關閉，無法加入",
        )

    # 檢查是否已加入
    existing = db.query(GroupOrderParticipant).filter(
        GroupOrderParticipant.group_order_id == group_order.id,
        GroupOrderParticipant.user_id == current_user.id,
    ).first()

    if existing:
        # 已加入，直接回傳
        return build_group_order_response(group_order)

    # 檢查人數上限
    if len(group_order.participants) >= group_order.max_participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"群組點餐已達人數上限（{group_order.max_participants} 人）",
        )

    participant = GroupOrderParticipant(
        group_order_id=group_order.id,
        user_id=current_user.id,
        display_name=current_user.display_name,
    )
    db.add(participant)
    db.commit()
    db.refresh(group_order)

    return build_group_order_response(group_order)


@router.put("/{share_code}/items", response_model=GroupOrderResponse)
async def update_participant_items(
    share_code: str,
    request: GroupOrderItemsUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    更新參與者的點餐品項
    """
    group_order = db.query(GroupOrder).filter(
        GroupOrder.share_code == share_code
    ).first()

    if not group_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="群組點餐不存在",
        )

    if group_order.status not in (GroupOrderStatus.OPEN.value,):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="群組點餐已鎖定或已結束，無法修改品項",
        )

    participant = db.query(GroupOrderParticipant).filter(
        GroupOrderParticipant.group_order_id == group_order.id,
        GroupOrderParticipant.user_id == current_user.id,
    ).first()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您尚未加入此群組點餐",
        )

    # 計算小計
    subtotal = Decimal("0")
    items_data = []
    for item in request.items:
        item_subtotal = Decimal(str(item.unit_price)) * item.quantity
        subtotal += item_subtotal
        items_data.append({
            "product_id": item.product_id,
            "product_name": item.product_name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "subtotal": float(item_subtotal),
            "customizations": item.customizations,
            "notes": item.notes,
        })

    participant.items = items_data
    participant.subtotal = subtotal
    participant.is_confirmed = True

    db.commit()
    db.refresh(group_order)

    return build_group_order_response(group_order)


@router.post("/{share_code}/lock", response_model=GroupOrderResponse)
async def lock_group_order(
    share_code: str,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    鎖定群組點餐（僅建立者可操作）

    鎖定後不再接受新參與者或品項變更
    """
    group_order = db.query(GroupOrder).filter(
        GroupOrder.share_code == share_code
    ).first()

    if not group_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="群組點餐不存在",
        )

    if group_order.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有建立者可以鎖定群組點餐",
        )

    if group_order.status != GroupOrderStatus.OPEN.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="群組點餐狀態不允許鎖定",
        )

    group_order.status = GroupOrderStatus.LOCKED.value
    db.commit()
    db.refresh(group_order)

    return build_group_order_response(group_order)


@router.post("/{share_code}/submit", response_model=GroupOrderResponse)
async def submit_group_order(
    share_code: str,
    current_user: CurrentUser,
    db: DbSession,
):
    """
    送出群組點餐為正式訂單（僅建立者可操作）

    將所有參與者的品項合併為一筆正式訂單
    """
    group_order = db.query(GroupOrder).filter(
        GroupOrder.share_code == share_code
    ).first()

    if not group_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="群組點餐不存在",
        )

    if group_order.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有建立者可以送出群組點餐",
        )

    if group_order.status not in (GroupOrderStatus.OPEN.value, GroupOrderStatus.LOCKED.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="群組點餐狀態不允許送出",
        )

    # 檢查至少有一位參與者有品項
    confirmed_participants = [
        p for p in group_order.participants
        if p.items and len(p.items) > 0
    ]

    if not confirmed_participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="沒有任何參與者選擇品項，無法送出",
        )

    # 合併所有品項建立正式訂單
    from app.api.v1.orders import generate_order_number, generate_pickup_number

    total_subtotal = Decimal("0")
    all_order_items = []

    for participant in confirmed_participants:
        for item_data in participant.items:
            product = db.query(Product).filter(
                Product.id == item_data["product_id"],
                Product.is_active == True,
            ).first()

            if not product:
                logger.warning(f"群組點餐品項商品不存在: {item_data['product_id']}")
                continue

            unit_price = Decimal(str(item_data["unit_price"]))
            quantity = item_data["quantity"]
            item_subtotal = unit_price * quantity
            total_subtotal += item_subtotal

            all_order_items.append({
                "product": product,
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": item_subtotal,
                "customizations": item_data.get("customizations"),
                "notes": item_data.get("notes"),
            })

    if not all_order_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="所有品項的商品均已下架，無法送出",
        )

    # 建立訂單
    pickup_number = generate_pickup_number(db)

    order = Order(
        order_number=generate_order_number(db),
        user_id=current_user.id,
        order_type=OrderType.PICKUP.value,
        status=OrderStatus.PENDING.value,
        subtotal=total_subtotal,
        delivery_fee=Decimal("0"),
        discount=Decimal("0"),
        total=total_subtotal,
        contact_name=current_user.display_name,
        contact_phone=getattr(current_user, "phone", None),
        notes=f"群組點餐：{group_order.title}（{len(confirmed_participants)} 人）",
        pickup_number=pickup_number,
    )
    db.add(order)
    db.flush()

    # 建立訂單明細
    for item_data in all_order_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data["product"].id,
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            subtotal=item_data["subtotal"],
            customizations=item_data["customizations"],
            notes=item_data["notes"],
        )
        db.add(order_item)

    # 更新群組點餐狀態
    group_order.status = GroupOrderStatus.ORDERED.value
    group_order.order_id = order.id

    db.commit()
    db.refresh(group_order)

    return build_group_order_response(group_order)
