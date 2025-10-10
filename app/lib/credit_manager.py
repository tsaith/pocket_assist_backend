from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from app.lib.supabase.admin import supabase_admin
import asyncio


class CreditBalance:
    def __init__(self, balance: float, updated_at: str):
        self.balance = balance
        self.updated_at = updated_at


class CreditTransaction:
    def __init__(self, id: str, type: str, amount: float, description: str, 
                 meta_data: Dict[str, Any], created_at: str):
        self.id = id
        self.type = type
        self.amount = amount
        self.description = description
        self.meta_data = meta_data
        self.created_at = created_at


class CreditTransactionResponse:
    def __init__(self, transactions: List[CreditTransaction], pagination: Dict[str, Any]):
        self.transactions = transactions
        self.pagination = pagination


class CreditManager:
    """
    Credit Manager for handling user credit operations
    """
    
    # 1 credit = 5000 tokens
    ratio_credit_to_token = 0.0002
    
    @staticmethod
    def get_fixed_amount(amount: float) -> float:
        """Convert amount to fixed decimal places"""
        return round(amount, 4)
    
    @staticmethod
    async def get_credit_balance(user_id: str) -> CreditBalance:
        """
        Get credit balance for a user
        Args:
            user_id: User ID
        Returns:
            Credit balance or creates new record with 0 balance
        """
        try:
            # Try to get existing credit balance
            response = supabase_admin.table('credits').select('balance, updated_at').eq('user_id', user_id).execute()
            
            if response.data and len(response.data) > 0:
                # Found existing record
                data = response.data[0]
                return CreditBalance(
                    balance=data['balance'],
                    updated_at=data['updated_at']
                )
            else:
                # Create new record with 0 balance
                create_response = supabase_admin.table('credits').insert({
                    'user_id': user_id,
                    'balance': 0
                }).select('balance, updated_at').execute()
                
                if create_response.data and len(create_response.data) > 0:
                    data = create_response.data[0]
                    return CreditBalance(
                        balance=data['balance'],
                        updated_at=data['updated_at']
                    )
                else:
                    raise Exception('創建 credit 記錄失敗')
            
        except Exception as error:
            print(f'Error in get_credit_balance: {error}')
            raise error
    
    @staticmethod
    async def get_credit_transactions(
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        transaction_type: Optional[str] = None
    ) -> CreditTransactionResponse:
        """
        Get credit transactions for a user
        Args:
            user_id: User ID
            limit: Number of records to return
            offset: Number of records to skip
            transaction_type: Filter by type ('recharge' or 'consumption')
        Returns:
            Credit transactions with pagination info
        """
        try:
            # Build query
            query = supabase_admin.table('credit_transactions').select('*').eq('user_id', user_id).order('created_at', desc=True)
            
            # Add type filter if specified
            if transaction_type and transaction_type in ['recharge', 'consumption']:
                query = query.eq('type', transaction_type)
            
            # Add pagination
            query = query.range(offset, offset + limit - 1)
            
            response = query.execute()
            
            if not response.data:
                # Return empty result if no data
                return CreditTransactionResponse([], {
                    'total': 0,
                    'limit': limit,
                    'offset': offset,
                    'has_more': False
                })
            
            # Get total count for pagination
            count_response = supabase_admin.table('credit_transactions').select('*', count='exact').eq('user_id', user_id).execute()
            
            total_count = count_response.count if hasattr(count_response, 'count') else len(response.data)
            
            # Convert to CreditTransaction objects
            transactions = []
            for transaction_data in response.data:
                transaction = CreditTransaction(
                    id=transaction_data['id'],
                    type=transaction_data['type'],
                    amount=transaction_data['amount'],
                    description=transaction_data['description'],
                    meta_data=transaction_data['meta_data'],
                    created_at=transaction_data['created_at']
                )
                transactions.append(transaction)
            
            pagination = {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': total_count > offset + limit
            }
            
            return CreditTransactionResponse(transactions, pagination)
            
        except Exception as error:
            print(f'Error in get_credit_transactions: {error}')
            raise error
    
    @staticmethod
    async def add_transaction(
        user_id: str,
        transaction_type: str,
        amount: float,
        description: str = '',
        meta_data: Dict[str, Any] = {}
    ) -> CreditTransaction:
        """
        Add credit transaction
        Args:
            user_id: User ID
            transaction_type: Transaction type ('recharge' or 'consumption')
            amount: Transaction amount
            description: Transaction description
            meta_data: Additional metadata
        Returns:
            Created transaction
        """
        try:
            amount_fixed = CreditManager.get_fixed_amount(amount)
            
            response = supabase_admin.table('credit_transactions').insert({
                'user_id': user_id,
                'type': transaction_type,
                'amount': amount_fixed,
                'description': description,
                'meta_data': meta_data
            }).execute()
            
            if not response.data or len(response.data) == 0:
                raise Exception('創建交易記錄失敗')
            
            transaction_data = response.data[0]
            return CreditTransaction(
                id=transaction_data['id'],
                type=transaction_data['type'],
                amount=transaction_data['amount'],
                description=transaction_data['description'],
                meta_data=transaction_data['meta_data'],
                created_at=transaction_data['created_at']
            )
            
        except Exception as error:
            print(f'Error in add_transaction: {error}')
            raise error
    
    @staticmethod
    async def update_balance(user_id: str, new_balance: float) -> CreditBalance:
        """
        Update credit balance
        Args:
            user_id: User ID
            new_balance: New balance amount
        Returns:
            Updated credit balance
        """
        try:
            response = supabase_admin.table('credits').update({
                'balance': new_balance,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).execute()
            
            if not response.data or len(response.data) == 0:
                raise Exception('更新 credit 餘額失敗')
            
            data = response.data[0]
            return CreditBalance(
                balance=data['balance'],
                updated_at=data['updated_at']
            )
            
        except Exception as error:
            print(f'Error in update_balance: {error}')
            raise error
    
    @staticmethod
    async def consume_credits(
        user_id: str,
        amount: float,
        description: str = 'Chatbot 對話消費',
        meta_data: Dict[str, Any] = {}
    ) -> float:
        """
        Consume credits for a user (with balance check and update)
        Args:
            user_id: User ID
            amount: Amount to consume
            description: Consumption description
            meta_data: Additional metadata
        Returns:
            Updated credit balance
        """
        try:
            # Get current balance
            current_balance = await CreditManager.get_credit_balance(user_id)
            if amount < 0:
                return current_balance.balance
            
            # Check if user has enough credits
            amount_fixed = CreditManager.get_fixed_amount(amount)
            if current_balance.balance < amount_fixed:
                return current_balance.balance
            
            new_balance = current_balance.balance - amount_fixed
            
            # Update balance and create transaction in sequence
            updated_balance, _ = await asyncio.gather(
                CreditManager.update_balance(user_id, new_balance),
                CreditManager.add_transaction(
                    user_id,
                    'consumption',
                    amount_fixed,
                    description,
                    {
                        **meta_data
                    }
                )
            )
            
            return updated_balance.balance
            
        except Exception as error:
            print(f'Error in consume_credits: {error}')
            raise error
    
    @staticmethod
    async def recharge_credits(
        user_id: str,
        amount: float,
        description: str = '管理員充值',
        admin_user_id: Optional[str] = None
    ) -> float:
        """
        Recharge credits for a user (Admin function)
        Args:
            user_id: User ID
            amount: Amount to recharge
            description: Recharge description
            admin_user_id: Admin user ID performing the operation
        Returns:
            Updated credit balance
        """
        try:
            if amount <= 0:
                raise Exception('充值金額必須大於 0')
            
            # Get current balance
            current_balance = await CreditManager.get_credit_balance(user_id)
            amount_fixed = CreditManager.get_fixed_amount(amount)
            new_balance = current_balance.balance + amount_fixed
            
            # Update balance and create transaction in sequence
            updated_balance, transaction = await asyncio.gather(
                CreditManager.update_balance(user_id, new_balance),
                CreditManager.add_transaction(
                    user_id,
                    'recharge',
                    amount_fixed,
                    description,
                    {
                        'admin_user_id': admin_user_id,
                        'operation_type': 'admin_recharge',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
            )
            
            return updated_balance.balance
            
        except Exception as error:
            print(f'Error in recharge_credits: {error}')
            raise error
    
    @staticmethod
    async def consume_credits_from_tokens(user_id: str, tokens: int) -> float:
        """
        Consume credits by tokens and update user Credit Balance
        Args:
            user_id: User ID
            tokens: Number of tokens to consume
        Returns:
            Updated credit balance
        """
        try:
            credits_consumed = CreditManager.get_fixed_amount(tokens * CreditManager.ratio_credit_to_token)
            if credits_consumed < 0:
                credits_consumed = 0
            
            # Get current balance
            current_balance = await CreditManager.get_credit_balance(user_id)
            if current_balance.balance < credits_consumed:
                credits_consumed = current_balance.balance
            
            # Use existing consume_credits method for deduction and recording
            updated_balance = await CreditManager.consume_credits(
                user_id,
                credits_consumed,
                f'Chatbot tokens 消耗: {tokens} tokens = {credits_consumed} credits',
                {
                    'operation_type': 'chatbot_token_consumption',
                    'tokens_consumed': tokens
                }
            )
            
            return updated_balance
            
        except Exception as error:
            print(f'Error in consume_credits_from_tokens: {error}')
            raise error
    
    @staticmethod
    async def get_user_by_email(email: str) -> Dict[str, Any]:
        """
        Get user by email (for admin use)
        Args:
            email: User email
        Returns:
            User information
        """
        try:
            result = supabase_admin.auth.admin.list_users()
            
            if result.error:
                raise Exception(f'查詢用戶時發生錯誤: {result.error.message}')
            
            found_user = None
            for user in result.users:
                if user.email == email:
                    found_user = user
                    break
            
            if not found_user:
                raise Exception(f'找不到 email 為 {email} 的用戶')
            
            return found_user
            
        except Exception as error:
            print(f'Error in get_user_by_email: {error}')
            raise error
