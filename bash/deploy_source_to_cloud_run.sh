#!/bin/bash

# 設定 GCP 專案相關變數
PROJECT_ID="assistbot-zendev"
REGION="asia-northeast1"
SERVICE_NAME="assistbot-service"

echo "部署到 Cloud Run..."
# 部署到 Cloud Run
gcloud run deploy $SERVICE_NAME --source . --region $REGION

echo "部署完成!"
