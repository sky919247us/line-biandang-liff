"""
資料庫連線模組

提供 SQLAlchemy 引擎和會話管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings


# 建立資料庫引擎
# NOTE: 若使用 SQLite，需要設定 check_same_thread=False
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=settings.debug,  # 開發模式時輸出 SQL 語句
)

# 建立會話工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """
    SQLAlchemy ORM 基礎類別
    
    所有模型都繼承自此類別
    """
    pass


def get_db():
    """
    取得資料庫會話
    
    用於 FastAPI 相依注入，確保會話正確關閉
    
    Yields:
        Session: 資料庫會話實例
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化資料庫
    
    建立所有資料表（開發用途，正式環境應使用 Alembic 遷移）
    """
    # 匯入所有模型以確保表格被註冊
    from app.models import user, product, order, material, coupon, loyalty, group_order, stamp_card, referral, permission  # noqa: F401
    
    Base.metadata.create_all(bind=engine)
