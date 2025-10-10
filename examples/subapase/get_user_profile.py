from app.lib.supabase.admin import supabase_admin
from app.core.config import settings


def get_user_profile(user_id):
    try:
        print(f"開始獲取用戶 ID: {user_id} 的資訊...")
        
        # 從 auth 獲取用戶認證資訊
        response = supabase_admin.auth.admin.get_user_by_id(user_id)
        user = response.user
        
        # 從數據庫獲取用戶詳細資料
        response = (
            supabase_admin.table('profiles')
            .select('*')
            .eq('id', user_id)
            .single()
            .execute()
        )

        profile_data = response.data
        
        # 合併兩部分資料
        user_info = {
            'id': user.id,
            'email': user.email,
            'full_name': user.user_metadata.get('full_name', '未設定'),
            'created_at': user.created_at,
            'updated_at': user.updated_at,
            'profile': profile_data if profile_data else {'message': '無用戶詳細資料'}
        }
        
        print(f"""
        用戶資訊:
        ID: {user_info['id']}
        Email: {user_info['email']}
        名稱: {user_info['full_name']}
        建立時間: {user_info['created_at']}
        詳細資料: {user_info['profile']}
        """)
        
        return user_info

    except Exception as error:
        print('獲取用戶資訊時發生錯誤:', str(error))
        return None

if __name__ == "__main__":
    # 使用範例
    user_id = settings.TEST_USER_ID
    get_user_profile(user_id)
