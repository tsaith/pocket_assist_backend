from typing import List, Tuple
import random
from langchain_core.tools import StructuredTool
from langchain_core.documents import Document
import json
import requests

from app.lib.supabase import supabase_admin
from app.core.config import settings
from app.lib.chatbot.utils import (
    get_city_coordinates
)
from app.lib.encryption import Encryption


def create_retrieve_knowledge_tool(embeddings, user_id: str, chatbot_id: str):
    """
    創建檢索工具
    
    Args:
        embeddings: 嵌入模型
        user_id: 用戶ID
        chatbot_id: 聊天機器人ID
        
    Returns:
        檢索工具
    """
    def retrieve_knowledge(query: str) -> Tuple[str, List[Document]]:
        """
        從Knowledge資料庫檢索與查詢使用者提供的資訊

        Args:
            query: 查詢字串

        Returns:
            serialized: 檢索結果
            retrieved_docs: 檢索結果
        """

        print(f"檢索Knowledge資料庫：{query}")
        
        # 生成查詢的嵌入向量
        query_embedding = embeddings.embed_query(query)
        
        # 調用 match_sections 函數
        response = supabase_admin.rpc(
            "match_sections", 
            {
                "query_embedding": query_embedding,
                "user_id": user_id,
                "chatbot_id": chatbot_id,
                "match_count": 5
            }
        ).execute()
        
        # 轉換結果為Document對象
        retrieved_docs = []
        if response.data:
            for item in response.data:
                metadata = item.get('metadata', {})
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        pass
                        
                doc = Document(
                    page_content=item.get('content', ''),
                    metadata=metadata
                )
                retrieved_docs.append(doc)

        # 格式化檢索結果為字符串
        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
            for doc in retrieved_docs
        )

        print(f"檢索結果: {serialized}")

        return serialized, retrieved_docs
    
    # 使用 StructuredTool 封裝
    retrieve_knowledge_tool = StructuredTool.from_function(
        func=retrieve_knowledge,
        name="retrieve_knowledge",
        description="從Knowledge資料庫檢索與查詢使用者提供的資訊",
        return_direct=False
    )
    
    return retrieve_knowledge_tool





def get_city_weather(city: str = "Taipei") -> Tuple[str, dict]:
    """獲取指定城市的天氣資訊"""

    city = city.lower()

    try:
        # 使用 Google Map Platform API 查詢天氣
        api_key = settings.GOOGLE_MAP_PLATFORM_API_KEY
        if not api_key:
            error_msg = "Google Map Platform API Key 未設置"
            return error_msg, {"error": "API key not configured"}

        base_url = "https://weather.googleapis.com/v1/currentConditions:lookup"

        # 台灣主要城市的座標
        city_coord = get_city_coordinates(city)
        
        params = {
            "key": api_key,
            "location.latitude": city_coord['lat'],
            "location.longitude": city_coord['lng'],
            "unitsSystem": "METRIC"
        }
        response = requests.get(base_url, params=params, timeout=10)

        if response.status_code == 200:
            weather_data = response.json()
            
            # 提取天氣資訊
            temp = weather_data.get("temperature", {}).get("degrees", "N/A")
            humidity = weather_data.get("relativeHumidity", "N/A")
            weather_condition = weather_data.get("weatherCondition", {})
            description = weather_condition.get("description", {}).get("text", "N/A")
            wind = weather_data.get("wind", {})
            wind_speed = wind.get("speed", {}).get("value", "N/A")
            wind_unit = wind.get("speed", {}).get("unit", "")
            feels_like = weather_data.get("feelsLikeTemperature", {}).get("degrees", "N/A")
            uv_index = weather_data.get("uvIndex", "N/A")
            precipitation_prob = weather_data.get("precipitation", {}).get("probability", {}).get("percent", "N/A")
            
            weather_info = {
                "city": city,
                "temperature": f"{temp}°C" if temp != "N/A" else "N/A",
                "feels_like": f"{feels_like}°C" if feels_like != "N/A" else "N/A",
                "humidity": f"{humidity}%" if humidity != "N/A" else "N/A",
                "description": description,
                "wind_speed": f"{wind_speed} {wind_unit}" if wind_speed != "N/A" else "N/A",
                "uv_index": uv_index,
                "precipitation_probability": f"{precipitation_prob}%" if precipitation_prob != "N/A" else "N/A"
            }
            
            content = f"{city}目前天氣：{description}，溫度{temp}°C（體感{feels_like}°C），濕度{humidity}%，風速{wind_speed} {wind_unit}，紫外線指數{uv_index}，降雨機率{precipitation_prob}%"
            
            return content, weather_info
        else:
            error_msg = f"無法獲取{city}的天氣資訊"
            print(f"無法獲取{city}的天氣資訊")
            return error_msg, {"error": "API request failed"}
            
    except Exception as e:
        error_msg = f"查詢天氣時發生錯誤：{str(e)}"
        print(f"查詢天氣時發生錯誤：{str(e)}")
        return error_msg, {"error": str(e)}


def get_city_weather_forecast(city: str = "Taipei", days: int = 3) -> Tuple[str, dict]:
    """獲取指定城市的未來天氣預報資訊"""

    city = city.lower()

    try:
        # 使用 Google Map Platform API 查詢天氣預報
        api_key = settings.GOOGLE_MAP_PLATFORM_API_KEY
        if not api_key:
            error_msg = "Google Map Platform API Key 未設置"
            return error_msg, {"error": "API key not configured"}

        if days > 5:
            days = 5
        elif days < 3:
            days = 3

        base_url = "https://weather.googleapis.com/v1/forecast/days:lookup"
        
        # 台灣主要城市的座標
        city_coord = get_city_coordinates(city)
        
        params = {
            "key": api_key,
            "location.latitude": city_coord['lat'],
            "location.longitude": city_coord['lng'],
            "days": days
        }
        
        response = requests.get(base_url, params=params, timeout=10)

        if response.status_code == 200:
            weather_data = response.json()
            forecast_days = weather_data.get("forecastDays", [])
            
            if not forecast_days:
                error_msg = f"無法獲取{city}的天氣預報資訊"
                return error_msg, {"error": "No forecast data available"}
            
            #forecast_days = forecast_days[1:days]
            
            # 解析預報資訊
            forecast_info = []
            for i, day in enumerate(forecast_days):

                display_date = day.get("displayDate", {})
                date_str = f"{display_date.get('year', 'N/A')}-{display_date.get('month', 'N/A')}-{display_date.get('day', 'N/A')}"
                
                max_temp = day.get("maxTemperature", {}).get("degrees", "N/A")
                min_temp = day.get("minTemperature", {}).get("degrees", "N/A")
                feels_like_max = day.get("feelsLikeMaxTemperature", {}).get("degrees", "N/A")
                feels_like_min = day.get("feelsLikeMinTemperature", {}).get("degrees", "N/A")
                
                # 日間預報
                daytime = day.get("daytimeForecast", {})
                daytime_desc = daytime.get("weatherCondition", {}).get("description", {}).get("text", "N/A")
                daytime_humidity = daytime.get("relativeHumidity", "N/A")
                daytime_precip_prob = daytime.get("precipitation", {}).get("probability", {}).get("percent", "N/A")
                daytime_wind = daytime.get("wind", {}).get("speed", {}).get("value", "N/A")
                daytime_wind_unit = daytime.get("wind", {}).get("speed", {}).get("unit", "")
                
                # 夜間預報
                nighttime = day.get("nighttimeForecast", {})
                nighttime_desc = nighttime.get("weatherCondition", {}).get("description", {}).get("text", "N/A")
                nighttime_humidity = nighttime.get("relativeHumidity", "N/A")
                nighttime_precip_prob = nighttime.get("precipitation", {}).get("probability", {}).get("percent", "N/A")
                nighttime_wind = nighttime.get("wind", {}).get("speed", {}).get("value", "N/A")
                nighttime_wind_unit = nighttime.get("wind", {}).get("speed", {}).get("unit", "")
                
                day_info = {
                    "date": date_str,
                    "max_temp": f"{max_temp}°C" if max_temp != "N/A" else "N/A",
                    "min_temp": f"{min_temp}°C" if min_temp != "N/A" else "N/A",
                    "feels_like_max": f"{feels_like_max}°C" if feels_like_max != "N/A" else "N/A",
                    "feels_like_min": f"{feels_like_min}°C" if feels_like_min != "N/A" else "N/A",
                    "daytime": {
                        "description": daytime_desc,
                        "humidity": f"{daytime_humidity}%" if daytime_humidity != "N/A" else "N/A",
                        "precipitation_probability": f"{daytime_precip_prob}%" if daytime_precip_prob != "N/A" else "N/A",
                        "wind_speed": f"{daytime_wind} {daytime_wind_unit}" if daytime_wind != "N/A" else "N/A"
                    },
                    "nighttime": {
                        "description": nighttime_desc,
                        "humidity": f"{nighttime_humidity}%" if nighttime_humidity != "N/A" else "N/A",
                        "precipitation_probability": f"{nighttime_precip_prob}%" if nighttime_precip_prob != "N/A" else "N/A",
                        "wind_speed": f"{nighttime_wind} {nighttime_wind_unit}" if nighttime_wind != "N/A" else "N/A"
                    }
                }
                forecast_info.append(day_info)
            
            # 生成預報內容
            content_parts = [f"{city}未來{days}天天氣預報："]
            for i, day_info in enumerate(forecast_info):
                day_num = i
                content_parts.append(f"\n第{day_num}天 ({day_info['date']})：")
                content_parts.append(f"  溫度：{day_info['min_temp']} ~ {day_info['max_temp']} (體感 {day_info['feels_like_min']} ~ {day_info['feels_like_max']})")
                content_parts.append(f"  日間：{day_info['daytime']['description']}，濕度{day_info['daytime']['humidity']}，降雨機率{day_info['daytime']['precipitation_probability']}，風速{day_info['daytime']['wind_speed']}")
                content_parts.append(f"  夜間：{day_info['nighttime']['description']}，濕度{day_info['nighttime']['humidity']}，降雨機率{day_info['nighttime']['precipitation_probability']}，風速{day_info['nighttime']['wind_speed']}")
            
            content = "".join(content_parts)

            current_time = get_city_time(city)
            content = f"目前時間：{current_time}\n\n{content}"
            
            print(f"天氣預報：{content}")

            return content, {
                "city": city,
                "days": days,
                "forecast": forecast_info,
            }
        else:
            error_msg = f"無法獲取{city}的天氣預報資訊"
            return error_msg, {"error": "API request failed"}
            
    except Exception as e:
        error_msg = f"查詢天氣預報時發生錯誤：{str(e)}"
        return error_msg, {"error": str(e)}

def generate_random_integer(min: int, max: int, size: int) -> Tuple[str, List[int]]:
    """Generate size random integers in the range [min, max]."""
    array = [random.randint(min, max) for _ in range(size)]
    content = f"Successfully generated array of {size} random integers in [{min}, {max}]."
    return content, array


# 使用 StructuredTool 封裝工具
generate_random_integer_tool = StructuredTool.from_function(
    func=generate_random_integer,
    name="generate_random_integer",
    description="Generate size random integers in the range [min, max].",
    return_direct=False
)

get_city_weather_tool = StructuredTool.from_function(
    func=get_city_weather,
    name="get_city_weather",
    description="獲取指定城市的目前天氣資訊，預設查詢台北天氣",
    return_direct=False
)

get_city_weather_forecast_tool = StructuredTool.from_function(
    func=get_city_weather_forecast,
    name="get_city_weather_forecast",
    description="獲取指定城市的未來天氣預報資訊，可查詢1-5天內的的預報。",
    return_direct=False
)

def create_create_user_secret_tool(user_id: str, chatbot_id: str) -> StructuredTool:
    """創建添加用戶密鑰工具"""

    def create_user_secret(platform: str, account: str, password: str) -> str:
        """添加新的用戶密鑰記錄"""

        print(f"添加用戶密鑰：Platform {platform}, Account {account}")
        try:
            # 檢查是否已存在相同的 platform 和 account 組合
            response = supabase_admin.from_("user_secrets").select("*").eq("user_id", user_id).eq("chatbot_id", chatbot_id).eq("platform", platform).eq("account", account).execute()
            
            if response.data:
                return f"已存在相同的 Platform: {platform}, Account: {account} 記錄"
            
            # 加密密碼
            encryption = Encryption()
            encrypted_password = encryption.encrypt_and_decode(password)
            
            # 添加新記錄
            result = supabase_admin.from_("user_secrets").insert({
                "user_id": user_id,
                "chatbot_id": chatbot_id,
                "platform": platform,
                "account": account,
                "password": encrypted_password
            }).execute()
            
            if result.data:
                new_record = result.data[0]
                return f"成功添加用戶密鑰記錄，ID: {new_record.get('id', '')}, Platform: {platform}, Account: {account}"
            else:
                return "添加用戶密鑰記錄失敗"
                
        except Exception as e:
            error_msg = f"添加用戶密鑰時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg

    create_user_secret_tool = StructuredTool.from_function(
        func=create_user_secret,
        name="create_user_secret",
        description="添加新的用戶密鑰記錄，需要提供 platform、account 和 password 參數",
    )

    return create_user_secret_tool


def create_read_user_secrets_tool(user_id: str, chatbot_id: str) -> StructuredTool:
    """創建讀取用戶密鑰工具"""

    def read_user_secrets() -> str:
        """讀取智能助理的用戶密鑰內容"""

        print(f"讀取用戶密鑰內容：{user_id}, chatbot_id：{chatbot_id}")
        content = ""
        try:
            response = supabase_admin.from_("user_secrets").select("id, platform, account, password, created_at, updated_at").eq("user_id", user_id).eq("chatbot_id", chatbot_id).execute()
            if response.data:
                encryption = Encryption()
                secrets_list = []
                for secret_data in response.data:
                    # 解密密碼
                    encrypted_password = secret_data.get('password', '')
                    decrypted_password = encryption.encode_and_decrypt(encrypted_password)
                    secret_info = f"ID: {secret_data.get('id', '')}, Platform: {secret_data.get('platform', '')}, Account: {secret_data.get('account', '')}, Password: {decrypted_password}, Created: {secret_data.get('created_at', '')}, Updated: {secret_data.get('updated_at', '')}"
                    secrets_list.append(secret_info)
                content = "\n".join(secrets_list)

                print(f"用戶密鑰內容：{content}")
                return content
            else:
                return "No user secrets found"
        except Exception as e:
            print(f"讀取用戶密鑰內容時發生錯誤：{str(e)}")
            return ""

    read_user_secrets_tool = StructuredTool.from_function(
        func=read_user_secrets,
        name="read_user_secrets",
        description="讀取智能助理的用戶密鑰內容，返回所有記錄的詳細信息",
    )

    return read_user_secrets_tool


def create_update_user_secret_tool(user_id: str, chatbot_id: str) -> StructuredTool:
    """創建更新用戶密鑰工具"""

    def update_user_secret(id: str, platform: str, account: str, password: str) -> bool:
        """更新智能助理的用戶密鑰內容"""

        print(f"更新用戶密鑰內容：ID {id}, Platform {platform}, Account {account}")
        is_updated = False
        try:
            # 檢查指定 ID 的記錄是否存在
            response = supabase_admin.from_("user_secrets").select("*").eq("id", id).eq("user_id", user_id).eq("chatbot_id", chatbot_id).execute()
            
            if response.data:
                # 加密密碼
                encryption = Encryption()
                encrypted_password = encryption.encrypt_and_decode(password)
                
                # 更新記錄
                supabase_admin.from_("user_secrets").update({
                    "platform": platform,
                    "account": account,
                    "password": encrypted_password,
                    "updated_at": "now()"
                }).eq("id", id).eq("user_id", user_id).eq("chatbot_id", chatbot_id).execute()
                is_updated = True
            else:
                print(f"找不到 ID {id} 的用戶密鑰記錄")
                
        except Exception as e:
            print(f"更新用戶密鑰時發生錯誤：{str(e)}")
            
        return is_updated

    update_user_secret_tool = StructuredTool.from_function(
        func=update_user_secret,
        name="update_user_secret",
        description="更新智能助理的用戶密鑰內容，需要提供 id、platform、account 和 password 參數",
    )

    return update_user_secret_tool


def create_delete_user_secret_tool(user_id: str, chatbot_id: str) -> StructuredTool:
    """創建刪除用戶密鑰工具"""

    def delete_user_secret(id: str) -> str:
        """刪除智能助理的用戶密鑰記錄"""

        print(f"刪除用戶密鑰記錄：ID {id}")
        try:
            # 檢查指定 ID 的記錄是否存在且屬於該 user
            response = supabase_admin.from_("user_secrets").select("*").eq("id", id).eq("user_id", user_id).eq("chatbot_id", chatbot_id).execute()
            
            if not response.data:
                return f"找不到 ID {id} 的用戶密鑰記錄"
            
            # 刪除記錄
            result = supabase_admin.from_("user_secrets").delete().eq("id", id).eq("user_id", user_id).eq("chatbot_id", chatbot_id).execute()
            
            if result.data:
                return f"成功刪除用戶密鑰記錄，ID: {id}"
            else:
                return "刪除用戶密鑰記錄失敗"
                
        except Exception as e:
            error_msg = f"刪除用戶密鑰記錄時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg

    delete_user_secret_tool = StructuredTool.from_function(
        func=delete_user_secret,
        name="delete_user_secret",
        description="刪除智能助理的用戶密鑰記錄，需要提供 id 參數",
    )

    return delete_user_secret_tool





