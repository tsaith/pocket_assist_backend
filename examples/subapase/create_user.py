from chatbot_service.lib.supabase.admin import supabase_admin
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def create_user(email, password, full_name=None):
    try:
        # 準備用戶資料
        user_data = {
            "email": email,
            "password": password,
            "email_confirm": True,  # 自動確認郵箱，跳過驗證步驟
        }
        
        # 如果提供了全名，添加到元數據中
        if full_name:
            user_data["user_metadata"] = {"full_name": full_name}
            
        # 使用 admin API 註冊使用者
        user = supabase_admin.auth.admin.create_user(user_data)

        print(f"""
        成功註冊使用者:
        ID: {user.id}
        Email: {user.email}
        名稱: {user.user_metadata.get('full_name', '未設定')}
        """)
        return user

    except Exception as error:
        print('註冊錯誤:', str(error))
        return None

if __name__ == "__main__":
    # 使用範例
    email = os.getenv("NEW_USER_EMAIL", "aerith@example.com")
    password = os.getenv("NEW_USER_PASSWORD", "aerith_password") 
    full_name = os.getenv("NEW_USER_NAME", "Aerith Gainsborough")
    
    print(f'開始創建用戶，郵箱: {email}...')
    create_user(email, password, full_name)
