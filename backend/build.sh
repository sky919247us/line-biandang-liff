#!/bin/bash
# Render Build Script
# 在部署時自動執行資料庫遷移

set -e

echo "=== 安裝依賴 ==="
pip install uv
uv sync --frozen --no-dev

echo "=== 執行資料庫遷移 ==="
uv run alembic upgrade head

echo "=== 建置完成 ==="
