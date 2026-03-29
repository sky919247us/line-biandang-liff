"""
Phase 1 更新

新增訂單欄位：table_number（內用桌號）、coupon_id（優惠券）
新增訂單類型：dine_in（內用，以字串儲存無需 DDL 變更）

Revision ID: 002_phase1_updates
Revises: 001_initial
Create Date: 2026-03-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# 版本識別
revision: str = '002_phase1_updates'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升級遷移 - 新增欄位"""

    # 新增桌號欄位（內用訂單用）
    op.add_column(
        'orders',
        sa.Column('table_number', sa.String(10), nullable=True)
    )

    # 新增優惠券關聯欄位
    op.add_column(
        'orders',
        sa.Column('coupon_id', sa.String(36), sa.ForeignKey('coupons.id'), nullable=True)
    )

    # 註：order_type 欄位以字串儲存，新增 "dine_in" 值無需 DDL 變更


def downgrade() -> None:
    """降級遷移 - 移除欄位"""
    op.drop_column('orders', 'coupon_id')
    op.drop_column('orders', 'table_number')
