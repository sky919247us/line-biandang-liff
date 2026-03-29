"""
群組點餐 API 測試
"""
import pytest
from app.core.security import create_access_token  # 若函式名不同請調整


class TestGroupOrdersAPI:
    def _auth_headers(self, user):
        token = create_access_token({"sub": user.id})
        return {"Authorization": f"Bearer {token}"}

    def test_create_group_order(self, client, test_user):
        """成功建立群組點餐"""
        headers = self._auth_headers(test_user)
        response = client.post(
            "/api/v1/group-orders",
            json={"title": "午餐群組點餐", "max_participants": 5},
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "午餐群組點餐"
        assert data["status"] == "open"
        assert len(data["share_code"]) == 6
        assert len(data["participants"]) == 1  # 建立者自動加入

    def test_get_group_order_by_code(self, client, test_group_order):
        """透過分享碼取得群組點餐詳情（公開）"""
        response = client.get(f"/api/v1/group-orders/{test_group_order.share_code}")
        assert response.status_code == 200
        data = response.json()
        assert data["share_code"] == test_group_order.share_code

    def test_get_nonexistent_group_order_fails(self, client):
        """不存在的分享碼回傳 404"""
        response = client.get("/api/v1/group-orders/XXXXXX")
        assert response.status_code == 404

    def test_join_group_order(self, client, test_group_order, test_admin):
        """第二個使用者加入群組點餐"""
        headers = self._auth_headers(test_admin)
        response = client.post(
            f"/api/v1/group-orders/{test_group_order.share_code}/join",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["participants"]) == 2

    def test_join_already_joined_is_idempotent(self, client, test_group_order, test_user):
        """重複加入回傳現有資料（不報錯）"""
        headers = self._auth_headers(test_user)
        r1 = client.post(
            f"/api/v1/group-orders/{test_group_order.share_code}/join",
            headers=headers,
        )
        assert r1.status_code == 200

    def test_update_participant_items(self, client, test_group_order, test_user, test_product):
        """更新參與者品項"""
        headers = self._auth_headers(test_user)
        items = [
            {
                "product_id": test_product.id,
                "product_name": test_product.name,
                "quantity": 2,
                "unit_price": float(test_product.price),
            }
        ]
        response = client.put(
            f"/api/v1/group-orders/{test_group_order.share_code}/items",
            json={"items": items},
            headers=headers,
        )
        assert response.status_code == 200

    def test_lock_group_order_by_creator(self, client, test_group_order, test_user):
        """建立者可鎖定群組點餐"""
        headers = self._auth_headers(test_user)
        response = client.post(
            f"/api/v1/group-orders/{test_group_order.share_code}/lock",
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "locked"

    def test_lock_group_order_by_non_creator_fails(self, client, test_group_order, test_admin):
        """非建立者無法鎖定"""
        headers = self._auth_headers(test_admin)
        # 先加入
        client.post(
            f"/api/v1/group-orders/{test_group_order.share_code}/join",
            headers=headers,
        )
        response = client.post(
            f"/api/v1/group-orders/{test_group_order.share_code}/lock",
            headers=headers,
        )
        assert response.status_code == 403

    def test_get_my_group_orders(self, client, test_user, test_group_order):
        """取得自己的群組點餐列表"""
        headers = self._auth_headers(test_user)
        response = client.get("/api/v1/group-orders/my", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_unauthenticated_create_fails(self, client):
        """未登入無法建立群組點餐"""
        response = client.post(
            "/api/v1/group-orders",
            json={"title": "未登入點餐"},
        )
        assert response.status_code == 401
