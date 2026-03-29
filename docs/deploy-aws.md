# AWS 部署指南

本文件說明如何將 LINE LIFF 便當訂購系統部署到 AWS。

## 目錄

1. [架構概覽](#架構概覽)
2. [前置需求](#前置需求)
3. [部署步驟](#部署步驟)
4. [成本估算](#成本估算)

---

## 架構概覽

```
                    ┌─────────────────┐
                    │   Route 53      │
                    │   (DNS)         │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   CloudFront    │
                    │   (CDN)         │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
     ┌────────▼────────┐          ┌────────▼────────┐
     │   S3 Bucket     │          │   ALB           │
     │   (Frontend)    │          │   (負載均衡器)   │
     └─────────────────┘          └────────┬────────┘
                                           │
                                  ┌────────▼────────┐
                                  │  ECS Fargate    │
                                  │  (Backend)      │
                                  └────────┬────────┘
                                           │
                    ┌─────────────────────┴─────────────────────┐
                    │                                           │
           ┌────────▼────────┐                        ┌────────▼────────┐
           │   RDS           │                        │   ElastiCache   │
           │   (PostgreSQL)  │                        │   (Redis)       │
           └─────────────────┘                        └─────────────────┘
```

---

## 前置需求

1. **AWS 帳號**
2. **AWS CLI** 已安裝並設定
3. **Terraform** (建議) 或熟悉 AWS Console
4. **Docker** 已安裝

---

## 部署步驟

### 1. 建立 ECR 儲存庫

```bash
# 登入 ECR
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com

# 建立儲存庫
aws ecr create-repository --repository-name biandang-backend --region ap-northeast-1
```

### 2. 建置並推送 Docker 映像檔

```bash
# 建置後端映像檔
cd backend
docker build -t biandang-backend .

# 標記
docker tag biandang-backend:latest <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/biandang-backend:latest

# 推送
docker push <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/biandang-backend:latest
```

### 3. 建立前端 S3 Bucket

```bash
# 建立 Bucket
aws s3 mb s3://biandang-frontend --region ap-northeast-1

# 設定靜態網站託管
aws s3 website s3://biandang-frontend --index-document index.html --error-document index.html

# 建置並上傳前端
cd frontend
npm run build
aws s3 sync dist/ s3://biandang-frontend --delete
```

### 4. 建立 RDS PostgreSQL

```bash
aws rds create-db-instance \
    --db-instance-identifier biandang-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 16 \
    --master-username postgres \
    --master-user-password <your-password> \
    --allocated-storage 20 \
    --vpc-security-group-ids <sg-id> \
    --db-subnet-group-name <subnet-group> \
    --backup-retention-period 7 \
    --multi-az \
    --storage-encrypted
```

### 5. 建立 ECS 服務

使用 AWS Console 或 Terraform 建立：
- ECS Cluster
- Task Definition
- Service
- Application Load Balancer

### 6. 設定環境變數

在 ECS Task Definition 中設定：
```json
{
  "containerDefinitions": [
    {
      "name": "biandang-backend",
      "image": "<ecr-uri>:latest",
      "portMappings": [
        {"containerPort": 8000}
      ],
      "environment": [
        {"name": "DATABASE_URL", "value": "postgresql://..."},
        {"name": "SECRET_KEY", "value": "..."}
      ],
      "secrets": [
        {"name": "LINE_CHANNEL_SECRET", "valueFrom": "arn:aws:secretsmanager:..."}
      ]
    }
  ]
}
```

---

## 成本估算（月）

| 服務 | 規格 | 預估費用 |
|------|------|----------|
| ECS Fargate | 0.5 vCPU, 1GB | ~$15 |
| RDS PostgreSQL | db.t3.micro | ~$15 |
| ElastiCache | cache.t3.micro | ~$12 |
| S3 + CloudFront | - | ~$5 |
| ALB | - | ~$20 |
| **總計** | | **~$67/月** |

---

## 注意事項

1. 設定 VPC 安全群組，限制資料庫只能從 ECS 存取
2. 使用 AWS Secrets Manager 管理敏感資訊
3. 設定 CloudWatch 監控和告警
4. 建議使用 Terraform 進行基礎設施即程式碼 (IaC)
