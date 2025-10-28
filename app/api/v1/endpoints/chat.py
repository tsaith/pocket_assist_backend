from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

from app.lib.chatbot_manager import chatbot_manager
from app.lib.supabase.admin import supabase_admin
from app.core.config import settings

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# Define request model
class ChatRequest(BaseModel):
    chatbot_id: str
    message: str
    thread_id: str = "default"  # Add thread ID parameter, default is "default"
    platform: str = "app"  # Add platform parameter, default is "app"

# Define response model
class ChatResponse(BaseModel):
    result: str
    chatbot_id: str
    status: str
    token_usage: dict
    sources: list = []  # Add source information field

# Define Push Message request model
class PushMessageRequest(BaseModel):
    user_id: str
    chatbot_id: str
    platform: str = "app"
    sender: str  # 'human' or 'bot'
    content: str
    meta_data: Optional[dict] = {}
    private_access_token: Optional[str] = None

# Define Push Message response model
class PushMessageResponse(BaseModel):
    success: bool
    message: str
    data: dict

@router.post("/invoke", response_model=ChatResponse)
async def chat_invoke(chat_request: ChatRequest):
    try:
        # Get or create chatbot instance from chatbot_manager
        chatbot = chatbot_manager.get_chatbot(chat_request.chatbot_id)
        
        # Use chatbot instance to process request
        response = await chatbot.invoke(
            user_message=chat_request.message,
            thread_id=chat_request.thread_id,
            platform=chat_request.platform,
        )
        
        # Build API response
        return ChatResponse(
            result=response["result"],
            chatbot_id=chat_request.chatbot_id,
            token_usage=response["token_usage"],
            sources=response.get("sources", []),
            status="success",
        )
    except Exception as e:
        # Catch and log all exceptions
        error_message = f"Error occurred while processing chat request: {str(e)}"
        print(error_message)
        raise HTTPException(status_code=500, detail=error_message)

@router.post("/push-message", response_model=PushMessageResponse)
async def push_message(push_request: PushMessageRequest):
    try:
        # Validate required fields
        if not push_request.user_id or not push_request.chatbot_id or not push_request.sender or not push_request.content:
            raise HTTPException(
                status_code=400, 
                detail="Missing required fields: user_id, chatbot_id, sender, and content are required"
            )
        
        # Validate sender value
        if push_request.sender not in ['human', 'bot']:
            raise HTTPException(
                status_code=400, 
                detail="Invalid sender value. Must be either 'human' or 'bot'"
            )
        
        # Basic validation for external service calls
        if push_request.private_access_token:
            if push_request.private_access_token != settings.PRIVATE_ACCESS_TOKEN:
                raise HTTPException(
                    status_code=401, 
                    detail="Invalid private access token"
                )
        
        # Validate if chatbot belongs to the user
        chatbot_response = supabase_admin.table('chatbots').select('id, user_id, name').eq('id', push_request.chatbot_id).eq('user_id', push_request.user_id).execute()
        
        if not chatbot_response.data or len(chatbot_response.data) == 0:
            raise HTTPException(
                status_code=404, 
                detail="Chatbot not found or access denied"
            )
        
        chatbot = chatbot_response.data[0]
        
        # Insert message into chat_messages table
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
