# LINE LIFF 便當訂購系統 - 後端 API

## 專案說明

此為 LINE LIFF 便當訂購系統的後端 API 服務，使用 FastAPI 框架開發。

## 技術棧

- **框架**: FastAPI
- **資料庫**: PostgreSQL / SQLite（開發用）
- **ORM**: SQLAlchemy 2.x
- **資料驗證**: Pydantic v2
- **認證**: LINE Login + JWT

## 開發環境設定

### 1. 建立虛擬環境

```bash
uv venv
```

### 2. 安裝相依套件

```bash
uv sync
```

### 3. 設定環境變數

複製 `.env.example` 為 `.env` 並填入必要設定：

```bash
cp .env.example .env
```

### 4. 啟動開發伺服器

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API 文件

開發模式下可存取：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 目錄結構

```
backend/
├── app/
│   ├── api/              # API 路由
│   │   ├── v1/           # API v1 版本
│   │   └── deps.py       # 相依注入
│   ├── core/             # 核心設定
│   │   ├── config.py     # 應用程式設定
│   │   ├── database.py   # 資料庫連線
│   │   └── security.py   # 安全性模組
│   ├── models/           # SQLAlchemy 模型
│   ├── schemas/          # Pydantic Schema
│   ├── services/         # 業務邏輯
│   ├── repositories/     # 資料存取層
│   └── main.py           # 應用程式入口
├── migrations/           # Alembic 資料庫遷移
├── tests/                # 測試
├── pyproject.toml        # 專案設定
└── .env.example          # 環境變數範例
```

## 授權

MIT License
