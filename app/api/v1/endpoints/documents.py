from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json

from app.lib.supabase.admin import supabase_admin
from app.lib.supabase.utils import require_authenticated_user


router = APIRouter(prefix="/api/v1/chatbots", tags=["documents"])

# 定義回應模型
class DocumentResponse(BaseModel):
    id: str
    chatbot_id: str
    user_id: str
    file_name: str
    file_type: str
    file_size: int
    content_preview: str
    content_count: int
    created_at: str
    updated_at: str

class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int

class DocumentDetailResponse(BaseModel):
    document: DocumentResponse

class CreateDocumentResponse(BaseModel):
    document: DocumentResponse

@router.get("/{chatbot_id}/documents", response_model=DocumentListResponse)
async def get_documents(
    chatbot_id: str,
    authorization: str = Header(None)
):
    """
    GET /api/v1/chatbots/:id/documents
    獲取聊天機器人的所有文檔列表
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
        
        # 獲取文檔列表
        response = supabase_admin.table('documents').select('*').eq('chatbot_id', chatbot_id).eq('user_id', user_id).order('created_at', desc=True).execute()
        
        if not response.data:
            return DocumentListResponse(documents=[], total=0)
        
        documents = [DocumentResponse(**doc) for doc in response.data]
        return DocumentListResponse(documents=documents, total=len(documents))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"處理文檔列表請求時出錯: {e}")
        raise HTTPException(status_code=500, detail="服務器錯誤")

@router.post("/{chatbot_id}/documents", response_model=CreateDocumentResponse)
async def upload_document(
    chatbot_id: str,
    file: UploadFile = File(...),
    authorization: str = Header(None)
):
    """
    POST /api/v1/chatbots/:id/documents
    上傳文檔到聊天機器人
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
        
        # 驗證文件類型
        allowed_types = ['text/plain', 'application/pdf']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="僅支持 .txt 和 .pdf 文件")
        
        # 驗證文件大小（10MB）
        if file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超過 10MB")
        
        # 讀取文件內容
        content = await file.read()
        content_text = content.decode('utf-8')
        
        if not content_text.strip():
            raise HTTPException(status_code=400, detail="文件內容為空或無法讀取")
        
        # 取前 1000 字元作為 content_preview
        content_preview = content_text[:1000]
        
        # 創建文檔記錄
        now = datetime.utcnow().isoformat()
        insert_data = {
            'chatbot_id': chatbot_id,
            'user_id': user_id,
            'content': content_text.strip(),
            'content_preview': content_preview.strip(),
            'content_count': len(content_text),
            'file_name': file.filename,
            'file_type': file.content_type,
            'file_size': file.size,
            'created_at': now,
            'updated_at': now
        }
        
        response = supabase_admin.table('documents').insert(insert_data).select().execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=500, detail="上傳文件失敗")
        
        document_data = response.data[0]
        return CreateDocumentResponse(document=DocumentResponse(**document_data))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"處理文件上傳請求時出錯: {e}")
        raise HTTPException(status_code=500, detail="服務器錯誤")

@router.get("/{chatbot_id}/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    chatbot_id: str,
    document_id: str,
    authorization: str = Header(None)
):
    """
    GET /api/v1/chatbots/:id/documents/:documentId
    獲取單個文檔詳情
    """
    try:
        # 驗證用戶
        if not authorization:
            raise HTTPException(status_code=401, detail="未授權訪問")
        
        token = authorization.split(" ")[1] if " " in authorization else authorization
        user_id = await require_authenticated_user(token)
        
        # 獲取文檔詳情
        response = supabase_admin.table('documents').select(
            'id, chatbot_id, user_id, file_name, file_type, file_size, created_at, updated_at, content_preview'
        ).eq('id', document_id).eq('chatbot_id', chatbot_id).eq('user_id', user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="找不到此文檔或您沒有訪問權限")
        
        document_data = response.data[0]
        return DocumentDetailResponse(document=DocumentResponse(**document_data))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"獲取文檔時出錯: {e}")
        raise HTTPException(status_code=500, detail="服務器錯誤")

@router.delete("/{chatbot_id}/documents/{document_id}")
async def delete_document(
    chatbot_id: str,
    document_id: str,
    authorization: str = Header(None)
):
    """
    DELETE /api/v1/chatbots/:id/documents/:documentId
    刪除文檔
    """
    try:
        # 驗證用戶
        if not authorization:
            raise HTTPException(status_code=401, detail="未授權訪問")
        
        token = authorization.split(" ")[1] if " " in authorization else authorization
        user_id = await require_authenticated_user(token)
        
        # 驗證文檔是否存在且屬於當前用戶和聊天機器人
        existing_response = supabase_admin.table('documents').select('id').eq('id', document_id).eq('chatbot_id', chatbot_id).eq('user_id', user_id).execute()
        
        if not existing_response.data or len(existing_response.data) == 0:
            raise HTTPException(status_code=404, detail="找不到文檔或無權限")
        
        # 刪除文檔
        response = supabase_admin.table('documents').delete().eq('id', document_id).eq('chatbot_id', chatbot_id).eq('user_id', user_id).execute()
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"刪除文檔時出錯: {e}")
        raise HTTPException(status_code=500, detail="服務器錯誤") 