from datetime import datetime
import pytz


def convert_utc_to_taiwan_time(time: str) -> str:
    """將UTC時間轉換為台灣時間"""
    utc_time = datetime.fromisoformat(time)
    taiwan_time = utc_time.astimezone(pytz.timezone('Asia/Taipei'))
    return taiwan_time.isoformat()

def convert_taiwan_to_utc_time(time: str) -> str:
    """將台灣時間轉換為UTC時間"""
    taiwan_time = datetime.fromisoformat(time)
    utc_time = taiwan_time.astimezone(pytz.timezone('UTC'))
    return utc_time.isoformat()

def get_current_time(region: str = "Asia/Taipei") -> str:
    """獲取指定地區目前時間"""

    region_tz = pytz.timezone(region)
    region_time = datetime.now(region_tz)
    formatted_time = region_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time

def get_city_local_time(city: str = "Taipei") -> str:
    """
    獲取台灣、日本和美國任意城市的在地時間
    
    Args:
        city: 城市名稱，預設為Taipei
        
    Returns:
        str: 格式化的時間字串 "YYYY-MM-DD HH:MM:SS"
    """
    # 將輸入的城市名稱轉換為小寫
    city = city.lower()
    
    # 台灣城市時區對應
    taiwan_cities = {
        "taipei": "Asia/Taipei",
        "new taipei": "Asia/Taipei", 
        "taoyuan": "Asia/Taipei",
        "taichung": "Asia/Taipei",
        "tainan": "Asia/Taipei",
        "kaohsiung": "Asia/Taipei",
        "keelung": "Asia/Taipei",
        "hsinchu": "Asia/Taipei",
        "chiayi": "Asia/Taipei",
        "yilan": "Asia/Taipei",
        "hualien": "Asia/Taipei",
        "taitung": "Asia/Taipei",
        "pingtung": "Asia/Taipei",
        "miaoli": "Asia/Taipei",
        "changhua": "Asia/Taipei",
        "nantou": "Asia/Taipei",
        "yunlin": "Asia/Taipei",
        "penghu": "Asia/Taipei",
        "kinmen": "Asia/Taipei",
        "lienchiang": "Asia/Taipei"
    }
    
    # 日本城市時區對應
    japan_cities = {
        "tokyo": "Asia/Tokyo",
        "osaka": "Asia/Tokyo",
        "kyoto": "Asia/Tokyo",
        "nagoya": "Asia/Tokyo",
        "yokohama": "Asia/Tokyo",
        "kobe": "Asia/Tokyo",
        "fukuoka": "Asia/Tokyo",
        "sapporo": "Asia/Tokyo",
        "sendai": "Asia/Tokyo",
        "hiroshima": "Asia/Tokyo",
        "niigata": "Asia/Tokyo",
        "shizuoka": "Asia/Tokyo",
        "okayama": "Asia/Tokyo",
        "kumamoto": "Asia/Tokyo",
        "kagoshima": "Asia/Tokyo",
        "okinawa": "Asia/Tokyo",
        "naha": "Asia/Tokyo"
    }
    
    # 美國城市時區對應
    us_cities = {
        # 東部時區 (UTC-5/UTC-4)
        "new york": "America/New_York",
        "miami": "America/New_York",
        "atlanta": "America/New_York",
        "boston": "America/New_York",
        "philadelphia": "America/New_York",
        "washington": "America/New_York",
        "detroit": "America/New_York",
        "chicago": "America/Chicago",
        "houston": "America/Chicago",
        "dallas": "America/Chicago",
        "minneapolis": "America/Chicago",
        "denver": "America/Denver",
        "phoenix": "America/Denver",
        "salt lake city": "America/Denver",
        "los angeles": "America/Los_Angeles",
        "san francisco": "America/Los_Angeles",
        "seattle": "America/Los_Angeles",
        "portland": "America/Los_Angeles",
        "san diego": "America/Los_Angeles",
        "las vegas": "America/Los_Angeles",
        "anchorage": "America/Anchorage",
        "honolulu": "Pacific/Honolulu"
    }
    
    # 合併所有支援的城市
    all_cities = {**taiwan_cities, **japan_cities, **us_cities}
    
    # 獲取城市對應的時區，如果找不到則使用台北時區
    timezone = all_cities.get(city, "Asia/Taipei")
    
    return get_current_time(timezone)


def get_city_coordinates(city: str = "Taipei") -> dict:
    """
    獲取台灣、日本和美國主要城市的座標資訊
    
    Args:
        city: 城市名稱，預設為Taipei
        
    Returns:
        dict: 包含城市座標的字典 {"lat": float, "lng": float}
    """
    # 將輸入的城市名稱轉換為小寫
    city = city.lower()
    
    # 台灣城市座標
    taiwan_cities = {
        "taipei": {"lat": 25.0330, "lng": 121.5654},
        "new taipei": {"lat": 25.0120, "lng": 121.4657},
        "taoyuan": {"lat": 24.9936, "lng": 121.3010},
        "taichung": {"lat": 24.1477, "lng": 120.6736},
        "tainan": {"lat": 22.9997, "lng": 120.2270},
        "kaohsiung": {"lat": 22.6273, "lng": 120.3014},
        "keelung": {"lat": 25.1276, "lng": 121.7392},
        "hsinchu": {"lat": 24.8138, "lng": 120.9675},
        "chiayi": {"lat": 23.4800, "lng": 120.4491},
        "yilan": {"lat": 24.7021, "lng": 121.7377},
        "hualien": {"lat": 23.9871, "lng": 121.6011},
        "taitung": {"lat": 22.7583, "lng": 121.1444},
        "pingtung": {"lat": 22.5519, "lng": 120.5487},
        "miaoli": {"lat": 24.5601, "lng": 120.8214},
        "changhua": {"lat": 24.0809, "lng": 120.5383},
        "nantou": {"lat": 23.9609, "lng": 120.6863},
        "yunlin": {"lat": 23.7092, "lng": 120.4313},
        "penghu": {"lat": 23.5711, "lng": 119.5793},
        "kinmen": {"lat": 24.4491, "lng": 118.3189},
        "lienchiang": {"lat": 26.1975, "lng": 119.5451}
    }
    
    # 日本城市座標
    japan_cities = {
        "tokyo": {"lat": 35.6762, "lng": 139.6503},
        "osaka": {"lat": 34.6937, "lng": 135.5023},
        "kyoto": {"lat": 35.0116, "lng": 135.7681},
        "nagoya": {"lat": 35.1815, "lng": 136.9066},
        "yokohama": {"lat": 35.4437, "lng": 139.6380},
        "kobe": {"lat": 34.6901, "lng": 135.1955},
        "fukuoka": {"lat": 33.5902, "lng": 130.4017},
        "sapporo": {"lat": 43.0618, "lng": 141.3545},
        "sendai": {"lat": 38.2688, "lng": 140.8721},
        "hiroshima": {"lat": 34.3853, "lng": 132.4553},
        "niigata": {"lat": 37.9022, "lng": 139.0232},
        "shizuoka": {"lat": 34.9769, "lng": 138.3831},
        "okayama": {"lat": 34.6618, "lng": 133.9344},
        "kumamoto": {"lat": 32.7898, "lng": 130.7414},
        "kagoshima": {"lat": 31.5602, "lng": 130.5581},
        "okinawa": {"lat": 26.2124, "lng": 127.6809},
        "naha": {"lat": 26.2124, "lng": 127.6809}
    }
    
    # 美國城市座標
    us_cities = {
        # 東部時區
        "new york": {"lat": 40.7128, "lng": -74.0060},
        "miami": {"lat": 25.7617, "lng": -80.1918},
        "atlanta": {"lat": 33.7490, "lng": -84.3880},
        "boston": {"lat": 42.3601, "lng": -71.0589},
        "philadelphia": {"lat": 39.9526, "lng": -75.1652},
        "washington": {"lat": 38.9072, "lng": -77.0369},
        "detroit": {"lat": 42.3314, "lng": -83.0458},
        # 中部時區
        "chicago": {"lat": 41.8781, "lng": -87.6298},
        "houston": {"lat": 29.7604, "lng": -95.3698},
        "dallas": {"lat": 32.7767, "lng": -96.7970},
        "minneapolis": {"lat": 44.9778, "lng": -93.2650},
        # 山地時區
        "denver": {"lat": 39.7392, "lng": -104.9903},
        "phoenix": {"lat": 33.4484, "lng": -112.0740},
        "salt lake city": {"lat": 40.7608, "lng": -111.8910},
        # 太平洋時區
        "los angeles": {"lat": 34.0522, "lng": -118.2437},
        "san francisco": {"lat": 37.7749, "lng": -122.4194},
        "seattle": {"lat": 47.6062, "lng": -122.3321},
        "portland": {"lat": 45.5152, "lng": -122.6784},
        "san diego": {"lat": 32.7157, "lng": -117.1611},
        "las vegas": {"lat": 36.1699, "lng": -115.1398},
        # 阿拉斯加時區
        "anchorage": {"lat": 61.2181, "lng": -149.9003},
        # 夏威夷時區
        "honolulu": {"lat": 21.3099, "lng": -157.8581}
    }
    
    # 合併所有城市座標
    all_cities = {**taiwan_cities, **japan_cities, **us_cities}
    
    return all_cities.get(city, taiwan_cities["taipei"])
