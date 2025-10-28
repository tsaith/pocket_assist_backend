
from app.lib.utils.time_utils import (
    get_weekday,
    get_date,
    get_current_time,
    get_user_timezone,
    get_weekday_date,
    get_relative_date,
    convert_user_local_to_utc_time,
    convert_utc_to_user_local_time
)


class UserTimeManager:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.timezone = get_user_timezone(user_id)

    def get_timezone(self) -> str:
        """Get timezone information"""

        return self.timezone

    def get_weekday(self) -> str:
        """Get what day of the week it is today"""

        return get_weekday(self.timezone)

    def get_date(self) -> str:
        """Get today's date (ISO format: YYYY-MM-DD)"""

        return get_date(self.timezone)

    def get_current_time(self) -> str:
        """Get current time (format: YYYY-MM-DD HH:MM:SS)"""

        return get_current_time(self.timezone)

    def get_relative_date(self, days_offset: int = 0) -> str:
        """
        Get relative date
        
        Args:
            days_offset: Days offset (-3=three days ago, -2=day before yesterday, -1=yesterday, 0=today, 1=tomorrow, 2=day after tomorrow, 3=three days from now)
        
        Returns:
            str: Date string (YYYY-MM-DD)
        
        Examples:
            manager.get_relative_date(1)   # tomorrow
            manager.get_relative_date(2)   # day after tomorrow
            manager.get_relative_date(-1)  # yesterday
            manager.get_relative_date(-2)  # day before yesterday
        """
        return get_relative_date(self.timezone, days_offset)

    def get_weekday_date(self, weekday: int, weeks_offset: int = 0) -> str:
        """
        Get relative weekday date
        
        Args:
            weekday: Day of week (1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday, 7=Sunday)
            weeks_offset: Weeks offset (-2=two weeks ago, -1=last week, 0=this week, 1=next week, 2=in two weeks)
        
        Returns:
            str: Date string (YYYY-MM-DD)
        
        Examples:
            manager.get_weekday_date(3, 1)   # next Wednesday
            manager.get_weekday_date(4, -1)  # last Thursday
            manager.get_weekday_date(1, 2)   # Monday in two weeks
        """
        return get_weekday_date(self.timezone, weekday, weeks_offset)

    def convert_local_to_utc_time(self, time_local: str) -> str:
        """
        Convert local time to UTC time (ISO 8601/RFC 3339 format)
        
        Args:
            time_local: Local time string (format: YYYY-MM-DD HH:MM:SS or ISO 8601 format)
        
        Returns:
            str: UTC time string (ISO 8601/RFC 3339 format, ending with Z)
        
        Examples:
            manager.convert_local_to_utc_time("2025-10-13 15:30:00")
            # Returns: "2025-10-13T07:30:00Z" (assuming timezone is Asia/Taipei, UTC+8)
        """
        utc_time, time_info = convert_user_local_to_utc_time(self.user_id, time_local)
        return utc_time

    def convert_utc_to_local_time(self, time_utc: str) -> str:
        """
        Convert UTC time to local time (ISO 8601/RFC 3339 format)
        
        Args:
            time_utc: UTC time string (format: YYYY-MM-DD HH:MM:SS or ISO 8601 format)
        
        Returns:
            str: Local time string (ISO 8601/RFC 3339 format, with timezone offset)
        
        Examples:
            manager.convert_utc_to_local_time("2025-10-13 07:30:00")
            # Returns: "2025-10-13T15:30:00+08:00" (assuming timezone is Asia/Taipei, UTC+8)
        """
        local_time, time_info = convert_utc_to_user_local_time(self.user_id, time_utc)
        return local_time
