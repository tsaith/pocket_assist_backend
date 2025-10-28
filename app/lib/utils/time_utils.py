from typing import Tuple
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.lib.supabase import supabase_admin


def get_weekday(timezone: str) -> str:
    """Get today's weekday in the specified timezone"""

    try:
        # 1. Set specified timezone
        target_tz = ZoneInfo(timezone)
        
        # 2. Get current time in specified timezone
        target_time = datetime.now(target_tz)
        
        # 3. Get weekday (number 1=Monday, 7=Sunday, following ISO standard)
        iso_weekday_num = target_time.isoweekday()
        
        # 4. Convert to English weekday name
        weekday_names = ["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday = weekday_names[iso_weekday_num]
        
        return weekday
        
    except Exception as e:
        error_msg = f"Error occurred while getting weekday for {timezone} timezone: {str(e)}"
        print(error_msg)
        return error_msg


def get_date(timezone: str) -> str:
    """Get today's date in the specified timezone (ISO format: YYYY-MM-DD)"""

    try:
        # 1. Set specified timezone
        target_tz = ZoneInfo(timezone)
        
        # 2. Get current time in specified timezone
        target_time = datetime.now(target_tz)
        
        # 3. Format date to ISO format (YYYY-MM-DD)
        date_str = target_time.strftime("%Y-%m-%d")
        
        return date_str
        
    except Exception as e:
        error_msg = f"Error occurred while getting date for {timezone} timezone: {str(e)}"
        print(error_msg)
        return error_msg


def get_current_time(timezone: str) -> str:
    """Get current time in the specified timezone (format: YYYY-MM-DD HH:MM:SS)"""

    try:
        # 1. Set specified timezone
        target_tz = ZoneInfo(timezone)
        
        # 2. Get current time in specified timezone
        target_time = datetime.now(target_tz)
        
        # 3. Format as datetime string (YYYY-MM-DD HH:MM:SS)
        time_str = target_time.strftime("%Y-%m-%d %H:%M:%S")
        
        return time_str
        
    except Exception as e:
        error_msg = f"Error occurred while getting current time for {timezone} timezone: {str(e)}"
        print(error_msg)
        return error_msg


def get_user_timezone(user_id: str) -> str:
    """Get timezone information for specified user from database"""

    try:
        # Get timezone from profiles table
        profile_response = supabase_admin.from_("profiles").select("timezone").eq("id", user_id).execute()
        
        if not profile_response.data:
            error_msg = f"Cannot find profile record for user ID {user_id}"
            print(error_msg)
            return error_msg
        
        timezone = profile_response.data[0].get("timezone", "Asia/Taipei")
        
        return timezone
        
    except Exception as e:
        error_msg = f"Error occurred while getting timezone information: {str(e)}"
        print(error_msg)
        return error_msg


def get_relative_date(timezone: str, days_offset: int = 0) -> str:
    """
    Get relative date in specified timezone
    
    Args:
        timezone: Timezone
        days_offset: Days offset (-3=three days ago, -2=day before yesterday, -1=yesterday, 0=today, 1=tomorrow, 2=day after tomorrow, 3=three days later)
    
    Returns:
        str: Date string (YYYY-MM-DD)
    
    Examples:
        get_relative_date("Asia/Taipei", 1)   # tomorrow
        get_relative_date("Asia/Taipei", 2)   # day after tomorrow
        get_relative_date("Asia/Taipei", -1)  # yesterday
        get_relative_date("Asia/Taipei", -2)  # day before yesterday
    """
    try:
        # Set specified timezone
        target_tz = ZoneInfo(timezone)
        
        # Get current date in specified timezone
        current_time = datetime.now(target_tz)
        
        # Calculate target date
        target_date = current_time + timedelta(days=days_offset)
        
        # Format as date string
        date_str = target_date.strftime("%Y-%m-%d")
        
        return date_str
        
    except Exception as e:
        error_msg = f"Error occurred while getting relative date: {str(e)}"
        print(error_msg)
        return error_msg


def get_user_relative_date(user_id: str, days_offset: int = 0) -> str:
    """
    Get relative date in specified user's timezone
    
    Args:
        user_id: User ID
        days_offset: Days offset (-3=three days ago, -2=day before yesterday, -1=yesterday, 0=today, 1=tomorrow, 2=day after tomorrow, 3=three days later)
    
    Returns:
        str: Date string (YYYY-MM-DD)
    
    Examples:
        get_user_relative_date(user_id, 1)   # tomorrow
        get_user_relative_date(user_id, 2)   # day after tomorrow
        get_user_relative_date(user_id, -1)  # yesterday
    """
    try:
        # Get user timezone
        user_timezone = get_user_timezone(user_id)
        
        # Check for errors
        if "Error" in user_timezone or "Cannot find" in user_timezone:
            return user_timezone
        
        # Call get_relative_date function
        return get_relative_date(user_timezone, days_offset)
        
    except Exception as e:
        error_msg = f"Error occurred while getting user relative date: {str(e)}"
        print(error_msg)
        return error_msg


def get_weekday_date(timezone: str, weekday: int, weeks_offset: int = 0) -> str:
    """
    Get relative weekday date in specified timezone
    
    Args:
        timezone: Timezone
        weekday: Weekday (1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday, 7=Sunday)
        weeks_offset: Weeks offset (-2=two weeks ago, -1=last week, 0=this week, 1=next week, 2=two weeks later)
    
    Returns:
        str: Date string (YYYY-MM-DD)
    
    Examples:
        get_weekday_date("Asia/Taipei", 3, 1)  # next Wednesday
        get_weekday_date("Asia/Taipei", 4, -1)  # last Thursday
        get_weekday_date("Asia/Taipei", 1, 2)  # Monday two weeks later
    """
    try:
        # Validate weekday parameter
        if not 1 <= weekday <= 7:
            error_msg = f"weekday must be between 1-7 (1=Monday, 7=Sunday), current value: {weekday}"
            print(error_msg)
            return error_msg
        
        # Set specified timezone
        target_tz = ZoneInfo(timezone)
        
        # Get current date in specified timezone
        current_time = datetime.now(target_tz)
        current_weekday = current_time.isoweekday()  # 1=Monday, 7=Sunday
        
        # Calculate days difference to target weekday
        days_until_target = weekday - current_weekday
        
        # If target weekday has passed (in this week), jump to next week
        if weeks_offset == 0 and days_until_target < 0:
            days_until_target += 7
        
        # Add weeks offset
        total_days_offset = days_until_target + (weeks_offset * 7)
        
        # Calculate target date
        target_date = current_time + timedelta(days=total_days_offset)
        
        # Format as date string
        date_str = target_date.strftime("%Y-%m-%d")
        
        return date_str
        
    except Exception as e:
        error_msg = f"Error occurred while getting weekday date: {str(e)}"
        print(error_msg)
        return error_msg


def get_user_weekday_date(user_id: str, weekday: int, weeks_offset: int = 0) -> str:
    """
    Get relative weekday date in specified user's timezone
    
    Args:
        user_id: User ID
        weekday: Weekday (1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday, 7=Sunday)
        weeks_offset: Weeks offset (-2=two weeks ago, -1=last week, 0=this week, 1=next week, 2=two weeks later)
    
    Returns:
        str: Date string (YYYY-MM-DD)
    
    Examples:
        get_user_weekday_date(user_id, 3, 1)   # next Wednesday
        get_user_weekday_date(user_id, 4, -1)  # last Thursday
        get_user_weekday_date(user_id, 1, 2)   # Monday two weeks later
    """
    try:
        # Get user timezone
        user_timezone = get_user_timezone(user_id)
        
        # Check for errors
        if "Error" in user_timezone or "Cannot find" in user_timezone:
            return user_timezone
        
        # Call get_weekday_date function
        return get_weekday_date(user_timezone, weekday, weeks_offset)
        
    except Exception as e:
        error_msg = f"Error occurred while getting user weekday date: {str(e)}"
        print(error_msg)
        return error_msg


def convert_utc_to_local_time(time_utc: str, timezone: str) -> str:
    """Convert UTC time to local time in specified timezone (ISO 8601/RFC 3339 format)"""
    try:
        # Parse UTC time
        utc_dt = datetime.fromisoformat(time_utc.replace('Z', '+00:00'))
        
        # If time has no timezone info, set as UTC
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=ZoneInfo('UTC'))
        
        # Convert to specified timezone
        local_tz = ZoneInfo(timezone)
        local_dt = utc_dt.astimezone(local_tz)
        
        # Return local time string (ISO 8601/RFC 3339 format, including timezone info)
        return local_dt.isoformat()
        
    except Exception as e:
        print(f"Error occurred while converting UTC time to local time: {str(e)}")
        return time_utc


def convert_local_to_utc_time(time_local: str, timezone: str) -> str:
    """Convert local timezone time to UTC time (ISO 8601/RFC 3339 format)"""
    try:
        # Parse local time
        local_dt = datetime.fromisoformat(time_local)
        
        # Set local timezone
        local_tz = ZoneInfo(timezone)
        local_dt = local_dt.replace(tzinfo=local_tz)
        
        # Convert to UTC
        utc_dt = local_dt.astimezone(ZoneInfo('UTC'))
        
        # Return UTC time string (ISO 8601/RFC 3339 format, ending with Z to indicate UTC)
        return utc_dt.isoformat().replace('+00:00', 'Z')
        
    except Exception as e:
        print(f"Error occurred while converting local time to UTC time: {str(e)}")
        return time_local


def convert_user_local_to_utc_time(user_id: str, time_local: str) -> Tuple[str, dict]:
    """Convert user local time to UTC time (ISO 8601/RFC 3339 format)"""
    try:
        # Get user timezone
        user_timezone = get_user_timezone(user_id)
        
        # Check for errors
        if "Error" in user_timezone or "Cannot find" in user_timezone:
            return time_local, {"error": user_timezone}
        
        # Convert time
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
        error_msg = f"Error occurred while converting user local time to UTC time: {str(e)}"
        print(error_msg)
        return time_local, {"error": str(e)}


def convert_utc_to_user_local_time(user_id: str, time_utc: str) -> Tuple[str, dict]:
    """Convert UTC time to user's local time in their timezone (ISO 8601/RFC 3339 format)"""
    try:
        # Get user timezone
        user_timezone = get_user_timezone(user_id)
        
        # Check for errors
        if "Error" in user_timezone or "Cannot find" in user_timezone:
            return time_utc, {"error": user_timezone}
        
        # Convert time
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
        error_msg = f"Error occurred while converting UTC time to user local time: {str(e)}"
        print(error_msg)
        return time_utc, {"error": str(e)}


def convert_local_to_utc_date(date_local: str, timezone: str) -> str:
    """Convert local timezone date to UTC date"""
    try:
        # Parse local date (assuming midnight time)
        local_dt = datetime.strptime(date_local, '%Y-%m-%d')
        
        # Set local timezone
        local_tz = ZoneInfo(timezone)
        local_dt = local_dt.replace(tzinfo=local_tz)
        
        # Convert to UTC
        utc_dt = local_dt.astimezone(ZoneInfo('UTC'))
        
        # Return UTC date string
        return utc_dt.strftime('%Y-%m-%d')
        
    except Exception as e:
        print(f"Error occurred while converting local date to UTC date: {str(e)}")
        return date_local


def convert_utc_to_local_date(date_utc: str, timezone: str) -> str:
    """Convert UTC date to local date in specified timezone"""
    try:
        # Parse UTC date (assuming midnight time)
        utc_dt = datetime.strptime(date_utc, '%Y-%m-%d')
        
        # Set as UTC timezone
        utc_dt = utc_dt.replace(tzinfo=ZoneInfo('UTC'))
        
        # Convert to specified timezone
        local_tz = ZoneInfo(timezone)
        local_dt = utc_dt.astimezone(local_tz)
        
        # Return local date string
        return local_dt.strftime('%Y-%m-%d')
        
    except Exception as e:
        print(f"Error occurred while converting UTC date to local date: {str(e)}")
        return date_utc


def convert_user_local_to_utc_date(user_id: str, date_local: str) -> Tuple[str, dict]:
    """Convert user local date to UTC date"""
    try:
        # Get user timezone
        user_timezone = get_user_timezone(user_id)
        
        # Check for errors
        if "Error" in user_timezone or "Cannot find" in user_timezone:
            return date_local, {"error": user_timezone}
        
        # Convert date
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
        error_msg = f"Error occurred while converting user local date to UTC date: {str(e)}"
        print(error_msg)
        return date_local, {"error": str(e)}


def convert_utc_to_user_local_date(user_id: str, date_utc: str) -> Tuple[str, dict]:
    """Convert UTC date to user's local date in their timezone"""
    try:
        # Get user timezone
        user_timezone = get_user_timezone(user_id)
        
        # Check for errors
        if "Error" in user_timezone or "Cannot find" in user_timezone:
            return date_utc, {"error": user_timezone}
        
        # Convert date
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
        error_msg = f"Error occurred while converting UTC date to user local date: {str(e)}"
        print(error_msg)
        return date_utc, {"error": str(e)}
