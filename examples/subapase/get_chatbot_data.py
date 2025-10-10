from app.lib.supabase.admin import supabase_admin
from app.core.config import settings
import os
import json


def get_chatbot_info(chatbot_id, include_sections=True):
    try:
        print(f'開始獲取 Chatbot ID: {chatbot_id} 的資訊...')
        
        # 獲取 chatbot 資訊
        response = (
            supabase_admin.table('chatbots')
            .select('*')
            .eq('id', chatbot_id)
            .single()
            .execute()
        )
        
        if not response.data:
            print(f'找不到 ID 為 {chatbot_id} 的 chatbot')
            return None
            
        chatbot_data = response.data
        
        # 獲取關聯的用戶資訊
        user_id = chatbot_data.get('user_id')
        user_info = None
        
        if user_id:
            try:
                # 從 auth 獲取用戶認證資訊
                user_response = supabase_admin.auth.admin.get_user_by_id(user_id)
                
                # 檢查用戶資訊結構
                if hasattr(user_response, 'user'):
                    user_info = user_response.user
                elif hasattr(user_response, 'id'):
                    user_info = user_response
                else:
                    # 假設 user_response 本身就是我們需要的對象
                    user_info = user_response
            except Exception as user_error:
                print(f'獲取用戶資訊時發生錯誤: {str(user_error)}')
        
        # 構建完整的 chatbot 信息
        chatbot_info = {
            'id': chatbot_data.get('id'),
            'name': chatbot_data.get('name'),
            'description': chatbot_data.get('description'),
            'created_at': chatbot_data.get('created_at'),
            'updated_at': chatbot_data.get('updated_at'),
            'user_id': user_id,
            'user': None,
            'document_sections': []
        }
        
        # 如果獲取到用戶信息，添加到結果中
        if user_info:
            try:
                chatbot_info['user'] = {
                    'id': getattr(user_info, 'id', None),
                    'email': getattr(user_info, 'email', None),
                    'full_name': getattr(user_info, 'user_metadata', {}).get('full_name', '未設定') if hasattr(user_info, 'user_metadata') else '未設定',
                    'created_at': getattr(user_info, 'created_at', None)
                }
            except Exception as attr_error:
                print(f'處理用戶資訊時發生錯誤: {str(attr_error)}')
                if isinstance(user_info, dict):
                    chatbot_info['user'] = user_info
        
        # 獲取關聯的 document_sections - 直接使用 chatbot_id
        if include_sections:
            try:
                print(f'獲取 Chatbot ID: {chatbot_id} 的所有文檔片段...')
                response = (
                    supabase_admin.table('document_sections')
                    .select('id, section_index, content, metadata, created_at')
                    .eq('chatbot_id', chatbot_id)
                    .order('created_at')  # 默認升序
                    .execute()
                )
                
                section_data = response.data
                print(f'取得 {len(section_data)} 個文檔片段')
                
                chatbot_info['document_sections'] = section_data
                
            except Exception as section_error:
                print(f'獲取文檔片段時發生錯誤: {str(section_error)}')
                print(f'錯誤詳情: {type(section_error).__name__}')
        
        # 輸出結果
        print("\nChatbot 資訊:")
        print(f"ID: {chatbot_info['id']}")
        print(f"名稱: {chatbot_info['name']}")
        print(f"描述: {chatbot_info['description']}")
        print(f"創建時間: {chatbot_info['created_at']}")
        print(f"更新時間: {chatbot_info['updated_at']}")
        
        if chatbot_info['user']:
            print("\n關聯用戶資訊:")
            user = chatbot_info['user']
            print(f"用戶 ID: {user.get('id')}")
            print(f"Email: {user.get('email')}")
            print(f"名稱: {user.get('full_name')}")
            print(f"創建時間: {user.get('created_at')}")
        
        # 輸出文檔片段信息 - 直接列出所有片段，不按文檔分組
        if include_sections and 'document_sections' in chatbot_info:
            sections = chatbot_info['document_sections']
            
            if sections:
                print(f"\n文檔片段列表 (總數: {len(sections)}):")
                
                for idx, section in enumerate(sections, 1):
                    print(f"\n片段 #{idx}:")
                    print(f"ID: {section.get('id')}")
                    print(f"索引: {section.get('section_index')}")
                    
                    # 打印內容
                    content = section.get('content', '')
                    # 檢查內容長度，如果太長則截斷顯示
                    if len(content) > 100:
                        content_preview = content[:97] + "..."
                        print(f"內容 (前100字符): {content_preview}")
                    else:
                        print(f"內容: {content}")
                    
                    # 打印元數據
                    metadata = section.get('metadata', {})
                    if metadata:
                        try:
                            if isinstance(metadata, str):
                                metadata = json.loads(metadata)
                            print(f"元數據: {json.dumps(metadata, ensure_ascii=False, indent=2)}")
                        except:
                            print(f"元數據: {metadata}")
                    
                    print(f"創建時間: {section.get('created_at')}")
            else:
                print("\n沒有找到關聯的文檔片段")
        
        return chatbot_info
            
    except Exception as error:
        print('獲取 Chatbot 資訊時發生錯誤:', str(error))
        return None

if __name__ == "__main__":
    # 從環境變數或設置獲取 chatbot ID
    chatbot_id = settings.TEST_CHATBOT_ID
    
    if not chatbot_id:
        print("請提供一個有效的 Chatbot ID")
    else:
        get_chatbot_info(chatbot_id)
