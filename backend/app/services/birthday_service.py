"""生日優惠自動發送服務"""
import logging
import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.coupon import Coupon, CouponType

logger = logging.getLogger(__name__)

def generate_birthday_coupon_code() -> str:
    """Generate unique birthday coupon code like BDAY-XXXX"""
    chars = string.ascii_uppercase + string.digits
    return f"BDAY-{''.join(random.choices(chars, k=6))}"

def create_birthday_coupon(db: Session, user: User) -> Coupon:
    """Create a birthday discount coupon for a user"""
    code = generate_birthday_coupon_code()
    # Ensure unique
    while db.query(Coupon).filter(Coupon.code == code).first():
        code = generate_birthday_coupon_code()

    coupon = Coupon(
        code=code,
        coupon_type=CouponType.PERCENTAGE.value,
        discount_value=15,  # 15% off birthday discount
        min_order_amount=0,
        max_uses=1,
        used_count=0,
        is_active=True,
        expires_at=datetime.now() + timedelta(days=30),  # Valid for 30 days
        description=f"{user.display_name or '會員'} 生日優惠券",
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    logger.info(f"Created birthday coupon {code} for user {user.id}")
    return coupon

def check_and_send_birthday_coupons(db: Session) -> int:
    """
    Check for users with birthdays today and send coupons.
    Returns count of coupons created.

    NOTE: Requires 'birthday' field on User model (future migration).
    Currently a no-op placeholder.
    """
    # Placeholder: When birthday field is added to User model,
    # query users whose birthday month/day matches today
    # and create coupons for them.
    today = datetime.now()
    logger.info(f"Birthday coupon check for {today.strftime('%m-%d')}: no birthday field yet")
    return 0
