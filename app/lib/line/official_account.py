from typing import Dict, List, Optional, Any
import asyncio
from dataclasses import dataclass

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, TextMessage, ReplyMessageRequest
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage, ApiClient
from linebot.v3.messaging import PushMessageRequest

from app.lib.supabase import supabase_admin
from app.core.config import settings
from app.lib.chatbot_manager import chatbot_manager


@dataclass
class OfficialAccountConfig:
    """OfficialAccount 配置數據類"""
    channel_secret: str
    channel_access_token: str


@dataclass
class ChatbotResponse:
    """聊天機器人回應數據類"""
    result: str
    chatbot_id: str
    status: str
    sources: List[Any]


class OfficialAccount:
    """
    LINE Official Account 類，處理 LINE 官方帳號的相關功能
    """
    
    def __init__(self):
        """
        初始化 OfficialAccount
        """
        self.config: Optional[OfficialAccountConfig] = None
        self.messaging_api: Optional[MessagingApi] = None
        self.webhook_handler: Optional[WebhookHandler] = None

    def _get_config(self) -> OfficialAccountConfig:
        """
        從設定檔獲取 OfficialAccount 配置
        
        Returns:
            config: OfficialAccount 配置
            
        """
        if self.config:
            return self.config

        self.config = OfficialAccountConfig(
            channel_secret=settings.LINE_CHANNEL_SECRET,
            channel_access_token=settings.LINE_CHANNEL_ACCESS_TOKEN
        )

        return self.config

    def _get_messaging_api(self) -> MessagingApi:
        """
        獲取或創建 LINE Official Account Messaging API 客戶端
        
        Returns:
            MessagingApi: LINE Official Account API 客戶端
        """
        if self.messaging_api:
            return self.messaging_api

        config = self._get_config()
        
        configuration = Configuration(
            access_token=config.channel_access_token
        )
        api_client = ApiClient(configuration)
        self.messaging_api = MessagingApi(api_client)

        return self.messaging_api

    def _get_webhook_handler(self) -> WebhookHandler:
        """
        獲取或創建 Webhook Handler
        
        Returns:
            WebhookHandler: Webhook 處理器
        """
        if self.webhook_handler:
            return self.webhook_handler

        config = self._get_config()
        self.webhook_handler = WebhookHandler(config.channel_secret)

        return self.webhook_handler

    async def invoke(self, message: str, thread_id: str, platform: str = "line") -> str:
        """
        調用聊天機器人 API 獲取回覆
        
        Args:
            message: 用戶發送的訊息
            thread_id: LINE 用戶的 user_id
            platform: 平台名稱，預設為 "line"
            
        Returns:
            str: 聊天機器人的回覆
        """
        try:
            # 從 line_user_profiles 表獲取 user_id
            user_id = await self.get_user_id_by_line_user_id(thread_id)
            if not user_id:
                return '抱歉，我無法識別您的身份。請先在網站上註冊並綁定 LINE 帳號。'
            
            # 從 chatbots 表獲取 chatbot_id
            chatbot_id = await self.get_chatbot_id_by_user_id(user_id)
            if not chatbot_id:
                return '抱歉，我找不到對應的聊天機器人。請聯繫管理員。'
            
            # 獲取 chatbot 實例
            try:
                chatbot = chatbot_manager.get_chatbot(chatbot_id)
            except Exception as e:
                print(f"獲取 chatbot {chatbot_id} 失敗: {str(e)}")
                return '抱歉，聊天機器人暫時無法使用。請稍後再試。'
            
            # 調用 chatbot 獲取回應
            try:
                response = await chatbot.invoke(message, thread_id, platform)
                bot_reply = response.get('result', '抱歉，我暫時無法回應您的訊息。')
                return bot_reply
            except Exception as e:
                print(f"調用 chatbot 失敗: {str(e)}")
                return '抱歉，我暫時無法回應您的訊息。請稍後再試。'

        except Exception as e:
            error_msg = f"調用聊天機器人時發生錯誤: {str(e)}"
            print(f"[OfficialAccount] {error_msg}")
            return '抱歉，我暫時無法回應您的訊息。請稍後再試。'

    async def _process_line_event(self, event: dict, messaging_api: MessagingApi) -> bool:
        """
        處理單個 LINE 事件
        
        Args:
            event: LINE 事件對象
            messaging_api: LINE Messaging API 實例
            
        Returns:
            bool: 是否成功處理事件
        """
        try:
            # 只處理文字訊息事件
            if event.get('type') != 'message' or event.get('message', {}).get('type') != 'text':
                return False
            
            # 獲取用戶訊息和用戶ID
            user_message = event.get('message', {}).get('text', '')
            line_user_id = event.get('source', {}).get('userId', '')
            reply_token = event.get('replyToken', '')
            
            if not user_message or not line_user_id or not reply_token:
                print(f"事件缺少必要資訊: user_message={user_message}, line_user_id={line_user_id}, reply_token={reply_token}")
                return False
            
            print(f"接收到 LINE 用戶 {line_user_id} 的訊息: {user_message}")
            
            # 調用 chatbot 獲取回應
            try:
                bot_reply = await self.invoke(user_message, line_user_id, "line")
            except Exception as e:
                print(f"調用 chatbot 失敗: {str(e)}")
                bot_reply = '抱歉，我暫時無法回應您的訊息。請稍後再試。'
            
            # 回覆訊息給 LINE 用戶
            try:
                reply_message = TextMessage(text=bot_reply)
                messaging_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=[reply_message]
                    )
                )
                print(f"已回覆 LINE 用戶 {line_user_id}: {bot_reply}")
                return True
                
            except Exception as e:
                print(f"回覆 LINE 用戶失敗: {str(e)}")
                return False
                
        except Exception as e:
            print(f"處理 LINE 事件時發生錯誤: {str(e)}")
            return False

    async def get_user_id_by_line_user_id(self, line_user_id: str) -> str:
        """
        從 line_user_profiles 表獲取 user_id
        
        Args:
            line_user_id: LINE 用戶ID
            
        Returns:
            str: user_id，如果找不到則返回空字串
        """
        try:
            response = supabase_admin.table('line_user_profiles').select('user_id').eq('line_user_id', line_user_id).single().execute()
            
            if response.data and response.data.get('user_id'):
                user_id = str(response.data['user_id'])
                print(f"找到 LINE 用戶 {line_user_id} 對應的 user_id: {user_id}")
                return user_id
            else:
                print(f"找不到 LINE 用戶 {line_user_id} 對應的 user_id")
                return ""
                
        except Exception as e:
            print(f"查詢 line_user_profiles 表時發生錯誤: {str(e)}")
            return ""

    async def get_chatbot_id_by_user_id(self, user_id: str) -> str:
        """
        從 chatbots 表獲取 chatbot_id
        
        Args:
            user_id: 用戶ID
            
        Returns:
            str: chatbot_id，如果找不到則返回空字串
        """
        try:
            response = supabase_admin.table('chatbots').select('id').eq('user_id', user_id).single().execute()
            
            if response.data and response.data.get('id'):
                chatbot_id = str(response.data['id'])
                print(f"找到用戶 {user_id} 對應的 chatbot_id: {chatbot_id}")
                return chatbot_id
            else:
                print(f"找不到用戶 {user_id} 對應的 chatbot")
                return ""
                
        except Exception as e:
            print(f"查詢 chatbots 表時發生錯誤: {str(e)}")
            return ""



    def get_line_user_id_by_user_id(self, user_id: str) -> Optional[str]:
        """
        根據 user_id 獲取對應的 line_user_id
        
        Args:
            user_id: 用戶ID
            
        Returns:
            Optional[str]: line_user_id，如果找不到則返回 None
        """
        try:
            # 從 line_user_profiles 表獲取 line_user_id
            response = supabase_admin.table('line_user_profiles').select('line_user_id').eq('user_id', user_id).single().execute()
            
            if not response.data:
                print(f"找不到 user_id {user_id} 對應的 LINE 用戶資料")
                return None
            
            line_user_id = response.data.get('line_user_id')
            if line_user_id:
                print(f"找到 user_id {user_id} 對應的 line_user_id: {line_user_id}")
                return str(line_user_id)
            else:
                print(f"user_id {user_id} 沒有綁定 LINE 帳號")
                return None
                
        except Exception as e:
            print(f"根據 user_id 獲取 line_user_id 時發生錯誤: {str(e)}")
            return None

    def check_line_user_exist(self, line_user_id: str) -> bool:
        """
        檢查指定的 line_user_id 是否存在於 line_user_profiles 表中
        
        Args:
            line_user_id: LINE 用戶ID
            
        Returns:
            bool: 如果存在則返回 True，否則返回 False
        """
        try:
            response = supabase_admin.table('line_user_profiles').select('id').eq('line_user_id', line_user_id).execute()
            
            if response.data and len(response.data) > 0:
                print(f"LINE 用戶 {line_user_id} 存在")
                return True
            else:
                print(f"LINE 用戶 {line_user_id} 不存在")
                return False
                
        except Exception as e:
            print(f"檢查 LINE 用戶是否存在時發生錯誤: {str(e)}")
            return False

    async def handle_events(self, events: List[dict]) -> None:
        """
        處理 LINE Webhook 事件
        
        Args:
            events: LINE Webhook 事件列表
        """
        try:
            # 初始化 LINE Messaging API
            messaging_api = self._get_messaging_api()
            
            tasks = []
            for event in events:
                if event.get('type') == 'message' and event.get('message', {}).get('type') == 'text':
                    tasks.append(self._process_line_event(event, messaging_api))
            if tasks:
                await asyncio.gather(*tasks)
        except Exception as e:
            print(f"處理LINE Webhook事件時發生錯誤: {str(e)}")
            raise

    def push_message(self, user_id: str, message: str) -> None:
        """
        發送訊息到 LINE 用戶
        """
        try:
            messaging_api = self._get_messaging_api()
            messaging_api.push_message(PushMessageRequest(to=user_id, messages=[TextMessage(text=message)]))
            print(f"已發送訊息到 LINE 用戶 {user_id}: {message}")
        except Exception as e:
            print(f"發送訊息到 LINE 用戶時發生錯誤: {str(e)}")
            raise

    def is_configured(self) -> bool:
        """
        檢查 OfficialAccount 配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        try:
            config = self._get_config()
            return bool(config.channel_secret and config.channel_access_token)
        except Exception:
            return False

    def get_channel_secret(self) -> str:
        """
        獲取 Channel Secret（用於簽名驗證）
        
        Returns:
            str: Channel Secret
        """
        config = self._get_config()
        return config.channel_secret

    def get_webhook_handler(self) -> WebhookHandler:
        """
        獲取 Webhook Handler（供外部使用）
        
        Returns:
            WebhookHandler: Webhook 處理器
        """
        return self._get_webhook_handler()
    

# 單例模式
official_account = OfficialAccount()
