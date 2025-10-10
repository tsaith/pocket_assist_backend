from typing import Tuple
from datetime import datetime
from zoneinfo import ZoneInfo
from langchain_core.tools import StructuredTool
from app.lib.chatbot.utils import (
    get_city_local_time
)
from app.lib.supabase import supabase_admin
from app.lib.utils import get_user_timezone


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
        # 先獲取用戶的時區設定
        timezone_content, timezone_info = get_user_timezone(user_id)
        
        # 檢查是否成功獲取時區
        if "error" in timezone_info:
            return timezone_content, timezone_info
        
        # 獲取用戶的時區
        user_timezone = timezone_info.get("timezone", "Asia/Taipei")
        
        # 獲取該時區的今天是禮拜幾
        weekday_content, weekday_info = get_weekday(user_timezone)
        
        # 構建回應
        combined_info = {
            "user_id": user_id,
            "timezone": user_timezone,
            "weekday": weekday_info.get("weekday", ""),
            "date": weekday_info.get("date", ""),
            "status": "success"
        }
        
        content = f"您所在時區 ({user_timezone}) 今天是：{weekday_info.get('weekday', '')}"
        
        return content, combined_info
        
    except Exception as e:
        error_msg = f"獲取用戶時區星期幾時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}


def get_user_current_time(user_id: str) -> Tuple[str, dict]:
    """獲取指定用戶所在時區的目前時間"""
    print(f"獲取 user ID {user_id} 所在時區的目前時間")
    
    try:
        # 先獲取用戶的時區設定
        timezone_content, timezone_info = get_user_timezone(user_id)
        
        # 檢查是否成功獲取時區
        if "error" in timezone_info:
            return timezone_content, timezone_info
        
        # 獲取用戶的時區
        user_timezone = timezone_info.get("timezone", "Asia/Taipei")
        
        # 獲取該時區的當前時間
        current_time_content, current_time_info = get_current_time_with_timezone(user_timezone)
        
        # 構建回應
        combined_info = {
            "user_id": user_id,
            "timezone": user_timezone,
            "current_time": current_time_info.get("current_time", ""),
            "status": "success"
        }
        
        content = f"您目前所在時區 ({user_timezone}) 的時間是：{current_time_info.get('current_time', '')}"
        
        return content, combined_info
        
    except Exception as e:
        error_msg = f"獲取用戶時區時間時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}


def get_current_timezone(user_id: str) -> Tuple[str, dict]:
    """獲取指定用戶的時區資訊"""
    print(f"查詢用戶的時區")
    
    try:
        # 從 profiles 表取得 timezone
        profile_response = supabase_admin.from_("profiles").select("timezone").eq("id", user_id).execute()
        
        if not profile_response.data:
            error_msg = f"找不到 user ID {user_id} 的 profile 記錄"
            print(error_msg)
            return error_msg, {"error": "Profile not found"}
        
        timezone = profile_response.data[0].get("timezone", "Asia/Taipei")
        
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
