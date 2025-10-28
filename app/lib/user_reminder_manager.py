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
        print(f"Getting reminder count for user_id: {self.user_id}")
        try:
            response = supabase_admin.from_("reminders").select("*", count="exact").eq("user_id", self.user_id).eq("status", "active").execute()
            count = response.count if response.count is not None else 0
            print(f"Reminder count: {count}")
            return count
        except Exception as e:
            print(f"Error occurred while getting reminder count: {str(e)}")
            return 0
    
    def get_reminder_method(self) -> str:
        """
        Retrieve reminder delivery method for the user from Supabase
        
        Returns:
            str: Reminder method or error message
        """
        print(f"Getting reminder method for user ID {self.user_id}")
        try:
            response = supabase_admin.from_("profiles").select("reminder_method").eq("id", self.user_id).execute()
            
            if not response.data:
                error_msg = f"Profile record not found for user ID {self.user_id}"
                print(error_msg)
                return error_msg
            
            reminder_method = response.data[0].get("reminder_method", "app")
            print(f"Current reminder method: {reminder_method}")
            return reminder_method
        except Exception as e:
            error_msg = f"Error occurred while getting reminder method: {str(e)}"
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
        print(f"Setting reminder method for user ID {self.user_id} to: {reminder_method}")
        try:
            allowed_methods = ["notification", "alarm"]
            normalized_method = reminder_method.lower()
            
            if normalized_method not in allowed_methods:
                return f"Error: reminder method '{reminder_method}' is not supported. Allowed values are: {', '.join(allowed_methods)}"
            
            response = supabase_admin.from_("profiles").update({
                "reminder_method": normalized_method
            }).eq("id", self.user_id).execute()
            
            if response.data:
                print(f"Successfully set reminder method for user {self.user_id} to: {normalized_method}")
                return f"Successfully set reminder method to: {normalized_method}"
            else:
                error_msg = f"Failed to update reminder method, user {self.user_id} not found"
                print(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"Error occurred while setting reminder method: {str(e)}"
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
        print(f"Creating reminder: Remind At {remind_at}, Method {method}, Description {description}")
        
        try:
            # 1. Validate method first
            valid_methods = ['notification', 'alarm']
            if method not in valid_methods:
                return f"Error: method must be one of {', '.join(valid_methods)}"
            
            # 2. Validate recurrence_rule if recurring
            if is_recurring and not recurrence_rule:
                return f"Error: recurrence_rule is required when is_recurring is true"
            
            # 3. Check reminders count limit
            if not self._check_reminders_limit():
                return f"Cannot create reminder: maximum reminders limit reached ({Constants.REMINDERS_MAX} reminders)"
                
            # 4. Convert remind_at to UTC time
            remind_at_utc = self._convert_to_utc_time(remind_at)
            if remind_at_utc.startswith("Error"):
                return remind_at_utc
            
            # 5. Process recurrence_exceptions
            recurrence_exceptions_array = self._process_recurrence_exceptions(recurrence_exceptions)
            if isinstance(recurrence_exceptions_array, str) and recurrence_exceptions_array.startswith("Error"):
                return recurrence_exceptions_array
            
            # 6. Check for duplicate reminders (only for non-recurring)
            if not is_recurring and self._is_duplicate_reminder(remind_at_utc, method):
                return f"Reminder with same time and method already exists"
            
            # 7. Prepare and insert reminder data
            insert_data = self._prepare_reminder_data(
                remind_at_utc, method, description, 
                is_recurring, recurrence_rule, recurrence_exceptions_array
            )
            
            # 8. Insert into database
            result = supabase_admin.from_("reminders").insert(insert_data).execute()
            
            if result.data:
                new_record = result.data[0]
                method_display = "alarm" if method == "alarm" else "notification"
                recurring_info = f", Recurring: {'Yes' if is_recurring else 'No'}"
                return f"Successfully created reminder, Method: {method_display}, ID: {new_record.get('id', '')}, Remind At (UTC): {remind_at_utc}{recurring_info}"
            else:
                return "Failed to create reminder"
                
        except Exception as e:
            error_msg = f"Error occurred while creating reminder: {str(e)}"
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
            error_msg = f"Error: Invalid time format. Please use local time format YYYY-MM-DD HH:MM:SS or ISO format with timezone YYYY-MM-DDTHH:MM:SS+HH:MM. Error details: {str(e)}"
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
            print(f"Maximum reminders limit exceeded: {Constants.REMINDERS_MAX}")
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
            print(f"Error occurred while processing recurrence_exceptions: {str(e)}")
            return "Error: Invalid recurrence_exceptions format"
    
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
        print(f"Reading all reminders for user: {self.user_id}")
        try:
            response = supabase_admin.from_("reminders").select("id, description, remind_at, method, is_sent, sent_at, created_at").eq("user_id", self.user_id).execute()
            if response.data:
                reminders_list = []
                for reminder_data in response.data:
                    reminder_info = f"ID: {reminder_data.get('id', '')}, Description: {reminder_data.get('description', '')}, Remind At: {reminder_data.get('remind_at', '')}, Method: {reminder_data.get('method', '')}, Is Sent: {reminder_data.get('is_sent', '')}, Sent At: {reminder_data.get('sent_at', '')}, Created: {reminder_data.get('created_at', '')}"
                    reminders_list.append(reminder_info)
                content = "\n".join(reminders_list)
                
                print(f"Reminder content: {content}")
                return content
            else:
                return "No reminders found"
        except Exception as e:
            print(f"Error occurred while reading reminders: {str(e)}")
            return ""
    
    def read_reminder(self, id: str) -> str:
        """
        Read a single reminder
        
        Args:
            id: Reminder ID
            
        Returns:
            str: Reminder information or error message
        """
        print(f"Reading single reminder: ID {id}")
        try:
            response = supabase_admin.from_("reminders").select("id, description, remind_at, method, is_sent, sent_at, created_at").eq("id", id).eq("user_id", self.user_id).execute()
            
            if response.data:
                reminder_data = response.data[0]
                reminder_info = f"ID: {reminder_data.get('id', '')}, Description: {reminder_data.get('description', '')}, Remind At: {reminder_data.get('remind_at', '')}, Method: {reminder_data.get('method', '')}, Is Sent: {reminder_data.get('is_sent', '')}, Sent At: {reminder_data.get('sent_at', '')}, Created: {reminder_data.get('created_at', '')}"
                
                print(f"Reminder content: {reminder_info}")
                return reminder_info
            else:
                return f"Reminder record with ID {id} not found"
        except Exception as e:
            print(f"Error occurred while reading single reminder: {str(e)}")
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
        print(f"Updating reminder: ID {id}, Remind At {remind_at}, Method {method}, Description {description}")
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
                print(f"Reminder record with ID {id} not found")
                return False
                
        except Exception as e:
            print(f"Error occurred while updating reminder: {str(e)}")
            return False
    
    def delete_reminder(self, id: str) -> str:
        """
        Delete a reminder
        
        Args:
            id: Reminder ID
            
        Returns:
            str: Success or error message
        """
        print(f"Deleting reminder: ID {id}")
        try:
            # Check if record exists
            response = supabase_admin.from_("reminders").select("*").eq("id", id).eq("user_id", self.user_id).execute()
            
            if not response.data:
                return f"Reminder record with ID {id} not found"
            
            # Delete record
            result = supabase_admin.from_("reminders").delete().eq("id", id).eq("user_id", self.user_id).execute()
            
            if result.data:
                return f"Successfully deleted reminder record, ID: {id}"
            else:
                return "Failed to delete reminder record"
                
        except Exception as e:
            error_msg = f"Error occurred while deleting reminder: {str(e)}"
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
        print(f"Searching reminders for user_id: {self.user_id}, keyword: {keyword}")
        try:
            # Search in description field
            response = supabase_admin.from_("reminders").select("id, description, remind_at, method, is_sent, sent_at, created_at").eq("user_id", self.user_id).or_(f"description.ilike.%{keyword}%").execute()
            
            if response.data:
                reminders_list = []
                for reminder_data in response.data:
                    reminder_info = f"ID: {reminder_data.get('id', '')}, Description: {reminder_data.get('description', '')}, Remind At: {reminder_data.get('remind_at', '')}, Method: {reminder_data.get('method', '')}, Is Sent: {reminder_data.get('is_sent', '')}, Sent At: {reminder_data.get('sent_at', '')}, Created: {reminder_data.get('created_at', '')}"
                    reminders_list.append(reminder_info)
                content = "\n".join(reminders_list)
                
                print(f"Search results: found {len(response.data)} reminders")
                return content
            else:
                return f"No reminders found containing keyword '{keyword}'"
        except Exception as e:
            print(f"Error occurred while searching reminders: {str(e)}")
            return f"Error occurred while searching reminders: {str(e)}"
    
    def search_reminders_by_time(self, start_at: str, end_at: str) -> str:
        """
        Search reminders by time range (supports both one-time and recurring reminders)
        
        Args:
            start_at: Start time (user local time, format: YYYY-MM-DD HH:MM:SS)
            end_at: End time (user local time, format: YYYY-MM-DD HH:MM:SS)
            
        Returns:
            str: Formatted reminders list or error message
        """
        print(f"Searching reminders by time range for user_id: {self.user_id}, start_at: {start_at}, end_at: {end_at}")
        try:
            # Convert user local time to UTC using UserTimeManager
            try:
                start_at_utc = self.time_manager.convert_local_to_utc_time(start_at)
                end_at_utc = self.time_manager.convert_local_to_utc_time(end_at)
                print(f"start_at_utc: {start_at_utc}, end_at_utc: {end_at_utc}")
            except Exception as e:
                return f"Time conversion failed, please check time format: {str(e)}"
            
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
                    
                    reminder_info = f"ID: {reminder_data.get('id', '')}, Description: {reminder_data.get('description', '')}, Remind At: {remind_at_local}, Method: {reminder_data.get('method', '')}, Is Sent: {reminder_data.get('is_sent', '')}, Sent At: {reminder_data.get('sent_at', '')}, Created: {reminder_data.get('created_at', '')}, Type: One-time reminder"
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
                                
                                reminder_info = f"ID: {reminder_data.get('id', '')}, Description: {reminder_data.get('description', '')}, Remind At: {remind_at_local}, Method: {reminder_data.get('method', '')}, Rule: {rule_display}, Created: {reminder_data.get('created_at', '')}, Type: Recurring reminder"
                                recurring_reminders.append(reminder_info)
                    
                    current_date += timedelta(days=1)
            
            # Combine results
            all_reminders = one_time_reminders + recurring_reminders
            
            if all_reminders:
                content = "\n".join(all_reminders)
                print(f"Search results: found {len(one_time_reminders)} one-time reminders, {len(recurring_reminders)} recurring reminder instances")
                return content
            else:
                return f"No reminders found in time range '{start_at}' to '{end_at}'"
                
        except Exception as e:
            print(f"Error occurred while searching reminders by time range: {str(e)}")
            return f"Error occurred while searching reminders by time range: {str(e)}"
