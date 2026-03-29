"""
商品 API 整合測試
"""
import pytest
from decimal import Decimal

from app.models.product import Product, Category


class TestProductsAPI:
    """商品 API 測試類別"""
    
    @pytest.mark.integration
    def test_get_products_list(self, client, db_session, test_product, test_category):
        """
        測試取得商品列表
        """
        response = client.get("/api/v1/products")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
    
    @pytest.mark.integration
    def test_get_products_with_category_filter(
        self, client, db_session, test_product, test_category
    ):
        """
        測試依分類篩選商品
        """
        response = client.get(f"/api/v1/products?category_id={test_category.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        
        # 所有商品都應屬於該分類
        for item in data["items"]:
            assert item["category_id"] == test_category.id
    
    @pytest.mark.integration
    def test_get_products_available_only(
        self, client, db_session, test_product, test_category
    ):
        """
        測試只取得可供應商品
        """
        # 建立一個不可供應的商品
        unavailable_product = Product(
            id="prod-unavailable",
            category_id=test_category.id,
            name="缺貨商品",
            price=Decimal("100"),
            is_available=False,
            is_active=True
        )
        db_session.add(unavailable_product)
        db_session.commit()
        
        response = client.get("/api/v1/products?available_only=true")
        
        assert response.status_code == 200
        data = response.json()
        
        # 不應包含不可供應的商品
        product_ids = [item["id"] for item in data["items"]]
        assert "prod-unavailable" not in product_ids
    
    @pytest.mark.integration
    def test_get_product_by_id(self, client, db_session, test_product):
        """
        測試取得單一商品
        """
        response = client.get(f"/api/v1/products/{test_product.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_product.id
        assert data["name"] == test_product.name
        assert "price" in data
    
    @pytest.mark.integration
    def test_get_product_not_found(self, client):
        """
        測試商品不存在
        """
        response = client.get("/api/v1/products/non-existent-id")
        
        assert response.status_code == 404
    
    @pytest.mark.integration
    def test_get_inactive_product_not_found(
        self, client, db_session, test_category
    ):
        """
        測試已下架商品不可查詢
        """
        inactive_product = Product(
            id="prod-inactive",
            category_id=test_category.id,
            name="已下架商品",
            price=Decimal("100"),
            is_available=True,
            is_active=False  # 已下架
        )
        db_session.add(inactive_product)
        db_session.commit()
        
        response = client.get("/api/v1/products/prod-inactive")
        
        # 應該返回 404
        assert response.status_code == 404


class TestCategoriesAPI:
    """分類 API 測試類別"""
    
    @pytest.mark.integration
    def test_get_categories(self, client, db_session, test_category):
        """
        測試取得分類列表
        """
        response = client.get("/api/v1/products/categories")
        
        assert response.status_code == 200
        data = response.json()["items"]
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.integration
    def test_get_categories_with_products(
        self, client, db_session, test_category, test_product
    ):
        """
        測試取得分類及其商品
        """
        response = client.get("/api/v1/products/categories")

        assert response.status_code == 200
        data = response.json()["items"]

        # 找到測試分類
        test_cat = next(
            (c for c in data if c["id"] == test_category.id),
            None
        )
        assert test_cat is not None
        assert test_cat["name"] == test_category.name

    @pytest.mark.integration
    def test_inactive_category_not_shown(
        self, client, db_session
    ):
        """
        測試已停用分類不顯示
        """
        inactive_category = Category(
            id="cat-inactive",
            name="已停用分類",
            is_active=False
        )
        db_session.add(inactive_category)
        db_session.commit()

        response = client.get("/api/v1/products/categories")

        assert response.status_code == 200
        data = response.json()["items"]

        category_ids = [c["id"] for c in data]
        assert "cat-inactive" not in category_ids


class TestProductModel:
    """商品模型測試類別"""
    
    @pytest.mark.unit
    def test_product_creation(self, db_session, test_category):
        """
        測試商品建立
        """
        product = Product(
            id="prod-new",
            category_id=test_category.id,
            name="新商品",
            description="商品描述",
            price=Decimal("150"),
            daily_limit=30,
            is_available=True,
            is_active=True
        )
        db_session.add(product)
        db_session.commit()
        
        # 查詢驗證
        saved = db_session.query(Product).filter(Product.id == "prod-new").first()
        assert saved is not None
        assert saved.name == "新商品"
        assert saved.price == Decimal("150")
    
    @pytest.mark.unit
    def test_product_daily_limit(self, db_session, test_product):
        """
        測試商品每日上限
        """
        test_product.daily_limit = 10
        test_product.today_sold = 10
        db_session.commit()
        
        # 今日已售完
        assert test_product.today_sold >= test_product.daily_limit
    
    @pytest.mark.unit
    def test_product_category_relationship(
        self, db_session, test_product, test_category
    ):
        """
        測試商品與分類的關聯
        """
        assert test_product.category_id == test_category.id
        assert test_product.category.name == test_category.name
