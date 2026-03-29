"""
Phase 3/4 更新

新增團購訂單、集點卡、推薦機制、角色權限資料表

Revision ID: 004_phase3_4_updates
Revises: 003_phase2_updates
Create Date: 2026-03-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# 版本識別
revision: str = '004_phase3_4_updates'
down_revision: Union[str, None] = '003_phase2_updates'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升級遷移 - Phase 3/4 資料表"""

    # ==================== 團購訂單主表 ====================
    op.create_table(
        'group_orders',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('creator_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='open'),
        sa.Column('order_id', sa.String(36), sa.ForeignKey('orders.id'), nullable=True),
        sa.Column('share_code', sa.String(20), unique=True, nullable=False, index=True),
        sa.Column('max_participants', sa.Integer, nullable=False, server_default='10'),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ==================== 團購參與者表 ====================
    op.create_table(
        'group_order_participants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('group_order_id', sa.String(36), sa.ForeignKey('group_orders.id'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('items', sa.JSON().with_variant(sa.Text, 'sqlite'), nullable=True),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('is_confirmed', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ==================== 集點卡範本表 ====================
    op.create_table(
        'stamp_card_templates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('stamps_required', sa.Integer, nullable=False, server_default='10'),
        sa.Column('reward_type', sa.String(20), nullable=False),
        sa.Column('reward_value', sa.Text, nullable=False),
        sa.Column('min_order_amount', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ==================== 集點卡實例表 ====================
    op.create_table(
        'stamp_cards',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('template_id', sa.String(36), sa.ForeignKey('stamp_card_templates.id'), nullable=False, index=True),
        sa.Column('stamps_collected', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_completed', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('is_reward_claimed', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ==================== 推薦記錄表 ====================
    op.create_table(
        'referrals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('referrer_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('referred_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('referral_code', sa.String(20), unique=True, nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('referrer_reward_type', sa.String(20), nullable=True),
        sa.Column('referrer_reward_value', sa.Text, nullable=True),
        sa.Column('referred_reward_type', sa.String(20), nullable=True),
        sa.Column('referred_reward_value', sa.Text, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ==================== 角色表 ====================
    op.create_table(
        'roles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(50), unique=True, nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_system', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ==================== 權限表 ====================
    op.create_table(
        'permissions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('code', sa.String(100), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
    )

    # ==================== 角色權限關聯表 ====================
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.String(36), sa.ForeignKey('roles.id'), primary_key=True),
        sa.Column('permission_id', sa.String(36), sa.ForeignKey('permissions.id'), primary_key=True),
    )


def downgrade() -> None:
    """降級遷移 - 移除 Phase 3/4 資料表"""

    # 先移除關聯表
    op.drop_table('role_permissions')

    # 移除權限與角色表
    op.drop_table('permissions')
    op.drop_table('roles')

    # 移除推薦記錄表
    op.drop_table('referrals')

    # 移除集點卡實例表（先，因 FK 指向 stamp_card_templates）
    op.drop_table('stamp_cards')

    # 移除集點卡範本表
    op.drop_table('stamp_card_templates')

    # 移除團購參與者表（先，因 FK 指向 group_orders）
    op.drop_table('group_order_participants')

    # 移除團購訂單主表
    op.drop_table('group_orders')
