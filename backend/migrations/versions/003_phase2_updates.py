"""
Phase 2 更新

新增客製化群組表、會員點數表
新增商品欄位：套餐、促銷、供應時段
新增訂單欄位：取餐號碼
新增客製化選項欄位：群組關聯

Revision ID: 003_phase2_updates
Revises: 002_phase1_updates
Create Date: 2026-03-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# 版本識別
revision: str = '003_phase2_updates'
down_revision: Union[str, None] = '002_phase1_updates'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升級遷移 - Phase 2 資料表與欄位"""

    # ==================== 客製化群組表 ====================
    op.create_table(
        'customization_groups',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('product_id', sa.String(36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('group_type', sa.String(20), nullable=False, server_default='single_select'),
        sa.Column('min_select', sa.Integer, nullable=False, server_default='0'),
        sa.Column('max_select', sa.Integer, nullable=False, server_default='1'),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_required', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='1'),
    )

    # ==================== 客製化選項：新增 group_id 欄位 ====================
    op.add_column(
        'customization_options',
        sa.Column('group_id', sa.String(36), sa.ForeignKey('customization_groups.id', ondelete='SET NULL'), nullable=True)
    )

    # ==================== 商品表：新增欄位 ====================
    op.add_column(
        'products',
        sa.Column('is_combo', sa.Boolean, nullable=False, server_default='0')
    )
    op.add_column(
        'products',
        sa.Column('combo_config', sa.JSON, nullable=True)
    )
    op.add_column(
        'products',
        sa.Column('available_periods', sa.JSON, nullable=True)
    )
    op.add_column(
        'products',
        sa.Column('sale_price', sa.Numeric(10, 2), nullable=True)
    )
    op.add_column(
        'products',
        sa.Column('sale_start', sa.DateTime, nullable=True)
    )
    op.add_column(
        'products',
        sa.Column('sale_end', sa.DateTime, nullable=True)
    )

    # ==================== 訂單表：新增取餐號碼 ====================
    op.add_column(
        'orders',
        sa.Column('pickup_number', sa.Integer, nullable=True)
    )

    # ==================== 會員點數帳戶表 ====================
    op.create_table(
        'loyalty_accounts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), unique=True, nullable=False, index=True),
        sa.Column('points_balance', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_earned', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_redeemed', sa.Integer, nullable=False, server_default='0'),
        sa.Column('tier', sa.String(20), nullable=False, server_default='normal'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ==================== 點數交易記錄表 ====================
    op.create_table(
        'point_transactions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('loyalty_account_id', sa.String(36), sa.ForeignKey('loyalty_accounts.id'), nullable=False, index=True),
        sa.Column('order_id', sa.String(36), sa.ForeignKey('orders.id'), nullable=True),
        sa.Column('points', sa.Integer, nullable=False),
        sa.Column('transaction_type', sa.String(20), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    """降級遷移 - 移除 Phase 2 資料表與欄位"""

    # 移除新建資料表（依相依順序）
    op.drop_table('point_transactions')
    op.drop_table('loyalty_accounts')

    # 移除訂單欄位
    op.drop_column('orders', 'pickup_number')

    # 移除商品欄位
    op.drop_column('products', 'sale_end')
    op.drop_column('products', 'sale_start')
    op.drop_column('products', 'sale_price')
    op.drop_column('products', 'available_periods')
    op.drop_column('products', 'combo_config')
    op.drop_column('products', 'is_combo')

    # 移除客製化選項欄位
    op.drop_column('customization_options', 'group_id')

    # 移除客製化群組表
    op.drop_table('customization_groups')
