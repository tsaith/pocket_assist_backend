from typing import Tuple
from datetime import datetime
from zoneinfo import ZoneInfo
from .user_utils import get_user_timezone
from ..chatbot.tools.time_tools import (
    get_user_current_time,
    create_get_user_current_time_tool,
    get_user_weekday,
    create_get_user_weekday_tool
)


def convert_utc_to_local_time(time_utc: str, timezone: str) -> str:
    """將 UTC 時間轉換為指定時區的本地時間"""
    try:
        # 解析 UTC 時間
        utc_dt = datetime.fromisoformat(time_utc.replace('Z', '+00:00'))
        
        # 如果時間沒有時區信息，設置為 UTC
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=ZoneInfo('UTC'))
        
        # 轉換到指定時區
        local_tz = ZoneInfo(timezone)
        local_dt = utc_dt.astimezone(local_tz)
        
        # 返回本地時間字符串（不包含時區信息）
        return local_dt.strftime('%Y-%m-%d %H:%M:%S')
        
    except Exception as e:
        print(f"轉換 UTC 時間到本地時間時發生錯誤：{str(e)}")
        return time_utc


def convert_local_to_utc_time(time_local: str, timezone: str) -> str:
    """將本地時區時間轉換為 UTC 時間"""
    try:
        # 解析本地時間
        local_dt = datetime.fromisoformat(time_local)
        
        # 設置本地時區
        local_tz = ZoneInfo(timezone)
        local_dt = local_dt.replace(tzinfo=local_tz)
        
        # 轉換到 UTC
        utc_dt = local_dt.astimezone(ZoneInfo('UTC'))
        
        # 返回 UTC 時間字符串
        return utc_dt.strftime('%Y-%m-%d %H:%M:%S')
        
    except Exception as e:
        print(f"轉換本地時間到 UTC 時間時發生錯誤：{str(e)}")
        return time_local


def convert_user_local_to_utc_time(user_id: str, time_local: str) -> Tuple[str, dict]:
    """將用戶本地時間轉換為 UTC 時間"""
    try:
        # 獲取用戶時區
        timezone_content, timezone_info = get_user_timezone(user_id)
        
        # 檢查是否成功獲取時區
        if "error" in timezone_info:
            return time_local, timezone_info
        
        # 獲取用戶的時區
        user_timezone = timezone_info.get("timezone", "Asia/Taipei")
        
        # 轉換時間
        utc_time = convert_local_to_utc_time(time_local, user_timezone)
        
        result_info = {
            "user_id": user_id,
            "timezone": user_timezone,
            "local_time": time_local,
            "utc_time": utc_time,
            "status": "success"
        }
        
        return utc_time, result_info
        
    except Exception as e:
        error_msg = f"轉換用戶本地時間到 UTC 時間時發生錯誤：{str(e)}"
        print(error_msg)
        return time_local, {"error": str(e)}


def convert_utc_to_user_local_time(user_id: str, time_utc: str) -> Tuple[str, dict]:
    """將 UTC 時間轉換為用戶所在時區的本地時間"""
    try:
        # 獲取用戶時區
        timezone_content, timezone_info = get_user_timezone(user_id)
        
        # 檢查是否成功獲取時區
        if "error" in timezone_info:
            return time_utc, timezone_info
        
        # 獲取用戶的時區
        user_timezone = timezone_info.get("timezone", "Asia/Taipei")
        
        # 轉換時間
        local_time = convert_utc_to_local_time(time_utc, user_timezone)
        
        result_info = {
            "user_id": user_id,
            "timezone": user_timezone,
            "utc_time": time_utc,
            "local_time": local_time,
            "status": "success"
        }
        
        return local_time, result_info
        
    except Exception as e:
        error_msg = f"轉換 UTC 時間到用戶本地時間時發生錯誤：{str(e)}"
        print(error_msg)
        return time_utc, {"error": str(e)}


def convert_local_to_utc_date(date_local: str, timezone: str) -> str:
    """將本地時區日期轉換為 UTC 日期"""
    try:
        # 解析本地日期（假設是午夜時間）
        local_dt = datetime.strptime(date_local, '%Y-%m-%d')
        
        # 設置本地時區
        local_tz = ZoneInfo(timezone)
        local_dt = local_dt.replace(tzinfo=local_tz)
        
        # 轉換到 UTC
        utc_dt = local_dt.astimezone(ZoneInfo('UTC'))
        
        # 返回 UTC 日期字符串
        return utc_dt.strftime('%Y-%m-%d')
        
    except Exception as e:
        print(f"轉換本地日期到 UTC 日期時發生錯誤：{str(e)}")
        return date_local


def convert_utc_to_local_date(date_utc: str, timezone: str) -> str:
    """將 UTC 日期轉換為指定時區的本地日期"""
    try:
        # 解析 UTC 日期（假設是午夜時間）
        utc_dt = datetime.strptime(date_utc, '%Y-%m-%d')
        
        # 設置為 UTC 時區
        utc_dt = utc_dt.replace(tzinfo=ZoneInfo('UTC'))
        
        # 轉換到指定時區
        local_tz = ZoneInfo(timezone)
        local_dt = utc_dt.astimezone(local_tz)
        
        # 返回本地日期字符串
        return local_dt.strftime('%Y-%m-%d')
        
    except Exception as e:
        print(f"轉換 UTC 日期到本地日期時發生錯誤：{str(e)}")
        return date_utc


def convert_user_local_to_utc_date(user_id: str, date_local: str) -> Tuple[str, dict]:
    """將用戶本地日期轉換為 UTC 日期"""
    try:
        # 獲取用戶時區
        timezone_content, timezone_info = get_user_timezone(user_id)
        
        # 檢查是否成功獲取時區
        if "error" in timezone_info:
            return date_local, timezone_info
        
        # 獲取用戶的時區
        user_timezone = timezone_info.get("timezone", "Asia/Taipei")
        
        # 轉換日期
        utc_date = convert_local_to_utc_date(date_local, user_timezone)
        
        result_info = {
            "user_id": user_id,
            "timezone": user_timezone,
            "local_date": date_local,
            "utc_date": utc_date,
            "status": "success"
        }
        
        return utc_date, result_info
        
    except Exception as e:
        error_msg = f"轉換用戶本地日期到 UTC 日期時發生錯誤：{str(e)}"
        print(error_msg)
        return date_local, {"error": str(e)}


def convert_utc_to_user_local_date(user_id: str, date_utc: str) -> Tuple[str, dict]:
    """將 UTC 日期轉換為用戶所在時區的本地日期"""
    try:
        # 獲取用戶時區
        timezone_content, timezone_info = get_user_timezone(user_id)
        
        # 檢查是否成功獲取時區
        if "error" in timezone_info:
            return date_utc, timezone_info
        
        # 獲取用戶的時區
        user_timezone = timezone_info.get("timezone", "Asia/Taipei")
        
        # 轉換日期
        local_date = convert_utc_to_local_date(date_utc, user_timezone)
        
        result_info = {
            "user_id": user_id,
            "timezone": user_timezone,
            "utc_date": date_utc,
            "local_date": local_date,
            "status": "success"
        }
        
        return local_date, result_info
        
    except Exception as e:
        error_msg = f"轉換 UTC 日期到用戶本地日期時發生錯誤：{str(e)}"
        print(error_msg)
        return date_utc, {"error": str(e)}
