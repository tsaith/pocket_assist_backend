from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from app.lib.reminder_manager import ReminderManager

router = APIRouter(prefix="/api/v1/reminders", tags=["reminders"])


class ReminderTriggerResponse(BaseModel):
    success: bool
    message: str
    triggered_count: int = 0
    triggered_reminders: List[Dict[str, Any]] = []


@router.post("/reminder-trigger", response_model=ReminderTriggerResponse)
async def reminder_trigger_endpoint():
    """
    觸發提醒事件
    
    檢查所有提醒記錄，當 remind_at 時間在 (現在, 現在+一個小時) 之間
    且 is_sent = false 時，該提醒將被觸發
    """
    try:
        # 創建 ReminderManager 實例
        reminder_manager = ReminderManager()
        
        # 觸發提醒
        result = await reminder_manager.trigger_reminders()

        return ReminderTriggerResponse(
            success=result["success"],
            message=result["message"],
            triggered_count=result["triggered_count"],
            triggered_reminders=result["triggered_reminders"]
        )
        
    except Exception as e:
        error_msg = f"觸發提醒時發生錯誤：{str(e)}"
        print(error_msg)
        return ReminderTriggerResponse(
            success=False,
            message=error_msg,
            triggered_count=0,
            triggered_reminders=[]
        )