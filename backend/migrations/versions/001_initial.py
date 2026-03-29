"""
初始資料庫遷移

建立所有基本資料表

Revision ID: 001
Revises: 
Create Date: 2026-02-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# 版本識別
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升級遷移 - 建立資料表"""
    
    # ==================== 使用者表 ====================
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('line_user_id', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('display_name', sa.String(128), nullable=True),
        sa.Column('picture_url', sa.String(512), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(128), nullable=True),
        sa.Column('default_address', sa.Text, nullable=True),
        sa.Column('role', sa.String(20), nullable=False, server_default='customer'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # ==================== 分類表 ====================
    op.create_table(
        'categories',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('image_url', sa.String(512), nullable=True),
        sa.Column('display_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # ==================== 商品表 ====================
    op.create_table(
        'products',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('category_id', sa.String(36), sa.ForeignKey('categories.id'), nullable=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('image_url', sa.String(512), nullable=True),
        sa.Column('daily_limit', sa.Integer, nullable=False, server_default='0'),
        sa.Column('today_sold', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_available', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('display_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # ==================== 客製化選項表 ====================
    op.create_table(
        'customization_options',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('product_id', sa.String(36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('option_type', sa.String(20), nullable=False, server_default='modifier'),
        sa.Column('price_adjustment', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('is_default', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('display_order', sa.Integer, nullable=False, server_default='0'),
    )
    
    # ==================== 物料表 ====================
    op.create_table(
        'materials',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('unit', sa.String(20), nullable=False),
        sa.Column('current_stock', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('safety_stock', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # ==================== 商品物料關聯表 (BOM) ====================
    op.create_table(
        'product_materials',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('product_id', sa.String(36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('material_id', sa.String(36), sa.ForeignKey('materials.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quantity', sa.Numeric(10, 3), nullable=False),
    )
    
    # ==================== 訂單表 ====================
    op.create_table(
        'orders',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('order_number', sa.String(32), unique=True, nullable=False, index=True),
        sa.Column('order_type', sa.String(20), nullable=False, server_default='pickup'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending', index=True),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False),
        sa.Column('delivery_fee', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('discount', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('total', sa.Numeric(10, 2), nullable=False),
        sa.Column('delivery_address', sa.Text, nullable=True),
        sa.Column('contact_name', sa.String(64), nullable=True),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('pickup_time', sa.String(16), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('cancelled_reason', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # ==================== 訂單項目表 ====================
    op.create_table(
        'order_items',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('order_id', sa.String(36), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.String(36), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('product_name', sa.String(128), nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False),
        sa.Column('customizations', sa.JSON, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
    )
    
    # ==================== 庫存異動記錄表 ====================
    op.create_table(
        'inventory_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('material_id', sa.String(36), sa.ForeignKey('materials.id'), nullable=False),
        sa.Column('change_type', sa.String(20), nullable=False),
        sa.Column('quantity', sa.Numeric(10, 3), nullable=False),
        sa.Column('before_stock', sa.Numeric(10, 2), nullable=False),
        sa.Column('after_stock', sa.Numeric(10, 2), nullable=False),
        sa.Column('reference_id', sa.String(36), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # ==================== 店家設定表 ====================
    op.create_table(
        'store_settings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('key', sa.String(64), unique=True, nullable=False),
        sa.Column('value', sa.Text, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    """降級遷移 - 刪除資料表"""
    op.drop_table('store_settings')
    op.drop_table('inventory_logs')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('product_materials')
    op.drop_table('materials')
    op.drop_table('customization_options')
    op.drop_table('products')
    op.drop_table('categories')
    op.drop_table('users')
