# Render 部署指南

Render 是另一個優秀的雲端平台，提供免費 PostgreSQL 和簡單的部署流程。

## 優點

- 免費 PostgreSQL 資料庫（90 天）
- 自動 SSL 憑證
- GitHub/GitLab 整合
- 零配置部署
- 內建環境變數管理

---

## 部署步驟

### 1. 建立 Render 帳號

1. 前往 [Render.com](https://render.com/)
2. 使用 GitHub 帳號登入

### 2. 建立 PostgreSQL 資料庫

1. 點擊 "New +" → "PostgreSQL"
2. 填寫設定：
   - Name: `biandang-db`
   - Region: 選擇離台灣近的區域（Singapore）
   - Plan: Free（或付費方案）
3. 記下連線字串 `DATABASE_URL`

### 3. 建立 Redis（選擇性）

1. 點擊 "New +" → "Redis"
2. 填寫設定：
   - Name: `biandang-redis`
   - Region: 與資料庫相同
3. 記下連線字串 `REDIS_URL`

### 4. 部署後端

1. 點擊 "New +" → "Web Service"
2. 連結 GitHub 儲存庫
3. 設定：
   - Name: `biandang-backend`
   - Region: Singapore
   - Branch: `main`
   - Root Directory: `backend`
   - Runtime: Docker
4. 設定環境變數（見下方）
5. 點擊 "Create Web Service"

### 5. 部署前端

1. 點擊 "New +" → "Static Site"
2. 連結 GitHub 儲存庫
3. 設定：
   - Name: `biandang-frontend`
   - Branch: `main`
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Publish Directory: `dist`
4. 點擊 "Create Static Site"

---

## 環境變數設定

在 Render Dashboard → Environment 中設定：

### 後端

```
DATABASE_URL=<render-postgresql-url>
REDIS_URL=<render-redis-url>
SECRET_KEY=your-secret-key-here
DEBUG=false

# LINE 設定
LINE_CHANNEL_ID=your-channel-id
LINE_CHANNEL_SECRET=your-channel-secret
LINE_CHANNEL_ACCESS_TOKEN=your-token
LINE_LIFF_ID=your-liff-id

# 店家設定
STORE_LATITUDE=24.1378
STORE_LONGITUDE=120.6828
STORE_ADDRESS=台中市中區興中街20號
MAX_DELIVERY_DISTANCE_KM=5
MIN_ORDER_AMOUNT=150
```

### 前端

```
VITE_API_URL=https://biandang-backend.onrender.com
VITE_LIFF_ID=your-liff-id
```

---

## render.yaml 配置

在專案根目錄建立 `render.yaml`：

```yaml
services:
  # 後端服務
  - type: web
    name: biandang-backend
    env: docker
    region: singapore
    rootDir: backend
    dockerfilePath: ./Dockerfile
    healthCheckPath: /health
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: biandang-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: biandang-redis
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: false
      - key: LINE_CHANNEL_ID
        sync: false
      - key: LINE_CHANNEL_SECRET
        sync: false
      - key: LINE_CHANNEL_ACCESS_TOKEN
        sync: false
      - key: LINE_LIFF_ID
        sync: false

  # 前端靜態網站
  - type: web
    name: biandang-frontend
    env: static
    region: singapore
    rootDir: frontend
    buildCommand: npm run build
    staticPublishPath: dist
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
    envVars:
      - key: VITE_API_URL
        value: https://biandang-backend.onrender.com
      - key: VITE_LIFF_ID
        sync: false

databases:
  - name: biandang-db
    databaseName: biandang
    user: biandang
    region: singapore
    plan: free

services:
  - type: redis
    name: biandang-redis
    region: singapore
    plan: free
    maxmemoryPolicy: allkeys-lru
```

---

## 自動部署

1. 推送到 GitHub 時會自動觸發部署
2. 可在 Dashboard 設定只部署特定分支

---

## 監控

1. **Logs**: 在 Dashboard 查看即時日誌
2. **Metrics**: 查看 CPU、記憶體使用率
3. **Health Checks**: 自動健康檢查

---

## 成本估算

| 服務 | 方案 | 費用 |
|------|------|------|
| Web Service | Free | $0（750 小時/月） |
| Web Service | Starter | $7/月 |
| PostgreSQL | Free | $0（90 天） |
| PostgreSQL | Starter | $7/月 |
| Redis | Free | $0 |
| Static Site | Free | $0 |

---

## 注意事項

1. 免費方案服務會在 15 分鐘無活動後睡眠
2. 睡眠後首次請求需等待約 30 秒
3. 免費 PostgreSQL 90 天後需升級或重新建立
4. 建議使用 Starter 方案用於正式環境
