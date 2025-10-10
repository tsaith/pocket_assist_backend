from typing import Optional, Literal
from fastapi import HTTPException

from .admin import supabase_admin


UserRole = Literal['admin', 'user', 'guest'] | None

async def require_admin(token: str) -> str:
    """
    驗證用戶是否具有管理員權限，用於 API 路由
    
    Args:
        token: JWT token
        
    Returns:
        str: 用戶ID
        
    Raises:
        HTTPException: 如果驗證失敗或非管理員
    """
    try:
        if not token:
            raise HTTPException(status_code=401, detail="未授權訪問")

        # 使用 supabase_admin 檢查令牌
        user = supabase_admin.auth.get_user(token)

        if not user or not user.user:
            raise HTTPException(status_code=401, detail="未授權訪問")
        
        user_id = user.user.id
        
        # 檢查用戶角色
        response = supabase_admin.table('profiles').select('role').eq('id', user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=403, detail="需要管理員權限")
        
        role = response.data[0].get('role')

        if not role or role != 'admin':
            print(f'用戶非管理員，角色: {role or "未設置"}')
            raise HTTPException(status_code=403, detail="需要管理員權限")

        return user_id

    except HTTPException:
        raise
    except Exception as e:
        print(f'requireAdmin 函數發生錯誤: {e}')
        raise HTTPException(status_code=401, detail="未授權訪問")


async def require_authenticated_user(token: str) -> str:
    """
    驗證用戶是否已登入，用於 API 路由
    
    Args:
        token: JWT token
        
    Returns:
        str: 用戶ID
        
    Raises:
        HTTPException: 如果驗證失敗
    """
    try:
        if not token:
            raise HTTPException(status_code=401, detail="未授權訪問")

        # 正常的令牌驗證
        user = supabase_admin.auth.get_user(token)

        if not user or not user.user:
            raise HTTPException(status_code=401, detail="未授權訪問")

        return user.user.id

    except Exception as e:
        print(f'requireAuthenticatedUser 函數發生錯誤: {e}')
        raise HTTPException(status_code=401, detail="未授權訪問")


async def get_user(token: str) -> Optional[dict]:
    """
    獲取用戶資料
    
    Args:
        token: JWT token
        
    Returns:
        dict: 用戶資料，如果認證失敗則返回 None
        
    Raises:
        HTTPException: 如果認證失敗
    """
    try:
        if not token:
            raise HTTPException(status_code=401, detail="未提供認證令牌")

        user = supabase_admin.auth.get_user(token)

        if not user or not user.user:
            print('認證失敗: 無效的令牌')
            raise HTTPException(status_code=401, detail="認證失敗: 無效的令牌")
        
        print(f'使用者驗證成功，ID: {user.user.id}')
        
        return {
            'id': user.user.id,
            'email': user.user.email,
            'created_at': user.user.created_at,
            'updated_at': user.user.updated_at
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f'獲取用戶資料時發生錯誤: {e}')
        raise HTTPException(status_code=401, detail="認證失敗")


async def get_user_role(user_id: str) -> UserRole:
    """
    獲取用戶角色
    
    Args:
        user_id: 用戶ID
        
    Returns:
        UserRole: 用戶角色，如果找不到則返回 None
    """
    try:
        response = supabase_admin.table('profiles').select('role').eq('id', user_id).execute()
        
        # 如果找不到數據或 role 為空，返回 None
        if not response.data or len(response.data) == 0 or not response.data[0].get('role'):
            return None

        return response.data[0]['role']

    except Exception as e:
        print(f'[admin get_user_role] 獲取用戶角色時出錯: {e}')
        return None


async def get_user_by_id(user_id: str) -> Optional[dict]:
    """
    根據用戶ID獲取用戶信息
    
    Args:
        user_id: 用戶ID
        
    Returns:
        dict: 用戶信息，如果找不到則返回 None
    """
    try:
        # 使用 Supabase admin 獲取用戶信息
        user = supabase_admin.auth.admin.get_user_by_id(user_id)
        
        if not user or not user.user:
            return None
        
        return {
            'id': user.user.id,
            'email': user.user.email,
            'created_at': user.user.created_at,
            'updated_at': user.user.updated_at
        }
        
    except Exception as e:
        print(f"獲取用戶信息時出錯: {e}")
        return None 