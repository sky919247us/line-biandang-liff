# 部署指南：免費方案（$0/月）

## 架構

```
LINE 用戶 → Cloudflare Pages（前端）→ Render Free（後端）→ Neon PostgreSQL
                                                ↑
                                    UptimeRobot（每5分鐘 ping 保活）
```

## 前置準備

確認你有以下帳號和資料：
- [x] GitHub 帳號（程式碼託管）
- [x] LINE Developer Console 已建立 Messaging API + LINE Login Channel
- [ ] Neon.tech 帳號（免費 PostgreSQL）
- [ ] Render.com 帳號（免費後端）
- [ ] Cloudflare 帳號（免費前端 CDN）
- [ ] UptimeRobot 帳號（免費保活）

## 步驟一：推送至 GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的帳號/line-biandang-liff.git
git push -u origin main
```

## 步驟二：建立 Neon PostgreSQL

1. 前往 https://neon.tech → 免費註冊
2. Create Project → Region 選 **Singapore**
3. 建立後複製連線字串：
   ```
   postgresql://neondb_owner:xxxxxx@ep-xxxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```
4. 記下此連線字串，步驟三會用到

## 步驟三：部署後端到 Render

1. 前往 https://render.com → 用 GitHub 登入
2. New → **Web Service**
3. 連接 GitHub repo → 選擇 `line-biandang-liff`
4. 設定：
   - **Name**: `biandang-backend`
   - **Region**: Singapore
   - **Root Directory**: `backend`
   - **Runtime**: Docker
   - **Instance Type**: **Free**
5. 新增環境變數（Environment Variables）：

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `postgresql://...`（步驟二的 Neon 連線字串）|
| `SECRET_KEY` | 隨機字串（可用 `python -c "import secrets; print(secrets.token_hex(32))"` 產生）|
| `LINE_CHANNEL_ID` | `2009636994` |
| `LINE_CHANNEL_SECRET` | `769567f28e4a8f7fec15f8f702ccdec6` |
| `LINE_CHANNEL_ACCESS_TOKEN` | `z8fNO6F...`（完整 token）|
| `LINE_LIFF_ID` | `2009637072-d5vNxNR8` |
| `FRONTEND_URL` | （步驟四完成後回來填）|
| `DEBUG` | `false` |
| `REDIS_URL` | （留空）|

6. 點 **Create Web Service**
7. 等待部署完成，記下後端網址：`https://biandang-backend.onrender.com`

## 步驟四：部署前端到 Cloudflare Pages

1. 前往 https://dash.cloudflare.com → 註冊/登入
2. 左側選 **Workers & Pages** → **Create** → **Pages** → **Connect to Git**
3. 連接 GitHub repo → 選擇 `line-biandang-liff`
4. Build 設定：
   - **Framework preset**: None
   - **Build command**: `cd frontend && npm install && npm run build`
   - **Build output directory**: `frontend/dist`
5. 環境變數：

| Key | Value |
|-----|-------|
| `VITE_LIFF_ID` | `2009637072-d5vNxNR8` |
| `VITE_API_BASE_URL` | `https://biandang-backend.onrender.com/api/v1` |
| `NODE_VERSION` | `20` |

6. 點 **Save and Deploy**
7. 完成後取得前端網址：`https://line-biandang-liff.pages.dev`

## 步驟五：回填設定

### 5a. Render 環境變數
回到 Render Dashboard → biandang-backend → Environment：
- `FRONTEND_URL` = `https://line-biandang-liff.pages.dev`

### 5b. LINE LIFF Endpoint URL
回到 LINE Developers Console → LINE Login Channel → LIFF：
- 把 Endpoint URL 從 `https://example.com` 改為 `https://line-biandang-liff.pages.dev`

### 5c. LINE Webhook URL
回到 LINE Developers Console → Messaging API Channel → Messaging API：
- Webhook URL = `https://biandang-backend.onrender.com/api/v1/webhook`
- 打開 **Use webhook**

## 步驟六：設定 UptimeRobot 保活

1. 前往 https://uptimerobot.com → 免費註冊
2. Add New Monitor：
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: Biandang Backend
   - **URL**: `https://biandang-backend.onrender.com/health`
   - **Monitoring Interval**: 5 minutes
3. 這樣 Render Free 就不會因閒置而休眠

## 驗證部署

1. 開啟 `https://biandang-backend.onrender.com/health` → 應顯示 `{"status":"healthy"}`
2. 開啟 `https://line-biandang-liff.pages.dev` → 應顯示前端頁面
3. 在 LINE App 中開啟 LIFF URL：`https://liff.line.me/2009637072-d5vNxNR8`

## 費用總結

| 服務 | 費用 |
|------|------|
| Cloudflare Pages | 免費 |
| Render Free | 免費 |
| Neon PostgreSQL | 免費（0.5GB） |
| UptimeRobot | 免費 |
| **月總計** | **$0** |

## 未來升級路徑

當生意穩定後，只需：
1. Render Free → Starter（$7/月）：無冷啟動、更多 RAM
2. Neon Free → Launch（$19/月）：更大儲存空間
3. 加入 Redis（Render $7/月）：多實例快取
