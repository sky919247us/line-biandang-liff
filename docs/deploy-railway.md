# Railway 部署指南

Railway 是一個簡單易用的雲端平台，適合快速部署。

## 優點

- 免費額度適合小型應用
- 自動偵測專案類型
- 內建資料庫服務
- 自動 SSL 憑證
- GitHub 整合自動部署

---

## 部署步驟

### 1. 建立 Railway 帳號

1. 前往 [Railway.app](https://railway.app/)
2. 使用 GitHub 帳號登入

### 2. 建立新專案

```bash
# 安裝 Railway CLI
npm install -g @railway/cli

# 登入
railway login

# 建立專案
railway init
```

### 3. 部署後端

```bash
cd backend

# 連結專案
railway link

# 設定環境變數
railway variables set SECRET_KEY=your-secret-key
railway variables set LINE_CHANNEL_ID=your-channel-id
railway variables set LINE_CHANNEL_SECRET=your-channel-secret
railway variables set LINE_CHANNEL_ACCESS_TOKEN=your-token
railway variables set LINE_LIFF_ID=your-liff-id

# 部署
railway up
```

### 4. 新增 PostgreSQL

1. 在 Railway Dashboard 中點擊 "+ New"
2. 選擇 "Database" → "PostgreSQL"
3. Railway 會自動設定 `DATABASE_URL` 環境變數

### 5. 新增 Redis

1. 點擊 "+ New" → "Database" → "Redis"
2. Railway 會自動設定 `REDIS_URL` 環境變數

### 6. 部署前端

```bash
cd frontend

# 建立新服務
railway link

# 設定環境變數
railway variables set VITE_API_URL=https://your-backend.railway.app
railway variables set VITE_LIFF_ID=your-liff-id

# 部署
railway up
```

### 7. 設定自訂網域

1. 在 Railway Dashboard 中選擇服務
2. 點擊 "Settings" → "Domains"
3. 新增自訂網域或使用 Railway 提供的網域

---

## railway.toml 配置

### 後端配置

建立 `backend/railway.toml`：

```toml
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 5
```

### 前端配置

建立 `frontend/railway.toml`：

```toml
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
```

---

## GitHub 自動部署

1. 在 Railway Dashboard 連結 GitHub 儲存庫
2. 設定部署分支（通常是 `main`）
3. 每次推送到該分支時會自動部署

---

## 監控與日誌

```bash
# 即時日誌
railway logs

# 進入容器 Shell
railway shell
```

---

## 成本估算

| 方案 | 記憶體 | 費用 |
|------|--------|------|
| Hobby | 512MB | $5/月 |
| Pro | 8GB | $20/月起 |

---

## 注意事項

1. Railway 的免費額度每月 $5 美金
2. 睡眠功能：免費方案下服務可能會進入睡眠狀態
3. 建議使用 Pro 方案用於正式環境
