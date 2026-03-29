"""
Alembic 遷移環境設定

設定資料庫連線和模型載入
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# 載入應用程式設定和模型
from app.core.config import settings
from app.core.database import Base

# 載入所有模型以便 Alembic 自動偵測
from app.models import (  # noqa: F401
    user, product, order, material, coupon,
    loyalty, group_order, stamp_card, referral, permission,
)

# Alembic Config 物件
config = context.config

# 設定資料庫 URL
config.set_main_option("sqlalchemy.url", settings.database_url)

# 設定 logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目標 metadata（用於自動遷移產生）
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    離線模式遷移

    不需要資料庫連線，直接產生 SQL
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    線上模式遷移

    連接資料庫後執行遷移
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
