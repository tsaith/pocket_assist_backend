from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.lib.supabase.admin import supabase_admin
from app.lib.supabase.utils import require_authenticated_user
from app.core.config import settings
from pydantic import EmailStr
import resend
import re

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class DeleteAccountRequest(BaseModel):
    user_id: str

class DeleteAccountResponse(BaseModel):
    message: str
    deleted_user_id: str


@router.post("/delete-account", response_model=DeleteAccountResponse)
async def delete_account(request: DeleteAccountRequest):
    """
    刪除用戶帳戶（不需身份驗證）
    """
    try:
        user_id = request.user_id
        print(f'[DeleteAccount] 開始刪除用戶帳號: {user_id}')
        
        # 驗證 user_id 格式
        if not user_id or not user_id.strip():
            raise HTTPException(status_code=400, detail="user_id 不能為空")
        
        delete_user_response = supabase_admin.auth.admin.delete_user(user_id)
        
        # 檢查回應的異常情況
        if delete_user_response is not None and hasattr(delete_user_response, 'error') and delete_user_response.error:
            print(f'[DeleteAccount] 刪除用戶帳號時出錯: {delete_user_response.error}')
            raise HTTPException(status_code=500, detail="刪除用戶帳號時發生錯誤")
        
        # 如果是 None 或沒有錯誤，視為成功
        print(f'[DeleteAccount] 用戶帳號刪除成功: {user_id}')
        
        return DeleteAccountResponse(
            message="帳號已成功刪除",
            deleted_user_id=user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f'[DeleteAccount] 刪除帳號時發生錯誤: {e}')
        raise HTTPException(status_code=500, detail="刪除帳號時發生內部錯誤") 


class ResetPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    emailId: Optional[str] = None
    recipient: Optional[str] = None
    timestamp: Optional[str] = None


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(request: ResetPasswordRequest):
    """
    發送密碼重置郵件
    """
    try:
        email = request.email
        print(f'[ResetPassword] 收到密碼重置請求: {email}')
        
        # 驗證信箱格式
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            raise HTTPException(status_code=400, detail="信箱格式不正確")
        
        # 檢查用戶是否存在
        response = supabase_admin.auth.admin.list_users()
        
        if response.error:
            print(f'[ResetPassword] 獲取用戶列表失敗: {response.error}')
            raise HTTPException(status_code=500, detail="伺服器錯誤，請稍後重試")
        
        user = None
        for u in response.data:
            if u.email == email:
                user = u
                break
        
        if not user:
            # 為了安全考慮，即使用戶不存在也返回成功訊息
            print(f'[ResetPassword] 用戶不存在: {email}')
            return ResetPasswordResponse(
                success=True,
                message="如果該信箱地址存在於我們的系統中，您將收到密碼重置郵件。"
            )
        
        print(f'[ResetPassword] 找到用戶: {user.id}, {user.email}, {user.app_metadata}')
        
        # 檢查是否是 OAuth 用戶
        if user.app_metadata and user.app_metadata.get('provider') and user.app_metadata['provider'] != 'email':
            provider = user.app_metadata['provider']
            return ResetPasswordResponse(
                success=False,
                error=f"此帳戶使用 {provider} 登入，無法重置密碼。請使用 {provider} 登入。"
            )
        
        # 生成密碼重置連結
        print('[ResetPassword] 開始生成密碼重置連結')
        link_response = supabase_admin.auth.admin.generate_link(
            type='recovery',
            email=user.email,
            options={
                'redirect_to': f"{settings.SITE_URL}/auth/callback?type=recovery"
            }
        )
        
        if link_response.error or not link_response.data:
            print(f'[ResetPassword] 生成重置連結失敗: {link_response.error}')
            raise HTTPException(status_code=500, detail="生成重置連結失敗，請稍後重試")
        
        print('[ResetPassword] 重置連結生成成功')
        
        # 獲取重置連結
        reset_url = link_response.data.properties.get('action_link') if link_response.data.properties else None
        
        if not reset_url:
            print('[ResetPassword] 無法獲得重置連結')
            raise HTTPException(status_code=500, detail="無法生成重置連結")
        
        # 準備郵件內容
        email_html = f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>重置您的 Assistbot 密碼</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    background-color: white;
                    border-radius: 8px;
                    padding: 40px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2563eb;
                    margin-bottom: 20px;
                }}
                .title {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #1f2937;
                    margin-bottom: 10px;
                }}
                .subtitle {{
                    font-size: 16px;
                    color: #6b7280;
                    margin-bottom: 30px;
                }}
                .button {{
                    display: inline-block;
                    background-color: #2563eb;
                    color: #ffffff !important;
                    padding: 16px 32px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    text-align: center;
                    margin: 20px 0;
                    border: 2px solid #2563eb;
                    box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
                    transition: all 0.2s ease-in-out;
                    min-width: 200px;
                }}
                .button:hover {{
                    background-color: #1d4ed8 !important;
                    border-color: #1d4ed8;
                    box-shadow: 0 6px 8px rgba(29, 78, 216, 0.3);
                    transform: translateY(-1px);
                }}
                .button:visited {{
                    color: #ffffff !important;
                }}
                .button:active {{
                    color: #ffffff !important;
                    background-color: #1e40af !important;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    text-align: center;
                    font-size: 14px;
                    color: #6b7280;
                }}
                .note {{
                    background-color: #f3f4f6;
                    padding: 15px;
                    border-radius: 6px;
                    margin: 20px 0;
                    font-size: 14px;
                    color: #4b5563;
                }}
                .warning {{
                    background-color: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 15px;
                    margin: 20px 0;
                    font-size: 14px;
                    color: #92400e;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🔐 Assistbot</div>
                    <h1 class="title">重置您的密碼</h1>
                    <p class="subtitle">我們收到了您的密碼重置請求</p>
                </div>

                <p>您好，</p>
                
                <p>我們收到了重置您 Assistbot 帳戶密碼的請求。如果這是您本人的操作，請點擊下方按鈕設置新密碼：</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" class="button" style="display: inline-block; background-color: #2563eb; color: #ffffff !important; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; text-align: center; border: 2px solid #2563eb; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2); min-width: 200px;">
                      <strong style="color: #ffffff !important;">🔐 重置密碼</strong>
                    </a>
                </div>
                
                <div class="warning">
                    <strong>⚠️ 如果您沒有請求重置密碼</strong><br>
                    請忽略此郵件，您的密碼不會被更改。如果您擔心帳戶安全，請立即聯繫我們的客服支援。
                </div>

                <div class="footer">
                    <p>© 2025 Assistbot. 保留所有權利。</p>
                    <p>如有問題，請聯繫我們的客服支援：<a href="mailto:support@assistbot.cloud">support@assistbot.cloud</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        print(f'[ResetPassword] 開始發送郵件到: {email}')
        
        # 發送郵件
        email_response = resend.emails.send({
            'from': 'Assisbot <noreply@assistbot.cloud>',
            'to': [email],
            'subject': '重置您的 Assisbot 密碼',
            'html': email_html,
            'text': f'重置您的 Assisbot 密碼\\n\\n我們收到了重置您帳戶密碼的請求。請點擊以下連結設置新密碼：\\n\\n{reset_url}\\n\\n此連結將在 1 小時後過期。如果您沒有請求重置密碼，請忽略此郵件。\\n\\n如有問題，請聯繫客服支援：support@assistbot.cloud'
        })
        
        if email_response.get('error'):
            print(f'[ResetPassword] ❌ 發送重置郵件失敗: {email_response["error"]}')
            raise HTTPException(status_code=500, detail="發送郵件失敗，請稍後重試")
        
        print('[ResetPassword] ✅ 重置郵件發送成功!')
        print(f'[ResetPassword] Email ID: {email_response.get("id")}')
        
        return ResetPasswordResponse(
            success=True,
            message="密碼重置郵件已發送！請檢查您的信箱並點擊連結重置密碼。",
            emailId=email_response.get("id"),
            recipient=email,
            timestamp=settings.get_current_timestamp()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f'❌ 發送重置郵件時發生錯誤: {e}')
        raise HTTPException(status_code=500, detail="伺服器錯誤，請稍後重試") 


class SendConfirmationEmailRequest(BaseModel):
    email: EmailStr

class SendConfirmationEmailResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    emailId: Optional[str] = None
    recipient: Optional[str] = None
    timestamp: Optional[str] = None


@router.post("/send-confirmation-email", response_model=SendConfirmationEmailResponse)
async def send_confirmation_email(request: SendConfirmationEmailRequest):
    """
    發送確認郵件給新註冊的用戶
    """
    try:
        email = request.email
        print(f'[SendConfirmation] 收到確認郵件請求: {email}')
        
        # 查找用戶
        response = supabase_admin.auth.admin.list_users()
        
        if response.error:
            print(f'[SendConfirmation] 獲取用戶列表失敗: {response.error}')
            raise HTTPException(status_code=500, detail="伺服器錯誤")
        
        user = None
        for u in response.data:
            if u.email == email:
                user = u
                break
        
        if not user:
            print(f'[SendConfirmation] 找不到用戶: {email}')
            raise HTTPException(status_code=404, detail="找不到該用戶")
        
        print(f'[SendConfirmation] 找到用戶: {user.id}, {user.email}, {user.email_confirmed_at}')
        
        if user.email_confirmed_at:
            print('[SendConfirmation] 用戶郵箱已確認')
            raise HTTPException(status_code=400, detail="該用戶郵箱已經確認過了")
        
        # 生成確認鏈接
        print('[SendConfirmation] 開始生成確認鏈接')
        link_response = supabase_admin.auth.admin.generate_link(
            type='magiclink',
            email=user.email,
            options={
                'redirect_to': f"{settings.SITE_URL}/auth/callback"
            }
        )
        
        if link_response.error or not link_response.data:
            print(f'[SendConfirmation] 生成確認鏈接失敗: {link_response.error}')
            raise HTTPException(status_code=500, detail=f"生成確認鏈接失敗: {link_response.error.message if link_response.error else '未知錯誤'}")
        
        print('[SendConfirmation] 確認鏈接生成成功')
        
        # 獲取確認鏈接
        confirmation_url = link_response.data.properties.get('action_link') if link_response.data.properties else None
        
        if not confirmation_url:
            print('[SendConfirmation] 無法獲得確認鏈接')
            raise HTTPException(status_code=500, detail="無法獲得確認鏈接")
        
        print(f'[SendConfirmation] 確認鏈接: {confirmation_url}')
        
        # 準備郵件內容
        email_html = f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>確認您的 Assistbot 帳戶</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    background-color: white;
                    border-radius: 8px;
                    padding: 40px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2563eb;
                    margin-bottom: 20px;
                }}
                .title {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #1f2937;
                    margin-bottom: 10px;
                }}
                .subtitle {{
                    font-size: 16px;
                    color: #6b7280;
                    margin-bottom: 30px;
                }}
                .button {{
                    display: inline-block;
                    background-color: #2563eb;
                    color: #ffffff !important;
                    padding: 16px 32px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    text-align: center;
                    margin: 20px 0;
                    border: 2px solid #2563eb;
                    box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
                    transition: all 0.2s ease-in-out;
                    min-width: 200px;
                }}
                .button:hover {{
                    background-color: #1d4ed8 !important;
                    border-color: #1d4ed8;
                    box-shadow: 0 6px 8px rgba(29, 78, 216, 0.3);
                    transform: translateY(-1px);
                }}
                .button:visited {{
                    color: #ffffff !important;
                }}
                .button:active {{
                    color: #ffffff !important;
                    background-color: #1e40af !important;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    text-align: center;
                    font-size: 14px;
                    color: #6b7280;
                }}
                .note {{
                    background-color: #f3f4f6;
                    padding: 15px;
                    border-radius: 6px;
                    margin: 20px 0;
                    font-size: 14px;
                    color: #4b5563;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🤖 Assistbot</div>
                    <h1 class="title">歡迎加入 Assistbot！</h1>
                    <p class="subtitle">請確認您的電子郵件地址以完成註冊</p>
                </div>

                <p>親愛的用戶，</p>
                
                <p>感謝您註冊 Assistbot 服務！為了確保帳戶安全，請點擊下方按鈕確認您的電子郵件地址：</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{confirmation_url}" class="button" style="display: inline-block; background-color: #2563eb; color: #ffffff !important; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; text-align: center; border: 2px solid #2563eb; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2); min-width: 200px;">
                      <strong style="color: #ffffff !important;">✅ 確認電子郵件地址</strong>
                    </a>
                </div>
                
                <div class="note">
                    <strong>注意：</strong>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>如果您沒有註冊 Assistbot 帳戶，請忽略此郵件</li>
                    </ul>
                </div>

                <p>確認後，您將可以：</p>
                <ul>
                    <li>🚀 建立和管理聊天機器人</li>
                    <li>📚 上傳文件建立知識庫</li>
                    <li>📊 查看使用分析</li>
                    <li>⚡ 享受完整功能</li>
                </ul>

                <div class="footer">
                    <p>© 2025 Assistbot. 保留所有權利。</p>
                    <p>如有問題，請聯繫我們的客服支援：<a href="mailto:support@assistbot.cloud">support@assistbot.cloud</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        print(f'[SendConfirmation] 開始發送郵件到: {email}')
        
        # 發送郵件
        email_response = resend.emails.send({
            'from': 'Assisbot <noreply@assistbot.cloud>',
            'to': [email],
            'subject': '確認您的 Assisbot 帳戶',
            'html': email_html,
            'text': f'歡迎加入 Assisbot！請點擊以下鏈接確認您的電子郵件地址：{confirmation_url}'
        })
        
        if email_response.get('error'):
            print(f'[SendConfirmation] ❌ 發送確認郵件失敗: {email_response["error"]}')
            raise HTTPException(status_code=500, detail=email_response['error'])
        
        print('[SendConfirmation] ✅ 確認郵件發送成功!')
        print(f'[SendConfirmation] Email ID: {email_response.get("id")}')
        
        return SendConfirmationEmailResponse(
            success=True,
            message="確認郵件發送成功！",
            emailId=email_response.get("id"),
            recipient=email,
            timestamp=settings.get_current_timestamp()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f'❌ 發送確認郵件時發生錯誤: {e}')
        raise HTTPException(status_code=500, detail="伺服器錯誤，請稍後重試") 


class UpdatePasswordRequest(BaseModel):
    password: str
    userId: str
    createEmailIdentity: Optional[bool] = False


class UpdatePasswordResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None


@router.post("/update-password", response_model=UpdatePasswordResponse)
async def update_password(
    request: UpdatePasswordRequest,
    token: str = Depends(require_authenticated_user)
):
    """
    使用管理員權限更新用戶密碼
    """
    try:
        password = request.password
        user_id = request.userId
        create_email_identity = request.createEmailIdentity
        
        print(f'[UpdatePassword] 收到密碼更新請求: {user_id}, {create_email_identity}')
        
        if not password or not user_id:
            raise HTTPException(status_code=400, detail="需要提供 password 和 userId 參數")
        
        # 驗證密碼強度
        if len(password) < 6:
            raise HTTPException(status_code=400, detail="密碼至少需要 6 個字符")
        
        # 檢查用戶ID是否匹配
        if token != user_id:
            print(f'[UpdatePassword] 用戶ID不匹配: {token}, {user_id}')
            raise HTTPException(status_code=401, detail="用戶ID不匹配")
        
        # 獲取用戶資訊
        print('[UpdatePassword] 獲取用戶資訊')
        user_response = supabase_admin.auth.admin.get_user_by_id(user_id)
        
        if user_response.error or not user_response.user:
            print(f'[UpdatePassword] 獲取用戶資訊失敗: {user_response.error}')
            raise HTTPException(status_code=404, detail="找不到用戶資訊")
        
        user = user_response.user
        print(f'[UpdatePassword] 更新前用戶資訊: {user.email}, {user.identities}')
        
        # 更新用戶密碼
        print('[UpdatePassword] 開始更新用戶密碼')
        update_response = supabase_admin.auth.admin.update_user_by_id(
            user_id,
            password=password,
            email_confirm=True  # 確保 email 已確認
        )
        
        if update_response.error:
            print(f'[UpdatePassword] 更新密碼失敗: {update_response.error}')
            raise HTTPException(
                status_code=500, 
                detail=update_response.error.message if update_response.error else "密碼更新失敗，請重試"
            )
        
        print('[UpdatePassword] 密碼更新成功')
        
        # 再次獲取用戶資訊查看更新後的狀態
        updated_user_response = supabase_admin.auth.admin.get_user_by_id(user_id)
        if updated_user_response.user:
            print(f'[UpdatePassword] 更新後用戶資訊: {updated_user_response.user.email}, {updated_user_response.user.identities}')
            
            # 檢查是否需要創建 email identity
            has_email_identity = any(
                identity.provider == 'email' 
                for identity in (updated_user_response.user.identities or [])
            )
            
            if create_email_identity and not has_email_identity:
                print('[UpdatePassword] 嘗試創建 email identity')
                # 注意：這個功能需要特殊實現，因為 Supabase 通常不允許手動創建 identity
                print('[UpdatePassword] Email identity 創建功能需要特殊實現')
        
        return UpdatePasswordResponse(
            success=True,
            message="密碼更新成功",
            timestamp=settings.get_current_timestamp()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f'❌ 更新密碼時發生錯誤: {e}')
        raise HTTPException(status_code=500, detail="伺服器錯誤，請稍後重試") 


class WelcomeCreditsRequest(BaseModel):
    email: EmailStr

class WelcomeCreditsResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    credits_added: Optional[float] = None
    user_id: Optional[str] = None
    timestamp: Optional[str] = None


@router.post("/welcome-credits", response_model=WelcomeCreditsResponse)
async def welcome_credits(request: WelcomeCreditsRequest):
    """
    為新用戶添加歡迎積分
    """
    try:
        email = request.email
        print(f'[WelcomeCredits] 收到歡迎積分請求: {email}')
        
        # 查找用戶
        response = supabase_admin.auth.admin.list_users()
        
        if response.error:
            print(f'[WelcomeCredits] 獲取用戶列表失敗: {response.error}')
            raise HTTPException(status_code=500, detail="伺服器錯誤")
        
        user = None
        for u in response.data:
            if u.email == email:
                user = u
                break
        
        if not user:
            print(f'[WelcomeCredits] 找不到用戶: {email}')
            raise HTTPException(status_code=404, detail="找不到該用戶")
        
        user_id = user.id
        print(f'[WelcomeCredits] 找到用戶: {user_id}')
        
        # 檢查是否已經有積分記錄
        credits_response = supabase_admin.table('credits').select('*').eq('user_id', user_id).execute()
        
        if credits_response.error:
            print(f'[WelcomeCredits] 檢查積分記錄時出錯: {credits_response.error}')
            raise HTTPException(status_code=500, detail="檢查積分記錄時發生錯誤")
        
        # 如果已經有積分記錄，檢查是否已經領取過歡迎積分
        if credits_response.data and len(credits_response.data) > 0:
            existing_credits = credits_response.data[0]
            
            # 檢查是否有歡迎積分的交易記錄
            transactions_response = supabase_admin.table('credit_transactions').select('*').eq('user_id', user_id).eq('type', 'welcome_bonus').execute()
            
            if transactions_response.error:
                print(f'[WelcomeCredits] 檢查交易記錄時出錯: {transactions_response.error}')
                raise HTTPException(status_code=500, detail="檢查交易記錄時發生錯誤")
            
            if transactions_response.data and len(transactions_response.data) > 0:
                print(f'[WelcomeCredits] 用戶已經領取過歡迎積分: {user_id}')
                return WelcomeCreditsResponse(
                    success=False,
                    error="您已經領取過歡迎積分了"
                )
        
        # 添加歡迎積分（假設為 10 積分）
        welcome_credits_amount = 10.0
        
        # 創建或更新積分記錄
        if credits_response.data and len(credits_response.data) > 0:
            # 更新現有積分
            current_balance = credits_response.data[0].get('balance', 0)
            new_balance = current_balance + welcome_credits_amount
            
            update_response = supabase_admin.table('credits').update({
                'balance': new_balance,
                'updated_at': settings.get_current_timestamp()
            }).eq('user_id', user_id).execute()
            
            if update_response.error:
                print(f'[WelcomeCredits] 更新積分失敗: {update_response.error}')
                raise HTTPException(status_code=500, detail="更新積分失敗")
        else:
            # 創建新的積分記錄
            create_response = supabase_admin.table('credits').insert({
                'user_id': user_id,
                'balance': welcome_credits_amount,
                'created_at': settings.get_current_timestamp(),
                'updated_at': settings.get_current_timestamp()
            }).execute()
            
            if create_response.error:
                print(f'[WelcomeCredits] 創建積分記錄失敗: {create_response.error}')
                raise HTTPException(status_code=500, detail="創建積分記錄失敗")
        
        # 添加交易記錄
        transaction_response = supabase_admin.table('credit_transactions').insert({
            'user_id': user_id,
            'type': 'welcome_bonus',
            'amount': welcome_credits_amount,
            'description': '歡迎積分',
            'meta_data': {
                'source': 'welcome_bonus',
                'email': email
            },
            'created_at': settings.get_current_timestamp()
        }).execute()
        
        if transaction_response.error:
            print(f'[WelcomeCredits] 創建交易記錄失敗: {transaction_response.error}')
            # 不拋出錯誤，因為積分已經添加成功
        
        print(f'[WelcomeCredits] ✅ 歡迎積分添加成功: {user_id}, +{welcome_credits_amount}')
        
        return WelcomeCreditsResponse(
            success=True,
            message="歡迎積分已成功添加到您的帳戶！",
            credits_added=welcome_credits_amount,
            user_id=user_id,
            timestamp=settings.get_current_timestamp()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f'❌ 添加歡迎積分時發生錯誤: {e}')
        raise HTTPException(status_code=500, detail="伺服器錯誤，請稍後重試") 