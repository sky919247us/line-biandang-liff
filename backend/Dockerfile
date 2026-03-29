# LINE LIFF 便當訂購系統 - 後端服務
FROM python:3.12-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安裝 uv
RUN pip install uv

# 複製專案檔案
COPY pyproject.toml ./
COPY uv.lock ./

# 安裝 Python 依賴
RUN uv sync --frozen --no-dev

# 複製應用程式碼
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./

# 建立非 root 使用者
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露埠號
EXPOSE 8000

# Render 使用 PORT 環境變數
ENV PORT=8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# 啟動時執行遷移 + 啟動伺服器
CMD uv run alembic upgrade head && \
    uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
