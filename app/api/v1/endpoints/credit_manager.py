from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
from app.lib.credit_manager import CreditManager
from app.lib.supabase.utils import require_authenticated_user

router = APIRouter(prefix="/api/v1/credit-manager", tags=["credit-manager"])


class ConsumeCreditsFromTokensRequest(BaseModel):
    user_id: str
    tokens: int


class ConsumeCreditsFromTokensResponse(BaseModel):
    success: bool
    message: str
    updated_balance: float


class RatioCreditToTokenResponse(BaseModel):
    success: bool
    ratio_credit_to_token: float
    message: str


@router.post("/consume-credits-from-tokens", response_model=ConsumeCreditsFromTokensResponse)
async def consume_credits_from_tokens(
    request: ConsumeCreditsFromTokensRequest,
    authorization: str = Header(None)
):
    """
    根據 tokens 消耗用戶積分並更新用戶積分餘額
    Args:
        request: 包含 tokens 和 user_id 的請求
        authorization: JWT token header
    Returns:
        更新後的積分餘額和消耗詳情
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="未授權訪問")
        jwt_token = authorization.split(" ")[1] if " " in authorization else authorization

        user_id = request.user_id
        tokens = request.tokens
        print(f'[CreditManager API] 收到積分消耗請求: user_id={user_id}, tokens={tokens}')

        # 驗證 jwt token 是否有效
        authed_user_id = await require_authenticated_user(jwt_token)
        if authed_user_id != user_id:
            print(f'[CreditManager API] 用戶ID不匹配: {authed_user_id} != {user_id}')
            raise HTTPException(status_code=401, detail="用戶ID不匹配")

        if tokens <= 0:
            raise HTTPException(status_code=400, detail="tokens 必須大於 0")

        updated_balance = await CreditManager.consume_credits_from_tokens(user_id, tokens)
        print(f'[CreditManager API] 積分消耗成功: user_id={user_id}, tokens={tokens}, updated_balance={updated_balance}')
        return ConsumeCreditsFromTokensResponse(
            success=True,
            message="積分消耗成功",
            updated_balance=updated_balance,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f'[CreditManager API] 積分消耗失敗: {e}')
        raise HTTPException(status_code=500, detail=f"積分消耗失敗: {str(e)}")


@router.get("/ratio-credit-to-token", response_model=RatioCreditToTokenResponse)
async def get_ratio_credit_to_token():
    """
    獲取積分與 token 的轉換比例
    
    Returns:
        積分與 token 的轉換比例
    """
    try:
        ratio = CreditManager.ratio_credit_to_token
        print(f'[CreditManager API] 獲取轉換比例: {ratio}')
        
        return RatioCreditToTokenResponse(
            success=True,
            ratio_credit_to_token=ratio,
            message="獲取轉換比例成功"
        )
        
    except Exception as e:
        print(f'[CreditManager API] 獲取轉換比例失敗: {e}')
        raise HTTPException(status_code=500, detail=f"獲取轉換比例失敗: {str(e)}")


class GetCreditBalanceRequest(BaseModel):
    user_id: str


class GetCreditBalanceResponse(BaseModel):
    success: bool
    balance: float
    updated_at: str
    user_id: str


@router.get("/credit-balance/{user_id}", response_model=GetCreditBalanceResponse)
async def get_credit_balance(
    user_id: str,
    token: str = Depends(require_authenticated_user)
):
    """
    獲取用戶積分餘額
    
    Args:
        user_id: 用戶ID
        token: 認證令牌
        
    Returns:
        用戶積分餘額
    """
    try:
        print(f'[CreditManager API] 獲取積分餘額: user_id={user_id}')
        
        # 驗證用戶身份
        if token != user_id:
            print(f'[CreditManager API] 用戶ID不匹配: {token} != {user_id}')
            raise HTTPException(status_code=401, detail="用戶ID不匹配")
        
        # 調用 CreditManager 的 get_credit_balance 方法
        credit_balance = await CreditManager.get_credit_balance(user_id)
        
        print(f'[CreditManager API] 積分餘額獲取成功: user_id={user_id}, balance={credit_balance.balance}')
        
        return GetCreditBalanceResponse(
            success=True,
            balance=credit_balance.balance,
            updated_at=credit_balance.updated_at,
            user_id=user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f'[CreditManager API] 獲取積分餘額失敗: {e}')
        raise HTTPException(status_code=500, detail=f"獲取積分餘額失敗: {str(e)}")


class ConsumeCreditsRequest(BaseModel):
    user_id: str
    amount: float
    description: Optional[str] = "Chatbot 對話消費"
    meta_data: Optional[dict] = {}


class ConsumeCreditsResponse(BaseModel):
    success: bool
    message: str
    updated_balance: float
    credits_consumed: float
    user_id: str


@router.post("/consume-credits", response_model=ConsumeCreditsResponse)
async def consume_credits(
    request: ConsumeCreditsRequest,
    token: str = Depends(require_authenticated_user)
):
    """
    直接消耗用戶積分
    
    Args:
        request: 包含 user_id、amount、description 和 meta_data 的請求
        token: 認證令牌
        
    Returns:
        更新後的積分餘額
    """
    try:
        user_id = request.user_id
        amount = request.amount
        description = request.description or "Chatbot 對話消費"
        meta_data = request.meta_data or {}
        
        print(f'[CreditManager API] 收到直接積分消耗請求: user_id={user_id}, amount={amount}')
        
        # 驗證 amount 參數
        if amount <= 0:
            raise HTTPException(status_code=400, detail="amount 必須大於 0")
        
        # 驗證用戶身份
        if token != user_id:
            print(f'[CreditManager API] 用戶ID不匹配: {token} != {user_id}')
            raise HTTPException(status_code=401, detail="用戶ID不匹配")
        
        # 調用 CreditManager 的 consume_credits 方法
        updated_balance = await CreditManager.consume_credits(
            user_id, 
            amount, 
            description, 
            meta_data
        )
        
        print(f'[CreditManager API] 直接積分消耗成功: user_id={user_id}, amount={amount}, updated_balance={updated_balance}')
        
        return ConsumeCreditsResponse(
            success=True,
            message="積分消耗成功",
            updated_balance=updated_balance,
            credits_consumed=amount,
            user_id=user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f'[CreditManager API] 直接積分消耗失敗: {e}')
        raise HTTPException(status_code=500, detail=f"積分消耗失敗: {str(e)}")
