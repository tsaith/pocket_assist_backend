from chatbot_service.lib.supabase.admin import supabase_admin

try:
    print('開始獲取用戶列表...')
    
    # 獲取所有用戶
    users = supabase_admin.auth.admin.list_users()

    print('用戶列表:')
    for user in users:
        print(f"""
        ID: {user.id}
        Email: {user.email}
        名稱: {user.user_metadata.get('full_name', '未設定')}
        建立時間: {user.created_at}
        """)

except Exception as error:
    print('獲取用戶列表時發生錯誤:', str(error))
