/**
 * LINE LIFF 便當訂購系統
 * 
 * 主應用程式入口
 */
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { HomePage } from './pages/home';
import { MenuPage } from './pages/menu';
import { CartPage } from './pages/cart';
import { CheckoutPage, OrderPreviewPage } from './pages/checkout';
import { OrdersPage } from './pages/orders';
import { ProfilePage } from './pages/profile';
import {
  AdminLayout,
  AdminDashboard,
  AdminOrders,
  AdminProducts,
  AdminInventory,
  AdminSettings,
  AdminManualOrder,
  AdminKDS,
  AdminMembers,
  AdminReports,
} from './pages/admin';
import { LoyaltyPage } from './pages/loyalty';
import { GroupOrderPage, JoinGroupPage } from './pages/group';
import { StampCardPage } from './pages/stamp';
import { ReferralPage } from './pages/referral';
import { AdminBroadcast } from './pages/admin/AdminBroadcast';

// 匯入全域樣式
import './styles/global.css';
import './styles/button.css';
import './styles/card.css';
import './styles/form.css';

function App() {
  console.log('App component rendered'); // 偵錯用

  return (
    <Router>
      <Routes>
        {/* 顧客端路由 */}
        <Route path="/" element={<HomePage />} />
        <Route path="/menu" element={<MenuPage />} />
        <Route path="/cart" element={<CartPage />} />
        <Route path="/checkout/preview" element={<OrderPreviewPage />} />
        <Route path="/checkout" element={<CheckoutPage />} />
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/loyalty" element={<LoyaltyPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/group" element={<GroupOrderPage />} />
        <Route path="/group/join" element={<JoinGroupPage />} />
        <Route path="/stamps" element={<StampCardPage />} />
        <Route path="/referral" element={<ReferralPage />} />

        {/* 管理後台路由 */}
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<AdminDashboard />} />
          <Route path="orders" element={<AdminOrders />} />
          <Route path="products" element={<AdminProducts />} />
          <Route path="inventory" element={<AdminInventory />} />
          <Route path="orders/manual" element={<AdminManualOrder />} />
          <Route path="kds" element={<AdminKDS />} />
          <Route path="members" element={<AdminMembers />} />
          <Route path="reports" element={<AdminReports />} />
          <Route path="broadcast" element={<AdminBroadcast />} />
          <Route path="settings" element={<AdminSettings />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
