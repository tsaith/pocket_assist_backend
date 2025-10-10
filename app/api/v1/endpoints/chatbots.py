from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json

from app.core.config import settings
from app.lib.supabase.admin import supabase_admin
from app.lib.supabase.utils import require_authenticated_user


router = APIRouter(prefix="/api/v1/chatbots", tags=["chatbots"])

# 定義請求模型
class CreateChatbotRequest(BaseModel):
    name: str
    character_traits: Optional[str] = "You are a professional and witty AI assistant."

class UpdateChatbotRequest(BaseModel):
    name: Optional[str] = None
    character_traits: Optional[str] = None

# 定義回應模型
class ChatbotResponse(BaseModel):
    id: str
    user_id: str
    name: str
    character_traits: str
    created_at: str
    updated_at: str
    notebook_count: int = 0
    document_count: int = 0
    total_file_size: Optional[int] = None

class ChatbotListResponse(BaseModel):
    chatbots: List[ChatbotResponse]
    total: int

class CreateChatbotResponse(BaseModel):
    chatbot: ChatbotResponse

@router.post("/", response_model=CreateChatbotResponse, status_code=201)
async def create_chatbot(
    request: CreateChatbotRequest,
    authorization: str = Header(None)
):
    """
    POST /api/v1/chatbots
    創建新的聊天機器人
    """
    try:
        # 驗證用戶
        if not authorization:
            raise HTTPException(status_code=401, detail="未授權訪問")
        
        token = authorization.split(" ")[1] if " " in authorization else authorization
        user_id = await require_authenticated_user(token)
        
        # 檢查用戶現有聊天機器人數量是否已達到上限
        count_response = supabase_admin.table('chatbots').select('*', count='exact').eq('user_id', user_id).execute()
        current_count = count_response.count if hasattr(count_response, 'count') else 0
        
        if current_count >= 5:
            raise HTTPException(
                status_code=403, 
                detail="您已達到聊天機器人創建上限（5個）。如需創建更多，請聯繫管理員。"
            )
        
        # 驗證輸入
        if not request.name or not request.name.strip():
            raise HTTPException(status_code=400, detail="請提供有效的聊天機器人名稱")
        
        # 創建新的聊天機器人
        now = datetime.now().isoformat()
        insert_data = {
            'user_id': user_id,
            'name': request.name.strip(),
            'character_traits': request.character_traits or "You are a professional and witty AI assistant.",
            'created_at': now,
            'updated_at': now
        }
        
        response = supabase_admin.table('chatbots').insert(insert_data).select().execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=500, detail="創建聊天機器人失敗")
        
        chatbot_data = response.data[0]
        return CreateChatbotResponse(chatbot=ChatbotResponse(**chatbot_data))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"處理創建聊天機器人請求時出錯: {e}")
        raise HTTPException(status_code=500, detail="服務器錯誤") 

@router.get("/", response_model=ChatbotListResponse)
async def get_chatbots(authorization: str = Header(None)):
    """
    GET /api/v1/chatbots
    獲取當前用戶的所有聊天機器人列表
    """
    try:
        # 驗證用戶
        if not authorization:
            raise HTTPException(status_code=401, detail="未授權訪問")
        
        token = authorization.split(" ")[1] if " " in authorization else authorization
        user_id = await require_authenticated_user(token)
        
        # 獲取所有聊天機器人
        response = supabase_admin.table('chatbots').select(
            '*, notebooks:notebooks(count), documents:documents(count)'
        ).eq('user_id', user_id).order('updated_at', desc=True).execute()
        
        if not response.data:
            return ChatbotListResponse(chatbots=[], total=0)
        
        # 處理返回數據
        chatbots = []
        for chatbot in response.data:
            chatbot_data = {
                **chatbot,
                'notebook_count': chatbot.get('notebooks', [{}])[0].get('count', 0) if chatbot.get('notebooks') else 0,
                'document_count': chatbot.get('documents', [{}])[0].get('count', 0) if chatbot.get('documents') else 0,
            }
            # 移除關聯數據
            chatbot_data.pop('notebooks', None)
            chatbot_data.pop('documents', None)
            chatbots.append(ChatbotResponse(**chatbot_data))
        
        return ChatbotListResponse(chatbots=chatbots, total=len(chatbots))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"處理聊天機器人列表請求時出錯: {e}")
        raise HTTPException(status_code=500, detail="服務器錯誤")


# 定義請求模型
class UpdateChatbotRequest(BaseModel):
    name: Optional[str] = None
    character_traits: Optional[str] = None

# 定義回應模型
class ChatbotDetailResponse(BaseModel):
    id: str
    user_id: str
    name: str
    character_traits: str
    created_at: str
    updated_at: str
    notebook_count: int = 0
    document_count: int = 0
    total_file_size: Optional[int] = None

class ChatbotDetailResponseWrapper(BaseModel):
    chatbot: ChatbotDetailResponse

class SuccessResponse(BaseModel):
    success: bool

@router.get("/{chatbot_id}", response_model=ChatbotDetailResponseWrapper)
async def get_chatbot(
    chatbot_id: str,
    include_sizes: Optional[bool] = Query(False, alias="include_sizes"),
    authorization: str = Header(None)
):
    """
    GET /api/v1/chatbots/:id
    獲取單個聊天機器人詳情
    """
    try:
        # 驗證用戶
        if not authorization:
            raise HTTPException(status_code=401, detail="未授權訪問")
        
        token = authorization.split(" ")[1] if " " in authorization else authorization
        user_id = await require_authenticated_user(token)
        
        # 獲取聊天機器人信息
        response = supabase_admin.table('chatbots').select(
            '*, notebooks:notebooks(count), documents:documents(count)'
        ).eq('id', chatbot_id).eq('user_id', user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="找不到聊天機器人")
        
        chatbot = response.data[0]
        
        # 如果需要包含文件大小信息
        if include_sizes:
            # 獲取所有文件的總大小
            documents_response = supabase_admin.table('documents').select('file_size').eq('chatbot_id', chatbot_id).eq('user_id', user_id).execute()
            
            if documents_response.data:
                total_file_size = sum(doc.get('file_size', 0) for doc in documents_response.data)
                chatbot['total_file_size'] = total_file_size
        
        # 處理返回數據
        chatbot_data = {
            **chatbot,
            'notebook_count': chatbot.get('notebooks', [{}])[0].get('count', 0) if chatbot.get('notebooks') else 0,
            'document_count': chatbot.get('documents', [{}])[0].get('count', 0) if chatbot.get('documents') else 0,
        }
        # 移除關聯數據
        chatbot_data.pop('notebooks', None)
        chatbot_data.pop('documents', None)
        
        return ChatbotDetailResponseWrapper(chatbot=ChatbotDetailResponse(**chatbot_data))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"處理聊天機器人請求時出錯: {e}")
        raise HTTPException(status_code=500, detail="服務器錯誤")


@router.patch("/{chatbot_id}", response_model=ChatbotDetailResponseWrapper)
async def update_chatbot(
    chatbot_id: str,
    request: UpdateChatbotRequest,
    authorization: str = Header(None)
):
    """
    PATCH /api/v1/chatbots/:id
    更新聊天機器人
    """
    try:
        # 驗證用戶
        if not authorization:
            raise HTTPException(status_code=401, detail="未授權訪問")
        
        token = authorization.split(" ")[1] if " " in authorization else authorization
        user_id = await require_authenticated_user(token)
        
        # 驗證輸入
        if request.name is not None and (not request.name or not request.name.strip()):
            raise HTTPException(status_code=400, detail="請提供有效的名稱")
        
        # 驗證聊天機器人是否存在且屬於當前用戶
        existing_response = supabase_admin.table('chatbots').select('id').eq('id', chatbot_id).eq('user_id', user_id).execute()
        
        if not existing_response.data or len(existing_response.data) == 0:
            raise HTTPException(status_code=404, detail="找不到聊天機器人或無權限")
        
        # 準備更新數據
        updates = {
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if request.name is not None:
            updates['name'] = request.name.strip()
        if request.character_traits is not None:
            updates['character_traits'] = request.character_traits
        
        # 更新聊天機器人
        response = supabase_admin.table('chatbots').update(updates).eq('id', chatbot_id).eq('user_id', user_id).select().execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=500, detail="更新聊天機器人失敗")
        
        chatbot_data = response.data[0]
        return ChatbotDetailResponseWrapper(chatbot=ChatbotDetailResponse(**chatbot_data))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"更新聊天機器人API錯誤: {e}")
        raise HTTPException(status_code=500, detail="服務器錯誤")

@router.delete("/{chatbot_id}", response_model=SuccessResponse)
async def delete_chatbot(
    chatbot_id: str,
    authorization: str = Header(None)
):
    """
    DELETE /api/v1/chatbots/:id
    刪除聊天機器人
    """
    try:
        # 驗證用戶
        if not authorization:
            raise HTTPException(status_code=401, detail="未授權訪問")
        
        token = authorization.split(" ")[1] if " " in authorization else authorization
        user_id = await require_authenticated_user(token)
        
        # 驗證聊天機器人是否存在且屬於當前用戶
        existing_response = supabase_admin.table('chatbots').select('id').eq('id', chatbot_id).eq('user_id', user_id).execute()
        
        if not existing_response.data or len(existing_response.data) == 0:
            raise HTTPException(status_code=404, detail="找不到聊天機器人或無權限")
        
        # 刪除聊天機器人（相關的筆記本和筆記本章節會通過級聯刪除）
        response = supabase_admin.table('chatbots').delete().eq('id', chatbot_id).eq('user_id', user_id).execute()
        
        return SuccessResponse(success=True)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"刪除聊天機器人API錯誤: {e}")
        raise HTTPException(status_code=500, detail="服務器錯誤") 