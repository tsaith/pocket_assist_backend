import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

def deploy():
    """
    使用 shell 命令部署 Line Bot 專案到 Google Cloud Functions
    """
    region = "asia-east1"
    function_name = "assistbot_service" 
    runtime = "python310"
    entry_point = "entry_point"

    RUN_ENV = "production"

    deploy_command = f"""
    gcloud functions deploy {function_name} \
        --gen2 \
        --runtime {runtime} \
        --region {region} \
        --source . \
        --entry-point {entry_point} \
        --update-env-vars RUN_ENV={RUN_ENV} \
        --trigger-http \
        --allow-unauthenticated
    """

    try:
        subprocess.run(deploy_command, shell=True, check=True)
        print("部署成功!")
    except subprocess.CalledProcessError as e:
        print(f"部署失敗: {str(e)}")
        raise e

if __name__ == "__main__":

    print("Start deploy...")
    deploy()