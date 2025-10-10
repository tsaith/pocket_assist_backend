from app.lib.supabase.admin import supabase_admin
from app.core.config import settings
import os


def set_user_as_admin(user_id, role='admin'):
    try:
        # 設置用戶角色
        response = (
            supabase_admin.table('profiles')
            .update({'role': role})
            .eq('id', user_id)
            .execute()
        )

        if not response.data:
            print(f'無法找到用戶 ID: {user_id} 的資料')
            return False
            
        # 獲取更新後的資料
        updated_user = response.data[0]
        
        print(f"""
        用戶角色已更新：
        ID: {updated_user.get('id')}
        角色: {updated_user.get('role')}
        更新時間: {updated_user.get('updated_at')}
        """)
        
        return updated_user

    except Exception as error:
        print('更新用戶角色時發生錯誤:', str(error))
        return None

if __name__ == "__main__":
    # 使用範例
    user_id = settings().TEST_USER_ID
    role = 'admin'
    
    print(f'開始設置用戶 ID: {user_id} 為 {role} 角色...')
    set_user_as_admin(user_id, role)
