# 一米粒 便當訂購系統

LINE LIFF 便當訂購系統 - 專為「一米粒 弁当専門店」打造的 OMO 線上訂餐平台。

![LINE](https://img.shields.io/badge/LINE-00C300?style=for-the-badge&logo=line&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)

## 🍱 功能特色

### 顧客端
- **LINE 登入整合** - 使用 LINE 帳號快速登入
- **線上菜單瀏覽** - 瀏覽完整便當菜單
- **客製化選項** - 少飯、加辣、不要蔥等個人化選擇
- **購物車管理** - 新增、修改、刪除訂單項目
- **多種取餐方式** - 自取或外送
- **訂單追蹤** - 即時查看訂單狀態
- **LINE 推播通知** - 訂單確認、餐點完成通知

### 管理後台
- **訂單管理** - 查看、確認、更新訂單狀態
- **商品管理** - 上下架、價格調整、每日限量設定
- **庫存管理** - 物料監控、低庫存警示、補貨記錄
- **系統設定** - 營業時間、外送設定、店家資訊

## 🛠️ 技術架構

### 前端
- **React 18** + **TypeScript**
- **Vite** - 開發建置工具
- **React Router v6** - 路由管理
- **Zustand** - 狀態管理
- **LINE LIFF SDK** - LINE 整合

### 後端
- **Python 3.12** + **FastAPI**
- **SQLAlchemy** + **Alembic** - 資料庫 ORM 與遷移
- **Pydantic** - 資料驗證
- **LINE Messaging API** - 訊息推播

### 部署
- **Docker** + **Docker Compose**
- **Nginx** - 反向代理
- **SQLite** / **PostgreSQL** - 資料庫

## 📁 專案結構

```
LINE Biandang LIFF/
├── frontend/                 # 前端專案
│   ├── src/
│   │   ├── components/       # 共用元件
│   │   ├── pages/            # 頁面元件
│   │   ├── services/         # API 服務
│   │   ├── stores/           # 狀態管理
│   │   ├── styles/           # 全域樣式
│   │   └── types/            # TypeScript 型別
│   ├── Dockerfile
│   └── nginx.conf
│
├── backend/                  # 後端專案
│   ├── app/
│   │   ├── api/              # API 路由
│   │   ├── core/             # 核心設定
│   │   ├── models/           # 資料模型
│   │   ├── services/         # 業務邏輯
│   │   └── main.py           # 應用程式入口
│   ├── migrations/           # 資料庫遷移
│   └── Dockerfile
│
├── docker-compose.yml        # Docker 配置
└── .env.example              # 環境變數範本
```

## 🚀 快速開始

### 開發環境

#### 前端
```bash
cd frontend
npm install
npm run dev
```

#### 後端
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

### Docker 部署
```bash
# 複製環境變數
cp .env.example .env
# 編輯 .env 填入實際值

# 建置並啟動
docker-compose up -d
```

## ⚙️ 環境變數

| 變數名稱 | 說明 | 必填 |
|---------|------|------|
| `SECRET_KEY` | JWT 簽名密鑰 | ✅ |
| `LINE_CHANNEL_ID` | LINE Channel ID | ✅ |
| `LINE_CHANNEL_SECRET` | LINE Channel Secret | ✅ |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging API Token | ✅ |
| `LINE_LIFF_ID` | LIFF ID | ✅ |
| `DATABASE_URL` | 資料庫連線字串 | ✅ |
| `GOOGLE_MAPS_API_KEY` | Google Maps API Key | ❌ |

## 📱 LINE 設定

### 1. 建立 LINE Official Account
1. 前往 [LINE Official Account Manager](https://manager.line.biz/)
2. 建立新的官方帳號

### 2. 建立 LINE Login Channel
1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 建立新的 Provider（如果沒有）
3. 建立 LINE Login Channel

### 3. 建立 LIFF App
1. 在 LINE Login Channel 中
2. 前往 LIFF 分頁
3. 新增 LIFF App，設定 Endpoint URL

### 4. 設定 Webhook URL
在 Messaging API 設定中：
```
https://your-domain.com/api/v1/webhook
```

## 📖 API 文件

啟動後端後，訪問：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🏪 店家資訊

**一米粒 弁当専門店**
- 📍 地址：台中市中區興中街20號
- 📞 電話：0909-998-952
- ⏰ 營業時間：週一至週五 10:00 - 16:30
- 🚗 外送範圍：3 公里內（滿 $300 免運）

## 📝 License

MIT License

---

Made with ❤️ for 一米粒 弁当専門店
