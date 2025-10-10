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


@dataclass
class LinebotConfig:
    """Linebot 配置數據類"""
    id: str
    chatbot_id: str
    channel_secret: str
    channel_access_token: str


@dataclass
class ChatbotResponse:
    """聊天機器人回應數據類"""
    result: str
    chatbot_id: str
    status: str
    sources: List[Any]


class Linebot:
    """
    LINE Bot 類，處理 LINE 機器人的相關功能
    """
    
    def __init__(self, linebot_id: str):
        """
        初始化 Linebot
        
        Args:
            linebot_id: LINE 機器人ID
        """
        self.linebot_id = linebot_id
        self.config: Optional[LinebotConfig] = None
        self.messaging_api: Optional[MessagingApi] = None
        self.webhook_handler: Optional[WebhookHandler] = None
        self.line_user_id: Optional[str] = None

    def _get_linebot_config(self) -> LinebotConfig:
        """
        從 Supabase 獲取 Linebot 配置
        
        Returns:
            LinebotConfig: Linebot 配置
            
        Raises:
            ValueError: 當找不到配置或配置無效時
        """
        if self.config:
            return self.config

        try:
            response = supabase_admin.table('linebots').select(
                'id, chatbot_id, channel_secret, channel_access_token'
            ).eq('id', self.linebot_id).single().execute()

            if not response.data:
                raise ValueError(f"找不到 ID 為 {self.linebot_id} 的 linebot")

            data = response.data
            self.config = LinebotConfig(
                id=data['id'],
                chatbot_id=data['chatbot_id'],
                channel_secret=data['channel_secret'],
                channel_access_token=data['channel_access_token']
            )

            return self.config

        except Exception as e:
            error_msg = f"獲取 linebot 配置時發生錯誤: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)

    def _get_messaging_api(self) -> MessagingApi:
        """
        獲取或創建 LINE Bot Messaging API 客戶端
        
        Returns:
            MessagingApi: LINE Bot API 客戶端
        """
        if self.messaging_api:
            return self.messaging_api

        config = self._get_linebot_config()
        
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

        config = self._get_linebot_config()
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
            config = self._get_linebot_config()
            chatbot_id = config.chatbot_id
            
            #print(f"[Linebot] 調用聊天機器人獲取回覆: {message}, {thread_id}, {platform}")
            
            # lazy import，避免循環導入
            from app.lib.chatbot_manager import chatbot_manager
            chatbot = chatbot_manager.get_chatbot(chatbot_id)

            response = await chatbot.invoke(message, thread_id, platform)
            #print(f"[Linebot] 聊天機器人回覆: {response}")
            
            # 處理新的回應格式
            if isinstance(response, dict):
                if 'result' in response:
                    return response['result']
                else:
                    raise ValueError('聊天機器人回應格式無效')
            elif isinstance(response, str):
                return response
            else:
                raise ValueError('聊天機器人回應格式無效')

        except Exception as e:
            error_msg = f"調用聊天機器人時發生錯誤: {str(e)}"
            print(f"[Linebot] {error_msg}")
            return '抱歉，我暫時無法回應您的訊息。請稍後再試。'

    async def _handle_message(self, event: dict) -> None:
        """
        處理 LINE Bot 訊息事件
        
        Args:
            event: MessageEvent 對象
        """
        # 獲取用戶ID和訊息內容
        user_id = event.get('source', {}).get('userId', 'unknown')
        user_message = event.get('message', {}).get('text', '')
        platform = "line"
        
        #print(f"接收到LINE用戶 {user_id} 的訊息: {user_message}")

        if self.line_user_id is None:
            self.line_user_id = user_id
            try:
                self._save_user_id(user_id)
            except Exception as e:
                print(f"儲存 LINE user ID 時發生錯誤: {str(e)}")

        print(f"user_id: {user_id}")
        try:
            # 使用 with ApiClient 方式發送訊息
            config = self._get_linebot_config()
            configuration = Configuration(access_token=config.channel_access_token)

            # 調用聊天機器人獲取回覆
            bot_reply = await self.invoke(user_message, user_id, platform)

            #print(f"bot_reply: {bot_reply}")
            reply_message = TextMessage(text=bot_reply)
            reply_token = event.get('replyToken')

            messaging_api = self._get_messaging_api()
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[reply_message]
                )
            )

            #print(f"已回覆LINE用戶 {user_id}: {bot_reply}")

        except Exception as e:
            print(f"處理LINE訊息時發生錯誤: {str(e)}")
            # 發送錯誤回覆
            try:
                error_message = TextMessage(text='抱歉，我暫時無法回應您的訊息。請稍後再試。')

                messaging_api = self._get_messaging_api()
                messaging_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=[error_message]
                    )
                )

            except Exception as reply_error:
                print(f"發送錯誤回覆時也失敗了: {str(reply_error)}")

    async def handle_events(self, events: List[dict]) -> None:
        """
        處理 LINE Webhook 事件
        
        Args:
            events: LINE Webhook 事件列表
        """
        try:
            tasks = []
            for event in events:
                if event.get('type') == 'message' and event.get('message', {}).get('type') == 'text':
                    tasks.append(self._handle_message(event))
            if tasks:
                await asyncio.gather(*tasks)
        except Exception as e:
            print(f"處理LINE Webhook事件時發生錯誤: {str(e)}")
            raise

    def send_message(self, message: str) -> None:
        """
        發送訊息到 LINE 用戶
        """
        user_id = self._get_line_user_id()
        if user_id:
            self.push_message(user_id, message)
        else:
            print(f"找不到 LINE user ID")

    def push_message(self, user_id: str, message: str) -> None:
        """
        發送訊息到 LINE 用戶
        """
        try:
            config = self._get_linebot_config()
            configuration = Configuration(access_token=config.channel_access_token)
            api_client = ApiClient(configuration)
            messaging_api = MessagingApi(api_client)
            messaging_api.push_message(PushMessageRequest(to=user_id, messages=[TextMessage(text=message)]))

        except Exception as e:
            print(f"發送訊息到 LINE 用戶時發生錯誤: {str(e)}")
            raise

    def get_info(self) -> Dict[str, str]:
        """
        獲取 Linebot 的基本信息
        
        Returns:
            Dict[str, str]: 包含 linebot_id 和 chatbot_id 的字典
        """
        config = self._get_linebot_config()
        return {
            "linebot_id": config.id,
            "chatbot_id": config.chatbot_id
        }

    def is_configured(self) -> bool:
        """
        檢查 Linebot 配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        try:
            config = self._get_linebot_config()
            return bool(config.channel_secret and config.channel_access_token)
        except Exception:
            return False

    def get_channel_secret(self) -> str:
        """
        獲取 Channel Secret（用於簽名驗證）
        
        Returns:
            str: Channel Secret
        """
        config = self._get_linebot_config()
        return config.channel_secret

    def get_webhook_handler(self) -> WebhookHandler:
        """
        獲取 Webhook Handler（供外部使用）
        
        Returns:
            WebhookHandler: Webhook 處理器
        """
        return self._get_webhook_handler()

    def _save_user_id(self, user_id: str) -> bool:
        """
        儲存 LINE user ID 到 linebots 表中
        
        Args:
            user_id: LINE 用戶 ID
            
        Returns:
            bool: 儲存成功回傳 True，失敗回傳 False
        """
        try:
            # 更新 linebots 表中的 line_user_id 欄位
            response = supabase_admin.table('linebots').update({
                'line_user_id': user_id,
                'updated_at': 'now()'
            }).eq('id', self.linebot_id).execute()
            
            if response.data and len(response.data) > 0:
                print(f"成功儲存 LINE user ID: {user_id} 到 linebot ID: {self.linebot_id}")
                return True
            else:
                print(f"儲存 LINE user ID 失敗：找不到 linebot ID: {self.linebot_id}")
                return False
                
        except Exception as e:
            error_msg = f"儲存 LINE user ID 時發生錯誤: {str(e)}"
            print(error_msg)
            return False

    def _get_line_user_id(self) -> str:
        """
        從 linebots 表中取得 line_user_id 欄位的值
        
        Returns:
            str: line_user_id 的值，如果沒有找到或發生錯誤則回傳空字串
        """

        if self.line_user_id:
            return self.line_user_id

        try:
            # 查詢 linebots 表中的 line_user_id 欄位
            response = supabase_admin.table('linebots').select('line_user_id').eq('id', self.linebot_id).execute()
            
            if response.data and len(response.data) > 0:
                line_user_id = response.data[0].get('line_user_id', '')
                print(f"成功取得 LINE user ID: {line_user_id} 從 linebot ID: {self.linebot_id}")
                return line_user_id
            else:
                print(f"取得 LINE user ID 失敗：找不到 linebot ID: {self.linebot_id}")
                return ''
                
        except Exception as e:
            error_msg = f"取得 LINE user ID 時發生錯誤: {str(e)}"
            print(error_msg)
            return ''
