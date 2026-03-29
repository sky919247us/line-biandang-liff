"""
AI 智慧推薦服務

基於使用者消費習慣提供商品推薦
目前使用簡易協同過濾，未來可整合外部 ML API
"""
import logging
from typing import List, Dict, Optional
from collections import Counter

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product

logger = logging.getLogger(__name__)


class RecommendationService:
    """智慧推薦服務"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_recommendations(self, user_id: str, limit: int = 6) -> List[Dict]:
        """取得個人化推薦"""
        # 1. 取得使用者常買的商品
        user_products = (
            self.db.query(OrderItem.product_id, func.count().label("cnt"))
            .join(Order, Order.id == OrderItem.order_id)
            .filter(
                Order.user_id == user_id,
                Order.status != OrderStatus.CANCELLED.value,
            )
            .group_by(OrderItem.product_id)
            .all()
        )

        if not user_products:
            return self.get_popular_recommendations(limit)

        user_product_ids = {row.product_id for row in user_products}

        # 2. 找「也買了這些商品」的其他使用者
        similar_users = (
            self.db.query(Order.user_id)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .filter(
                OrderItem.product_id.in_(user_product_ids),
                Order.user_id != user_id,
                Order.status != OrderStatus.CANCELLED.value,
            )
            .distinct()
            .limit(50)
            .all()
        )

        similar_user_ids = [u.user_id for u in similar_users]

        if not similar_user_ids:
            return self.get_popular_recommendations(limit)

        # 3. 取得相似使用者買過但目前使用者沒買過的商品
        recommendations = (
            self.db.query(
                OrderItem.product_id,
                func.count().label("score"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .filter(
                Order.user_id.in_(similar_user_ids),
                ~OrderItem.product_id.in_(user_product_ids),
                Order.status != OrderStatus.CANCELLED.value,
            )
            .group_by(OrderItem.product_id)
            .order_by(desc("score"))
            .limit(limit)
            .all()
        )

        product_ids = [r.product_id for r in recommendations]
        products = self.db.query(Product).filter(
            Product.id.in_(product_ids),
            Product.is_active == True,
            Product.is_available == True,
        ).all()

        product_map = {p.id: p for p in products}
        result = []
        for r in recommendations:
            p = product_map.get(r.product_id)
            if p:
                result.append({
                    "id": p.id,
                    "name": p.name,
                    "price": float(p.price),
                    "image_url": p.image_url,
                    "reason": "similar_users",
                })

        return result[:limit]

    def get_popular_recommendations(self, limit: int = 6) -> List[Dict]:
        """取得熱門推薦（fallback）"""
        popular = (
            self.db.query(
                OrderItem.product_id,
                func.count().label("cnt"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.status != OrderStatus.CANCELLED.value)
            .group_by(OrderItem.product_id)
            .order_by(desc("cnt"))
            .limit(limit)
            .all()
        )

        product_ids = [r.product_id for r in popular]
        products = self.db.query(Product).filter(
            Product.id.in_(product_ids),
            Product.is_active == True,
        ).all()

        return [
            {
                "id": p.id,
                "name": p.name,
                "price": float(p.price),
                "image_url": p.image_url,
                "reason": "popular",
            }
            for p in products
        ]
