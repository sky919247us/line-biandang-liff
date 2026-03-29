"""
測試配置和 Fixtures

提供測試用的資料庫連線、測試客戶端和共用測試資料
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Generator
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.product import Product, Category
from app.models.material import Material, ProductMaterial
from app.models.coupon import Coupon, CouponType
from app.models.order import Order, OrderItem, OrderStatus


# 測試用記憶體資料庫
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆蓋資料庫依賴"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """
    建立測試資料庫會話
    
    每個測試函式有獨立的資料庫狀態
    """
    # 建立所有資料表
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # 清理所有資料表
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    """
    建立測試客戶端
    """
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session) -> User:
    """建立測試使用者"""
    user = User(
        line_user_id="U1234567890abcdef",
        display_name="測試使用者",
        picture_url="https://example.com/avatar.jpg",
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin(db_session) -> User:
    """建立測試管理員"""
    admin = User(
        line_user_id="U0987654321fedcba",
        display_name="測試管理員",
        picture_url="https://example.com/admin.jpg",
        role="admin"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def test_category(db_session) -> Category:
    """建立測試分類"""
    category = Category(
        id="cat-test",
        name="測試分類",
        description="測試用分類",
        sort_order=1,
        is_active=True
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def test_product(db_session, test_category) -> Product:
    """建立測試商品"""
    product = Product(
        id="prod-test-1",
        category_id=test_category.id,
        name="測試便當",
        description="測試用便當商品",
        price=Decimal("100"),
        daily_limit=50,
        today_sold=0,
        is_available=True,
        is_active=True
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def test_material(db_session) -> Material:
    """建立測試物料"""
    material = Material(
        id="mat-test-1",
        name="測試物料",
        description="測試用物料",
        unit="份",
        current_stock=Decimal("100"),
        safety_stock=Decimal("10"),
        unit_cost=Decimal("20")
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)
    return material


@pytest.fixture
def test_bom(db_session, test_product, test_material) -> ProductMaterial:
    """建立測試 BOM 對應"""
    bom = ProductMaterial(
        product_id=test_product.id,
        material_id=test_material.id,
        quantity=Decimal("1")
    )
    db_session.add(bom)
    db_session.commit()
    db_session.refresh(bom)
    return bom


@pytest.fixture
def test_coupon(db_session) -> Coupon:
    """建立測試優惠券"""
    coupon = Coupon(
        code="TEST100",
        name="測試優惠券",
        description="測試用優惠券",
        coupon_type=CouponType.FIXED.value,
        discount_value=Decimal("100"),
        min_order_amount=Decimal("200"),
        usage_limit=100,
        per_user_limit=1,
        valid_from=datetime.now() - timedelta(days=1),
        valid_until=datetime.now() + timedelta(days=30),
        is_active=True,
        used_count=0
    )
    db_session.add(coupon)
    db_session.commit()
    db_session.refresh(coupon)
    return coupon


@pytest.fixture
def test_order(db_session, test_user, test_product) -> Order:
    """建立測試訂單"""
    order = Order(
        user_id=test_user.id,
        order_number="TEST-20260207-001",
        order_type="pickup",
        status=OrderStatus.PENDING.value,
        subtotal=Decimal("100"),
        delivery_fee=Decimal("0"),
        discount=Decimal("0"),
        total=Decimal("100"),
        contact_name="測試",
        contact_phone="0912345678"
    )
    db_session.add(order)
    db_session.flush()
    
    order_item = OrderItem(
        order_id=order.id,
        product_id=test_product.id,
        quantity=1,
        unit_price=Decimal("100"),
        subtotal=Decimal("100")
    )
    db_session.add(order_item)
    db_session.commit()
    db_session.refresh(order)
    
    return order


# ===== Phase 3/4 新增 Fixtures =====

from app.models.stamp_card import StampCardTemplate, StampCard
from app.models.referral import Referral
from app.models.group_order import GroupOrder, GroupOrderParticipant


@pytest.fixture
def test_stamp_template(db_session) -> StampCardTemplate:
    """建立測試集點卡模板"""
    template = StampCardTemplate(
        name="測試集點卡",
        description="集滿10章送50點",
        stamps_required=10,
        reward_type="points",
        reward_value="50",
        min_order_amount=Decimal("100"),
        is_active=True,
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


@pytest.fixture
def test_stamp_card(db_session, test_user, test_stamp_template) -> StampCard:
    """建立測試集點卡（進行中）"""
    card = StampCard(
        user_id=test_user.id,
        template_id=test_stamp_template.id,
        stamps_collected=3,
        is_completed=False,
        is_reward_claimed=False,
    )
    db_session.add(card)
    db_session.commit()
    db_session.refresh(card)
    return card


@pytest.fixture
def test_completed_stamp_card(db_session, test_user, test_stamp_template) -> StampCard:
    """建立已集滿的集點卡"""
    from datetime import datetime
    card = StampCard(
        user_id=test_user.id,
        template_id=test_stamp_template.id,
        stamps_collected=10,
        is_completed=True,
        is_reward_claimed=False,
        completed_at=datetime.now(),
    )
    db_session.add(card)
    db_session.commit()
    db_session.refresh(card)
    return card


@pytest.fixture
def test_referral(db_session, test_user, test_admin) -> Referral:
    """建立測試推薦紀錄"""
    referral = Referral(
        referrer_id=test_admin.id,
        referred_id=test_user.id,
        referral_code="REF-TEST1",
        status="pending",
    )
    db_session.add(referral)
    db_session.commit()
    db_session.refresh(referral)
    return referral


@pytest.fixture
def test_group_order(db_session, test_user) -> GroupOrder:
    """建立測試群組點餐"""
    group_order = GroupOrder(
        creator_id=test_user.id,
        title="測試群組點餐",
        share_code="TSTG01",
        max_participants=5,
    )
    db_session.add(group_order)
    db_session.flush()

    participant = GroupOrderParticipant(
        group_order_id=group_order.id,
        user_id=test_user.id,
        display_name=test_user.display_name,
    )
    db_session.add(participant)
    db_session.commit()
    db_session.refresh(group_order)
    return group_order
