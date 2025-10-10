from google.cloud import storage

def gcs_download(bucket_name, source_file_path, destination_file_path):
    """從 Google Cloud Storage 下載檔案"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_file_path)
    blob.download_to_filename(destination_file_path)

    print(f"檔案 {source_file_path} 已下載到 {destination_file_path}.")

if __name__ == "__main__":

    bucket_name = "ibot_bucket"
    source_file_path = "data/1/notebook.txt"
    destination_file_path = "./data/1/notebook.txt"

    gcs_download(bucket_name, source_file_path, destination_file_path)