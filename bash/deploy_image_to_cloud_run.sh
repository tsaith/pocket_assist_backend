#!/bin/bash

# 檢查是否提供 image 名稱參數
if [ $# -eq 0 ]; then
    echo "請提供 image 名稱"
    echo "使用方式: $0 <image-name>"
    exit 1
fi

IMAGE_NAME=$1

# 設定 GCP 專案相關變數
PROJECT_ID="Assistbot-455712"
REGION="asia-east1"
ARTIFACT_REPO="docker-images"
APP_NAME="chatbot-service"

# 完整的 image tag
IMAGE_TAG="$REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO/$IMAGE_NAME"

echo "開始建置 Docker image..."
# 建置 Docker image
docker build -t $IMAGE_NAME .

echo "提交 image 到 Google Cloud..."
docker tag $IMAGE_NAME $IMAGE_TAG
docker push $IMAGE_TAG

# 提交 image 到 Google Cloud Artifacts Registry
#gcloud builds submit --tag $IMAGE_TAG

echo "部署到 Cloud Run..."
# 部署到 Cloud Run
gcloud run deploy $APP_NAME --image $IMAGE_TAG

echo "部署完成!"
