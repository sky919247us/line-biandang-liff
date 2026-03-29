# 部署指南

本文件說明如何將 LINE LIFF 便當訂購系統部署到生產環境。

## 目錄

1. [系統需求](#系統需求)
2. [快速部署](#快速部署)
3. [環境配置](#環境配置)
4. [LINE 設定](#line-設定)
5. [資料庫初始化](#資料庫初始化)
6. [HTTPS 設定](#https-設定)
7. [雲端部署選項](#雲端部署選項)
8. [CI/CD 設定](#cicd-設定)
9. [維護指令](#維護指令)


---

## 系統需求

- Docker 24.0+
- Docker Compose 2.0+
- 2GB+ RAM
- 10GB+ 硬碟空間

## 快速部署

### 1. 複製專案

```bash
git clone https://github.com/your-repo/biandang-liff.git
cd biandang-liff
```

### 2. 建立環境設定

```bash
cp .env.example .env
```

編輯 `.env` 檔案，填入實際設定值。

### 3. 啟動服務

```bash
# 開發環境
docker compose up -d

# 生產環境
docker compose -f docker-compose.prod.yml up -d
```

### 4. 初始化資料庫

```bash
# 執行資料庫遷移
docker compose exec backend uv run alembic upgrade head

# 載入種子資料
docker compose exec backend uv run python migrations/load_seeds.py
```

### 5. 建立管理員帳號

```bash
docker compose exec backend uv run python -c "
from app.core.database import SessionLocal
from app.models.user import User

db = SessionLocal()
admin = User(
    line_user_id='ADMIN_LINE_USER_ID',  # 替換為您的 LINE User ID
    display_name='管理員',
    role='admin'
)
db.add(admin)
db.commit()
print('管理員帳號已建立')
"
```

---

## 環境配置

### 必要設定

| 變數名稱 | 說明 | 範例 |
|---------|------|------|
| `POSTGRES_PASSWORD` | 資料庫密碼 | `your-secure-password` |
| `SECRET_KEY` | JWT 簽名金鑰 | `random-32-char-string` |
| `LINE_CHANNEL_ID` | LINE Login Channel ID | `1234567890` |
| `LINE_CHANNEL_SECRET` | LINE Channel Secret | `abcdef123456` |
| `LINE_CHANNEL_ACCESS_TOKEN` | Messaging API Token | `xyz...` |
| `LINE_LIFF_ID` | LIFF App ID | `1234567890-abcdefgh` |

### 選填設定

| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `GOOGLE_MAPS_API_KEY` | Google Maps API 金鑰 | (空) |
| `GOOGLE_MAPS_ENABLED` | 啟用 Google Maps | `false` |
| `MAX_DELIVERY_DISTANCE_KM` | 最大配送距離 (公里) | `5` |
| `MIN_ORDER_AMOUNT` | 最低消費金額 | `150` |

---

## LINE 設定

### 1. 建立 LINE Login Channel

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 建立 Provider（若尚未建立）
3. 建立 LINE Login Channel
4. 記下 Channel ID 和 Channel Secret

### 2. 建立 LIFF App

1. 在 LINE Login Channel 中建立 LIFF App
2. 設定 Endpoint URL 為您的前端網址
3. 選擇 Size: `Full`
4. 記下 LIFF ID

### 3. 建立 Messaging API Channel

1. 建立 Messaging API Channel
2. 取得 Channel Access Token
3. 設定 Webhook URL 為 `https://your-domain.com/api/v1/webhook`

---

## 資料庫初始化

### 執行遷移

```bash
docker compose exec backend uv run alembic upgrade head
```

### 載入種子資料

```bash
docker compose exec backend uv run python migrations/load_seeds.py
```

### 備份資料庫

```bash
docker compose exec db pg_dump -U postgres biandang > backup/backup_$(date +%Y%m%d).sql
```

### 還原資料庫

```bash
docker compose exec -T db psql -U postgres biandang < backup/backup_20260205.sql
```

---

## HTTPS 設定

### 使用 Let's Encrypt

1. 安裝 certbot

```bash
apt-get install certbot
```

2. 取得憑證

```bash
certbot certonly --standalone -d your-domain.com
```

3. 複製憑證到 ssl 目錄

```bash
mkdir -p ssl
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/
```

4. 更新 nginx.conf 加入 SSL 設定

---

## 雲端部署選項

除了自建伺服器，本專案也支援多種雲端平台部署：

### Railway（推薦入門）

- 簡單易用，適合快速部署
- 內建 PostgreSQL 和 Redis
- 詳細說明：[docs/deploy-railway.md](docs/deploy-railway.md)

### Render

- 免費 PostgreSQL（90 天）
- 自動 SSL 和 GitHub 整合
- 詳細說明：[docs/deploy-render.md](docs/deploy-render.md)

### AWS

- 適合企業級部署
- 使用 ECS Fargate + RDS
- 詳細說明：[docs/deploy-aws.md](docs/deploy-aws.md)

---

## CI/CD 設定

本專案已配置 GitHub Actions 工作流程：

### 持續整合 (CI)

`.github/workflows/ci.yml` 在每次推送和 PR 時執行：
- 後端 Python 測試
- 前端 TypeScript 建置
- Docker 映像檔建置驗證

### 持續部署 (CD)

`.github/workflows/cd.yml` 在推送到 main 分支時：
- 建置並推送 Docker 映像檔到 GHCR
- 自動部署到指定雲端平台
- 發送 LINE Notify 通知

### 設定 GitHub Secrets

在 GitHub 儲存庫設定中新增以下 Secrets：

| Secret 名稱 | 說明 |
|------------|------|
| `LIFF_ID` | LINE LIFF App ID |
| `API_URL` | 後端 API 網址 |
| `LINE_NOTIFY_TOKEN` | LINE Notify Token（選填）|
| `RAILWAY_TOKEN` | Railway API Token（使用 Railway 時）|
| `RENDER_BACKEND_DEPLOY_HOOK` | Render 後端 Deploy Hook（使用 Render 時）|
| `RENDER_FRONTEND_DEPLOY_HOOK` | Render 前端 Deploy Hook（使用 Render 時）|

### 設定 GitHub Variables

| Variable 名稱 | 說明 | 值 |
|--------------|------|-----|
| `DEPLOY_TARGET` | 部署目標平台 | `railway` 或 `render` |

---

## 維護指令

### 檢視日誌

```bash
# 所有服務
docker compose logs -f

# 特定服務
docker compose logs -f backend
```

### 重啟服務

```bash
docker compose restart backend
```

### 更新映像檔

```bash
docker compose pull
docker compose up -d --build
```

### 清理未使用資源

```bash
docker system prune -f
```

### 進入容器

```bash
docker compose exec backend bash
```

---

## 故障排除

### 後端無法啟動

1. 檢查資料庫連線
   ```bash
   docker compose logs db
   ```

2. 檢查環境變數
   ```bash
   docker compose exec backend env
   ```

### 前端無法連線 API

1. 檢查 nginx 設定
2. 確認後端健康狀態
   ```bash
   curl http://localhost:8000/health
   ```

### 資料庫連線失敗

1. 確認 PostgreSQL 容器正在運行
2. 檢查密碼是否正確
3. 確認網路連線

---

## 聯絡方式

如有問題，請聯繫系統管理員。
