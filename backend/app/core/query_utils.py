"""
查詢優化工具

提供常用的資料庫查詢優化功能
"""
from typing import TypeVar, Generic, List, Optional, Any
from dataclasses import dataclass

from sqlalchemy.orm import Session, Query
from sqlalchemy import func


T = TypeVar("T")


@dataclass
class PaginatedResult(Generic[T]):
    """
    分頁結果
    """
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


def paginate(
    query: Query,
    page: int = 1,
    page_size: int = 20
) -> PaginatedResult:
    """
    對查詢結果進行分頁
    
    Args:
        query: SQLAlchemy 查詢物件
        page: 頁碼（從 1 開始）
        page_size: 每頁筆數
        
    Returns:
        PaginatedResult: 分頁結果
    """
    # 確保頁碼和頁面大小有效
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    
    # 計算總筆數
    total = query.count()
    
    # 計算總頁數
    total_pages = (total + page_size - 1) // page_size
    
    # 調整頁碼不超過總頁數
    page = min(page, max(1, total_pages))
    
    # 取得分頁資料
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


def bulk_insert(
    db: Session,
    model_class: Any,
    data_list: List[dict],
    batch_size: int = 100
) -> int:
    """
    批量插入資料
    
    Args:
        db: 資料庫會話
        model_class: 模型類別
        data_list: 資料列表
        batch_size: 每批次插入筆數
        
    Returns:
        int: 插入的總筆數
    """
    total_inserted = 0
    
    for i in range(0, len(data_list), batch_size):
        batch = data_list[i:i + batch_size]
        objects = [model_class(**data) for data in batch]
        db.bulk_save_objects(objects)
        total_inserted += len(batch)
    
    db.commit()
    return total_inserted


def bulk_update(
    db: Session,
    model_class: Any,
    updates: List[dict],
    id_field: str = "id"
) -> int:
    """
    批量更新資料
    
    Args:
        db: 資料庫會話
        model_class: 模型類別
        updates: 更新資料列表（必須包含 ID）
        id_field: ID 欄位名稱
        
    Returns:
        int: 更新的總筆數
    """
    total_updated = 0
    
    for update_data in updates:
        obj_id = update_data.pop(id_field, None)
        if obj_id is None:
            continue
        
        result = db.query(model_class).filter(
            getattr(model_class, id_field) == obj_id
        ).update(update_data, synchronize_session=False)
        
        total_updated += result
    
    db.commit()
    return total_updated


def get_or_create(
    db: Session,
    model_class: Any,
    defaults: Optional[dict] = None,
    **kwargs
) -> tuple[Any, bool]:
    """
    取得或建立物件
    
    Args:
        db: 資料庫會話
        model_class: 模型類別
        defaults: 建立時的預設值
        **kwargs: 查詢條件
        
    Returns:
        tuple: (物件, 是否為新建立)
    """
    instance = db.query(model_class).filter_by(**kwargs).first()
    
    if instance:
        return instance, False
    
    # 合併查詢條件和預設值
    params = {**kwargs, **(defaults or {})}
    instance = model_class(**params)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    
    return instance, True


def count_by(
    db: Session,
    model_class: Any,
    group_by_field: str
) -> dict:
    """
    按欄位分組計數
    
    Args:
        db: 資料庫會話
        model_class: 模型類別
        group_by_field: 分組欄位名稱
        
    Returns:
        dict: {分組值: 計數}
    """
    field = getattr(model_class, group_by_field)
    
    results = db.query(
        field,
        func.count(model_class.id)
    ).group_by(field).all()
    
    return {str(key): count for key, count in results}
