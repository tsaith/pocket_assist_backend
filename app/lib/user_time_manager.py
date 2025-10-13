
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

    def get_relative_date(self, days_offset: int = 0) -> str:
        """
        獲取相對日期
        
        Args:
            days_offset: 天數偏移 (-3=大前天, -2=前天, -1=昨天, 0=今天, 1=明天, 2=後天, 3=大後天)
        
        Returns:
            str: 日期字符串 (YYYY-MM-DD)
        
        Examples:
            manager.get_relative_date(1)   # 明天
            manager.get_relative_date(2)   # 後天
            manager.get_relative_date(-1)  # 昨天
            manager.get_relative_date(-2)  # 前天
        """
        return get_relative_date(self.timezone, days_offset)

    def get_weekday_date(self, weekday: int, weeks_offset: int = 0) -> str:
        """
        獲取相對星期幾的日期
        
        Args:
            weekday: 星期幾 (1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday, 7=Sunday)
            weeks_offset: 周數偏移 (-2=上上週, -1=上週, 0=本週, 1=下週, 2=下下週)
        
        Returns:
            str: 日期字符串 (YYYY-MM-DD)
        
        Examples:
            manager.get_weekday_date(3, 1)   # 下週三
            manager.get_weekday_date(4, -1)  # 上週四
            manager.get_weekday_date(1, 2)   # 下下週一
        """
        return get_weekday_date(self.timezone, weekday, weeks_offset)

    def convert_local_to_utc_time(self, time_local: str) -> str:
        """
        將本地時間轉換為 UTC 時間（ISO 8601/RFC 3339 格式）
        
        Args:
            time_local: 本地時間字符串（格式：YYYY-MM-DD HH:MM:SS 或 ISO 8601 格式）
        
        Returns:
            str: UTC 時間字符串（ISO 8601/RFC 3339 格式，以 Z 結尾）
        
        Examples:
            manager.convert_local_to_utc_time("2025-10-13 15:30:00")
            # 返回: "2025-10-13T07:30:00Z" (假設時區為 Asia/Taipei, UTC+8)
        """
        utc_time, time_info = convert_user_local_to_utc_time(self.user_id, time_local)
        return utc_time

    def convert_utc_to_local_time(self, time_utc: str) -> str:
        """
        將 UTC 時間轉換為本地時間（ISO 8601/RFC 3339 格式）
        
        Args:
            time_utc: UTC 時間字符串（格式：YYYY-MM-DD HH:MM:SS 或 ISO 8601 格式）
        
        Returns:
            str: 本地時間字符串（ISO 8601/RFC 3339 格式，包含時區偏移）
        
        Examples:
            manager.convert_utc_to_local_time("2025-10-13 07:30:00")
            # 返回: "2025-10-13T15:30:00+08:00" (假設時區為 Asia/Taipei, UTC+8)
        """
        local_time, time_info = convert_utc_to_user_local_time(self.user_id, time_utc)
        return local_time
