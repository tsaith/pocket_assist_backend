from langchain_core.tools import StructuredTool

from app.lib.user_subscription_manager import UserSubscriptionManager


def create_get_user_tier_tool(user_id: str) -> StructuredTool:
    """創建獲取用戶訂閱層級工具"""
    
    def get_user_tier() -> str:
        """
        獲取用戶的訂閱層級
        
        Returns:
            str: 用戶的訂閱層級和相關資訊
        """
        try:
            subscription_manager = UserSubscriptionManager(user_id)
            tier = subscription_manager.get_tier()
            
            # 獲取各項功能的限制
            reminders_limit = subscription_manager.get_reminders_limit()
            notes_limit = subscription_manager.get_notes_limit()
            bookkeeping_months_limit = subscription_manager.get_bookkeeping_months_limit()
            
            # 格式化限制顯示
            reminders_display = "unlimited" if reminders_limit == -1 else str(reminders_limit)
            notes_display = "unlimited" if notes_limit == -1 else str(notes_limit)
            bookkeeping_display = "unlimited" if bookkeeping_months_limit == -1 else f"{bookkeeping_months_limit} months"
            
            result = f"""Current Subscription Tier: {tier.upper()}

Feature Limits:
- Reminders: {reminders_display}
- Notes: {notes_display}
- Bookkeeping Records: {bookkeeping_display}
"""
            
            print(f"主人的訂閱層級：{tier}")
            return result
            
        except Exception as e:
            error_msg = f"Error getting user subscription tier: {str(e)}"
            print(error_msg)
            return error_msg
    
    get_user_tier_tool = StructuredTool.from_function(
        func=get_user_tier,
        name="get_user_tier",
        description="獲取主人的訂閱層級（free, pro, vip, vvip）以及各項功能的限制資訊。",
        return_direct=False
    )
    
    return get_user_tier_tool
