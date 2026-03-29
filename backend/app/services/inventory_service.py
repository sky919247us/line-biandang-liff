"""
庫存服務

處理庫存扣減、回補和低庫存警示
"""
import logging
from decimal import Decimal
from typing import List, Optional, Tuple
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.material import Material, ProductMaterial
from app.models.product import Product


logger = logging.getLogger(__name__)


@dataclass
class StockCheckResult:
    """庫存檢查結果"""
    is_available: bool
    insufficient_materials: List[dict]  # {'material_id': str, 'name': str, 'required': Decimal, 'available': Decimal}


@dataclass
class StockDeductionResult:
    """庫存扣減結果"""
    success: bool
    error_message: Optional[str] = None
    low_stock_alerts: List[dict] = None  # 低庫存警示清單
    
    def __post_init__(self):
        if self.low_stock_alerts is None:
            self.low_stock_alerts = []


class InventoryService:
    """
    庫存管理服務
    
    負責處理：
    1. 庫存檢查（訂單前確認物料充足）
    2. 庫存扣減（訂單成立時依 BOM 扣減）
    3. 庫存回補（訂單取消時回補）
    4. 低庫存警示
    5. 商品自動上下架
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_product_stock(
        self,
        product_id: str,
        quantity: int = 1
    ) -> StockCheckResult:
        """
        檢查商品庫存是否足夠
        
        根據商品的 BOM（物料清單）檢查所需物料是否足夠
        
        Args:
            product_id: 商品 ID
            quantity: 訂購數量
            
        Returns:
            StockCheckResult: 庫存檢查結果
        """
        # 取得商品的 BOM
        product_materials = self.db.query(ProductMaterial).filter(
            ProductMaterial.product_id == product_id
        ).all()
        
        if not product_materials:
            # 若無 BOM 設定，視為庫存充足
            logger.warning(f"商品 {product_id} 未設定 BOM，將視為庫存充足")
            return StockCheckResult(is_available=True, insufficient_materials=[])
        
        insufficient = []
        
        for pm in product_materials:
            material = self.db.query(Material).filter(
                Material.id == pm.material_id
            ).first()
            
            if not material:
                logger.error(f"找不到物料 {pm.material_id}")
                continue
            
            required_qty = pm.quantity * quantity
            
            if material.current_stock < required_qty:
                insufficient.append({
                    'material_id': material.id,
                    'name': material.name,
                    'required': required_qty,
                    'available': material.current_stock,
                    'unit': material.unit
                })
        
        return StockCheckResult(
            is_available=len(insufficient) == 0,
            insufficient_materials=insufficient
        )
    
    def check_order_stock(
        self,
        items: List[dict]
    ) -> StockCheckResult:
        """
        檢查整筆訂單的庫存是否足夠
        
        Args:
            items: 訂單明細 [{'product_id': str, 'quantity': int}, ...]
            
        Returns:
            StockCheckResult: 庫存檢查結果
        """
        # 彙整所有物料需求
        material_requirements: dict[str, Decimal] = {}
        
        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            
            product_materials = self.db.query(ProductMaterial).filter(
                ProductMaterial.product_id == product_id
            ).all()
            
            for pm in product_materials:
                required = pm.quantity * quantity
                if pm.material_id in material_requirements:
                    material_requirements[pm.material_id] += required
                else:
                    material_requirements[pm.material_id] = required
        
        # 檢查每種物料是否足夠
        insufficient = []
        
        for material_id, required_qty in material_requirements.items():
            material = self.db.query(Material).filter(
                Material.id == material_id
            ).first()
            
            if not material:
                logger.error(f"找不到物料 {material_id}")
                continue
            
            if material.current_stock < required_qty:
                insufficient.append({
                    'material_id': material.id,
                    'name': material.name,
                    'required': required_qty,
                    'available': material.current_stock,
                    'unit': material.unit
                })
        
        return StockCheckResult(
            is_available=len(insufficient) == 0,
            insufficient_materials=insufficient
        )
    
    def deduct_stock_for_order(
        self,
        items: List[dict]
    ) -> StockDeductionResult:
        """
        扣減訂單所需的庫存
        
        依據訂單明細和各商品的 BOM，扣減對應物料庫存
        
        Args:
            items: 訂單明細 [{'product_id': str, 'quantity': int}, ...]
            
        Returns:
            StockDeductionResult: 扣減結果
        """
        # 先檢查庫存是否足夠
        check_result = self.check_order_stock(items)
        
        if not check_result.is_available:
            material_names = [m['name'] for m in check_result.insufficient_materials]
            return StockDeductionResult(
                success=False,
                error_message=f"庫存不足：{', '.join(material_names)}"
            )
        
        # 彙整物料需求
        material_requirements: dict[str, Decimal] = {}
        
        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            
            product_materials = self.db.query(ProductMaterial).filter(
                ProductMaterial.product_id == product_id
            ).all()
            
            for pm in product_materials:
                required = pm.quantity * quantity
                if pm.material_id in material_requirements:
                    material_requirements[pm.material_id] += required
                else:
                    material_requirements[pm.material_id] = required
        
        # 扣減庫存
        low_stock_alerts = []
        
        for material_id, deduct_qty in material_requirements.items():
            material = self.db.query(Material).filter(
                Material.id == material_id
            ).with_for_update().first()  # 使用行級鎖定避免競爭條件
            
            if material:
                material.current_stock -= deduct_qty
                
                logger.info(
                    f"扣減物料 {material.name}: -{deduct_qty} {material.unit}, "
                    f"剩餘: {material.current_stock} {material.unit}"
                )
                
                # 檢查是否低於安全庫存
                if material.is_low_stock:
                    low_stock_alerts.append({
                        'material_id': material.id,
                        'name': material.name,
                        'current_stock': float(material.current_stock),
                        'safety_stock': float(material.safety_stock),
                        'unit': material.unit
                    })
        
        # 更新相關商品的可供應狀態
        self._update_products_availability()
        self.db.flush()

        return StockDeductionResult(
            success=True,
            low_stock_alerts=low_stock_alerts
        )

    def restore_stock_for_order(
        self,
        items: List[dict]
    ) -> StockDeductionResult:
        """
        回補訂單取消時的庫存
        
        Args:
            items: 訂單明細 [{'product_id': str, 'quantity': int}, ...]
            
        Returns:
            StockDeductionResult: 回補結果
        """
        # 彙整物料需求
        material_requirements: dict[str, Decimal] = {}
        
        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            
            product_materials = self.db.query(ProductMaterial).filter(
                ProductMaterial.product_id == product_id
            ).all()
            
            for pm in product_materials:
                required = pm.quantity * quantity
                if pm.material_id in material_requirements:
                    material_requirements[pm.material_id] += required
                else:
                    material_requirements[pm.material_id] = required
        
        # 回補庫存
        for material_id, restore_qty in material_requirements.items():
            material = self.db.query(Material).filter(
                Material.id == material_id
            ).with_for_update().first()
            
            if material:
                material.current_stock += restore_qty
                
                logger.info(
                    f"回補物料 {material.name}: +{restore_qty} {material.unit}, "
                    f"目前: {material.current_stock} {material.unit}"
                )
        
        # 更新相關商品的可供應狀態
        self._update_products_availability()
        self.db.flush()

        return StockDeductionResult(success=True)

    def _update_products_availability(self):
        """
        更新所有商品的可供應狀態
        
        根據 BOM 和物料庫存，自動設定商品是否可供應
        """
        products = self.db.query(Product).filter(
            Product.is_active == True
        ).all()
        
        for product in products:
            check_result = self.check_product_stock(product.id, 1)
            
            # 若庫存狀態改變，更新商品
            if product.is_available != check_result.is_available:
                product.is_available = check_result.is_available
                logger.info(
                    f"商品 {product.name} 可供應狀態更新為: {check_result.is_available}"
                )
    
    def get_low_stock_materials(self) -> List[dict]:
        """
        取得低於安全庫存的物料清單
        
        Returns:
            低庫存物料清單
        """
        materials = self.db.query(Material).all()
        
        low_stock = []
        for material in materials:
            if material.is_low_stock:
                low_stock.append({
                    'id': material.id,
                    'name': material.name,
                    'current_stock': float(material.current_stock),
                    'safety_stock': float(material.safety_stock),
                    'unit': material.unit,
                    'shortage': float(material.safety_stock - material.current_stock)
                })
        
        return low_stock
    
    def update_material_stock(
        self,
        material_id: str,
        new_stock: Decimal,
        reason: str = ""
    ) -> bool:
        """
        手動更新物料庫存
        
        Args:
            material_id: 物料 ID
            new_stock: 新庫存數量
            reason: 調整原因
            
        Returns:
            是否成功
        """
        material = self.db.query(Material).filter(
            Material.id == material_id
        ).first()
        
        if not material:
            logger.error(f"物料 {material_id} 不存在")
            return False
        
        old_stock = material.current_stock
        material.current_stock = new_stock

        logger.info(
            f"物料 {material.name} 庫存調整: {old_stock} -> {new_stock} {material.unit}"
            f"{f', 原因: {reason}' if reason else ''}"
        )

        # 更新相關商品的可供應狀態
        self._update_products_availability()
        self.db.flush()

        return True
    
    def add_material_stock(
        self,
        material_id: str,
        quantity: Decimal,
        reason: str = ""
    ) -> bool:
        """
        增加物料庫存（進貨）
        
        Args:
            material_id: 物料 ID
            quantity: 增加數量
            reason: 進貨原因
            
        Returns:
            是否成功
        """
        material = self.db.query(Material).filter(
            Material.id == material_id
        ).first()
        
        if not material:
            logger.error(f"物料 {material_id} 不存在")
            return False
        
        material.current_stock += quantity

        logger.info(
            f"物料 {material.name} 進貨: +{quantity} {material.unit}, "
            f"目前: {material.current_stock} {material.unit}"
            f"{f', 原因: {reason}' if reason else ''}"
        )

        # 更新相關商品的可供應狀態
        self._update_products_availability()
        self.db.flush()

        return True


def get_inventory_service(db: Session) -> InventoryService:
    """
    取得庫存服務實例
    
    用於 FastAPI 相依注入
    """
    return InventoryService(db)
