from chatbot_service.lib.supabase.admin import supabase_admin
import os


def delete_user(user_id):
    try:
        # 使用 admin API 刪除使用者
        supabase_admin.auth.admin.delete_user(user_id)
        print('成功刪除使用者:', user_id)
        return True

    except Exception as error:
        print('刪除使用者時發生錯誤:', str(error))
        return False

if __name__ == "__main__":
    # 使用範例
    user_id = os.getenv("USER_ID_TO_DELETE", '3b76526a-c2c3-44c6-942f-7ff9b7ab6362')
    print(f'開始刪除用戶 ID: {user_id}...')
    delete_user(user_id)
