from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.lib.supabase.admin import supabase_admin
from app.lib.supabase.utils import require_authenticated_user


router = APIRouter(prefix="/api/v1/chatbots", tags=["notebooks"])

# 定義請求模型
class CreateNotebookRequest(BaseModel):
    title: str
    content: str

class UpdateNotebookRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

# 定義回應模型
class NotebookResponse(BaseModel):
    id: str
    chatbot_id: str
    user_id: str
    title: str
    content: str
    created_at: str
    updated_at: str

class NotebookListResponse(BaseModel):
    notebooks: List[NotebookResponse]
    total: int

class NotebookDetailResponse(BaseModel):
    notebook: NotebookResponse

class CreateNotebookResponse(BaseModel):
    notebook: NotebookResponse

@router.post("/{chatbot_id}/notebooks", response_model=CreateNotebookResponse)
async def create_notebook(
    chatbot_id: str,
    request: CreateNotebookRequest,
    authorization: str = Header(None)
):
    """
    POST /api/v1/chatbots/:id/notebooks
    創建新的筆記本
    """
    try:
        # 驗證用戶
        if not authorization:
            raise HTTPException(status_code=401, detail="未授權訪問")
        
        token = authorization.split(" ")[1] if " " in authorization else authorization
        user_id = await require_authenticated_user(token)
        
        # 驗證聊天機器人是否存在且屬於當前用戶
        chatbot_response = supabase_admin.table('chatbots').select('id').eq('id', chatbot_id).eq('user_id', user_id).execute()
        
        if not chatbot_response.data or len(chatbot_response.data) == 0:
            raise HTTPException(status_code=404, detail="找不到聊天機器人")
        
        # 驗證輸入
        if not request.title or not request.title.strip():
            raise HTTPException(status_code=400, detail="請提供有效的筆記本標題")
        
        # 創建筆記本
        now = datetime.utcnow().isoformat()
        insert_data = {
            'chatbot_id': chatbot_id,
            'user_id': user_id,
            'title': request.title.strip(),
            'content': request.content or "",
            'created_at': now,
            'updated_at': now
        }
        
        response = supabase_admin.table('notebooks').insert(insert_data).select().execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=500, detail="創建筆記本失敗")
        
        notebook_data = response.data[0]
        return CreateNotebookResponse(notebook=NotebookResponse(**notebook_data))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"處理創建筆記本請求時出錯: {e}")
        raise HTTPException(status_code=500, detail="服務器錯誤")
@router.get("/{chatbot_id}/notebooks", response_model=NotebookListResponse)
async def get_notebooks(
    chatbot_id: str,
    authorization: str = Header(None)
):
    """
    GET /api/v1/chatbots/:id/notebooks
    獲取聊天機器人的所有筆記本列表
    """
    try:
        # 驗證用戶
        if not authorization:
            raise HTTPException(status_code=401, detail="未授權訪問")
        
        token = authorization.split(" ")[1] if " " in authorization else authorization
        user_id = await require_authenticated_user(token)
        
        # 驗證聊天機器人是否存在且屬於當前用戶
        chatbot_response = supabase_admin.table('chatbots').select('id').eq('id', chatbot_id).eq('user_id', user_id).execute()
        
        if not chatbot_response.data or len(chatbot_response.data) == 0:
            raise HTTPException(status_code=404, detail="找不到聊天機器人或無權限")
        
        # 獲取筆記本列表
        response = supabase_admin.table('notebooks').select('*').eq('chatbot_id', chatbot_id).eq('user_id', user_id).order('updated_at', desc=True).execute()
        
        if not response.data:
            return NotebookListResponse(notebooks=[], total=0)
        
        notebooks = [NotebookResponse(**notebook) for notebook in response.data]
        return NotebookListResponse(notebooks=notebooks, total=len(notebooks))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"處理筆記本列表請求時出錯: {e}")
        raise HTTPException(status_code=500, detail="服務器錯誤")


@router.get("/{chatbot_id}/notebooks/{notebook_id}", response_model=NotebookDetailResponse)
async def get_notebook(
    chatbot_id: str,
    notebook_id: str,
    authorization: str = Header(None)
):
    """
    GET /api/v1/chatbots/:id/notebooks/:notebookId
    獲取單個筆記本詳情
    """
    try:
        # 驗證用戶
        if not authorization:
            raise HTTPException(status_code=401, detail="未授權訪問")
        
        token = authorization.split(" ")[1] if " " in authorization else authorization
        user_id = await require_authenticated_user(token)
        
        # 獲取筆記本詳情
        response = supabase_admin.table('notebooks').select('*').eq('id', notebook_id).eq('chatbot_id', chatbot_id).eq('user_id', user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="找不到此筆記本或您沒有訪問權限")
        
        notebook_data = response.data[0]
        return NotebookDetailResponse(notebook=NotebookResponse(**notebook_data))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"獲取筆記本時出錯: {e}")
        raise HTTPException(status_code=500, detail="服務器錯誤")

@router.patch("/{chatbot_id}/notebooks/{notebook_id}", response_model=NotebookDetailResponse)
async def update_notebook(
    chatbot_id: str,
    notebook_id: str,
    request: UpdateNotebookRequest,
    authorization: str = Header(None)
):
    """
    PATCH /api/v1/chatbots/:id/notebooks/:notebookId
    更新筆記本
    """
    try:
        # 驗證用戶
        if not authorization:
            raise HTTPException(status_code=401, detail="未授權訪問")
        
        token = authorization.split(" ")[1] if " " in authorization else authorization
        user_id = await require_authenticated_user(token)
        
        # 驗證筆記本是否存在且屬於當前用戶和聊天機器人
        existing_response = supabase_admin.table('notebooks').select('id').eq('id', notebook_id).eq('chatbot_id', chatbot_id).eq('user_id', user_id).execute()
        
        if not existing_response.data or len(existing_response.data) == 0:
            raise HTTPException(status_code=404, detail="找不到筆記本或無權限")
        
        # 準備更新數據
        updates = {
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if request.title is not None:
            if not request.title.strip():
                raise HTTPException(status_code=400, detail="請提供有效的標題")
            updates['title'] = request.title.strip()
        
        if request.content is not None:
            updates['content'] = request.content
        
        # 更新筆記本
        response = supabase_admin.table('notebooks').update(updates).eq('id', notebook_id).eq('chatbot_id', chatbot_id).eq('user_id', user_id).select().execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=500, detail="更新筆記本失敗")
        
        notebook_data = response.data[0]
        return NotebookDetailResponse(notebook=NotebookResponse(**notebook_data))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"更新筆記本時出錯: {e}")
        raise HTTPException(status_code=500, detail="服務器錯誤")

@router.delete("/{chatbot_id}/notebooks/{notebook_id}")
async def delete_notebook(
    chatbot_id: str,
    notebook_id: str,
    authorization: str = Header(None)
):
    """
    DELETE /api/v1/chatbots/:id/notebooks/:notebookId
    刪除筆記本
    """
    try:
        # 驗證用戶
        if not authorization:
            raise HTTPException(status_code=401, detail="未授權訪問")
        
        token = authorization.split(" ")[1] if " " in authorization else authorization
        user_id = await require_authenticated_user(token)
        
        # 驗證筆記本是否存在且屬於當前用戶和聊天機器人
        existing_response = supabase_admin.table('notebooks').select('id').eq('id', notebook_id).eq('chatbot_id', chatbot_id).eq('user_id', user_id).execute()
        
        if not existing_response.data or len(existing_response.data) == 0:
            raise HTTPException(status_code=404, detail="找不到筆記本或無權限")
        
        # 刪除筆記本
        response = supabase_admin.table('notebooks').delete().eq('id', notebook_id).eq('chatbot_id', chatbot_id).eq('user_id', user_id).execute()
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"刪除筆記本時出錯: {e}")
        raise HTTPException(status_code=500, detail="服務器錯誤") 