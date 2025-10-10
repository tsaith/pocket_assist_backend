from chatbot_service.lib.supabase.admin import supabase_admin
import os


def update_user(user_id, user_data):
    try:
        # 過濾掉空值
        filtered_data = {k: v for k, v in user_data.items() if v not in ['', None]}
        
        results = {}
        
        # 更新用戶認證資訊
        if 'email' in filtered_data or 'password' in filtered_data:
            auth_data = {}
            if 'email' in filtered_data:
                auth_data['email'] = filtered_data.pop('email')
            if 'password' in filtered_data:
                auth_data['password'] = filtered_data.pop('password')
            
            updated_user = supabase_admin.auth.admin.update_user_by_id(user_id, auth_data)
            results['auth_update'] = {
                'email': updated_user.email,
                'updated_at': updated_user.updated_at
            }
            print('更新用戶認證資訊成功')

        # 更新用戶資料表
        if filtered_data:
            response = (
                supabase_admin.table('profiles')
                .update(filtered_data)
                .eq('id', user_id)
                .execute()
            )
            results['profile_update'] = response.data
            print('更新用戶資料表成功:', response.data)
            
        return results

    except Exception as error:
        print('更新用戶資料時發生錯誤:', str(error))
        return None

if __name__ == "__main__":
    # 使用範例
    user_id = os.getenv("USER_ID_TO_UPDATE", '189cd60c-7c7c-445e-a053-63560d754803')
    user_data = {
        'email': os.getenv("NEW_EMAIL", "tifa@example.com"),
        'role': os.getenv("NEW_ROLE", "admin")
    }
    
    print(f'開始更新用戶 ID: {user_id}...')
    update_user(user_id, user_data)
