import requests
from typing import Tuple
from langchain_core.tools import StructuredTool


def get_current_city() -> Tuple[str, dict]:
    """獲取目前所在城市"""
    print(f'取得目前所在城市')
    try:
        city_info = get_city_by_ip()
        print(f'city_info: {city_info}')
        
        if city_info and city_info is not None:
            city_data = {
                "city": city_info,
                "method": "ip_geolocation",
                "status": "success"
            }
            return city_info, city_data
        else:
            error_msg = "無法取得目前所在城市資訊，可能是網路問題或 API 服務不可用"
            print(error_msg)
            return error_msg, {
                "error": "Failed to get city information",
                "method": "ip_geolocation",
                "status": "failed"
            }
    except Exception as e:
        error_msg = f"取得目前所在城市時發生錯誤：{str(e)}"
        print(error_msg)
        return error_msg, {
            "error": str(e),
            "method": "ip_geolocation",
            "status": "error"
        }


def get_city_by_ip() -> str:
    """透過 IP 地址獲取城市資訊"""
    try:
        print("正在透過 IP 地址查詢城市資訊...")
        response = requests.get('https://ipapi.co/json/', timeout=3)
        response.raise_for_status()  # 檢查 HTTP 狀態碼
        
        data = response.json()
        
        # 檢查必要的欄位是否存在
        if not data:
            print("API 回應為空")
            return None
            
        city = data.get("city")
        country = data.get("country_name")
        region = data.get("region")
        
        if not city:
            print("無法從 API 回應中取得城市資訊")
            return None
        
        # 構建城市資訊字串
        if region and region != city:
            content = f"目前所在城市：{city}，{region}，{country}"
        else:
            content = f"目前所在城市：{city}，{country}"
        
        print(f"成功取得城市資訊: {content}")
        return content
        
    except requests.exceptions.RequestException as e:
        print(f'網路請求失敗: {e}')
        return None
    except requests.exceptions.Timeout as e:
        print(f'請求超時: {e}')
        return None
    except ValueError as e:
        print(f'JSON 解析失敗: {e}')
        return None
    except Exception as e:
        print(f'透過IP獲取城市失敗: {e}')
        return None


def create_get_current_city_tool() -> StructuredTool:
    """創建獲取目前所在城市工具"""
    
    def get_current_city_wrapper() -> Tuple[str, dict]:
        """獲取目前所在城市的包裝函數"""
        return get_current_city()
    
    get_current_city_tool = StructuredTool.from_function(
        func=get_current_city_wrapper,
        name="get_current_city",
        description="透過 IP 地址獲取目前所在的城市資訊，包括城市名稱、地區和國家",
        return_direct=False
    )
    
    return get_current_city_tool