from typing import Tuple
from datetime import datetime
from zoneinfo import ZoneInfo
from langchain_core.tools import StructuredTool
from app.lib.chatbot.utils import (
    get_city_local_time
)
from app.lib.supabase import supabase_admin
from app.lib.utils import get_user_timezone
from app.lib.user_time_manager import UserTimeManager


def get_weekday(timezone: str = "Asia/Taipei") -> Tuple[str, dict]:
    """獲取指定時區的今天是禮拜幾"""

    print(f"獲取 {timezone} 時區的今天是禮拜幾")
    
    try:
        # 1. 設定指定時區
        target_tz = ZoneInfo(timezone)
        
        # 2. 取得指定時區的當前時間
        target_time = datetime.now(target_tz)
        
        # 3. 獲取星期幾（數字 1=星期一, 7=星期日，符合 ISO 標準）
        iso_weekday_num = target_time.isoweekday()
        
        # 4. 轉換為中文星期名稱
        weekday_names = ["", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday = weekday_names[iso_weekday_num]
        
        # 5. 構建詳細資訊
        weekday_info = {
            "timezone": timezone,
            "weekday": weekday,
            "date": target_time.strftime("%Y-%m-%d")
        }
        
        # 6. 生成內容字串
        content = f"{timezone} 時區今天是: {weekday}"
        
        return content, weekday_info
        
    except Exception as e:
        error_msg = f"獲取 {timezone} 時區星期幾時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}


def get_current_time_with_timezone(timezone: str) -> Tuple[str, dict]:
    """獲取指定時區的目前時間"""
    print(f"查詢 {timezone} 時區的目前時間")
    
    try:
        # 使用 utils.py 中的 get_current_time 函數獲取指定時區的時間
        from app.lib.chatbot.utils import get_current_time
        current_time = get_current_time(timezone)
        
        time_info = {
            "timezone": timezone,
            "current_time": current_time
        }
        
        content = f"{timezone} 時區目前時間：{current_time}"
        
        return content, time_info
        
    except Exception as e:
        error_msg = f"獲取 {timezone} 時區時間時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}

def get_taiwan_time() -> Tuple[str, str]:
    """獲取台灣目前時間"""
    print("獲取台灣目前時間")
    return get_city_local_time("Taipei")


def get_city_time(city: str = "Taipei") -> Tuple[str, dict]:
    """獲取指定城市的目前時間"""

    print(f"獲取{city}目前時間")

    city = city.lower()
    
    try:
        # 獲取城市時間
        current_time = get_city_local_time(city)
        
        time_info = {
            "city": city,
            "current_time": current_time,
            "timezone": "local"
        }
        
        content = f"{city}目前時間：{current_time}"
        
        return content, time_info
        
    except Exception as e:
        error_msg = f"查詢{city}時間時發生錯誤：{str(e)}"
        return error_msg, {"error": str(e)}


def get_user_weekday(user_id: str) -> Tuple[str, dict]:
    """獲取指定用戶所在時區的今天是禮拜幾"""
    print(f"獲取 user ID {user_id} 所在時區的今天是禮拜幾")
    
    try:
        # 使用 UserTimeManager
        time_manager = UserTimeManager(user_id)
        timezone = time_manager.get_timezone()
        weekday = time_manager.get_weekday()
        date = time_manager.get_date()
        
        # 構建回應
        combined_info = {
            "user_id": user_id,
            "timezone": timezone,
            "weekday": weekday,
            "date": date,
            "status": "success"
        }
        
        content = f"您所在時區 ({timezone}) 今天是：{weekday}"
        
        return content, combined_info
        
    except Exception as e:
        error_msg = f"獲取用戶時區星期幾時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}


def get_user_current_time(user_id: str) -> Tuple[str, dict]:
    """獲取指定用戶所在時區的目前時間"""
    print(f"獲取 user ID {user_id} 所在時區的目前時間")
    
    try:
        # 使用 UserTimeManager
        time_manager = UserTimeManager(user_id)
        timezone = time_manager.get_timezone()
        current_time = time_manager.get_current_time()
        
        # 構建回應
        combined_info = {
            "user_id": user_id,
            "timezone": timezone,
            "current_time": current_time,
            "status": "success"
        }
        
        content = f"您目前所在時區 ({timezone}) 的時間是：{current_time}"
        
        return content, combined_info
        
    except Exception as e:
        error_msg = f"獲取用戶時區時間時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}


def get_current_timezone(user_id: str) -> Tuple[str, dict]:
    """獲取指定用戶的時區資訊"""
    print(f"查詢用戶的時區")
    
    try:
        # 使用 UserTimeManager
        time_manager = UserTimeManager(user_id)
        timezone = time_manager.get_timezone()
        
        timezone_info = {
            "user_id": user_id,
            "timezone": timezone
        }
        
        content = f"目前時區：{timezone}"
        
        return content, timezone_info
        
    except Exception as e:
        error_msg = f"獲取時區資訊時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}


def get_user_relative_date(user_id: str, days_offset: int) -> Tuple[str, dict]:
    """獲取指定用戶所在時區的相對日期"""
    print(f"獲取 user ID {user_id} 所在時區的相對日期：days_offset={days_offset}")
    
    try:
        # 使用 UserTimeManager
        time_manager = UserTimeManager(user_id)
        timezone = time_manager.get_timezone()
        target_date = time_manager.get_relative_date(days_offset)
        
        # 日期描述
        days_description = {
            -3: "大前天", -2: "前天", -1: "昨天", 0: "今天",
            1: "明天", 2: "後天", 3: "大後天"
        }
        days_desc = days_description.get(days_offset, f"{days_offset}天後" if days_offset > 0 else f"{abs(days_offset)}天前")
        
        # 構建回應
        date_info = {
            "user_id": user_id,
            "timezone": timezone,
            "date": target_date,
            "days_offset": days_offset,
            "description": days_desc,
            "status": "success"
        }
        
        content = f"{days_desc}的日期是：{target_date}"
        
        return content, date_info
        
    except Exception as e:
        error_msg = f"獲取相對日期時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}


def get_user_relative_weekday_date(user_id: str, weekday: int, weeks_offset: int) -> Tuple[str, dict]:
    """獲取指定用戶所在時區的相對星期幾日期"""
    print(f"獲取 user ID {user_id} 所在時區的相對星期幾日期：weekday={weekday}, weeks_offset={weeks_offset}")
    
    try:
        # 使用 UserTimeManager
        time_manager = UserTimeManager(user_id)
        timezone = time_manager.get_timezone()
        target_date = time_manager.get_weekday_date(weekday, weeks_offset)
        
        # 星期名稱對照
        weekday_names = {
            1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
            5: "Friday", 6: "Saturday", 7: "Sunday"
        }
        weekday_name = weekday_names.get(weekday, str(weekday))
        
        # 週數描述
        weeks_description = {
            -2: "上上週", -1: "上週", 0: "本週", 1: "下週", 2: "下下週"
        }
        weeks_desc = weeks_description.get(weeks_offset, f"{weeks_offset}週")
        
        # 構建回應
        date_info = {
            "user_id": user_id,
            "timezone": timezone,
            "date": target_date,
            "weekday": weekday_name,
            "weeks_offset": weeks_offset,
            "description": f"{weeks_desc}{weekday_name}",
            "status": "success"
        }
        
        content = f"{weeks_desc}{weekday_name}的日期是：{target_date}"
        
        return content, date_info
        
    except Exception as e:
        error_msg = f"獲取相對星期幾日期時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}


def create_get_weekday_tool(timezone) -> StructuredTool:
    """創建獲取今天是禮拜幾工具"""
    
    def get_weekday_wrapper() -> Tuple[str, dict]:
        """獲取今天是禮拜幾的包裝函數"""
        return get_weekday(timezone)
    
    get_weekday_tool = StructuredTool.from_function(
        func=get_weekday_wrapper,
        name="get_weekday",
        description=f"獲取 {timezone} 時區的今天是禮拜幾",
        return_direct=False
    )
    
    return get_weekday_tool

def create_get_current_time_tool(timezone: str) -> StructuredTool:
    """創建獲取目前時間工具"""
    
    def get_current_time_wrapper() -> Tuple[str, dict]:
        """獲取目前時間的包裝函數"""
        return get_current_time_with_timezone(timezone)
    
    get_current_time_tool = StructuredTool.from_function(
        func=get_current_time_wrapper,
        name="get_current_time",
        description=f"獲取所在時區的目前時間，使用這個工具前需要先查詢目前的時區; timezone 參數是時區名稱，例如：Asia/Taipei。",
        return_direct=False
    )
    
    return get_current_time_tool

get_taiwan_time_tool = StructuredTool.from_function(
    func=get_taiwan_time,
    name="get_taiwan_time",
    description="獲取台灣目前時間",
    return_direct=False
)

get_city_time_tool = StructuredTool.from_function(
    func=get_city_time,
    name="get_city_time",
    description="獲取指定城市的目前時間，支援台灣、日本和美國主要城市，預設查詢台北時間",
    return_direct=False
)

def create_get_user_weekday_tool(user_id: str) -> StructuredTool:
    """創建獲取用戶今天是禮拜幾工具"""
    
    def get_user_weekday_wrapper() -> Tuple[str, dict]:
        """獲取用戶今天是禮拜幾的包裝函數"""
        return get_user_weekday(user_id)
    
    get_user_weekday_tool = StructuredTool.from_function(
        func=get_user_weekday_wrapper,
        name="get_user_weekday",
        description="獲取用戶所在時區的今天是禮拜幾。此工具會自動查詢用戶的時區設定，然後返回該時區今天是星期幾。",
        return_direct=False
    )
    
    return get_user_weekday_tool


def create_get_user_current_time_tool(user_id: str) -> StructuredTool:
    """創建獲取用戶目前時間工具"""
    
    def get_user_current_time_wrapper() -> Tuple[str, dict]:
        """獲取用戶目前時間的包裝函數"""
        return get_user_current_time(user_id)
    
    get_user_current_time_tool = StructuredTool.from_function(
        func=get_user_current_time_wrapper,
        name="get_user_current_time",
        description="獲取用戶所在時區的目前時間。此工具會自動查詢用戶的時區設定，然後返回該時區的當前時間。",
        return_direct=False
    )
    
    return get_user_current_time_tool


def create_get_current_timezone_tool(user_id: str) -> StructuredTool:
    """創建獲取時區工具"""
    
    def get_current_timezone_wrapper() -> Tuple[str, dict]:
        """獲取目前時區資訊的包裝函數"""
        return get_current_timezone(user_id)
    
    get_current_timezone_tool = StructuredTool.from_function(
        func=get_current_timezone_wrapper,
        name="get_current_timezone",
        description="獲取所在地的時區資訊。",
        return_direct=False
    )
    
    return get_current_timezone_tool


def create_get_relative_date_tool(user_id: str) -> StructuredTool:
    """創建獲取相對日期工具"""
    
    def get_relative_date_wrapper(days_offset: int) -> Tuple[str, dict]:
        """
        獲取相對日期的包裝函數
        
        Args:
            days_offset: 天數偏移 (-3=大前天, -2=前天, -1=昨天, 0=今天, 1=明天, 2=後天, 3=大後天)
        """
        return get_user_relative_date(user_id, days_offset)
    
    get_relative_date_tool = StructuredTool.from_function(
        func=get_relative_date_wrapper,
        name="get_relative_date",
        description="""
            獲取相對日期。需要提供一個參數：
            - days_offset: 天數偏移
              -3 = 大前天
              -2 = 前天
              -1 = 昨天
              0 = 今天
              1 = 明天
              2 = 後天
              3 = 大後天
            
            也可以使用其他數字，例如 7 表示 7 天後，-7 表示 7 天前。
            
            此工具會自動使用用戶所在時區計算指定的日期（YYYY-MM-DD格式）。
        """,
        return_direct=False
    )
    
    return get_relative_date_tool


def create_get_relative_weekday_date_tool(user_id: str) -> StructuredTool:
    """創建獲取相對星期幾日期工具"""
    
    def get_relative_weekday_date_wrapper(weekday: int, weeks_offset: int = 0) -> Tuple[str, dict]:
        """
        獲取相對星期幾日期的包裝函數
        
        Args:
            weekday: 星期幾 (1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday, 7=Sunday)
            weeks_offset: 周數偏移 (-2=上上週, -1=上週, 0=本週, 1=下週, 2=下下週)
        """
        return get_user_relative_weekday_date(user_id, weekday, weeks_offset)
    
    get_relative_weekday_date_tool = StructuredTool.from_function(
        func=get_relative_weekday_date_wrapper,
        name="get_relative_weekday_date",
        description="""
            獲取相對星期幾的日期。需要提供兩個參數：
            - weekday: 星期幾，1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday, 7=Sunday
            - weeks_offset: 周數偏移，-2=上上週, -1=上週, 0=本週, 1=下週, 2=下下週
            
            例如：
            - 下週三：weekday=3, weeks_offset=1
            - 上週五：weekday=5, weeks_offset=-1
            - 下下週一：weekday=1, weeks_offset=2
            
            此工具會自動使用用戶所在時區計算指定的日期（YYYY-MM-DD格式）。
        """,
        return_direct=False
    )
    
    return get_relative_weekday_date_tool
