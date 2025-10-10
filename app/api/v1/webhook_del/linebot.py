import os
import requests
import json
from fastapi import APIRouter, Request, HTTPException, Depends
from dotenv import load_dotenv

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)

from app.lib.chatbot_manager import chatbot_manager


# 創建 LINE 路由器
router = APIRouter(prefix="/api/v1/webhook")


@router.post("/linebots/{linebot_id}/callback")
async def callback(request: Request, linebot_id: str):
    """
    LINE Bot Webhook Callback
    
    處理 LINE Bot 發送的 webhook 事件
    
    Args:
        request: FastAPI Request 對象
        linebot_id: LINE Bot ID
        
    Returns:
        dict: 處理結果
        
    Raises:
        HTTPException: 當簽名驗證失敗或處理錯誤時
    """
    import time
    start_time = time.time()
    
    try:
        signature = request.headers.get('x-line-signature', '')
        if not signature:
            raise HTTPException(status_code=400, detail="Missing X-Line-Signature header")
        
        body = await request.body()
        body_str = body.decode('utf-8')
        
        print(f"[{linebot_id}] 收到 LINE Bot Webhook 請求")
        
        # 取得 chatbot/linebot 實例
        chatbot_id = chatbot_manager.get_chatbot_id_by_linebot_id(linebot_id)
        if not chatbot_id:
            raise HTTPException(status_code=404, detail="找不到對應 chatbot")
        chatbot = chatbot_manager.get_chatbot(chatbot_id)
        linebot = chatbot.get_linebot()

        # 取得 channel_secret
        channel_secret = linebot.get_channel_secret()

        # 解析 events
        data = json.loads(body_str)
        events = data.get('events', [])

        # 處理 events
        if events:
            await linebot.handle_events(events)
        processing_time = int((time.time() - start_time) * 1000)
        return {
            'status': 'success',
            'processed_events': len(events),
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
