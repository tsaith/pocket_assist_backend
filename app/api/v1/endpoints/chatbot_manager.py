from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from app.lib.chatbot_manager import chatbot_manager
from app.core.config import settings

router = APIRouter(prefix="/api/v1/chatbot-manager", tags=["chatbot-manager"])

class ResetChatbotRequest(BaseModel):
    chatbot_id: str

class ResetChatbotResponse(BaseModel):
    success: bool
    message: str
    chatbot_id: str

@router.post("/reset-chatbot", response_model=ResetChatbotResponse)
async def reset_chatbot(
    request: ResetChatbotRequest,
    authorization: str = Header(None)
):
    """
    重新初始化指定的聊天機器人
    
    Args:
        request: 包含 chatbot_id 的請求
        authorization: JWT token header
        
    Returns:
        重設結果
    """
    try:

        print(f'[ChatbotManager API] 收到重設聊天機器人請求: {request}')
        print(f'[ChatbotManager API] 收到 authorization: {authorization}')

        if not authorization:
            raise HTTPException(status_code=401, detail="缺少 authorization header")
        
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="無效的 authorization 格式")
        
        access_token = authorization.split(" ")[1]

        if access_token != settings.PRIVATE_ACCESS_TOKEN:
            raise HTTPException(status_code=401, detail="無效的 JWT token")
        
        chatbot_id = request.chatbot_id
        print(f'[ChatbotManager API] 收到重設聊天機器人請求: chatbot_id={chatbot_id}')
        
        # 呼叫 chatbot_manager 的 reset_chatbot 方法
        success = chatbot_manager.reset_chatbot(chatbot_id)
        
        if success:
            print(f'[ChatbotManager API] 聊天機器人重設成功: chatbot_id={chatbot_id}')
            return ResetChatbotResponse(
                success=True,
                message="聊天機器人重設成功",
                chatbot_id=chatbot_id
            )
        else:
            print(f'[ChatbotManager API] 聊天機器人重設失敗: chatbot_id={chatbot_id}')
            return ResetChatbotResponse(
                success=False,
                message="聊天機器人重設失敗或不存在",
                chatbot_id=chatbot_id
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f'[ChatbotManager API] 重設聊天機器人時發生錯誤: {e}')
        raise HTTPException(status_code=500, detail=f"重設聊天機器人失敗: {str(e)}")
