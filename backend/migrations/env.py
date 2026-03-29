"""
Alembic 遷移環境設定

設定資料庫連線和模型載入
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 載入應用程式設定和模型
from app.core.config import settings
from app.models.base import Base

# 載入所有模型以便 Alembic 自動偵測
from app.models import user, product, order, material

# Alembic Config 物件
config = context.config

# 設定資料庫 URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

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


def do_run_migrations(connection: Connection) -> None:
    """執行遷移"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """非同步模式遷移"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    線上模式遷移
    
    連接資料庫後執行遷移
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
