# LINE LIFF 便當訂購系統 - 前端服務
FROM node:20-alpine AS builder

# 設定工作目錄
WORKDIR /app

# 複製專案檔案
COPY package*.json ./

# 安裝依賴
RUN npm ci

# 複製原始碼
COPY . .

# 建置生產版本
RUN npm run build

# 生產階段
FROM nginx:alpine

# 複製 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 複製建置產物
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露埠號
EXPOSE 80

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# 啟動 nginx
CMD ["nginx", "-g", "daemon off;"]
