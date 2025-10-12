from typing import Tuple
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.lib.supabase import supabase_admin
from .user_utils import get_user_timezone as get_user_timezone_with_info


def get_weekday(timezone: str) -> str:
    """獲取指定時區的今天是星期幾"""

    try:
        # 1. 設定指定時區
        target_tz = ZoneInfo(timezone)
        
        # 2. 取得指定時區的當前時間
        target_time = datetime.now(target_tz)
        
        # 3. 獲取星期幾（數字 1=星期一, 7=星期日，符合 ISO 標準）
        iso_weekday_num = target_time.isoweekday()
        
        # 4. 轉換為英文星期名稱
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


def get_relative_date(timezone: str, days_offset: int = 0) -> str:
    """
    獲取指定時區的相對日期
    
    Args:
        timezone: 時區
        days_offset: 天數偏移 (-3=大前天, -2=前天, -1=昨天, 0=今天, 1=明天, 2=後天, 3=大後天)
    
    Returns:
        str: 日期字符串 (YYYY-MM-DD)
    
    Examples:
        get_relative_date("Asia/Taipei", 1)   # 明天
        get_relative_date("Asia/Taipei", 2)   # 後天
        get_relative_date("Asia/Taipei", -1)  # 昨天
        get_relative_date("Asia/Taipei", -2)  # 前天
    """
    try:
        # 設定指定時區
        target_tz = ZoneInfo(timezone)
        
        # 取得指定時區的當前日期
        current_time = datetime.now(target_tz)
        
        # 計算目標日期
        target_date = current_time + timedelta(days=days_offset)
        
        # 格式化為日期字串
        date_str = target_date.strftime("%Y-%m-%d")
        
        return date_str
        
    except Exception as e:
        error_msg = f"獲取相對日期時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg


def get_user_relative_date(user_id: str, days_offset: int = 0) -> str:
    """
    獲取指定用戶時區的相對日期
    
    Args:
        user_id: 用戶 ID
        days_offset: 天數偏移 (-3=大前天, -2=前天, -1=昨天, 0=今天, 1=明天, 2=後天, 3=大後天)
    
    Returns:
        str: 日期字符串 (YYYY-MM-DD)
    
    Examples:
        get_user_relative_date(user_id, 1)   # 明天
        get_user_relative_date(user_id, 2)   # 後天
        get_user_relative_date(user_id, -1)  # 昨天
    """
    try:
        # 獲取用戶時區
        user_timezone = get_user_timezone(user_id)
        
        # 檢查是否有錯誤
        if "錯誤" in user_timezone or "找不到" in user_timezone:
            return user_timezone
        
        # 調用 get_relative_date 函數
        return get_relative_date(user_timezone, days_offset)
        
    except Exception as e:
        error_msg = f"獲取用戶相對日期時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg


def get_weekday_date(timezone: str, weekday: int, weeks_offset: int = 0) -> str:
    """
    獲取指定時區的相對星期幾日期
    
    Args:
        timezone: 時區
        weekday: 星期幾 (1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday, 7=Sunday)
        weeks_offset: 周數偏移 (-2=上上週, -1=上週, 0=本週, 1=下週, 2=下下週)
    
    Returns:
        str: 日期字符串 (YYYY-MM-DD)
    
    Examples:
        get_weekday_date("Asia/Taipei", 3, 1)  # 下週三
        get_weekday_date("Asia/Taipei", 4, -1)  # 上週四
        get_weekday_date("Asia/Taipei", 1, 2)  # 下下週一
    """
    try:
        # 驗證 weekday 參數
        if not 1 <= weekday <= 7:
            error_msg = f"weekday 必須在 1-7 之間 (1=Monday, 7=Sunday)，當前值：{weekday}"
            print(error_msg)
            return error_msg
        
        # 設定指定時區
        target_tz = ZoneInfo(timezone)
        
        # 取得指定時區的當前日期
        current_time = datetime.now(target_tz)
        current_weekday = current_time.isoweekday()  # 1=Monday, 7=Sunday
        
        # 計算到目標星期幾的天數差異
        days_until_target = weekday - current_weekday
        
        # 如果目標星期幾已經過去（在本週），則跳到下週
        if weeks_offset == 0 and days_until_target < 0:
            days_until_target += 7
        
        # 加上週數偏移
        total_days_offset = days_until_target + (weeks_offset * 7)
        
        # 計算目標日期
        target_date = current_time + timedelta(days=total_days_offset)
        
        # 格式化為日期字串
        date_str = target_date.strftime("%Y-%m-%d")
        
        return date_str
        
    except Exception as e:
        error_msg = f"獲取星期幾日期時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg


def get_user_weekday_date(user_id: str, weekday: int, weeks_offset: int = 0) -> str:
    """
    獲取指定用戶時區的相對星期幾日期
    
    Args:
        user_id: 用戶 ID
        weekday: 星期幾 (1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday, 7=Sunday)
        weeks_offset: 周數偏移 (-2=上上週, -1=上週, 0=本週, 1=下週, 2=下下週)
    
    Returns:
        str: 日期字符串 (YYYY-MM-DD)
    
    Examples:
        get_user_weekday_date(user_id, 3, 1)   # 下週三
        get_user_weekday_date(user_id, 4, -1)  # 上週四
        get_user_weekday_date(user_id, 1, 2)   # 下下週一
    """
    try:
        # 獲取用戶時區
        user_timezone = get_user_timezone(user_id)
        
        # 檢查是否有錯誤
        if "錯誤" in user_timezone or "找不到" in user_timezone:
            return user_timezone
        
        # 調用 get_weekday_date 函數
        return get_weekday_date(user_timezone, weekday, weeks_offset)
        
    except Exception as e:
        error_msg = f"獲取用戶星期幾日期時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg


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
        timezone_content, timezone_info = get_user_timezone_with_info(user_id)
        
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
        timezone_content, timezone_info = get_user_timezone_with_info(user_id)
        
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
        timezone_content, timezone_info = get_user_timezone_with_info(user_id)
        
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
        timezone_content, timezone_info = get_user_timezone_with_info(user_id)
        
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
