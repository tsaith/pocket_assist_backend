from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import time
from linebot.v3 import WebhookHandler
from app.core.config import settings
from app.lib.line.official_account import OfficialAccount
from app.lib.chatbot.linebot import Linebot


router = APIRouter(prefix="/api/v1/line", tags=["line"])


@router.post("/official-account/callback")
async def official_account_callback(request: Request):
    """
    LINE Official Account Webhook Callback
    
    處理 LINE Official Account 發送的 webhook 事件
    
    Args:
        request: FastAPI Request 對象
        
    Returns:
        dict: 處理結果
        
    Raises:
        HTTPException: 當簽名驗證失敗或處理錯誤時
    """
    start_time = time.time()
    
    try:
        # 檢查 LINE Channel Secret 和 Access Token 是否已配置
        if not settings.LINE_CHANNEL_SECRET or not settings.LINE_CHANNEL_ACCESS_TOKEN:
            raise HTTPException(
                status_code=500, 
                detail="LINE Channel Secret 或 Access Token 未配置"
            )
        
        # 驗證 LINE 簽名
        print(f"request.headers: {request.headers}")
        signature = request.headers.get('x-line-signature', '')
        if not signature:
            raise HTTPException(status_code=400, detail="Missing X-Line-Signature header")
        
        # 獲取請求體
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # 驗證簽名
        handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
        try:
            handler.handle(body_str, signature) 
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid signature: {str(e)}")

        # 解析 events
        data = json.loads(body_str)
        events = data.get('events', [])
        
        if not events:
            processing_time = int((time.time() - start_time) * 1000)
            return {
                'status': 'success',
                'processed_events': 0,
                'processing_time_ms': processing_time
            }
        
        print(f"接收到 {len(events)} 個 LINE 事件")
        
        # 使用 OfficialAccount 處理事件
        try:
            official_account = OfficialAccount()
            await official_account.handle_events(events)
            
            processing_time = int((time.time() - start_time) * 1000)
            return {
                'status': 'success',
                'processed_events': len(events),
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            print(f"OfficialAccount 處理事件失敗: {str(e)}")
            processing_time = int((time.time() - start_time) * 1000)
            return {
                'status': 'error',
                'error': str(e),
                'processed_events': 0,
                'processing_time_ms': processing_time
            }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'Internal server error',
                'message': str(e),
                'processing_time_ms': processing_time
            }
        )


class PushMessageResponse(BaseModel):
    success: bool
    message: str


@router.post("/official-account/push-message", response_model=PushMessageResponse)
async def official_account_push_message_endpoint(request: Request):
    """
    發送訊息到 LINE 用戶
    """

    data = await request.json()

    print(f"data: {data}")
    user_id = data.get("user_id")
    message = data.get("message")

    try:
        # 使用 OfficialAccount 發送訊息
        official_account = OfficialAccount()
        official_account.push_message(user_id, message)
        
        return PushMessageResponse(
            success=True,
            message="訊息已發送"
        )
        
    except Exception as e:
        error_msg = f"發送訊息到 LINE 用戶時發生錯誤：{str(e)}"
        print(error_msg)
        return PushMessageResponse(
            success=False,
            message=error_msg
        )
    
@router.post("/push-message", response_model=PushMessageResponse)
async def push_message_endpoint(request: Request):
    """
    發送訊息到 LINE 用戶
    """

    data = await request.json()

    print(f"data: {data}")
    linebot_id = data.get("linebot_id")
    user_id = data.get("user_id")
    message = data.get("message")

    try:
        linebot = Linebot(linebot_id)
        linebot.push_message(user_id, message)
        
        return PushMessageResponse(
            success=True,
            message="訊息已發送"
        )
        
    except Exception as e:
        error_msg = f"發送訊息到 LINE 用戶時發生錯誤：{str(e)}"
        print(error_msg)
        return PushMessageResponse(
            success=False,
            message=error_msg
        )