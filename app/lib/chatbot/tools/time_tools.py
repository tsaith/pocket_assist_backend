from typing import Tuple
from datetime import datetime
from zoneinfo import ZoneInfo
from langchain_core.tools import StructuredTool
from app.lib.chatbot.utils import (
    get_city_local_time
)
from app.lib.supabase import supabase_admin
from app.lib.user_time_manager import UserTimeManager
from app.lib.utils.time_utils import get_user_timezone


def get_weekday(timezone: str = "Asia/Taipei") -> Tuple[str, dict]:
    """Get what day of the week it is today in the specified timezone"""

    print(f"Getting what day of the week it is today in {timezone} timezone")
    
    try:
        # 1. Set specified timezone
        target_tz = ZoneInfo(timezone)
        
        # 2. Get current time in specified timezone
        target_time = datetime.now(target_tz)
        
        # 3. Get weekday number (1=Monday, 7=Sunday, following ISO standard)
        iso_weekday_num = target_time.isoweekday()
        
        # 4. Convert to English weekday names
        weekday_names = ["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday = weekday_names[iso_weekday_num]
        
        # 5. Build detailed information
        weekday_info = {
            "timezone": timezone,
            "weekday": weekday,
            "date": target_time.strftime("%Y-%m-%d")
        }
        
        # 6. Generate content string
        content = f"Today in {timezone} timezone is: {weekday}"
        
        return content, weekday_info
        
    except Exception as e:
        error_msg = f"Error occurred while getting weekday for {timezone} timezone: {str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}


def get_current_time_with_timezone(timezone: str) -> Tuple[str, dict]:
    """Get current time in specified timezone"""
    print(f"Querying current time in {timezone} timezone")
    
    try:
        # Use get_current_time function from utils.py to get time in specified timezone
        from app.lib.chatbot.utils import get_current_time
        current_time = get_current_time(timezone)
        
        time_info = {
            "timezone": timezone,
            "current_time": current_time
        }
        
        content = f"Current time in {timezone} timezone: {current_time}"
        
        return content, time_info
        
    except Exception as e:
        error_msg = f"Error occurred while getting time for {timezone} timezone: {str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}

def get_taiwan_time() -> Tuple[str, str]:
    """Get current time in Taiwan"""
    print("Getting current time in Taiwan")
    return get_city_local_time("Taipei")


def get_city_time(city: str = "Taipei") -> Tuple[str, dict]:
    """Get current time in specified city"""

    print(f"Getting current time in {city}")

    city = city.lower()
    
    try:
        # Get city time
        current_time = get_city_local_time(city)
        
        time_info = {
            "city": city,
            "current_time": current_time,
            "timezone": "local"
        }
        
        content = f"Current time in {city}: {current_time}"
        
        return content, time_info
        
    except Exception as e:
        error_msg = f"Error occurred while querying {city} time: {str(e)}"
        return error_msg, {"error": str(e)}


def get_user_weekday(user_id: str) -> Tuple[str, dict]:
    """Get what day of the week it is today in the specified user's timezone"""
    print(f"Getting what day of the week it is today in user ID {user_id}'s timezone")
    
    try:
        # Use UserTimeManager
        time_manager = UserTimeManager(user_id)
        timezone = time_manager.get_timezone()
        weekday = time_manager.get_weekday()
        date = time_manager.get_date()
        
        # Build response
        combined_info = {
            "user_id": user_id,
            "timezone": timezone,
            "weekday": weekday,
            "date": date,
            "status": "success"
        }
        
        content = f"Today in your timezone ({timezone}) is: {weekday}"
        
        return content, combined_info
        
    except Exception as e:
        error_msg = f"Error occurred while getting user timezone weekday: {str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}


def get_user_current_time(user_id: str) -> Tuple[str, dict]:
    """Get current time in the specified user's timezone"""
    print(f"Getting current time in user ID {user_id}'s timezone")
    
    try:
        # Use UserTimeManager
        time_manager = UserTimeManager(user_id)
        timezone = time_manager.get_timezone()
        current_time = time_manager.get_current_time()
        
        # Build response
        combined_info = {
            "user_id": user_id,
            "timezone": timezone,
            "current_time": current_time,
            "status": "success"
        }
        
        content = f"Current time in your timezone ({timezone}) is: {current_time}"
        
        return content, combined_info
        
    except Exception as e:
        error_msg = f"Error occurred while getting user timezone time: {str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}


def get_current_timezone(user_id: str) -> Tuple[str, dict]:
    """Get timezone information for the specified user"""
    print(f"Querying user's timezone")
    
    try:
        # Use UserTimeManager
        time_manager = UserTimeManager(user_id)
        timezone = time_manager.get_timezone()
        
        timezone_info = {
            "user_id": user_id,
            "timezone": timezone
        }
        
        content = f"Current timezone: {timezone}"
        
        return content, timezone_info
        
    except Exception as e:
        error_msg = f"Error occurred while getting timezone information: {str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}


def get_user_relative_date(user_id: str, days_offset: int) -> Tuple[str, dict]:
    """Get relative date in the specified user's timezone"""
    print(f"Getting relative date in user ID {user_id}'s timezone: days_offset={days_offset}")
    
    try:
        # Use UserTimeManager
        time_manager = UserTimeManager(user_id)
        timezone = time_manager.get_timezone()
        target_date = time_manager.get_relative_date(days_offset)
        
        # Date descriptions
        days_description = {
            -3: "three days ago", -2: "day before yesterday", -1: "yesterday", 0: "today",
            1: "tomorrow", 2: "day after tomorrow", 3: "three days from now"
        }
        days_desc = days_description.get(days_offset, f"{days_offset} days from now" if days_offset > 0 else f"{abs(days_offset)} days ago")
        
        # Build response
        date_info = {
            "user_id": user_id,
            "timezone": timezone,
            "date": target_date,
            "days_offset": days_offset,
            "description": days_desc,
            "status": "success"
        }
        
        content = f"Date for {days_desc}: {target_date}"
        
        return content, date_info
        
    except Exception as e:
        error_msg = f"Error occurred while getting relative date: {str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}


def get_user_relative_weekday_date(user_id: str, weekday: int, weeks_offset: int) -> Tuple[str, dict]:
    """Get relative weekday date in the specified user's timezone"""
    print(f"Getting relative weekday date in user ID {user_id}'s timezone: weekday={weekday}, weeks_offset={weeks_offset}")
    
    try:
        # Use UserTimeManager
        time_manager = UserTimeManager(user_id)
        timezone = time_manager.get_timezone()
        target_date = time_manager.get_weekday_date(weekday, weeks_offset)
        
        # Weekday name mapping
        weekday_names = {
            1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
            5: "Friday", 6: "Saturday", 7: "Sunday"
        }
        weekday_name = weekday_names.get(weekday, str(weekday))
        
        # Week description
        weeks_description = {
            -2: "two weeks ago", -1: "last week", 0: "this week", 1: "next week", 2: "in two weeks"
        }
        weeks_desc = weeks_description.get(weeks_offset, f"{weeks_offset} weeks")
        
        # Build response
        date_info = {
            "user_id": user_id,
            "timezone": timezone,
            "date": target_date,
            "weekday": weekday_name,
            "weeks_offset": weeks_offset,
            "description": f"{weeks_desc} {weekday_name}",
            "status": "success"
        }
        
        content = f"Date for {weeks_desc} {weekday_name}: {target_date}"
        
        return content, date_info
        
    except Exception as e:
        error_msg = f"Error occurred while getting relative weekday date: {str(e)}"
        print(error_msg)
        return error_msg, {"error": str(e)}


def create_get_weekday_tool(timezone) -> StructuredTool:
    """Create get weekday tool"""
    
    def get_weekday_wrapper() -> Tuple[str, dict]:
        """Wrapper function to get what day of the week it is today"""
        return get_weekday(timezone)
    
    get_weekday_tool = StructuredTool.from_function(
        func=get_weekday_wrapper,
        name="get_weekday",
        description=f"Get what day of the week it is today in {timezone} timezone",
        return_direct=False
    )
    
    return get_weekday_tool

def create_get_current_time_tool(timezone: str) -> StructuredTool:
    """Create get current time tool"""
    
    def get_current_time_wrapper() -> Tuple[str, dict]:
        """Wrapper function to get current time"""
        return get_current_time_with_timezone(timezone)
    
    get_current_time_tool = StructuredTool.from_function(
        func=get_current_time_wrapper,
        name="get_current_time",
        description=f"Get current time in the specified timezone. Query current timezone before using this tool; timezone parameter is timezone name, e.g.: Asia/Taipei.",
        return_direct=False
    )
    
    return get_current_time_tool

get_taiwan_time_tool = StructuredTool.from_function(
    func=get_taiwan_time,
    name="get_taiwan_time",
    description="Get current time in Taiwan",
    return_direct=False
)

get_city_time_tool = StructuredTool.from_function(
    func=get_city_time,
    name="get_city_time",
    description="Get current time in specified city, supports major cities in Taiwan, Japan and USA, defaults to Taipei time",
    return_direct=False
)

def create_get_user_weekday_tool(user_id: str) -> StructuredTool:
    """Create get user weekday tool"""
    
    def get_user_weekday_wrapper() -> Tuple[str, dict]:
        """Wrapper function to get user's weekday"""
        return get_user_weekday(user_id)
    
    get_user_weekday_tool = StructuredTool.from_function(
        func=get_user_weekday_wrapper,
        name="get_user_weekday",
        description="Get what day of the week it is today in the user's timezone. This tool will automatically query the user's timezone settings and return what day of the week it is in that timezone.",
        return_direct=False
    )
    
    return get_user_weekday_tool


def create_get_user_current_time_tool(user_id: str) -> StructuredTool:
    """Create get user current time tool"""
    
    def get_user_current_time_wrapper() -> Tuple[str, dict]:
        """Wrapper function to get user's current time"""
        return get_user_current_time(user_id)
    
    get_user_current_time_tool = StructuredTool.from_function(
        func=get_user_current_time_wrapper,
        name="get_user_current_time",
        description="Get current time in the user's timezone. This tool will automatically query the user's timezone settings and return the current time in that timezone.",
        return_direct=False
    )
    
    return get_user_current_time_tool


def create_get_current_timezone_tool(user_id: str) -> StructuredTool:
    """Create get timezone tool"""
    
    def get_current_timezone_wrapper() -> Tuple[str, dict]:
        """Wrapper function to get current timezone information"""
        return get_current_timezone(user_id)
    
    get_current_timezone_tool = StructuredTool.from_function(
        func=get_current_timezone_wrapper,
        name="get_current_timezone",
        description="Get timezone information for the current location.",
        return_direct=False
    )
    
    return get_current_timezone_tool


def create_get_relative_date_tool(user_id: str) -> StructuredTool:
    """Create get relative date tool"""
    
    def get_relative_date_wrapper(days_offset: int) -> Tuple[str, dict]:
        """
        Wrapper function to get relative date
        
        Args:
            days_offset: Days offset (-3=three days ago, -2=day before yesterday, -1=yesterday, 0=today, 1=tomorrow, 2=day after tomorrow, 3=three days from now)
        """
        return get_user_relative_date(user_id, days_offset)
    
    get_relative_date_tool = StructuredTool.from_function(
        func=get_relative_date_wrapper,
        name="get_relative_date",
        description="""
            Get relative date. Requires one parameter:
            - days_offset: Days offset
              -3 = three days ago
              -2 = day before yesterday
              -1 = yesterday
              0 = today
              1 = tomorrow
              2 = day after tomorrow
              3 = three days from now
            
            You can also use other numbers, e.g. 7 means 7 days from now, -7 means 7 days ago.
            
            This tool will automatically use the user's timezone to calculate the specified date (YYYY-MM-DD format).
        """,
        return_direct=False
    )
    
    return get_relative_date_tool


def create_get_relative_weekday_date_tool(user_id: str) -> StructuredTool:
    """Create get relative weekday date tool"""
    
    def get_relative_weekday_date_wrapper(weekday: int, weeks_offset: int = 0) -> Tuple[str, dict]:
        """
        Wrapper function to get relative weekday date
        
        Args:
            weekday: Day of week (1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday, 7=Sunday)
            weeks_offset: Weeks offset (-2=two weeks ago, -1=last week, 0=this week, 1=next week, 2=in two weeks)
        """
        return get_user_relative_weekday_date(user_id, weekday, weeks_offset)
    
    get_relative_weekday_date_tool = StructuredTool.from_function(
        func=get_relative_weekday_date_wrapper,
        name="get_relative_weekday_date",
        description="""
            Get relative weekday date. Requires two parameters:
            - weekday: Day of week, 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday, 7=Sunday
            - weeks_offset: Weeks offset, -2=two weeks ago, -1=last week, 0=this week, 1=next week, 2=in two weeks
            
            Examples:
            - Next Wednesday: weekday=3, weeks_offset=1
            - Last Friday: weekday=5, weeks_offset=-1
            - Monday in two weeks: weekday=1, weeks_offset=2
            
            This tool will automatically use the user's timezone to calculate the specified date (YYYY-MM-DD format).
        """,
        return_direct=False
    )
    
    return get_relative_weekday_date_tool
