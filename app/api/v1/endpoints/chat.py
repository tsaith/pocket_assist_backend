from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

from app.lib.chatbot_manager import chatbot_manager
from app.lib.supabase.admin import supabase_admin
from app.core.config import settings

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# 定義請求模型
class ChatRequest(BaseModel):
    chatbot_id: str
    message: str
    thread_id: str = "default"  # 添加線程ID參數，默認為"default"
    platform: str = "app"  # 添加平台參數，默認為"app"

# 定義回應模型
class ChatResponse(BaseModel):
    result: str
    chatbot_id: str
    status: str
    token_usage: dict
    sources: list = []  # 添加來源資訊欄位

# 定義 Push Message 請求模型
class PushMessageRequest(BaseModel):
    user_id: str
    chatbot_id: str
    platform: str = "app"
    sender: str  # 'human' or 'bot'
    content: str
    meta_data: Optional[dict] = {}
    private_access_token: Optional[str] = None

# 定義 Push Message 回應模型
class PushMessageResponse(BaseModel):
    success: bool
    message: str
    data: dict

@router.post("/invoke", response_model=ChatResponse)
async def chat_invoke(chat_request: ChatRequest):
    try:
        # 從chatbot_manager獲取或創建chatbot實例
        chatbot = chatbot_manager.get_chatbot(chat_request.chatbot_id)
        
        # 使用chatbot實例處理請求
        response = await chatbot.invoke(
            user_message=chat_request.message,
            thread_id=chat_request.thread_id,
            platform=chat_request.platform,
        )
        
        # 構建API回應
        return ChatResponse(
            result=response["result"],
            chatbot_id=chat_request.chatbot_id,
            token_usage=response["token_usage"],
            sources=response.get("sources", []),
            status="success",
        )
    except Exception as e:
        # 捕獲並記錄所有異常
        error_message = f"處理聊天請求時發生錯誤: {str(e)}"
        print(error_message)
        raise HTTPException(status_code=500, detail=error_message)

@router.post("/push-message", response_model=PushMessageResponse)
async def push_message(push_request: PushMessageRequest):
    try:
        # 驗證必要欄位
        if not push_request.user_id or not push_request.chatbot_id or not push_request.sender or not push_request.content:
            raise HTTPException(
                status_code=400, 
                detail="Missing required fields: user_id, chatbot_id, sender, and content are required"
            )
        
        # 驗證 sender 值
        if push_request.sender not in ['human', 'bot']:
            raise HTTPException(
                status_code=400, 
                detail="Invalid sender value. Must be either 'human' or 'bot'"
            )
        
        # 基本驗證外部服務呼叫
        if push_request.private_access_token:
            if push_request.private_access_token != settings.PRIVATE_ACCESS_TOKEN:
                raise HTTPException(
                    status_code=401, 
                    detail="Invalid private access token"
                )
        
        # 驗證 chatbot 是否屬於該用戶
        chatbot_response = supabase_admin.table('chatbots').select('id, user_id, name').eq('id', push_request.chatbot_id).eq('user_id', push_request.user_id).execute()
        
        if not chatbot_response.data or len(chatbot_response.data) == 0:
            raise HTTPException(
                status_code=404, 
                detail="Chatbot not found or access denied"
            )
        
        chatbot = chatbot_response.data[0]
        
        # 插入訊息到 chat_messages 表格
        message_data = {
            'user_id': push_request.user_id,
            'chatbot_id': push_request.chatbot_id,
            'platform': push_request.platform,
            'sender': push_request.sender,
            'content': push_request.content,
            'meta_data': {}
        }
        
        message_response = supabase_admin.table('chat_messages').insert(message_data).execute()
        
        if not message_response.data or len(message_response.data) == 0:
            raise HTTPException(
                status_code=500, 
                detail="Failed to store message"
            )
        
        message = message_response.data[0]
        
        print(f"Message pushed successfully.")
        
        return PushMessageResponse(
            success=True,
            message="Message pushed successfully",
            data={
                'message': {
                    'id': message['id'],
                    'user_id': message['user_id'],
                    'chatbot_id': message['chatbot_id'],
                    'platform': message['platform'],
                    'sender': message['sender'],
                    'content': message['content'],
                    'meta_data': message['meta_data'],
                    'created_at': message['created_at']
                },
                'chatbot': {
                    'id': chatbot['id'],
                    'name': chatbot['name']
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_message = f"Push message API error: {str(e)}"
        print(error_message)
        raise HTTPException(status_code=500, detail=error_message)
