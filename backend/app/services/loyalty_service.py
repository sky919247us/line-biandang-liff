"""
會員點數服務

處理點數帳戶管理、點數獲得與兌換、會員等級更新
"""
import logging
import math
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.loyalty import LoyaltyAccount, PointTransaction


logger = logging.getLogger(__name__)


# 會員等級點數倍率
TIER_MULTIPLIERS = {
    "normal": 1.0,
    "silver": 1.2,
    "gold": 1.5,
    "vip": 2.0,
}

# 會員等級門檻（依累計獲得點數）
TIER_THRESHOLDS = {
    "normal": 0,
    "silver": 500,
    "gold": 1500,
    "vip": 5000,
}


class LoyaltyService:
    """
    會員點數服務

    負責處理：
    1. 點數帳戶建立與查詢
    2. 消費獲得點數（含等級倍率）
    3. 點數兌換折扣
    4. 會員等級自動升降
    5. 獎勵點數發放
    """

    def get_or_create_account(self, db: Session, user_id: str) -> LoyaltyAccount:
        """
        取得或建立點數帳戶

        Args:
            db: 資料庫會話
            user_id: 使用者 ID

        Returns:
            LoyaltyAccount: 點數帳戶
        """
        account = db.query(LoyaltyAccount).filter(
            LoyaltyAccount.user_id == user_id
        ).first()

        if not account:
            account = LoyaltyAccount(user_id=user_id)
            db.add(account)
            db.commit()
            db.refresh(account)
            logger.info(f"已建立使用者 {user_id} 的點數帳戶")

        return account

    def earn_points(
        self,
        db: Session,
        user_id: str,
        order_id: str,
        order_total: float
    ) -> PointTransaction:
        """
        消費獲得點數

        每消費 NT$10 獲得 1 點，依會員等級乘以倍率

        Args:
            db: 資料庫會話
            user_id: 使用者 ID
            order_id: 訂單 ID
            order_total: 訂單總金額

        Returns:
            PointTransaction: 點數交易紀錄
        """
        account = self.get_or_create_account(db, user_id)

        # 基本點數：每 NT$10 得 1 點（無條件捨去）
        base_points = int(order_total // 10)

        # 依會員等級乘以倍率（無條件捨去）
        multiplier = TIER_MULTIPLIERS.get(account.tier, 1.0)
        earned_points = int(math.floor(base_points * multiplier))

        if earned_points <= 0:
            # 金額太小不給點數，但仍建立紀錄
            earned_points = 0

        # 更新帳戶餘額
        account.points_balance += earned_points
        account.total_earned += earned_points

        # 建立交易紀錄
        transaction = PointTransaction(
            loyalty_account_id=account.id,
            transaction_type="earn",
            points=earned_points,
            order_id=order_id,
            description=f"消費 NT${order_total:.0f} 獲得點數（{account.tier} {multiplier}x）"
        )
        db.add(transaction)

        # 自動更新會員等級
        self.update_tier(db, user_id)

        db.commit()
        db.refresh(transaction)

        logger.info(
            f"使用者 {user_id} 消費 NT${order_total:.0f} 獲得 {earned_points} 點 "
            f"（等級: {account.tier}, 倍率: {multiplier}x）"
        )

        return transaction

    def redeem_points(
        self,
        db: Session,
        user_id: str,
        points: int,
        order_id: Optional[str] = None
    ) -> PointTransaction:
        """
        兌換點數折扣

        1 點 = NT$1 折扣

        Args:
            db: 資料庫會話
            user_id: 使用者 ID
            points: 兌換點數
            order_id: 關聯訂單 ID（可選）

        Returns:
            PointTransaction: 點數交易紀錄

        Raises:
            ValueError: 點數不足或兌換數量無效
        """
        if points <= 0:
            raise ValueError("兌換點數必須大於 0")

        account = self.get_or_create_account(db, user_id)

        if account.points_balance < points:
            raise ValueError(
                f"點數餘額不足，目前餘額 {account.points_balance} 點，"
                f"欲兌換 {points} 點"
            )

        # 扣除點數
        account.points_balance -= points
        account.total_redeemed += points

        # 建立交易紀錄
        transaction = PointTransaction(
            loyalty_account_id=account.id,
            transaction_type="redeem",
            points=-points,
            order_id=order_id,
            description=f"兌換 {points} 點折抵 NT${points}"
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        logger.info(f"使用者 {user_id} 兌換 {points} 點（折抵 NT${points}）")

        return transaction

    def get_balance(self, db: Session, user_id: str) -> int:
        """
        取得點數餘額

        Args:
            db: 資料庫會話
            user_id: 使用者 ID

        Returns:
            int: 點數餘額
        """
        account = self.get_or_create_account(db, user_id)
        return account.points_balance

    def get_transactions(
        self,
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[PointTransaction]:
        """
        取得點數交易紀錄

        Args:
            db: 資料庫會話
            user_id: 使用者 ID
            skip: 分頁偏移量
            limit: 取得數量

        Returns:
            list: 點數交易紀錄列表
        """
        account = self.get_or_create_account(db, user_id)

        transactions = db.query(PointTransaction).filter(
            PointTransaction.loyalty_account_id == account.id
        ).order_by(
            PointTransaction.created_at.desc()
        ).offset(skip).limit(limit).all()

        return transactions

    def update_tier(self, db: Session, user_id: str) -> None:
        """
        自動更新會員等級

        依累計獲得點數判定等級：
        - normal: 0 ~ 499 點
        - silver: 500 ~ 1499 點
        - gold: 1500 ~ 4999 點
        - vip: 5000 點以上

        Args:
            db: 資料庫會話
            user_id: 使用者 ID
        """
        account = self.get_or_create_account(db, user_id)
        total = account.total_earned

        if total >= TIER_THRESHOLDS["vip"]:
            new_tier = "vip"
        elif total >= TIER_THRESHOLDS["gold"]:
            new_tier = "gold"
        elif total >= TIER_THRESHOLDS["silver"]:
            new_tier = "silver"
        else:
            new_tier = "normal"

        if account.tier != new_tier:
            old_tier = account.tier
            account.tier = new_tier
            logger.info(
                f"使用者 {user_id} 會員等級變更: {old_tier} → {new_tier} "
                f"（累計點數: {total}）"
            )

    def add_bonus_points(
        self,
        db: Session,
        user_id: str,
        points: int,
        description: str
    ) -> PointTransaction:
        """
        發放獎勵點數

        Args:
            db: 資料庫會話
            user_id: 使用者 ID
            points: 獎勵點數
            description: 獎勵說明

        Returns:
            PointTransaction: 點數交易紀錄

        Raises:
            ValueError: 獎勵點數無效
        """
        if points <= 0:
            raise ValueError("獎勵點數必須大於 0")

        account = self.get_or_create_account(db, user_id)

        # 更新帳戶餘額
        account.points_balance += points
        account.total_earned += points

        # 建立交易紀錄
        transaction = PointTransaction(
            loyalty_account_id=account.id,
            transaction_type="bonus",
            points=points,
            description=description
        )
        db.add(transaction)

        # 自動更新會員等級
        self.update_tier(db, user_id)

        db.commit()
        db.refresh(transaction)

        logger.info(f"使用者 {user_id} 獲得獎勵點數 {points} 點: {description}")

        return transaction
