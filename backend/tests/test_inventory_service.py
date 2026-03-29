"""
庫存服務單元測試
"""
import pytest
from decimal import Decimal

from app.services.inventory_service import InventoryService


class TestInventoryService:
    """庫存服務測試類別"""
    
    @pytest.mark.unit
    def test_check_product_stock_available(
        self, db_session, test_product, test_material, test_bom
    ):
        """
        測試商品庫存檢查 - 庫存充足
        """
        service = InventoryService(db_session)
        
        result = service.check_product_stock(test_product.id, quantity=1)
        
        assert result.is_available is True
        assert len(result.insufficient_materials) == 0
    
    @pytest.mark.unit
    def test_check_product_stock_insufficient(
        self, db_session, test_product, test_material, test_bom
    ):
        """
        測試商品庫存檢查 - 庫存不足
        """
        # 設定物料庫存為 0
        test_material.current_stock = Decimal("0")
        db_session.commit()
        
        service = InventoryService(db_session)
        
        result = service.check_product_stock(test_product.id, quantity=1)
        
        assert result.is_available is False
        assert len(result.insufficient_materials) == 1
        assert result.insufficient_materials[0]["material_id"] == test_material.id
    
    @pytest.mark.unit
    def test_deduct_stock_success(
        self, db_session, test_product, test_material, test_bom
    ):
        """
        測試庫存扣減成功
        """
        initial_stock = float(test_material.current_stock)
        
        service = InventoryService(db_session)
        items = [{"product_id": test_product.id, "quantity": 5}]
        
        result = service.deduct_stock_for_order(items)
        
        assert result.success is True
        
        db_session.refresh(test_material)
        expected_stock = initial_stock - (5 * float(test_bom.quantity))
        assert float(test_material.current_stock) == expected_stock
    
    @pytest.mark.unit
    def test_deduct_stock_insufficient(
        self, db_session, test_product, test_material, test_bom
    ):
        """
        測試庫存扣減失敗 - 庫存不足
        """
        # 設定物料庫存不足
        test_material.current_stock = Decimal("2")
        db_session.commit()
        
        service = InventoryService(db_session)
        items = [{"product_id": test_product.id, "quantity": 10}]  # 需要 10 份
        
        result = service.deduct_stock_for_order(items)
        
        assert result.success is False
        assert "庫存不足" in result.error_message
    
    @pytest.mark.unit
    def test_restore_stock(
        self, db_session, test_product, test_material, test_bom
    ):
        """
        測試庫存回補
        """
        # 先扣減
        test_material.current_stock = Decimal("50")
        db_session.commit()
        
        service = InventoryService(db_session)
        items = [{"product_id": test_product.id, "quantity": 10}]
        
        # 扣減
        service.deduct_stock_for_order(items)
        db_session.refresh(test_material)
        after_deduct = float(test_material.current_stock)
        
        # 回補
        service.restore_stock_for_order(items)
        db_session.refresh(test_material)
        after_restore = float(test_material.current_stock)
        
        assert after_restore == after_deduct + (10 * float(test_bom.quantity))
    
    @pytest.mark.unit
    def test_low_stock_alert(
        self, db_session, test_product, test_material, test_bom
    ):
        """
        測試低庫存警示
        """
        # 設定物料庫存低於安全庫存
        test_material.current_stock = Decimal("5")  # 低於 safety_stock=10
        db_session.commit()
        
        service = InventoryService(db_session)
        
        alerts = service.get_low_stock_materials()
        
        assert len(alerts) == 1
        assert alerts[0]["id"] == test_material.id
        assert alerts[0]["current_stock"] == 5
        assert alerts[0]["safety_stock"] == 10
    
    @pytest.mark.unit
    def test_update_material_stock(
        self, db_session, test_material
    ):
        """
        測試手動更新庫存
        """
        service = InventoryService(db_session)
        
        new_stock = Decimal("200")
        result = service.update_material_stock(
            material_id=test_material.id,
            new_stock=new_stock,
            reason="盤點調整"
        )
        
        assert result is True
        
        db_session.refresh(test_material)
        assert test_material.current_stock == new_stock
    
    @pytest.mark.unit
    def test_add_material_stock(
        self, db_session, test_material
    ):
        """
        測試增加庫存（進貨）
        """
        initial_stock = test_material.current_stock
        add_quantity = Decimal("50")
        
        service = InventoryService(db_session)
        
        result = service.add_material_stock(
            material_id=test_material.id,
            quantity=add_quantity,
            reason="進貨"
        )
        
        assert result is True
        
        db_session.refresh(test_material)
        assert test_material.current_stock == initial_stock + add_quantity
