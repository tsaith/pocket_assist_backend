from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone

from app.lib.supabase import supabase_admin
from app.lib.user_time_manager import UserTimeManager
from app.core.constants import Constants


class UserReminderManager:
    """Manager class for user reminder operations"""
    
    def __init__(self, user_id: str):
        """
        Initialize UserReminderManager
        
        Args:
            user_id: The user's ID
        """
        self.user_id = user_id
        self.time_manager = UserTimeManager(user_id)
    
    def get_reminder_count(self) -> int:
        """
        Get the count of user's active reminders
        
        Returns:
            int: Number of active reminders for the user
        """
        print(f"取得提醒數量 from user_id：{self.user_id}")
        try:
            response = supabase_admin.from_("reminders").select("*", count="exact").eq("user_id", self.user_id).eq("status", "active").execute()
            count = response.count if response.count is not None else 0
            print(f"提醒數量：{count}")
            return count
        except Exception as e:
            print(f"取得提醒數量時發生錯誤：{str(e)}")
            return 0
    
    def get_reminder_method(self) -> str:
        """
        Retrieve reminder delivery method for the user from Supabase
        
        Returns:
            str: Reminder method or error message
        """
        print(f"獲取 user ID {self.user_id} 的提醒方法")
        try:
            response = supabase_admin.from_("profiles").select("reminder_method").eq("id", self.user_id).execute()
            
            if not response.data:
                error_msg = f"找不到 user ID {self.user_id} 的 profile 記錄"
                print(error_msg)
                return error_msg
            
            reminder_method = response.data[0].get("reminder_method", "app")
            print(f"目前的提醒方法：{reminder_method}")
            return reminder_method
        except Exception as e:
            error_msg = f"獲取提醒方法時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg

    def set_reminder_method(self, reminder_method: str) -> str:
        """
        Update reminder delivery method for the user in Supabase
        
        Args:
            reminder_method: The reminder method to set ('notification' or 'alarm')
            
        Returns:
            str: Success message or error message
        """
        print(f"設定 user ID {self.user_id} 的提醒方法為：{reminder_method}")
        try:
            allowed_methods = ["notification", "alarm"]
            normalized_method = reminder_method.lower()
            
            if normalized_method not in allowed_methods:
                return f"錯誤：提醒方法 '{reminder_method}' 不被支援。允許的值有：{', '.join(allowed_methods)}"
            
            response = supabase_admin.from_("profiles").update({
                "reminder_method": normalized_method
            }).eq("id", self.user_id).execute()
            
            if response.data:
                print(f"成功設定用戶 {self.user_id} 的提醒方法為：{normalized_method}")
                return f"成功設定提醒方法為：{normalized_method}"
            else:
                error_msg = f"更新提醒方法失敗，找不到用戶 {self.user_id}"
                print(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"設定提醒方法時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg
    
    def create_reminder(self, remind_at: str, method: str, description: str,
                       is_recurring: bool = False, recurrence_rule: Optional[str] = None,
                       recurrence_exceptions: Optional[str] = None) -> str:
        """
        Create a new reminder.
        
        Args:
            remind_at: Reminder time (user local time or ISO format with timezone)
            method: Reminder method ('notification' or 'alarm')
            description: Reminder description
            is_recurring: Whether this is a recurring reminder
            recurrence_rule: Recurrence rule in iCalendar RRULE format
            recurrence_exceptions: Comma-separated exception dates
            
        Returns:
            str: Success or error message
        """
        method = method.lower()
        print(f"添加提醒： Remind At {remind_at}, Method {method}, Description {description}")
        
        try:
            # 1. Validate method first
            valid_methods = ['notification', 'alarm']
            if method not in valid_methods:
                return f"錯誤：method 必須是 {', '.join(valid_methods)} 其中之一"
            
            # 2. Validate recurrence_rule if recurring
            if is_recurring and not recurrence_rule:
                return f"錯誤：設定為重複提醒時必須提供 recurrence_rule"
            
            # 3. Check reminders count limit
            if not self._check_reminders_limit():
                return f"無法新增提醒：達到最大提醒數量上限，最多只能存在 {Constants.REMINDERS_MAX} 個提醒"
                
            # 4. Convert remind_at to UTC time
            remind_at_utc = self._convert_to_utc_time(remind_at)
            if remind_at_utc.startswith("錯誤"):
                return remind_at_utc
            
            # 5. Process recurrence_exceptions
            recurrence_exceptions_array = self._process_recurrence_exceptions(recurrence_exceptions)
            if isinstance(recurrence_exceptions_array, str) and recurrence_exceptions_array.startswith("錯誤"):
                return recurrence_exceptions_array
            
            # 6. Check for duplicate reminders (only for non-recurring)
            if not is_recurring and self._is_duplicate_reminder(remind_at_utc, method):
                return f"已存在相同的提醒記錄"
            
            # 7. Prepare and insert reminder data
            insert_data = self._prepare_reminder_data(
                remind_at_utc, method, description, 
                is_recurring, recurrence_rule, recurrence_exceptions_array
            )
            
            # 8. Insert into database
            result = supabase_admin.from_("reminders").insert(insert_data).execute()
            
            if result.data:
                new_record = result.data[0]
                method_display = "鬧鐘" if method == "alarm" else "通知"
                recurring_info = f", 重複提醒: {'是' if is_recurring else '否'}"
                return f"成功添加提醒，方式: {method_display}, ID: {new_record.get('id', '')}, Remind At (UTC): {remind_at_utc}{recurring_info}"
            else:
                return "添加提醒失敗"
                
        except Exception as e:
            error_msg = f"添加提醒時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg
    
    def _convert_to_utc_time(self, remind_at: str) -> str:
        """
        Convert remind_at time to UTC format using UserTimeManager
        
        Args:
            remind_at: Time string in local or ISO format
            
        Returns:
            str: UTC time string or error message
        """
        try:
            # Use UserTimeManager to handle time conversion
            # This handles both local time and ISO format with timezone
            return self.time_manager.convert_local_to_utc_time(remind_at)
        except Exception as e:
            error_msg = f"錯誤：時間格式不正確，請使用本地時間格式 YYYY-MM-DD HH:MM:SS 或包含時區的格式 YYYY-MM-DDTHH:MM:SS+HH:MM。錯誤詳情：{str(e)}"
            print(error_msg)
            return error_msg
    
    def _check_reminders_limit(self) -> bool:
        """
        Check if user has reached the maximum reminders limit
        
        Returns:
            bool: True if under limit, False otherwise
        """
        current_reminders_count = self.get_reminder_count()
        
        if current_reminders_count >= Constants.REMINDERS_MAX:
            print(f"超過最大提醒數量上限：{Constants.REMINDERS_MAX}")
            return False
        
        return True
    
    def _process_recurrence_exceptions(self, recurrence_exceptions: Optional[str]) -> Optional[List[str]]:
        """
        Process recurrence_exceptions string into array
        
        Args:
            recurrence_exceptions: Comma-separated exception dates string
            
        Returns:
            List of exception dates or None if not provided, or error message string
        """
        if not recurrence_exceptions:
            return None
        
        try:
            exceptions_list = [exc.strip() for exc in recurrence_exceptions.split(',')]
            return exceptions_list
        except Exception as e:
            print(f"處理 recurrence_exceptions 時發生錯誤：{str(e)}")
            return "錯誤：recurrence_exceptions 格式不正確"
    
    def _is_duplicate_reminder(self, remind_at_utc: str, method: str) -> bool:
        """
        Check if a duplicate reminder already exists
        
        Args:
            remind_at_utc: UTC time string
            method: Reminder method
            
        Returns:
            bool: True if duplicate exists, False otherwise
        """
        response = supabase_admin.from_("reminders").select("*").eq(
            "user_id", self.user_id
        ).eq("remind_at", remind_at_utc).eq("method", method).execute()
        
        return bool(response.data)
    
    def _prepare_reminder_data(self, remind_at_utc: str, method: str, description: str,
                              is_recurring: bool, recurrence_rule: Optional[str],
                              recurrence_exceptions_array: Optional[List[str]]) -> Dict[str, Any]:
        """
        Prepare reminder data for database insertion
        
        Args:
            remind_at_utc: UTC time string
            method: Reminder method
            description: Reminder description
            is_recurring: Whether this is recurring
            recurrence_rule: Recurrence rule string
            recurrence_exceptions_array: List of exception dates
            
        Returns:
            Dict containing reminder data
        """
        insert_data = {
            "user_id": self.user_id,
            "description": description,
            "remind_at": remind_at_utc,
            "method": method,
            "is_recurring": is_recurring
        }
        
        # Add optional fields
        if recurrence_rule:
            insert_data["recurrence_rule"] = recurrence_rule
        if recurrence_exceptions_array:
            insert_data["recurrence_exceptions"] = recurrence_exceptions_array
        
        return insert_data
    
    def read_reminders(self) -> str:
        """
        Read all reminders
        
        Returns:
            str: Formatted reminders list or error message
        """
        print(f"讀取全部提醒內容：{self.user_id}")
        try:
            response = supabase_admin.from_("reminders").select("id, description, remind_at, method, is_sent, sent_at, created_at").eq("user_id", self.user_id).execute()
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
    
    def read_reminder(self, id: str) -> str:
        """
        Read a single reminder
        
        Args:
            id: Reminder ID
            
        Returns:
            str: Reminder information or error message
        """
        print(f"讀取單一提醒內容：ID {id}")
        try:
            response = supabase_admin.from_("reminders").select("id, description, remind_at, method, is_sent, sent_at, created_at").eq("id", id).eq("user_id", self.user_id).execute()
            
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
    
    def update_reminder(self, id: str, remind_at: str, description: str, method: str = 'notification') -> bool:
        """
        Update a reminder
        
        Args:
            id: Reminder ID
            remind_at: New reminder time
            description: New description
            method: New reminder method
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        print(f"更新提醒內容：ID {id}, Remind At {remind_at}, Method {method}, Description {description}")
        try:
            # Check if record exists
            response = supabase_admin.from_("reminders").select("*").eq("id", id).eq("user_id", self.user_id).execute()
            
            if response.data:
                # Update record
                supabase_admin.from_("reminders").update({
                    "remind_at": remind_at,
                    "method": method,
                    "description": description
                }).eq("id", id).eq("user_id", self.user_id).execute()
                return True
            else:
                print(f"找不到 ID {id} 的提醒記錄")
                return False
                
        except Exception as e:
            print(f"更新提醒內容時發生錯誤：{str(e)}")
            return False
    
    def delete_reminder(self, id: str) -> str:
        """
        Delete a reminder
        
        Args:
            id: Reminder ID
            
        Returns:
            str: Success or error message
        """
        print(f"刪除提醒：ID {id}")
        try:
            # Check if record exists
            response = supabase_admin.from_("reminders").select("*").eq("id", id).eq("user_id", self.user_id).execute()
            
            if not response.data:
                return f"找不到 ID {id} 的提醒記錄"
            
            # Delete record
            result = supabase_admin.from_("reminders").delete().eq("id", id).eq("user_id", self.user_id).execute()
            
            if result.data:
                return f"成功刪除提醒記錄，ID: {id}"
            else:
                return "刪除提醒記錄失敗"
                
        except Exception as e:
            error_msg = f"刪除提醒時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg
    
    def search_reminders_by_keyword(self, keyword: str) -> str:
        """
        Search reminders by keyword in description
        
        Args:
            keyword: Search keyword
            
        Returns:
            str: Formatted reminders list or error message
        """
        print(f"搜尋提醒 from user_id：{self.user_id}, keyword：{keyword}")
        try:
            # Search in description field
            response = supabase_admin.from_("reminders").select("id, description, remind_at, method, is_sent, sent_at, created_at").eq("user_id", self.user_id).or_(f"description.ilike.%{keyword}%").execute()
            
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
    
    def search_reminders_by_time(self, start_at: str, end_at: str) -> str:
        """
        Search reminders by time range (supports both one-time and recurring reminders)
        
        Args:
            start_at: Start time (user local time, format: YYYY-MM-DD HH:MM:SS)
            end_at: End time (user local time, format: YYYY-MM-DD HH:MM:SS)
            
        Returns:
            str: Formatted reminders list or error message
        """
        print(f"根據時間範圍搜尋提醒 from user_id：{self.user_id}, start_at：{start_at}, end_at：{end_at}")
        try:
            # Convert user local time to UTC using UserTimeManager
            try:
                start_at_utc = self.time_manager.convert_local_to_utc_time(start_at)
                end_at_utc = self.time_manager.convert_local_to_utc_time(end_at)
                print(f"start_at_utc：{start_at_utc}, end_at_utc：{end_at_utc}")
            except Exception as e:
                return f"時間轉換失敗，請確認時間格式是否正確：{str(e)}"
            
            # Import ReminderManager for recurring reminder logic (lazy import to avoid circular import)
            from app.lib.reminder_manager import ReminderManager
            reminder_manager = ReminderManager()
            
            # 1. Search one-time reminders
            one_time_reminders = []
            one_time_response = supabase_admin.from_("reminders").select(
                "id, description, remind_at, method, is_sent, sent_at, created_at, is_recurring, recurrence_rule, status"
            ).eq("user_id", self.user_id).eq("is_recurring", False).eq("status", "active").gte("remind_at", start_at_utc).lte("remind_at", end_at_utc).execute()
            
            if one_time_response.data:
                for reminder_data in one_time_response.data:
                    remind_at = reminder_data.get('remind_at', '')
                    remind_at_local = self.time_manager.convert_utc_to_local_time(remind_at)
                    
                    reminder_info = f"ID: {reminder_data.get('id', '')}, Description: {reminder_data.get('description', '')}, Remind At: {remind_at_local}, Method: {reminder_data.get('method', '')}, Is Sent: {reminder_data.get('is_sent', '')}, Sent At: {reminder_data.get('sent_at', '')}, Created: {reminder_data.get('created_at', '')}, Type: 一次性提醒"
                    one_time_reminders.append(reminder_info)
            
            # 2. Search recurring reminders
            recurring_reminders = []
            recurring_response = supabase_admin.from_("reminders").select(
                "id, description, remind_at, method, is_sent, sent_at, created_at, is_recurring, recurrence_rule, recurrence_exceptions, status"
            ).eq("user_id", self.user_id).eq("is_recurring", True).eq("status", "active").execute()
            
            if recurring_response.data:
                # Parse time range
                start_date = datetime.fromisoformat(start_at_utc.replace('Z', '+00:00')).date()
                end_date = datetime.fromisoformat(end_at_utc.replace('Z', '+00:00')).date()
                
                # Check each day for recurring reminders
                current_date = start_date
                while current_date <= end_date:
                    current_datetime = datetime.combine(current_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                    
                    for reminder_data in recurring_response.data:
                        # Check if recurring reminder should occur on this day
                        if reminder_manager.should_reminder_occur_today(reminder_data, current_datetime):
                            # Generate reminder instance for this day
                            instance = reminder_manager.get_recurring_reminder_instance(reminder_data, current_datetime)
                            if instance:
                                remind_at = instance.get('remind_at', '')
                                remind_at_local = self.time_manager.convert_utc_to_local_time(remind_at)
                                
                                # Parse recurrence rule for display
                                recurrence_rule = reminder_data.get('recurrence_rule', '')
                                original_remind_at = datetime.fromisoformat(reminder_data.get('remind_at', '').replace('Z', '+00:00'))
                                rule_display = reminder_manager.parse_recurrence_rule_for_display(recurrence_rule, original_remind_at)
                                
                                reminder_info = f"ID: {reminder_data.get('id', '')}, Description: {reminder_data.get('description', '')}, Remind At: {remind_at_local}, Method: {reminder_data.get('method', '')}, Rule: {rule_display}, Created: {reminder_data.get('created_at', '')}, Type: 重複性提醒"
                                recurring_reminders.append(reminder_info)
                    
                    current_date += timedelta(days=1)
            
            # Combine results
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
