
from datetime import datetime
from zoneinfo import ZoneInfo

from app.lib.supabase import supabase_admin

def get_weekday(timezone: str) -> str:
    """獲取指定時區的今天是星期幾"""

    try:
        # 1. 設定指定時區
        target_tz = ZoneInfo(timezone)
        
        # 2. 取得指定時區的當前時間
        target_time = datetime.now(target_tz)
        
        # 3. 獲取星期幾（數字 1=星期一, 7=星期日，符合 ISO 標準）
        iso_weekday_num = target_time.isoweekday()
        
        # 4. 轉換為中文星期名稱
        weekday_names = ["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday = weekday_names[iso_weekday_num]
        
        return weekday
        
    except Exception as e:
        error_msg = f"獲取 {timezone} 時區星期幾時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg


def get_date(timezone: str) -> str:
    """獲取指定時區的今天日期（ISO 格式：YYYY-MM-DD）"""

    try:
        # 1. 設定指定時區
        target_tz = ZoneInfo(timezone)
        
        # 2. 取得指定時區的當前時間
        target_time = datetime.now(target_tz)
        
        # 3. 格式化日期為 ISO 格式（YYYY-MM-DD）
        date_str = target_time.strftime("%Y-%m-%d")
        
        return date_str
        
    except Exception as e:
        error_msg = f"獲取 {timezone} 時區日期時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg


def get_current_time(timezone: str) -> str:
    """獲取指定時區的當前時間（格式：YYYY-MM-DD HH:MM:SS）"""

    try:
        # 1. 設定指定時區
        target_tz = ZoneInfo(timezone)
        
        # 2. 取得指定時區的當前時間
        target_time = datetime.now(target_tz)
        
        # 3. 格式化為日期時間字串（YYYY-MM-DD HH:MM:SS）
        time_str = target_time.strftime("%Y-%m-%d %H:%M:%S")
        
        return time_str
        
    except Exception as e:
        error_msg = f"獲取 {timezone} 時區當前時間時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg


def get_user_timezone(user_id: str) -> str:
    """從資料庫獲取指定使用者的時區資訊"""

    try:
        # 從 profiles 表取得 timezone
        profile_response = supabase_admin.from_("profiles").select("timezone").eq("id", user_id).execute()
        
        if not profile_response.data:
            error_msg = f"找不到 user ID {user_id} 的 profile 記錄"
            print(error_msg)
            return error_msg
        
        timezone = profile_response.data[0].get("timezone", "Asia/Taipei")
        
        return timezone
        
    except Exception as e:
        error_msg = f"獲取時區資訊時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg


class UserTimeManager:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.timezone = get_user_timezone(user_id)

    def get_timezone(self) -> str:
        """獲取時區資訊"""

        return self.timezone

    def get_weekday(self) -> str:
        """獲取今天是星期幾"""

        return get_weekday(self.timezone)

    def get_date(self) -> str:
        """獲取今天的日期（ISO 格式：YYYY-MM-DD）"""

        return get_date(self.timezone)

    def get_current_time(self) -> str:
        """獲取當前時間（格式：YYYY-MM-DD HH:MM:SS）"""

        return get_current_time(self.timezone)