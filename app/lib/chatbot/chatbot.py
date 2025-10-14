from typing import List, Dict, Any, Tuple, Optional
import asyncio
from datetime import datetime

from app.lib.chatbot.chatbot_base import ChatbotBase
from app.lib.supabase import supabase_admin
from app.lib.chatbot.linebot import Linebot
from app.lib.utils import save_chat_message, save_token_usage
from app.lib.credit_manager import CreditManager

class Chatbot(ChatbotBase):
    """
    聊天機器人類，繼承 Agent 並添加聊天機器人特有的功能
    """

    #def __init__(self, model: str = "gpt-4o"):
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        初始化聊天機器人
        
        Args:
            chatbot_id: 聊天機器人ID
            model: 使用的模型名稱
        """
        # 初始化父類 Agent
        super().__init__(model)

        self.user_id = None

        # 聊天機器人特有屬性
        self.chatbot_id = None
        self.chatbot_data = None

        # 緩存屬性
        self.chatbot_info: Optional[Dict[str, Any]] = None
        self.linebot_id: Optional[str] = None
        self.linebot: Optional[Any] = None  # 避免循環導入，暫時用 Any
        self.user_id: Optional[str] = None

    def init(self, chatbot_id: str):
        """
        初始化聊天機器人，獲取相關數據並設置檢索器
        
        Args:
            chatbot_id: 聊天機器人ID
            
        Returns:
            self: 返回自身以支持鏈式調用
        """
        self.chatbot_id = chatbot_id
        # 清除緩存，因為 chatbot_id 可能已更改
        self.clear_cache()

        # 從 Supabase 獲取 chatbot 資料
        response = supabase_admin.table('chatbots').select('*').eq('id', chatbot_id).single().execute()

        if not response or not response.data:
            raise ValueError(f"找不到 ID 為 {chatbot_id} 的 chatbot")
            
        self.chatbot_data = response.data
        chatbot_name = self.chatbot_data.get('name', 'AI助手')
        character_traits = self.chatbot_data.get('character_traits', '')
        
        # 從 chatbot 資料中獲取 user_id
        self.user_id = self.chatbot_data.get('user_id')
        if not self.user_id:
            raise ValueError(f"找不到 chatbot {chatbot_id} 對應的 user_id")
        
        print(f"初始化 Chatbot: {chatbot_name}, User ID: {self.user_id}")
        
        self.setup_agent(self.user_id, chatbot_name, character_traits)
        
        return self

    async def invoke(self, user_message: str, thread_id: str = "default", platform: str = "app") -> Dict[str, Any]:
        """
        處理使用者訊息並儲存對話記錄
        
        Args:
            user_message: 使用者訊息
            thread_id: 對話線程ID
            platform: 平台類型 (app, line, unknown)
            
        Returns:
            Dict: 包含回應結果和相關資訊
        """
        
        try:
            # 獲取 chatbot 對應的 user_id
            user_id = self.get_user_id()
            if not user_id:
                raise ValueError('找不到對應的 chatbot 或 user_id')

            # 查詢 credit balance
            credit_balance = await CreditManager.get_credit_balance(user_id)

            print(f"user_id: {user_id}, chatbot_id: {self.chatbot_id}, thread_id: {thread_id}, platform: {platform}")

            # 判斷餘額
            if credit_balance.balance <= 0:
                error_message = '抱歉，由於 Credits 不足，無法繼續提供對話服務。'
                user_message = f'請回復 {error_message}'

            # 呼叫父類 Agent 的 invoke 方法
            response = super().invoke(user_message, thread_id)

            # 如果回應成功，儲存機器人回應並消耗 credits
            if 'result' in response:

                # Consume credits from tokens
                token_usage = response['token_usage']
                total_tokens = token_usage.get('total_tokens', 0)
                    
                try:
                    await CreditManager.consume_credits_from_tokens(user_id, total_tokens)
                except Exception as error:
                    print(f'Failed to consume credits: {error}')
                
                # 儲存 token 使用量
                input_tokens = token_usage.get('input_tokens', 0)
                output_tokens = token_usage.get('output_tokens', 0)
                total_tokens = token_usage.get('total_tokens', input_tokens + output_tokens)
                input_token_details = token_usage.get('input_token_details', {})
                output_token_details = token_usage.get('output_token_details', {})
                    
                try:
                    await save_token_usage(
                        self.chatbot_id,
                        input_tokens,
                        output_tokens,
                        total_tokens,
                        input_token_details,
                        output_token_details
                    )
                except Exception as error:
                    print(f'Failed to save token usage: {error}')

            return response

        except Exception as error:
            print(f'Error in Chatbot.invoke: {error}')
            raise error
        
    def get_chatbot_info(self) -> Optional[Dict[str, Any]]:
        """
        從 Supabase 獲取聊天機器人基本信息
        
        Returns:
            Dict 包含 id, name, description, user_id，如果找不到則返回 None
        """
        if self.chatbot_info:
            return self.chatbot_info

        if not self.chatbot_id:
            print("錯誤：chatbot_id 未設置")
            return None

        try:
            response = supabase_admin.table('chatbots').select(
                'id, user_id, name, character_traits'
            ).eq('id', self.chatbot_id).single().execute()

            if not response.data:
                print(f"找不到 chatbot_id: {self.chatbot_id}")
                return None

            # 將 character_traits 映射為 description
            data = response.data
            self.chatbot_info = {
                'id': data['id'],
                'name': data['name'], 
                'description': data['character_traits'],
                'user_id': data['user_id']
            }
            return self.chatbot_info

        except Exception as e:
            print(f"獲取聊天機器人信息時發生錯誤: {str(e)}")
            return None

    def get_linebot(self):
        """
        獲取此聊天機器人的 Linebot 實例
        
        Returns:
            Linebot: Linebot 實例
            
        Raises:
            ValueError: 當找不到關聯的 linebot_id 時
        """
        if self.linebot:
            return self.linebot
            
        linebot_id = self._get_linebot_id()
        if not linebot_id:
            raise ValueError(f'找不到 chatbot_id {self.chatbot_id} 對應的 linebot_id')
        
        # 延遲導入避免循環依賴
        self.linebot = Linebot(linebot_id)
        return self.linebot

    def _get_linebot_id(self) -> Optional[str]:
        """
        根據 chatbot_id 從 Supabase 獲取 linebot_id
        
        Returns:
            str: linebot_id，如果找不到則返回 None
        """
        if self.linebot_id:
            return self.linebot_id

        if not self.chatbot_id:
            return None

        try:
            response = supabase_admin.table('linebots').select(
                'id'
            ).eq('chatbot_id', self.chatbot_id).single().execute()

            if not response.data:
                print(f"找不到 chatbot_id {self.chatbot_id} 對應的 linebot")
                return None

            self.linebot_id = response.data['id']
            return self.linebot_id

        except Exception as e:
            print(f"獲取 linebot_id 時發生錯誤: {str(e)}")
            return None

    def has_linebot(self) -> bool:
        """
        檢查此聊天機器人是否有關聯的 linebot
        
        Returns:
            bool: 是否有關聯的 linebot
        """
        linebot_id = self._get_linebot_id()
        return linebot_id is not None

    def get_associated_linebot_id(self) -> Optional[str]:
        """
        獲取關聯的 linebot_id
        
        Returns:
            str: linebot_id，如果找不到則返回 None
        """
        return self._get_linebot_id()

    def is_valid(self) -> bool:
        """
        檢查聊天機器人是否存在且有效
        
        Returns:
            bool: 聊天機器人是否有效
        """
        info = self.get_chatbot_info()
        return info is not None

    def get_id(self) -> Optional[str]:
        """
        獲取聊天機器人 ID
        
        Returns:
            str: 聊天機器人 ID
        """
        return self.chatbot_id

    def get_user_id(self) -> Optional[str]:
        """
        獲取擁有此聊天機器人的用戶 ID
        
        Returns:
            str: 用戶 ID，如果找不到則返回 None
        """
        if self.user_id:
            return self.user_id

        try:
            chatbot_info = self.get_chatbot_info()
            if chatbot_info and chatbot_info.get('user_id'):
                self.user_id = chatbot_info['user_id']
                return self.user_id
            
            return None
        except Exception as e:
            print(f"獲取 user_id 時發生錯誤: {str(e)}")
            return None

    def clear_cache(self) -> None:
        """
        清除緩存數據（用於測試或當數據可能已更改時）
        """
        self.linebot_id = None
        self.linebot = None
        self.chatbot_info = None
        self.user_id = None

