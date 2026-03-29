"""
KDS 廚房顯示系統 API 測試
"""
import pytest
from decimal import Decimal
from app.core.security import create_access_token
from app.models.order import OrderStatus


class TestAdminKDSAPI:
    def _admin_headers(self, admin):
        token = create_access_token({"sub": admin.id})
        return {"Authorization": f"Bearer {token}"}

    def _user_headers(self, user):
        token = create_access_token({"sub": user.id})
        return {"Authorization": f"Bearer {token}"}

    def test_get_kds_orders_empty(self, client, test_admin):
        """無訂單時回傳空陣列"""
        headers = self._admin_headers(test_admin)
        response = client.get("/api/v1/admin/kds/orders", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_kds_orders_with_confirmed_order(self, client, test_admin, test_order, db_session):
        """已確認訂單出現在 KDS 清單中"""
        # 將訂單狀態改為 confirmed
        test_order.status = OrderStatus.CONFIRMED.value
        db_session.commit()

        headers = self._admin_headers(test_admin)
        response = client.get("/api/v1/admin/kds/orders", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        order_ids = [o["id"] for o in data]
        assert test_order.id in order_ids

    def test_start_preparing(self, client, test_admin, test_order, db_session):
        """成功將訂單狀態改為備餐中"""
        test_order.status = OrderStatus.CONFIRMED.value
        db_session.commit()

        headers = self._admin_headers(test_admin)
        response = client.patch(
            f"/api/v1/admin/kds/orders/{test_order.id}/start",
            headers=headers,
        )
        assert response.status_code == 200
        db_session.refresh(test_order)
        assert test_order.status == OrderStatus.PREPARING.value

    def test_mark_ready(self, client, test_admin, test_order, db_session):
        """成功將訂單狀態改為備餐完成"""
        test_order.status = OrderStatus.PREPARING.value
        db_session.commit()

        headers = self._admin_headers(test_admin)
        response = client.patch(
            f"/api/v1/admin/kds/orders/{test_order.id}/ready",
            headers=headers,
        )
        assert response.status_code == 200
        db_session.refresh(test_order)
        assert test_order.status == OrderStatus.READY.value

    def test_start_preparing_wrong_status_fails(self, client, test_admin, test_order, db_session):
        """pending 狀態無法開始備餐"""
        test_order.status = OrderStatus.PENDING.value
        db_session.commit()

        headers = self._admin_headers(test_admin)
        response = client.patch(
            f"/api/v1/admin/kds/orders/{test_order.id}/start",
            headers=headers,
        )
        assert response.status_code == 400

    def test_non_admin_access_forbidden(self, client, test_user):
        """一般使用者無法存取 KDS"""
        headers = self._user_headers(test_user)
        response = client.get("/api/v1/admin/kds/orders", headers=headers)
        assert response.status_code == 403

    def test_unauthenticated_access_fails(self, client):
        """未登入無法存取 KDS"""
        response = client.get("/api/v1/admin/kds/orders")
        assert response.status_code == 401
