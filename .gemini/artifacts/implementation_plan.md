# LINE LIFF 便當訂購系統 - 實作計畫

## 專案概述

建立一個整合 LINE Official Account 的 LIFF（LINE Front-end Framework）OMO 便當訂購系統，提供視覺化訂購介面、物料級庫存連動、配送驗證系統及成本控制邏輯。

---

## 技術架構

### 前端技術棧
- **框架**: React 18 + TypeScript
- **建構工具**: Vite
- **狀態管理**: Zustand
- **路由**: React Router v6
- **UI 元件**: 自訂元件庫 + CSS Modules
- **LINE 整合**: LIFF SDK v2.x
- **地圖服務**: Google Maps JavaScript API (可選)
- **HTTP 客戶端**: Axios

### 後端技術棧
- **框架**: Python FastAPI
- **資料庫**: PostgreSQL
- **ORM**: SQLAlchemy 2.x
- **資料驗證**: Pydantic v2
- **認證**: LINE Login + JWT
- **快取**: Redis
- **環境管理**: uv + .venv

### 部署環境
- **前端**: Vercel / Netlify
- **後端**: Railway / Render
- **資料庫**: Supabase / Railway PostgreSQL

---

## 系統模組規劃

### 模組一：消費者端訂購模組 (Consumer Ordering Module)

#### 1.1 取餐模式切換
| 功能 | 說明 |
|------|------|
| 自取模式 | 顯示店家地址、營業時間、可取餐時段 |
| 外送模式 | 地址輸入、距離計算、運費試算 |
| 模式切換 | 即時切換並重新計算訂單金額 |

#### 1.2 外送距離計算
| 功能 | 說明 |
|------|------|
| Google Maps API | 精確計算距離，限制配送範圍（預設 5km） |
| 手動輸入模式 | 無 API 時，允許自由輸入地址供人工審核 |
| 運費計算 | 依距離階梯計費（如 0-2km 免運、2-5km $30） |

#### 1.3 商品客製化
| 功能 | 說明 |
|------|------|
| 口味備註 | 少飯、加辣、不要蛋、加蔥等常用選項 |
| 自訂備註 | 自由文字輸入特殊需求 |
| 配料加購 | 加蛋 +$10、加滷蛋 +$15 等 |

#### 1.4 訂單追蹤
| 狀態 | 說明 |
|------|------|
| 待確認 | 訂單已送出，等待店家確認 |
| 備餐中 | 店家已確認，開始準備餐點 |
| 待取餐 | 餐點已完成，等待顧客取餐 |
| 配送中 | 外送訂單，正在配送途中 |
| 已完成 | 訂單完成 |
| 已取消 | 訂單被取消 |

---

### 模組二：智慧庫存與 BOM 邏輯 (Smart Inventory & BOM)

#### 2.1 核心物料管理
| 物料類型 | 範例 |
|----------|------|
| 主菜 | 雞腿、排骨、魚排、炸豬排 |
| 配菜 | 三色蛋、滷蛋、青菜 |
| 主食 | 白飯、糙米飯 |
| 調味料 | 醬油、辣椒醬 |

#### 2.2 BOM（物料清單）對應
```
雞腿便當 = {
  雞腿: 1,
  白飯: 200g,
  配菜A: 1份,
  配菜B: 1份,
  配菜C: 1份
}
```

#### 2.3 庫存扣減邏輯
- 訂單成立時預扣庫存
- 訂單取消時回補庫存
- 庫存不足時自動下架商品
- 低庫存警示通知

---

### 模組三：配送驗證與成本控制 (Delivery & Cost Control)

#### 3.1 配送驗證
| 功能 | 說明 |
|------|------|
| 地址驗證 | 使用 Google Geocoding API 驗證地址有效性 |
| 範圍驗證 | 計算與店家距離，超出範圍提示無法配送 |
| 時段驗證 | 檢查配送時段是否在營業時間內 |

#### 3.2 成本控制
| 控制項 | 說明 |
|--------|------|
| 最低消費 | 外送訂單需滿足最低金額（如 $150） |
| 運費階梯 | 根據距離計算運費 |
| 折扣上限 | 單筆訂單折扣金額上限 |
| 每日訂單上限 | 依據產能限制每日接單數量 |

---

## 資料庫設計

### 核心資料表

```sql
-- 使用者表
users (
  id UUID PRIMARY KEY,
  line_user_id VARCHAR(50) UNIQUE NOT NULL,
  display_name VARCHAR(100),
  phone VARCHAR(20),
  default_address TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- 商品表
products (
  id UUID PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  price DECIMAL(10,2) NOT NULL,
  image_url TEXT,
  category_id UUID REFERENCES categories(id),
  is_available BOOLEAN DEFAULT true,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- 物料表
materials (
  id UUID PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  unit VARCHAR(20) NOT NULL,
  current_stock DECIMAL(10,2) DEFAULT 0,
  safety_stock DECIMAL(10,2) DEFAULT 0,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- BOM 物料清單
product_materials (
  id UUID PRIMARY KEY,
  product_id UUID REFERENCES products(id),
  material_id UUID REFERENCES materials(id),
  quantity DECIMAL(10,2) NOT NULL
)

-- 訂單表
orders (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  order_number VARCHAR(20) UNIQUE NOT NULL,
  order_type VARCHAR(20) NOT NULL, -- 'pickup' | 'delivery'
  status VARCHAR(20) NOT NULL,
  subtotal DECIMAL(10,2) NOT NULL,
  delivery_fee DECIMAL(10,2) DEFAULT 0,
  discount DECIMAL(10,2) DEFAULT 0,
  total DECIMAL(10,2) NOT NULL,
  delivery_address TEXT,
  delivery_distance DECIMAL(10,2),
  notes TEXT,
  pickup_time TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- 訂單明細表
order_items (
  id UUID PRIMARY KEY,
  order_id UUID REFERENCES orders(id),
  product_id UUID REFERENCES products(id),
  quantity INTEGER NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL,
  customizations JSONB,
  notes TEXT
)

-- 商品客製化選項
customization_options (
  id UUID PRIMARY KEY,
  product_id UUID REFERENCES products(id),
  name VARCHAR(100) NOT NULL,
  type VARCHAR(20) NOT NULL, -- 'addon' | 'modifier'
  price_adjustment DECIMAL(10,2) DEFAULT 0,
  is_default BOOLEAN DEFAULT false
)
```

---

## API 端點設計

### 認證相關
| 方法 | 端點 | 說明 |
|------|------|------|
| POST | `/api/auth/login` | LINE Login 認證 |
| POST | `/api/auth/refresh` | 刷新 Token |
| GET | `/api/auth/me` | 取得當前使用者資訊 |

### 商品相關
| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/api/products` | 取得商品列表 |
| GET | `/api/products/{id}` | 取得商品詳情 |
| GET | `/api/categories` | 取得分類列表 |

### 訂單相關
| 方法 | 端點 | 說明 |
|------|------|------|
| POST | `/api/orders` | 建立訂單 |
| GET | `/api/orders` | 取得使用者訂單列表 |
| GET | `/api/orders/{id}` | 取得訂單詳情 |
| PATCH | `/api/orders/{id}/cancel` | 取消訂單 |

### 配送相關
| 方法 | 端點 | 說明 |
|------|------|------|
| POST | `/api/delivery/calculate` | 計算距離與運費 |
| POST | `/api/delivery/validate-address` | 驗證地址 |

### 庫存相關（管理端）
| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/api/admin/materials` | 取得物料列表 |
| PATCH | `/api/admin/materials/{id}/stock` | 更新庫存 |
| GET | `/api/admin/inventory/alerts` | 取得庫存警示 |

---

## 開發階段規劃

### Phase 1: 基礎建設 (Week 1-2)
- [x] 建立實作計畫文件
- [x] 初始化前端專案 (Vite + React + TypeScript)
- [x] 初始化後端專案 (FastAPI + SQLAlchemy)
- [x] 設計資料庫 Schema
- [ ] 實作 LINE Login 認證流程
- [x] 建立基礎 UI 元件庫

### Phase 2: 訂購核心功能 (Week 3-4)
- [x] 商品列表與詳情頁面
- [x] 購物車功能
- [x] 取餐模式切換 (自取/外送)
- [x] 商品客製化選項
- [x] 訂單建立流程

### Phase 3: 庫存與 BOM 系統 (Week 5-6)
- [x] 物料管理介面
- [x] BOM 對應關係設定（資料模型已建立）
- [x] 庫存自動扣減邏輯
- [x] 低庫存警示功能
- [x] 商品自動上下架

### Phase 4: 配送與成本控制 (Week 7-8)
- [x] Google Maps API 整合
- [x] 距離計算與運費試算
- [x] 配送範圍驗證
- [x] 最低消費與滿額免運
- [x] 每日訂單上限控制

### Phase 5: 訂單追蹤與通知 (Week 9-10)
- [x] 訂單狀態追蹤頁面
- [x] 訂單歷史記錄
- [x] LINE 推播通知整合
- [x] 即時訂單狀態更新

### Phase 6: 測試與優化 (Week 11-12)
- [ ] 單元測試
- [ ] 整合測試
- [ ] 效能優化
- [ ] 使用者體驗優化
- [x] 部署上線（Docker 配置已完成）

---

## 專案目錄結構

### 前端 (frontend/)
```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── assets/           # 靜態資源
│   ├── components/       # 共用元件
│   │   ├── common/       # 通用元件 (Button, Input, Modal...)
│   │   ├── layout/       # 佈局元件 (Header, Footer, Nav...)
│   │   └── features/     # 功能元件 (ProductCard, CartItem...)
│   ├── hooks/            # 自訂 Hooks
│   ├── pages/            # 頁面元件
│   │   ├── home/         # 首頁
│   │   ├── menu/         # 菜單頁
│   │   ├── cart/         # 購物車頁
│   │   ├── checkout/     # 結帳頁
│   │   ├── orders/       # 訂單頁
│   │   └── profile/      # 個人資料頁
│   ├── services/         # API 服務
│   ├── stores/           # Zustand 狀態管理
│   ├── types/            # TypeScript 型別定義
│   ├── utils/            # 工具函式
│   ├── styles/           # 全域樣式
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

### 後端 (backend/)
```
backend/
├── app/
│   ├── api/              # API 路由
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── products.py
│   │   │   ├── orders.py
│   │   │   ├── delivery.py
│   │   │   └── admin/
│   │   └── deps.py       # 相依注入
│   ├── core/             # 核心設定
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── models/           # SQLAlchemy 模型
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── order.py
│   │   └── material.py
│   ├── schemas/          # Pydantic Schema
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── order.py
│   │   └── material.py
│   ├── services/         # 業務邏輯
│   │   ├── auth.py
│   │   ├── product.py
│   │   ├── order.py
│   │   ├── inventory.py
│   │   └── delivery.py
│   ├── repositories/     # 資料存取層
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── order.py
│   │   └── material.py
│   └── main.py
├── migrations/           # Alembic 資料庫遷移
├── tests/                # 測試
├── pyproject.toml
├── .env.example
└── README.md
```

---

## 環境變數設定

### 前端 (.env)
```env
VITE_LIFF_ID=your-liff-id
VITE_API_BASE_URL=http://localhost:8000/api
VITE_GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

### 後端 (.env)
```env
# 應用程式設定
APP_NAME=LINE便當訂購系統
DEBUG=true
SECRET_KEY=your-secret-key

# 資料庫設定
DATABASE_URL=postgresql://user:password@localhost:5432/biandang

# Redis 設定
REDIS_URL=redis://localhost:6379

# LINE 設定
LINE_CHANNEL_ID=your-channel-id
LINE_CHANNEL_SECRET=your-channel-secret
LINE_LIFF_ID=your-liff-id

# Google Maps 設定 (可選)
GOOGLE_MAPS_API_KEY=your-api-key

# 配送設定
MAX_DELIVERY_DISTANCE_KM=5
MIN_ORDER_AMOUNT=150
```

---

## 下一步行動

### 已完成 ✅

1. ✅ 建立實作計畫文件
2. ✅ 初始化前端專案結構
3. ✅ 初始化後端專案結構
4. ✅ 設計前端 UI 介面
5. ✅ 實作 LINE LIFF SDK 整合
6. ✅ 建立管理後台前端頁面
7. ✅ 建立管理後台 API 端點
8. ✅ LINE Messaging API 整合（訂單通知）
9. ✅ LINE Webhook 處理
10. ✅ Docker 部署配置
11. ✅ 資料庫遷移腳本
12. ✅ 庫存自動扣減與回補邏輯
13. ✅ 商品自動上下架（依庫存狀態）
14. ✅ 每日訂單上限控制
15. ✅ 管理員權限驗證
16. ✅ 配送距離計算與運費試算
17. ✅ 訂單統計報表（銷售總覽、每日統計、熱門商品、分類分析、物料使用）
18. ✅ 優惠券系統（固定金額、百分比、免運費優惠）
19. ✅ 單元測試與整合測試框架
20. ✅ 雲端部署配置（Railway、Render、AWS 指南）
21. ✅ CI/CD 工作流程（GitHub Actions）
22. ✅ 效能監控中間件（請求追蹤、效能計量）
23. ✅ 日誌系統（JSON 格式、彩色終端輸出）
24. ✅ 快取服務（記憶體快取、Redis 快取）
25. ✅ 監控 API（健康檢查、效能統計、就緒/存活探測）

### 進行中 ⏳

1. ⏳ 實際資料庫連線（目前使用 SQLite，可切換到 PostgreSQL）

### 待處理 📋

（專案核心功能已全部完成）

---

## 開發備註

### 前端開發伺服器
```bash
cd frontend
npm run dev  # http://127.0.0.1:3000
```

### 後端開發伺服器
```bash
cd backend
uv run uvicorn app.main:app --reload  # http://127.0.0.1:8000
```

### Docker 部署
```bash
cp .env.example .env  # 編輯環境變數
docker compose up -d
```

### 載入種子資料
```bash
cd backend
uv run python migrations/load_seeds.py
```

### 執行測試
```bash
cd backend
uv run pytest tests/ -v         # 執行所有測試
uv run pytest tests/ -m unit    # 只執行單元測試
uv run pytest tests/ -m integration  # 只執行整合測試
```

---

*文件建立時間: 2026-02-04*
*最後更新: 2026-02-08 17:15*

