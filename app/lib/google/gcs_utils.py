from google.cloud import storage
import os
from typing import Optional

def gcs_download(bucket_name, source_file_path, destination_file_path):
    """從 Google Cloud Storage 下載檔案"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_file_path)
    blob.download_to_filename(destination_file_path)

    print(f"檔案 {source_file_path} 已下載到 {destination_file_path}.")

def gcs_upload(bucket_name: str, source_file_path: str, destination_file_path: str, 
               project_id: Optional[str] = None) -> None:
    """從 Google Cloud Storage 上傳檔案
    
    Args:
        bucket_name: GCS bucket 名稱
        source_file_path: 本地端檔案路徑
        destination_file_path: 要上傳到 GCS 中的路徑
        project_id: GCP 專案 ID，預設為 None 使用預設專案
    
    Raises:
        google.cloud.exceptions.NotFound: bucket 不存在時
        google.cloud.exceptions.Forbidden: 沒有權限時
        FileNotFoundError: 本地端檔案不存在時
    """
    # 檢查本地端檔案是否存在
    if not os.path.exists(source_file_path):
        raise FileNotFoundError(f"找不到檔案: {source_file_path}")
        
    try:
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_file_path)
        blob.upload_from_filename(source_file_path)
        print(f"檔案 {source_file_path} 已成功上傳到 {destination_file_path}.")

    except Exception as e:
        print(f"上傳失敗: {str(e)}")
        raise