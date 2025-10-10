from app.lib.supabase.admin import supabase_admin
from app.core.config import settings


try:
    # 從環境變數獲取用戶ID，若無則使用預設值
    user_id = settings.TEST_USER_ID
    
    print(f'開始獲取用戶 ID: {user_id} 的資訊...')
    
    # 獲取用戶認證資訊
    response = supabase_admin.auth.admin.get_user_by_id(user_id)

    print("response: ", response)
    
    user = response.user

    print(f"""
    用戶信息:
    ID: {user.id}
    Email: {user.email}
    名稱: {user.user_metadata.get('full_name', '未設定')}
    建立時間: {user.created_at}
    """)
    
except Exception as error:
    print('獲取用戶資訊時發生錯誤:', str(error))
