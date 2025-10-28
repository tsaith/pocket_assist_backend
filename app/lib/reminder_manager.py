from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import httpx
import re
from app.lib.supabase import supabase_admin
from app.core.config import settings


class ReminderManager:
    """
    Reminder manager responsible for handling reminder trigger logic
    """
    
    def __init__(self):
        self.private_access_token = settings.PRIVATE_ACCESS_TOKEN
    
    def should_reminder_occur_today(self, reminder: Dict[str, Any], today: datetime) -> bool:
        """
        Check if recurring reminder should be triggered today
        
        Args:
            reminder: Reminder data
            today: Today's date
            
        Returns:
            bool: Whether it should be triggered
        """
        try:
            is_recurring = reminder.get('is_recurring', False)
            recurrence_rule = reminder.get('recurrence_rule', '')
            remind_at = datetime.fromisoformat(reminder.get('remind_at', '').replace('Z', '+00:00'))
            
            # If not recurring reminder, check if it's today
            if not is_recurring:
                return remind_at.date() == today.date()
            
            # Check exception dates
            recurrence_exceptions = reminder.get('recurrence_exceptions', [])
            if recurrence_exceptions:
                today_str = today.date().isoformat()
                for exception in recurrence_exceptions:
                    if exception and today_str in str(exception):
                        return False
            
            # Parse recurrence rule
            if not recurrence_rule:
                return False
                
            # Check if after start date
            if remind_at.date() > today.date():
                return False
            
            # Parse different recurrence rules
            if 'FREQ=DAILY' in recurrence_rule:
                # Daily reminder
                return True
            elif 'FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR' in recurrence_rule:
                # Weekday reminder
                return today.weekday() < 5  # Monday=0, Friday=4
            elif 'FREQ=WEEKLY' in recurrence_rule:
                # Weekly reminder - support multiple weekdays
                if 'BYDAY=' in recurrence_rule:
                    # Parse multiple weekdays
                    byday_match = re.search(r'BYDAY=([^;]+)', recurrence_rule)
                    if byday_match:
                        days = byday_match.group(1).split(',')
                        today_weekday_code = self._get_weekday_code(today.weekday())
                        return today_weekday_code in [day.strip() for day in days]
                else:
                    # No BYDAY, use original reminder's weekday
                    return remind_at.weekday() == today.weekday()
            elif 'FREQ=MONTHLY' in recurrence_rule:
                # Monthly reminder - support multiple dates
                if 'BYMONTHDAY=' in recurrence_rule:
                    # Parse multiple dates
                    bymonthday_match = re.search(r'BYMONTHDAY=([^;]+)', recurrence_rule)
                    if bymonthday_match:
                        days = bymonthday_match.group(1).split(',')
                        try:
                            target_days = [int(day.strip()) for day in days if day.strip().isdigit()]
                            return today.day in target_days
                        except ValueError:
                            # If parsing fails, fallback to original logic
                            return remind_at.day == today.day
                    else:
                        return remind_at.day == today.day
                else:
                    # No BYMONTHDAY, use original reminder's date
                    return remind_at.day == today.day
            elif 'FREQ=YEARLY' in recurrence_rule:
                # Yearly reminder - check if same month and day
                return remind_at.month == today.month and remind_at.day == today.day
            
            return False
            
        except Exception as e:
            print(f"Error occurred while checking recurring reminder: {str(e)}")
            return False
    
    def get_recurring_reminder_instance(self, reminder: Dict[str, Any], target_date: datetime) -> Optional[Dict[str, Any]]:
        """
        Generate instance for recurring reminder on specified date
        
        Args:
            reminder: Original reminder data
            target_date: Target date
            
        Returns:
            Dict[str, Any]: Generated reminder instance, returns None if unable to generate
        """
        try:
            if not reminder.get('is_recurring', False):
                return reminder
            
            # Get original reminder time
            original_remind_at = datetime.fromisoformat(reminder.get('remind_at', '').replace('Z', '+00:00'))
            original_time = original_remind_at.time()
            
            # Create reminder time for target date
            target_remind_at = datetime.combine(target_date.date(), original_time)
            target_remind_at = target_remind_at.replace(tzinfo=timezone.utc)
            
            # Create virtual reminder instance
            virtual_reminder = reminder.copy()
            virtual_reminder['remind_at'] = target_remind_at.isoformat()
            virtual_reminder['is_sent'] = False  # Recurring reminder instances should not be marked as sent
            virtual_reminder['sent_at'] = None
            
            return virtual_reminder
            
        except Exception as e:
            print(f"Error occurred while generating recurring reminder instance: {str(e)}")
            return None
    
    def parse_recurrence_rule(self, rule: str) -> Dict[str, Any]:
        """
        Parse iCalendar RRULE format recurrence rule
        
        Args:
            rule: RRULE string
            
        Returns:
            Dict[str, Any]: Parsed rule information
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
            print(f"Error occurred while parsing recurrence rule: {str(e)}")
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
            
            print(f"Found {len(recurring_reminders)} recurring reminders that should be triggered today")
            return recurring_reminders
            
        except Exception as e:
            print(f"Error occurred while getting recurring reminders: {str(e)}")
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
            
            print(f"Checking reminder trigger conditions: current time {now}, target time {target_time}")
            
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
                    print(f"One-time reminder triggered: reminder id={reminder_id}")
                    
                    # Record triggered reminder information
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
                    print(f"Failed to update one-time reminder status: reminder id={reminder_id}")
            
            # 2. Handle recurring reminders
            recurring_reminders = await self.get_recurring_reminders_for_today()
            for reminder in recurring_reminders:
                # 檢查時間是否在觸發範圍內
                remind_at = datetime.fromisoformat(reminder.get('remind_at', '').replace('Z', '+00:00'))
                if now <= remind_at <= target_time:
                    print(f"Recurring reminder triggered: reminder id={reminder.get('id')}")
                    
                    # Record triggered reminder information (recurring reminders don't update database status)
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
                print("No reminders found that need to be triggered")
                return {
                    "success": True,
                    "message": "No reminders found that need to be triggered",
                    "triggered_count": 0,
                    "triggered_reminders": []
                }
            
            print(f"Successfully triggered {len(triggered_reminders)} reminders")
            await self.send_reminders(triggered_reminders)
            
            return {
                "success": True,
                "message": f"Successfully triggered {len(triggered_reminders)} reminders",
                "triggered_count": len(triggered_reminders),
                "triggered_reminders": triggered_reminders
            }
            
        except Exception as e:
            error_msg = f"Error occurred while triggering reminders: {str(e)}"
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
            print(f"Error occurred while getting one-time reminders: {str(e)}")
            return []
    
    def parse_recurrence_rule_for_display(self, rule: str, remind_at: datetime) -> str:
        """
        Parse recurrence rule and return display string
        
        Args:
            rule: RRULE string
            remind_at: Reminder time
            
        Returns:
            str: Display string for recurrence rule
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
            print(f"Error occurred while parsing recurrence rule for display: {str(e)}")
            return "Custom"
    
    def _get_weekday_name(self, weekday: int) -> str:
        """
        Get weekday name
        
        Args:
            weekday: Weekday number (0=Monday, 6=Sunday)
            
        Returns:
            str: Weekday name
        """
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return weekdays[weekday] if 0 <= weekday <= 6 else "Unknown"
    
    def _get_month_name(self, month: int) -> str:
        """
        Get month name
        
        Args:
            month: Month number (1-12)
            
        Returns:
            str: Month name
        """
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return months[month - 1] if 1 <= month <= 12 else "Unknown"
    
    def _parse_multiple_weekdays(self, rule: str) -> List[str]:
        """
        Parse multiple weekdays from rule
        
        Args:
            rule: RRULE string
            
        Returns:
            List[str]: List of weekdays
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
            print(f"Error occurred while parsing multiple weekdays: {str(e)}")
            return []
    
    def _parse_multiple_days(self, rule: str) -> List[int]:
        """
        Parse multiple days from rule
        
        Args:
            rule: RRULE string
            
        Returns:
            List[int]: List of days
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
            print(f"Error occurred while parsing multiple days: {str(e)}")
            return []
    
    def _get_weekday_code(self, weekday: int) -> str:
        """
        Convert Python weekday number to iCalendar weekday code
        
        Args:
            weekday: Python weekday (0=Monday, 6=Sunday)
            
        Returns:
            str: iCalendar weekday code (MO, TU, WE, TH, FR, SA, SU)
        """
        weekday_codes = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
        return weekday_codes[weekday] if 0 <= weekday <= 6 else "MO"
    
    def _convert_weekday_code(self, code: str) -> str:
        """
        Convert weekday code to name
        
        Args:
            code: Weekday code (MO, TU, WE, TH, FR, SA, SU)
            
        Returns:
            str: Weekday name
        """
        weekday_map = {
            'MO': 'Mon', 'TU': 'Tue', 'WE': 'Wed', 'TH': 'Thu',
            'FR': 'Fri', 'SA': 'Sat', 'SU': 'Sun'
        }
        return weekday_map.get(code, code)
    
    async def get_todays_reminders(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get today's reminders (including recurring reminders)
        
        Args:
            user_id: Optional user ID, if provided only returns reminders for that user
            
        Returns:
            List[Dict[str, Any]]: List of today's reminders
        """
        try:
            today = datetime.now(timezone.utc)
            todays_reminders = []
            
            # Build query conditions
            query = supabase_admin.from_("reminders").select(
                "id, user_id, description, remind_at, method, is_recurring, recurrence_rule, recurrence_exceptions, status"
            ).eq("status", "active")
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            response = query.execute()
            
            if not response.data:
                return []
            
            for reminder in response.data:
                # Check if it's today
                if not reminder.get('is_recurring', False):
                    # One-time reminder
                    remind_at = datetime.fromisoformat(reminder.get('remind_at', '').replace('Z', '+00:00'))
                    if remind_at.date() == today.date():
                        todays_reminders.append(reminder)
                else:
                    # Recurring reminder
                    if self.should_reminder_occur_today(reminder, today):
                        instance = self.get_recurring_reminder_instance(reminder, today)
                        if instance:
                            todays_reminders.append(instance)
            
            print(f"Found {len(todays_reminders)} reminders for today")
            return todays_reminders
            
        except Exception as e:
            print(f"Error occurred while getting today's reminders: {str(e)}")
            return []

    def get_user_id_by_reminder_id(self, reminder_id: str) -> Optional[str]:
        """
        Find corresponding user_id through reminder id
        
        Args:
            reminder_id: Reminder ID
            
        Returns:
            str: user_id, returns None if not found
        """
        try:
            # First get user_id from reminders table
            reminder_response = supabase_admin.from_("reminders").select("user_id").eq("id", reminder_id).single().execute()
            
            if not reminder_response.data:
                print(f"Cannot find record for reminder_id {reminder_id}")
                return None
            
            user_id = reminder_response.data.get('user_id')
            if not user_id:
                print(f"reminder_id {reminder_id} has no associated user_id")
                return None
            
            if user_id:
                print(f"Found user_id for reminder_id {reminder_id}: {user_id}")
                return str(user_id)
            else:
                print(f"reminder_id {reminder_id} has no associated user_id")
                return None
                
        except Exception as e:
            print(f"Error occurred while getting user_id through reminder_id: {str(e)}")
            return None

    async def send_reminders(self, triggered_reminders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send reminder messages to LINE users
        
        Supports three sending methods:
        1. App internal sending
        2. LINE Official Account (recommended, unified management)
        3. Linebot (retain original logic)
        
        Args:
            triggered_reminders: List of triggered reminders
            
        Returns:
            Dict[str, Any]: Sending results
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
                message = f"🔔 Reminder: {description}"
                
                try:
                    if not user_id:
                        failed_count += 1
                        failed_details.append({
                            "reminder_id": reminder_id,
                            "error": "Unable to get user_id"
                        })
                        continue

                    line_user_id = None
                    linebot_success = False

                    # Try using App internal sending
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
                            print(f"App internal sending failed, reminder_id: {reminder_id}, error: {str(e)}")

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
                            print(f"Line sending failed, reminder_id: {reminder_id}, error: {str(e)}")
                    
                    # Note: linebot method has been removed because chatbot_id is no longer used

                except Exception as e:
                    error_msg = f"Error occurred while processing reminder, reminder_id: {reminder_id}, error: {str(e)}"
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
            
            print(f"Reminder sending completed: {sent_count} successful, {failed_count} failed")
            return result
            
        except Exception as e:
            error_msg = f"Error occurred while sending reminders: {str(e)}"
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
        Send reminder message through App internal API
        
        Args:
            user_id: User ID
            message: Reminder message content
            
        Returns:
            Dict[str, Any]: Sending result
        """
        try:
            # Get chatbot_id
            chatbot_response = supabase_admin.from_("chatbots").select("id").eq("user_id", user_id).single().execute()
            if not chatbot_response.data:
                return {
                    "success": False,
                    "message": f"Cannot find chatbot for user_id {user_id}"
                }
            
            chatbot_id = chatbot_response.data['id']
            
            # Build request data
            request_data = {
                "user_id": user_id,
                "chatbot_id": chatbot_id,
                "platform": "app",
                "sender": "bot",
                "content": message,
                "meta_data": {},
                "private_access_token": self.private_access_token
            }
            
            # Call push-message API
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
                        print(f"Successfully sent reminder message through App internal API, user_id: {user_id}")
                        return {
                            "success": True,
                            "message": "Reminder message sent successfully",
                            "api_response": result
                        }
                    else:
                        error_msg = f"API response shows failure: {result.get('message', 'Unknown error')}"
                        print(error_msg)
                        return {
                            "success": False,
                            "message": error_msg,
                            "api_response": result
                        }
                else:
                    error_msg = f"API call failed, status code: {response.status_code}, response: {response.text}"
                    print(error_msg)
                    return {
                        "success": False,
                        "message": error_msg,
                        "status_code": response.status_code,
                        "response_text": response.text
                    }
                    
        except httpx.TimeoutException:
            error_msg = "API call timeout"
            print(error_msg)
            return {
                "success": False,
                "message": error_msg
            }
        except httpx.RequestError as e:
            error_msg = f"API request error: {str(e)}"
            print(error_msg)
            return {
                "success": False,
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"Error occurred while sending App internal reminder: {str(e)}"
            print(error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    async def send_line_reminder(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Send reminder message through LINE
        """
        try:
            # Delayed import to avoid circular import
            from app.lib.line.official_account import official_account
            
            line_user_id = official_account.get_line_user_id_by_user_id(user_id)

            if line_user_id and official_account.check_line_user_exist(line_user_id):
                # Send using LINE Official Account
                official_account.push_message(line_user_id, message)
                print(f"Successfully sent reminder message using LINE Official Account, line_user_id: {line_user_id}")
                return {
                    "success": True,
                    "message": "Reminder message sent successfully",
                    "user_id": user_id,
                    "line_user_id": line_user_id,
                    "message": message,
                    "method": "line"
                }
                                
            else:
                print(f"Unable to send using LINE Official Account, line_user_id: {line_user_id}")
                return {
                    "success": False,
                    "message": "Unable to get valid LINE user ID"
                }

        except Exception as e:
            error_msg = f"Error occurred while sending LINE reminder: {str(e)}"
            print(error_msg)
            return {
                "success": False,
                "message": error_msg
            }