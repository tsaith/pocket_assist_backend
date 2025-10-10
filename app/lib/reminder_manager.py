from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import httpx
import re
from app.lib.supabase import supabase_admin
from app.core.config import settings


class ReminderManager:
    """
    提醒管理器，負責處理提醒的觸發邏輯
    """
    
    def __init__(self):
        self.private_access_token = settings.PRIVATE_ACCESS_TOKEN
    
    def should_reminder_occur_today(self, reminder: Dict[str, Any], today: datetime) -> bool:
        """
        檢查重複性提醒是否應該在今天觸發
        
        Args:
            reminder: 提醒資料
            today: 今天日期
            
        Returns:
            bool: 是否應該觸發
        """
        try:
            is_recurring = reminder.get('is_recurring', False)
            recurrence_rule = reminder.get('recurrence_rule', '')
            remind_at = datetime.fromisoformat(reminder.get('remind_at', '').replace('Z', '+00:00'))
            
            # 如果不是重複性提醒，檢查是否為今天
            if not is_recurring:
                return remind_at.date() == today.date()
            
            # 檢查例外日期
            recurrence_exceptions = reminder.get('recurrence_exceptions', [])
            if recurrence_exceptions:
                today_str = today.date().isoformat()
                for exception in recurrence_exceptions:
                    if exception and today_str in str(exception):
                        return False
            
            # 解析重複規則
            if not recurrence_rule:
                return False
                
            # 檢查是否在開始日期之後
            if remind_at.date() > today.date():
                return False
            
            # 解析不同的重複規則
            if 'FREQ=DAILY' in recurrence_rule:
                # 每日提醒
                return True
            elif 'FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR' in recurrence_rule:
                # 工作日提醒
                return today.weekday() < 5  # Monday=0, Friday=4
            elif 'FREQ=WEEKLY' in recurrence_rule:
                # 每週提醒 - 檢查是否為相同的星期幾
                return remind_at.weekday() == today.weekday()
            elif 'FREQ=MONTHLY' in recurrence_rule:
                # 每月提醒 - 檢查是否為相同的日期
                return remind_at.day == today.day
            elif 'FREQ=YEARLY' in recurrence_rule:
                # 每年提醒 - 檢查是否為相同的月份和日期
                return remind_at.month == today.month and remind_at.day == today.day
            
            return False
            
        except Exception as e:
            print(f"檢查重複性提醒時發生錯誤：{str(e)}")
            return False
    
    def get_recurring_reminder_instance(self, reminder: Dict[str, Any], target_date: datetime) -> Optional[Dict[str, Any]]:
        """
        為重複性提醒生成指定日期的實例
        
        Args:
            reminder: 原始提醒資料
            target_date: 目標日期
            
        Returns:
            Dict[str, Any]: 生成的提醒實例，如果無法生成則返回 None
        """
        try:
            if not reminder.get('is_recurring', False):
                return reminder
            
            # 獲取原始提醒的時間
            original_remind_at = datetime.fromisoformat(reminder.get('remind_at', '').replace('Z', '+00:00'))
            original_time = original_remind_at.time()
            
            # 創建目標日期的提醒時間
            target_remind_at = datetime.combine(target_date.date(), original_time)
            target_remind_at = target_remind_at.replace(tzinfo=timezone.utc)
            
            # 創建虛擬提醒實例
            virtual_reminder = reminder.copy()
            virtual_reminder['remind_at'] = target_remind_at.isoformat()
            virtual_reminder['is_sent'] = False  # 重複性提醒的實例不應該標記為已發送
            virtual_reminder['sent_at'] = None
            
            return virtual_reminder
            
        except Exception as e:
            print(f"生成重複性提醒實例時發生錯誤：{str(e)}")
            return None
    
    def parse_recurrence_rule(self, rule: str) -> Dict[str, Any]:
        """
        解析 iCalendar RRULE 格式的重複規則
        
        Args:
            rule: RRULE 字串
            
        Returns:
            Dict[str, Any]: 解析後的規則資訊
        """
        try:
            if not rule:
                return {}
            
            parsed_rule = {}
            
            # 解析頻率
            if 'FREQ=DAILY' in rule:
                parsed_rule['frequency'] = 'daily'
            elif 'FREQ=WEEKLY' in rule:
                parsed_rule['frequency'] = 'weekly'
            elif 'FREQ=MONTHLY' in rule:
                parsed_rule['frequency'] = 'monthly'
            elif 'FREQ=YEARLY' in rule:
                parsed_rule['frequency'] = 'yearly'
            
            # 解析星期幾 (BYDAY)
            byday_match = re.search(r'BYDAY=([^;]+)', rule)
            if byday_match:
                days = byday_match.group(1).split(',')
                parsed_rule['byday'] = [day.strip() for day in days]
            
            # 解析月份日期 (BYMONTHDAY)
            bymonthday_match = re.search(r'BYMONTHDAY=([^;]+)', rule)
            if bymonthday_match:
                days = bymonthday_match.group(1).split(',')
                parsed_rule['bymonthday'] = [int(day.strip()) for day in days if day.strip().isdigit()]
            
            # 解析間隔 (INTERVAL)
            interval_match = re.search(r'INTERVAL=(\d+)', rule)
            if interval_match:
                parsed_rule['interval'] = int(interval_match.group(1))
            else:
                parsed_rule['interval'] = 1
            
            return parsed_rule
            
        except Exception as e:
            print(f"解析重複規則時發生錯誤：{str(e)}")
            return {}
    
    async def get_recurring_reminders_for_today(self) -> List[Dict[str, Any]]:
        """
        獲取今天應該觸發的重複性提醒
        
        Returns:
            List[Dict[str, Any]]: 今天應該觸發的重複性提醒列表
        """
        try:
            today = datetime.now(timezone.utc)
            
            # 查詢所有重複性提醒
            response = supabase_admin.from_("reminders").select(
                "id, user_id, description, remind_at, method, is_recurring, recurrence_rule, recurrence_exceptions, status"
            ).eq("is_recurring", True).eq("status", "active").execute()
            
            if not response.data:
                return []
            
            recurring_reminders = []
            
            for reminder in response.data:
                if self.should_reminder_occur_today(reminder, today):
                    # 生成今天的提醒實例
                    instance = self.get_recurring_reminder_instance(reminder, today)
                    if instance:
                        recurring_reminders.append(instance)
            
            print(f"找到 {len(recurring_reminders)} 個今天應該觸發的重複性提醒")
            return recurring_reminders
            
        except Exception as e:
            print(f"獲取重複性提醒時發生錯誤：{str(e)}")
            return []
    
    async def trigger_reminders(self) -> Dict[str, Any]:
        """
        觸發所有符合條件的提醒（包括重複性提醒）
        
        條件：
        - 一次性提醒：remind_at 時間在 (現在, 現在+一個小時) 之間，is_sent = false
        - 重複性提醒：今天應該觸發的重複性提醒
        
        觸發時：
        1. 一次性提醒：is_sent 設為 true，sent_at 設為觸發時的時間
        2. 重複性提醒：不更新資料庫狀態，直接發送
        """
        try:
            # 獲取當前時間
            now = datetime.now(timezone.utc)
            # 計算185秒後的時間
            target_time = now + timedelta(seconds=185)
            
            print(f"檢查提醒觸發條件：現在時間 {now}, 目標時間 {target_time}")
            
            triggered_reminders = []
            current_time = datetime.now(timezone.utc)
            
            # 1. 處理一次性提醒
            one_time_reminders = await self._get_one_time_reminders(now, target_time)
            for reminder in one_time_reminders:
                reminder_id = reminder.get('id')
                
                # 更新提醒狀態
                update_result = supabase_admin.from_("reminders").update({
                    "is_sent": True,
                    "sent_at": current_time.isoformat()
                }).eq("id", reminder_id).execute()
                
                if update_result.data:
                    print(f"一次性提醒已觸發：reminder id={reminder_id}")
                    
                    # 記錄觸發的提醒信息
                    triggered_info = {
                        "id": reminder_id,
                        "user_id": reminder.get('user_id'),
                        "description": reminder.get('description'),
                        "remind_at": reminder.get('remind_at'),
                        "method": reminder.get('method'),
                        "triggered_at": current_time.isoformat(),
                        "is_recurring": False
                    }
                    triggered_reminders.append(triggered_info)
                else:
                    print(f"更新一次性提醒狀態失敗：reminder id={reminder_id}")
            
            # 2. 處理重複性提醒
            recurring_reminders = await self.get_recurring_reminders_for_today()
            for reminder in recurring_reminders:
                # 檢查時間是否在觸發範圍內
                remind_at = datetime.fromisoformat(reminder.get('remind_at', '').replace('Z', '+00:00'))
                if now <= remind_at <= target_time:
                    print(f"重複性提醒已觸發：reminder id={reminder.get('id')}")
                    
                    # 記錄觸發的提醒信息（重複性提醒不更新資料庫狀態）
                    triggered_info = {
                        "id": reminder.get('id'),
                        "user_id": reminder.get('user_id'),
                        "description": reminder.get('description'),
                        "remind_at": reminder.get('remind_at'),
                        "method": reminder.get('method'),
                        "triggered_at": current_time.isoformat(),
                        "is_recurring": True
                    }
                    triggered_reminders.append(triggered_info)
            
            if not triggered_reminders:
                print("沒有找到需要觸發的提醒")
                return {
                    "success": True,
                    "message": "沒有找到需要觸發的提醒",
                    "triggered_count": 0,
                    "triggered_reminders": []
                }
            
            print(f"成功觸發 {len(triggered_reminders)} 個提醒")
            await self.send_reminders(triggered_reminders)
            
            return {
                "success": True,
                "message": f"成功觸發 {len(triggered_reminders)} 個提醒",
                "triggered_count": len(triggered_reminders),
                "triggered_reminders": triggered_reminders
            }
            
        except Exception as e:
            error_msg = f"觸發提醒時發生錯誤：{str(e)}"
            print(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "triggered_count": 0,
                "triggered_reminders": []
            }
    
    async def _get_one_time_reminders(self, now: datetime, target_time: datetime) -> List[Dict[str, Any]]:
        """
        獲取一次性提醒
        
        Args:
            now: 當前時間
            target_time: 目標時間
            
        Returns:
            List[Dict[str, Any]]: 一次性提醒列表
        """
        try:
            # 查詢符合條件的一次性提醒
            response = supabase_admin.from_("reminders").select(
                "id, user_id, description, remind_at, method, is_sent, sent_at, is_recurring"
            ).eq("is_sent", False).eq("is_recurring", False).gte("remind_at", now.isoformat()).lte("remind_at", target_time.isoformat()).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            print(f"獲取一次性提醒時發生錯誤：{str(e)}")
            return []
    
    def parse_recurrence_rule_for_display(self, rule: str, remind_at: datetime) -> str:
        """
        解析重複規則並返回用於顯示的字串
        
        Args:
            rule: RRULE 字串
            remind_at: 提醒時間
            
        Returns:
            str: 顯示用的重複規則字串
        """
        try:
            if not rule:
                return "Never"
            
            if 'FREQ=DAILY' in rule:
                return "Daily"
            elif 'FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR' in rule:
                return "Weekdays"
            elif 'FREQ=WEEKLY' in rule:
                # 檢查是否有特定的星期幾
                weekdays = self._parse_multiple_weekdays(rule)
                if weekdays:
                    return f"Weekly {', '.join(weekdays)}"
                else:
                    # 使用原始提醒的星期幾
                    weekday_name = self._get_weekday_name(remind_at.weekday())
                    return f"Weekly {weekday_name}"
            elif 'FREQ=MONTHLY' in rule:
                # 檢查是否有特定的日期
                days = self._parse_multiple_days(rule)
                if days:
                    sorted_days = sorted(days)
                    return f"Monthly {', '.join(map(str, sorted_days))}"
                else:
                    # 使用原始提醒的日期
                    return f"Monthly {remind_at.day}"
            elif 'FREQ=YEARLY' in rule:
                # 使用原始提醒的月份和日期
                month_name = self._get_month_name(remind_at.month)
                return f"Yearly {month_name} {remind_at.day}"
            
            return "Custom"
            
        except Exception as e:
            print(f"解析重複規則顯示時發生錯誤：{str(e)}")
            return "Custom"
    
    def _get_weekday_name(self, weekday: int) -> str:
        """
        獲取星期幾的名稱
        
        Args:
            weekday: 星期幾 (0=Monday, 6=Sunday)
            
        Returns:
            str: 星期幾名稱
        """
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return weekdays[weekday] if 0 <= weekday <= 6 else "Unknown"
    
    def _get_month_name(self, month: int) -> str:
        """
        獲取月份名稱
        
        Args:
            month: 月份 (1-12)
            
        Returns:
            str: 月份名稱
        """
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return months[month - 1] if 1 <= month <= 12 else "Unknown"
    
    def _parse_multiple_weekdays(self, rule: str) -> List[str]:
        """
        從規則中解析多個星期幾
        
        Args:
            rule: RRULE 字串
            
        Returns:
            List[str]: 星期幾列表
        """
        try:
            if 'BYDAY=' in rule:
                components = rule.split('BYDAY=')
                if len(components) > 1:
                    weekdays_string = components[1].split(';')[0]
                    weekdays = weekdays_string.split(',')
                    return [self._convert_weekday_code(day.strip()) for day in weekdays]
            return []
        except Exception as e:
            print(f"解析多個星期幾時發生錯誤：{str(e)}")
            return []
    
    def _parse_multiple_days(self, rule: str) -> List[int]:
        """
        從規則中解析多個日期
        
        Args:
            rule: RRULE 字串
            
        Returns:
            List[int]: 日期列表
        """
        try:
            if 'BYMONTHDAY=' in rule:
                components = rule.split('BYMONTHDAY=')
                if len(components) > 1:
                    days_string = components[1].split(';')[0]
                    days = days_string.split(',')
                    return [int(day.strip()) for day in days if day.strip().isdigit()]
            return []
        except Exception as e:
            print(f"解析多個日期時發生錯誤：{str(e)}")
            return []
    
    def _convert_weekday_code(self, code: str) -> str:
        """
        轉換星期幾代碼為名稱
        
        Args:
            code: 星期幾代碼 (MO, TU, WE, TH, FR, SA, SU)
            
        Returns:
            str: 星期幾名稱
        """
        weekday_map = {
            'MO': 'Mon', 'TU': 'Tue', 'WE': 'Wed', 'TH': 'Thu',
            'FR': 'Fri', 'SA': 'Sat', 'SU': 'Sun'
        }
        return weekday_map.get(code, code)
    
    async def get_todays_reminders(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        獲取今天的提醒（包括重複性提醒）
        
        Args:
            user_id: 可選的用戶ID，如果提供則只返回該用戶的提醒
            
        Returns:
            List[Dict[str, Any]]: 今天的提醒列表
        """
        try:
            today = datetime.now(timezone.utc)
            todays_reminders = []
            
            # 構建查詢條件
            query = supabase_admin.from_("reminders").select(
                "id, user_id, description, remind_at, method, is_recurring, recurrence_rule, recurrence_exceptions, status"
            ).eq("status", "active")
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            response = query.execute()
            
            if not response.data:
                return []
            
            for reminder in response.data:
                # 檢查是否為今天
                if not reminder.get('is_recurring', False):
                    # 一次性提醒
                    remind_at = datetime.fromisoformat(reminder.get('remind_at', '').replace('Z', '+00:00'))
                    if remind_at.date() == today.date():
                        todays_reminders.append(reminder)
                else:
                    # 重複性提醒
                    if self.should_reminder_occur_today(reminder, today):
                        instance = self.get_recurring_reminder_instance(reminder, today)
                        if instance:
                            todays_reminders.append(instance)
            
            print(f"找到 {len(todays_reminders)} 個今天的提醒")
            return todays_reminders
            
        except Exception as e:
            print(f"獲取今天的提醒時發生錯誤：{str(e)}")
            return []

    def get_user_id_by_reminder_id(self, reminder_id: str) -> Optional[str]:
        """
        透過 reminder id 找到對應的 user_id
        
        Args:
            reminder_id: 提醒ID
            
        Returns:
            str: user_id，如果找不到則返回 None
        """
        try:
            # 首先從 reminders 表獲取 user_id
            reminder_response = supabase_admin.from_("reminders").select("user_id").eq("id", reminder_id).single().execute()
            
            if not reminder_response.data:
                print(f"找不到 reminder_id {reminder_id} 的記錄")
                return None
            
            user_id = reminder_response.data.get('user_id')
            if not user_id:
                print(f"reminder_id {reminder_id} 沒有關聯的 user_id")
                return None
            
            if user_id:
                print(f"找到 reminder_id {reminder_id} 對應的 user_id: {user_id}")
                return str(user_id)
            else:
                print(f"reminder_id {reminder_id} 沒有關聯的 user_id")
                return None
                
        except Exception as e:
            print(f"透過 reminder_id 獲取 user_id 時發生錯誤: {str(e)}")
            return None

    async def send_reminders(self, triggered_reminders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        發送提醒訊息給 LINE 用戶
        
        支援三種發送方式：
        1. App 內部發送
        2. LINE Official Account（推薦，統一管理）
        3. Linebot（保留原有邏輯）
        
        Args:
            triggered_reminders: 已觸發的提醒列表
            
        Returns:
            Dict[str, Any]: 發送結果
        """
        try:
            
            sent_count = 0
            failed_count = 0
            sent_details = []
            failed_details = []
            
            for reminder in triggered_reminders:
                reminder_id = reminder.get('id')
                description = reminder.get('description', '')
                method = reminder.get('method', 'app')
                user_id = reminder.get('user_id')  # 從 triggered_reminders 中直接獲取
                message = f"🔔 提醒：{description}"
                
                try:
                    if not user_id:
                        failed_count += 1
                        failed_details.append({
                            "reminder_id": reminder_id,
                            "error": "無法取得 user_id"
                        })
                        continue

                    line_user_id = None
                    linebot_success = False

                    # 嘗試使用 App 內部發送訊息
                    if method == 'app' or method == 'notification':
                        try:
                            result = await self.send_app_reminder(user_id, message)
                            if result.get('success'):
                                sent_count += 1
                                sent_details.append({
                                    "reminder_id": reminder_id,
                                    "user_id": user_id,
                                    "message": message,
                                    "method": "app"
                                })
                        except Exception as e:
                            print(f"App 內部發送失敗，reminder_id: {reminder_id}, error: {str(e)}")

                    if method == 'line' or method == 'notification':
                        try:
                            result = await self.send_line_reminder(user_id, message)
                            if result.get('success'):
                                sent_count += 1
                                sent_details.append({
                                    "reminder_id": reminder_id,
                                    "user_id": user_id,
                                    "message": message,
                                    "method": "line"
                                })
                        except Exception as e:
                            print(f"Line 發送失敗，reminder_id: {reminder_id}, error: {str(e)}")
                    
                    # 注意：linebot 方法已移除，因為不再使用 chatbot_id

                except Exception as e:
                    error_msg = f"處理提醒時發生錯誤，reminder_id: {reminder_id}, error: {str(e)}"
                    print(error_msg)
                    failed_count += 1
                    failed_details.append({
                        "reminder_id": reminder_id,
                        "error": str(e)
                    })
            
            result = {
                "success": True,
                "sent_count": sent_count,
                "failed_count": failed_count,
                "sent_details": sent_details,
                "failed_details": failed_details
            }
            
            print(f"提醒發送完成：成功 {sent_count} 個，失敗 {failed_count} 個")
            return result
            
        except Exception as e:
            error_msg = f"發送提醒時發生錯誤：{str(e)}"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "sent_count": 0,
                "failed_count": len(triggered_reminders),
                "sent_details": [],
                "failed_details": []
            }

    async def send_app_reminder(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        透過 App 內部 API 發送提醒訊息
        
        Args:
            user_id: 用戶ID
            message: 提醒訊息內容
            
        Returns:
            Dict[str, Any]: 發送結果
        """
        try:
            # 獲取 chatbot_id
            chatbot_response = supabase_admin.from_("chatbots").select("id").eq("user_id", user_id).single().execute()
            if not chatbot_response.data:
                return {
                    "success": False,
                    "message": f"找不到 user_id {user_id} 對應的 chatbot"
                }
            
            chatbot_id = chatbot_response.data['id']
            
            # 構建請求數據
            request_data = {
                "user_id": user_id,
                "chatbot_id": chatbot_id,
                "platform": "app",
                "sender": "bot",
                "content": message,
                "meta_data": {},
                "private_access_token": self.private_access_token
            }
            
            # 呼叫 push-message API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.SITE_URL}/api/v1/chat/push-message",
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                    timeout=3.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        print(f"成功透過 App 內部 API 發送提醒訊息，user_id: {user_id}")
                        return {
                            "success": True,
                            "message": "提醒訊息發送成功",
                            "api_response": result
                        }
                    else:
                        error_msg = f"API 回應顯示失敗：{result.get('message', '未知錯誤')}"
                        print(error_msg)
                        return {
                            "success": False,
                            "message": error_msg,
                            "api_response": result
                        }
                else:
                    error_msg = f"API 呼叫失敗，狀態碼：{response.status_code}, 回應：{response.text}"
                    print(error_msg)
                    return {
                        "success": False,
                        "message": error_msg,
                        "status_code": response.status_code,
                        "response_text": response.text
                    }
                    
        except httpx.TimeoutException:
            error_msg = "API 呼叫超時"
            print(error_msg)
            return {
                "success": False,
                "message": error_msg
            }
        except httpx.RequestError as e:
            error_msg = f"API 請求錯誤：{str(e)}"
            print(error_msg)
            return {
                "success": False,
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"發送 App 內部提醒時發生錯誤：{str(e)}"
            print(error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    async def send_line_reminder(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        透過 LINE 發送提醒訊息
        """
        try:
            # 延遲導入以避免循環導入
            from app.lib.line.official_account import official_account
            
            line_user_id = official_account.get_line_user_id_by_user_id(user_id)

            if line_user_id and official_account.check_line_user_exist(line_user_id):
                # 使用 LINE Official Account 發送
                official_account.push_message(line_user_id, message)
                print(f"成功使用 LINE Official Account 發送提醒訊息，line_user_id: {line_user_id}")
                return {
                    "success": True,
                    "message": "提醒訊息發送成功",
                    "user_id": user_id,
                    "line_user_id": line_user_id,
                    "message": message,
                    "method": "line"
                }
                                
            else:
                print(f"無法使用 LINE Official Account 發送，line_user_id: {line_user_id}")
                return {
                    "success": False,
                    "message": "無法取得有效的 LINE 用戶 ID"
                }

        except Exception as e:
            error_msg = f"發送 LINE 提醒時發生錯誤：{str(e)}"
            print(error_msg)
            return {
                "success": False,
                "message": error_msg
            }