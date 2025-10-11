from typing import List, Tuple
from datetime import datetime, timedelta, timezone
from langchain_core.tools import StructuredTool

from app.lib.supabase import supabase_admin
from app.lib.utils.time_utils import (
    convert_user_local_to_utc_time,
    convert_utc_to_user_local_time
)
from app.core.constants import Constants


def create_create_reminder_tool(user_id: str) -> StructuredTool:
    """創建添加提醒工具"""

    def create_reminder(
        remind_at: str, 
        method: str, 
        description: str,
        is_recurring: bool = False,
        recurrence_rule: str = None,
        recurrence_exceptions: str = None,
        status: str = 'active'
    ) -> str:
        """添加新的提醒"""

        method = method.lower()
        print(f"添加提醒： Remind At {remind_at}, Method {method}, Description {description}")
        try:
            # 改進的時間比較邏輯，支援時區資訊
            print(f"提醒時間：{remind_at}")
            
            # 解析 remind_at 時間
            try:
                if '+' in remind_at or 'Z' in remind_at or remind_at.endswith('Z'):
                    # 包含時區資訊的時間，直接解析
                    if remind_at.endswith('Z'):
                        remind_at = remind_at.replace('Z', '+00:00')
                    remind_dt = datetime.fromisoformat(remind_at)
                else:
                    # 假設為用戶本地時間，需要轉換為 UTC 進行比較
                    remind_at_utc, convert_info = convert_user_local_to_utc_time(user_id, remind_at)
                    if "error" in convert_info:
                        return f"錯誤：時間格式不正確，請使用本地時間格式 YYYY-MM-DD HH:MM:SS 或包含時區的格式 YYYY-MM-DDTHH:MM:SS+HH:MM"
                    
                    # 將轉換後的 UTC 時間解析為 datetime 物件
                    remind_dt = datetime.fromisoformat(remind_at_utc)
                    if remind_dt.tzinfo is None:
                        remind_dt = remind_dt.replace(tzinfo=timezone.utc)
                
                # 獲取當前 UTC 時間
                current_utc = datetime.now(timezone.utc)
                
                # 確保 remind_dt 有時區資訊
                if remind_dt.tzinfo is None:
                    remind_dt = remind_dt.replace(tzinfo=timezone.utc)
                
                # 將 remind_dt 轉換為 UTC 進行比較
                if remind_dt.tzinfo != timezone.utc:
                    remind_dt = remind_dt.astimezone(timezone.utc)
                
                # 比較時間，要求提醒時間比目前時間至少晚 50 秒（約 1 分鐘）
                minimum_delay = timedelta(seconds=50)
                required_time = current_utc + minimum_delay
                
                if remind_dt < required_time:
                    print(f"錯誤：提醒時間必須比目前時間至少晚 1 分鐘）")
                    return f"錯誤：提醒時間必須比目前時間至少晚 1 分鐘。當前時間：{current_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC，最早可設定時間：{required_time.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    
            except ValueError as e:
                return f"錯誤：時間格式不正確，請使用格式 YYYY-MM-DDTHH:MM:SS+HH:MM，錯誤詳情：{str(e)}"
            
            # 驗證 method 是否在允許的值中
            valid_methods = ['notification', 'notification-long']
            if method not in valid_methods:
                return f"錯誤：method 必須是 {', '.join(valid_methods)} 其中之一"
            
            # 如果設定了重複提醒，驗證 recurrence_rule
            if is_recurring and not recurrence_rule:
                return f"錯誤：設定為重複提醒時必須提供 recurrence_rule"
            
            # 查詢當前用戶的提醒數量（只計算 active 狀態的提醒）
            reminders_response = supabase_admin.from_("reminders").select("id", count="exact").eq("user_id", user_id).eq("status", "active").execute()
            current_reminders_count = reminders_response.count if reminders_response.count is not None else 0
            
            print(f"當前提醒數量：{current_reminders_count}")
            
            # 檢查是否超過限制
            if current_reminders_count >= Constants.REMINDERS_MAX:
                print(f"無法新增提醒：超過訂閱限制：{Constants.REMINDERS_MAX}")
                return f"無法新增提醒：超過訂閱限制：{Constants.REMINDERS_MAX}"
            
            # 處理 recurrence_exceptions 字串轉換為陣列
            recurrence_exceptions_array = None
            if recurrence_exceptions:
                try:
                    # 假設輸入格式為 "2024-01-01T10:00:00,2024-01-02T10:00:00"
                    exceptions_list = [exc.strip() for exc in recurrence_exceptions.split(',')]
                    recurrence_exceptions_array = exceptions_list
                except Exception as e:
                    print(f"處理 recurrence_exceptions 時發生錯誤：{str(e)}")
                    return f"錯誤：recurrence_exceptions 格式不正確"
            
            # 檢查是否已存在相同的 user_id、 remind_at、 method 組合（僅對非重複提醒）
            if not is_recurring:
                response = supabase_admin.from_("reminders").select("*").eq("user_id", user_id).eq("remind_at", remind_at).eq("method", method).execute()
                
                if response.data:
                    return f"已存在相同的提醒記錄"
            
            # 準備插入資料
            insert_data = {
                "user_id": user_id,
                "description": description,
                "remind_at": remind_at,
                "method": method,
                "is_recurring": is_recurring,
                "status": status
            }

            # 添加可選欄位
            if recurrence_rule:
                insert_data["recurrence_rule"] = recurrence_rule
            if recurrence_exceptions_array:
                insert_data["recurrence_exceptions"] = recurrence_exceptions_array
            
            # 添加新記錄
            result = supabase_admin.from_("reminders").insert(insert_data).execute()
            
            if result.data:
                new_record = result.data[0]
                recurring_info = f", 重複提醒: {'是' if is_recurring else '否'}"
                return f"成功添加提醒，ID: {new_record.get('id', '')}, Remind At: {remind_at}{recurring_info}"
            else:
                return "添加提醒失敗"
                
        except Exception as e:
            error_msg = f"添加提醒時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg

    create_reminder_tool = StructuredTool.from_function(
        func=create_reminder,
        name="create_reminder",
        description="""
            添加新的提醒，需要提供 remind_at、method、description 等參數，
            時間參數時請用本地時間設定 remind_at;
            method 支援 notification、notification-long;
            is_recurring 設定是否為重複提醒（預設 false）;
            recurrence_rule 使用 iCalendar RRULE 格式設定重複規則，例如：
            - 每週一到週五：FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;
            - 每日：FREQ=DAILY
            - 每週：FREQ=WEEKLY
            - 每月：FREQ=MONTHLY
            - 每年：FREQ=YEARLY
            recurrence_exceptions 設定排除的例外日期，格式為逗號分隔的時間字串;
            status 設定提醒狀態，預設為 active。
            """
    )

    return create_reminder_tool


def create_read_reminders_tool(user_id: str) -> StructuredTool:
    """創建讀取提醒工具"""

    def read_reminders() -> str:
        """讀取智能助理的提醒內容"""

        print(f"讀取全部提醒內容：{user_id}")
        content = ""
        try:
            response = supabase_admin.from_("reminders").select("id, description, remind_at, method, is_sent, sent_at, created_at").eq("user_id", user_id).execute()
            if response.data:
                reminders_list = []
                for reminder_data in response.data:
                    reminder_info = f"ID: {reminder_data.get('id', '')}, Description: {reminder_data.get('description', '')}, Remind At: {reminder_data.get('remind_at', '')}, Method: {reminder_data.get('method', '')}, Is Sent: {reminder_data.get('is_sent', '')}, Sent At: {reminder_data.get('sent_at', '')}, Created: {reminder_data.get('created_at', '')}"
                    reminders_list.append(reminder_info)
                content = "\n".join(reminders_list)

                print(f"提醒內容：{content}")
                return content
            else:
                return "No reminders found"
        except Exception as e:
            print(f"讀取提醒內容時發生錯誤：{str(e)}")
            return ""

    read_reminders_tool = StructuredTool.from_function(
        func=read_reminders,
        name="read_reminders",
        description="讀取智能助理的提醒內容，返回所有記錄的詳細信息",
    )

    return read_reminders_tool

def create_read_reminder_tool(user_id: str) -> StructuredTool:
    """創建讀取單個提醒工具 """

    def read_reminder(id: str) -> str:
        """讀取智能助理的單個提醒內容"""

        print(f"讀取單一提醒內容：ID {id}")
        try:
            response = supabase_admin.from_("reminders").select("id, description, remind_at, method, is_sent, sent_at, created_at").eq("id", id).eq("user_id", user_id).execute()
            
            if response.data:
                reminder_data = response.data[0]

                reminder_info = f"ID: {reminder_data.get('id', '')}, Description: {reminder_data.get('description', '')}, Remind At: {reminder_data.get('remind_at', '')}, Method: {reminder_data.get('method', '')}, Is Sent: {reminder_data.get('is_sent', '')}, Sent At: {reminder_data.get('sent_at', '')}, Created: {reminder_data.get('created_at', '')}"
                
                print(f"提醒內容：{reminder_info}")
                return reminder_info
            else:
                return f"找不到 ID {id} 的提醒記錄"
        except Exception as e:
            print(f"讀取單一提醒內容時發生錯誤：{str(e)}")
            return ""

    read_reminder_tool = StructuredTool.from_function(
        func=read_reminder,
        name="read_reminder",
        description="讀取智能助理的單個提醒內容，需要提供 id 參數",
    )

    return read_reminder_tool


def create_update_reminder_tool(user_id: str) -> StructuredTool:
    """創建更新提醒工具"""

    def update_reminder(id: str, remind_at: str, description: str, method: str = 'notification') -> bool:
        """更新智能助理的提醒內容"""

        print(f"更新提醒內容：ID {id}, Remind At {remind_at}, Method {method}, Description {description}")
        is_updated = False
        try:
            # 檢查指定 ID 的記錄是否存在
            response = supabase_admin.from_("reminders").select("*").eq("id", id).eq("user_id", user_id).execute()
            
            if response.data:
                # 如果記錄存在，更新內容
                supabase_admin.from_("reminders").update({
                    "remind_at": remind_at,
                    "method": method,
                    "description": description
                }).eq("id", id).eq("user_id", user_id).execute()
                is_updated = True
            else:
                print(f"找不到 ID {id} 的提醒記錄")
                is_updated = False
                
        except Exception as e:
            is_updated = False
            print(f"更新提醒內容時發生錯誤：{str(e)}")

        return is_updated

    update_reminder_tool = StructuredTool.from_function(
        func=update_reminder,
        name="update_reminder",
        description="""
            更新智能助理的提醒內容，
            需要提供 id、remind_at、description、method 等參數，
            時間參數時請用本地時間設定 remind_at;
            method 支援 notification 或 app 或 line。
            """
    )

    return update_reminder_tool


def create_delete_reminder_tool(user_id: str) -> StructuredTool:
    """創建刪除提醒工具"""

    def delete_reminder(id: str) -> str:
        """刪除指定的提醒記錄"""

        print(f"刪除提醒：ID {id}")
        try:
            # 檢查指定 ID 的記錄是否存在且屬於該 user
            response = supabase_admin.from_("reminders").select("*").eq("id", id).eq("user_id", user_id).execute()
            
            if not response.data:
                return f"找不到 ID {id} 的提醒記錄"
            
            # 刪除記錄
            result = supabase_admin.from_("reminders").delete().eq("id", id).eq("user_id", user_id).execute()
            
            if result.data:
                return f"成功刪除提醒記錄，ID: {id}"
            else:
                return "刪除提醒記錄失敗"
                
        except Exception as e:
            error_msg = f"刪除提醒時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg

    delete_reminder_tool = StructuredTool.from_function(
        func=delete_reminder,
        name="delete_reminder",
        description="刪除指定的提醒記錄，需要提供 id 參數",
    )

    return delete_reminder_tool


def create_search_reminders_by_keyword_tool(user_id: str) -> StructuredTool:
    """創建搜尋提醒工具"""

    def search_reminders_by_keyword(keyword: str) -> str:
        """搜尋智能助理的提醒內容，根據關鍵字搜尋描述"""

        print(f"搜尋提醒 from user_id：{user_id}, keyword：{keyword}")
        content = ""
        try:
            # 使用 ilike 進行模糊搜尋，搜尋描述包含關鍵字的提醒
            response = supabase_admin.from_("reminders").select("id, description, remind_at, method, is_sent, sent_at, created_at").eq("user_id", user_id).or_(f"description.ilike.%{keyword}%").execute()

            if response.data:
                reminders_list = []
                for reminder_data in response.data:
                    reminder_info = f"ID: {reminder_data.get('id', '')}, Description: {reminder_data.get('description', '')}, Remind At: {reminder_data.get('remind_at', '')}, Method: {reminder_data.get('method', '')}, Is Sent: {reminder_data.get('is_sent', '')}, Sent At: {reminder_data.get('sent_at', '')}, Created: {reminder_data.get('created_at', '')}"
                    reminders_list.append(reminder_info)
                content = "\n".join(reminders_list)

                print(f"搜尋結果：找到 {len(response.data)} 個提醒")
                return content
            else:
                return f"沒有找到包含關鍵字 '{keyword}' 的提醒"
        except Exception as e:
            print(f"搜尋提醒時發生錯誤：{str(e)}")
            return f"搜尋提醒時發生錯誤：{str(e)}"

    search_reminders_by_keyword_tool = StructuredTool.from_function(
        func=search_reminders_by_keyword,
        name="search_reminders_by_keyword",
        description="搜尋智能助理的提醒內容，根據關鍵字搜尋描述，需要提供 keyword 參數",
    )

    return search_reminders_by_keyword_tool

def create_search_reminder_by_time_tool(user_id: str) -> StructuredTool:
    """創建根據時間範圍搜尋提醒工具"""

    def search_reminders_by_time(start_at: str, end_at: str) -> str:
        """搜尋智能助理的提醒內容，根據時間範圍搜尋 remind_at 介於指定時間之間的提醒（支援一次性和重複性提醒）"""

        print(f"根據時間範圍搜尋提醒 from user_id：{user_id}, start_at：{start_at}, end_at：{end_at}")
        content = ""
        try:
            # 使用新的時間轉換函數，將用戶本地時間轉換為 UTC
            start_at_utc, start_info = convert_user_local_to_utc_time(user_id, start_at)
            end_at_utc, end_info = convert_user_local_to_utc_time(user_id, end_at)
            
            # 檢查時間轉換是否成功
            if "error" in start_info or "error" in end_info:
                return f"時間轉換失敗，請確認時間格式是否正確"
            
            print(f"start_at_utc：{start_at_utc}, end_at_utc：{end_at_utc}")

            # 延遲導入以避免循環導入
            from app.lib.reminder_manager import ReminderManager
            reminder_manager = ReminderManager()
            
            # 1. 搜尋一次性提醒
            one_time_reminders = []
            one_time_response = supabase_admin.from_("reminders").select(
                "id, description, remind_at, method, is_sent, sent_at, created_at, is_recurring, recurrence_rule, status"
            ).eq("user_id", user_id).eq("is_recurring", False).eq("status", "active").gte("remind_at", start_at_utc).lte("remind_at", end_at_utc).execute()
            
            if one_time_response.data:
                for reminder_data in one_time_response.data:
                    remind_at = reminder_data.get('remind_at', '')
                    remind_at_local, local_info = convert_utc_to_user_local_time(user_id, remind_at)
                    
                    reminder_info = f"ID: {reminder_data.get('id', '')}, Description: {reminder_data.get('description', '')}, Remind At: {remind_at_local}, Method: {reminder_data.get('method', '')}, Is Sent: {reminder_data.get('is_sent', '')}, Sent At: {reminder_data.get('sent_at', '')}, Created: {reminder_data.get('created_at', '')}, Type: 一次性提醒"
                    one_time_reminders.append(reminder_info)
            
            # 2. 搜尋重複性提醒
            recurring_reminders = []
            recurring_response = supabase_admin.from_("reminders").select(
                "id, description, remind_at, method, is_sent, sent_at, created_at, is_recurring, recurrence_rule, recurrence_exceptions, status"
            ).eq("user_id", user_id).eq("is_recurring", True).eq("status", "active").execute()
            
            if recurring_response.data:
                # 解析時間範圍
                start_date = datetime.fromisoformat(start_at_utc.replace('Z', '+00:00')).date()
                end_date = datetime.fromisoformat(end_at_utc.replace('Z', '+00:00')).date()
                
                # 檢查每一天是否有重複性提醒應該觸發
                current_date = start_date
                while current_date <= end_date:
                    current_datetime = datetime.combine(current_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                    
                    for reminder_data in recurring_response.data:
                        # 檢查重複性提醒是否應該在這一天觸發
                        if reminder_manager.should_reminder_occur_today(reminder_data, current_datetime):
                            # 生成這一天的提醒實例
                            instance = reminder_manager.get_recurring_reminder_instance(reminder_data, current_datetime)
                            if instance:
                                remind_at = instance.get('remind_at', '')
                                remind_at_local, local_info = convert_utc_to_user_local_time(user_id, remind_at)
                                
                                # 解析重複規則顯示
                                recurrence_rule = reminder_data.get('recurrence_rule', '')
                                original_remind_at = datetime.fromisoformat(reminder_data.get('remind_at', '').replace('Z', '+00:00'))
                                rule_display = reminder_manager.parse_recurrence_rule_for_display(recurrence_rule, original_remind_at)
                                
                                reminder_info = f"ID: {reminder_data.get('id', '')}, Description: {reminder_data.get('description', '')}, Remind At: {remind_at_local}, Method: {reminder_data.get('method', '')}, Rule: {rule_display}, Created: {reminder_data.get('created_at', '')}, Type: 重複性提醒"
                                recurring_reminders.append(reminder_info)
                    
                    current_date += timedelta(days=1)
            
            # 合併結果
            all_reminders = one_time_reminders + recurring_reminders
            
            if all_reminders:
                content = "\n".join(all_reminders)
                print(f"搜尋結果：找到 {len(one_time_reminders)} 個一次性提醒，{len(recurring_reminders)} 個重複性提醒實例")
                return content
            else:
                return f"沒有找到在時間範圍 '{start_at}' 到 '{end_at}' 之間的提醒"
                
        except Exception as e:
            print(f"根據時間範圍搜尋提醒時發生錯誤：{str(e)}")
            return f"根據時間範圍搜尋提醒時發生錯誤：{str(e)}"

    search_reminders_by_time_tool = StructuredTool.from_function(
        func=search_reminders_by_time,
        name="search_reminders_by_time",
        description="搜尋提醒紀錄，根據時間範圍搜尋 remind_at 介於指定時間之間的提醒（支援一次性和重複性提醒），需要提供 start_at 和 end_at 參數（請使用本地的時間）。重複性提醒會顯示在指定時間範圍內的所有觸發實例。",
    )

    return search_reminders_by_time_tool
