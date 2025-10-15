"""
MockSupabaseAdmin - 模擬 Supabase Admin 客戶端的行為
用於測試中隔離數據庫操作，提供可控的響應數據
"""

from types import SimpleNamespace
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock


class MockSupabaseResponse:
    """模擬 Supabase 響應對象"""
    def __init__(self, data=None, count=None, error=None):
        self.data = data or []
        self.count = count
        self.error = error


class MockSupabaseQuery:
    """模擬 Supabase 查詢建構器"""
    def __init__(self, admin: 'MockSupabaseAdmin', table_name: str):
        self.admin = admin
        self.table_name = table_name
        self.conditions = {}
        self.insert_payload = None
        self.update_payload = None
        self._is_delete = False
        self._select_fields = None
        self._order_by = None
        self._range_start = None
        self._range_end = None
        
    def select(self, *fields, count=None):
        """模擬 select 查詢"""
        self._select_fields = fields if fields else ["*"]
        self._count_only = count is not None
        return self
    
    def insert(self, data):
        """模擬 insert 操作"""
        self.insert_payload = data
        return self
    
    def update(self, data):
        """模擬 update 操作"""
        self.update_payload = data
        return self
    
    def delete(self):
        """模擬 delete 操作"""
        self._is_delete = True
        return self
    
    def eq(self, column, value):
        """模擬 eq 條件"""
        self.conditions[f"{column}_eq"] = value
        return self
    
    def gte(self, column, value):
        """模擬 gte 條件"""
        self.conditions[f"{column}_gte"] = value
        return self
    
    def lte(self, column, value):
        """模擬 lte 條件"""
        self.conditions[f"{column}_lte"] = value
        return self
    
    def or_(self, condition):
        """模擬 or 條件"""
        self.conditions["or"] = condition
        return self
    
    def ilike(self, column, value):
        """模擬 ilike 條件（不區分大小寫的模糊匹配）"""
        self.conditions[f"{column}_ilike"] = value
        return self
    
    def order(self, column, desc=False):
        """模擬 order 排序"""
        self._order_by = (column, desc)
        return self
    
    def range(self, start, end):
        """模擬 range 分頁"""
        self._range_start = start
        self._range_end = end
        return self
    
    def execute(self):
        """執行查詢並返回模擬響應"""
        # 記錄操作調用
        operation_info = {
            "table": self.table_name,
            "conditions": self.conditions,
            "select_fields": self._select_fields,
            "order_by": self._order_by,
            "range": (self._range_start, self._range_end) if self._range_start is not None else None
        }
        
        if self.insert_payload:
            # 記錄 insert 調用
            self.admin.insert_calls.append({
                "table": self.table_name,
                "payload": self.insert_payload,
                **operation_info
            })
            
            # 返回預設的 insert 響應
            response = self.admin.get_response(self.table_name, "insert")
            if response is None:
                # 預設 insert 響應：返回插入的數據並添加 ID
                inserted_data = self.insert_payload.copy()
                if "id" not in inserted_data:
                    inserted_data["id"] = f"mock-id-{len(self.admin.insert_calls)}"
                response = MockSupabaseResponse(data=[inserted_data])
            
            # 如果有錯誤，拋出異常
            if response.error:
                raise Exception(response.error)
            return response
            
        elif self.update_payload:
            # 記錄 update 調用
            self.admin.update_calls.append({
                "table": self.table_name,
                "payload": self.update_payload,
                **operation_info
            })
            
            # 返回預設的 update 響應
            response = self.admin.get_response(self.table_name, "update")
            if response is None:
                response = MockSupabaseResponse(data=[self.update_payload])
            
            # 如果有錯誤，拋出異常
            if response.error:
                raise Exception(response.error)
            return response
            
        elif self._is_delete:
            # 記錄 delete 調用
            self.admin.delete_calls.append({
                "table": self.table_name,
                **operation_info
            })
            
            # 返回預設的 delete 響應
            response = self.admin.get_response(self.table_name, "delete")
            if response is None:
                response = MockSupabaseResponse(data=[{"deleted": True}])
            
            # 如果有錯誤，拋出異常
            if response.error:
                raise Exception(response.error)
            return response
            
        else:
            # 記錄 select 調用
            self.admin.select_calls.append({
                "table": self.table_name,
                "count_only": getattr(self, '_count_only', False),
                **operation_info
            })
            
            # 返回預設的 select 響應
            response = self.admin.get_response(self.table_name, "select")
            if response is None:
                # 如果是 count 查詢，返回 count 數據
                if getattr(self, '_count_only', False):
                    response = MockSupabaseResponse(data=[], count=0)
                else:
                    response = MockSupabaseResponse(data=[])
            
            # 如果有錯誤，拋出異常
            if response.error:
                raise Exception(response.error)
            return response


class MockSupabaseAdmin:
    """模擬 Supabase Admin 客戶端"""
    
    def __init__(self, responses: Optional[Dict[str, List[MockSupabaseResponse]]] = None):
        """
        初始化 MockSupabaseAdmin
        
        Args:
            responses: 預定義的響應數據，格式為 {table_name: [response1, response2, ...]}
        """
        self.responses = responses or {}
        self.response_counters = {}  # 追蹤每個表的響應使用次數
        
        # 記錄所有操作調用
        self.insert_calls = []
        self.update_calls = []
        self.delete_calls = []
        self.select_calls = []
        
        # Mock auth 相關功能
        self.auth = MagicMock()
        self.auth.admin = MagicMock()
        self.auth.admin.list_users = MagicMock()
    
    def from_(self, table_name: str) -> MockSupabaseQuery:
        """模擬 from_ 方法，返回查詢建構器"""
        return MockSupabaseQuery(self, table_name)
    
    def table(self, table_name: str) -> MockSupabaseQuery:
        """模擬 table 方法，返回查詢建構器（兼容舊版本）"""
        return MockSupabaseQuery(self, table_name)
    
    def set_response(self, table_name: str, operation: str, response: MockSupabaseResponse):
        """設置特定表和操作的響應"""
        key = f"{table_name}_{operation}"
        if key not in self.responses:
            self.responses[key] = []
        self.responses[key].append(response)
    
    def set_responses(self, table_name: str, responses: List[MockSupabaseResponse]):
        """設置表的多個響應（按順序使用）"""
        self.responses[table_name] = responses
        self.response_counters[table_name] = 0
    
    def get_response(self, table_name: str, operation: str = None) -> Optional[MockSupabaseResponse]:
        """獲取響應數據"""
        # 首先嘗試獲取特定操作的響應
        if operation:
            key = f"{table_name}_{operation}"
            if key in self.responses and self.responses[key]:
                return self.responses[key].pop(0)
        
        # 然後嘗試獲取表的通用響應
        if table_name in self.responses:
            responses = self.responses[table_name]
            counter = self.response_counters.get(table_name, 0)
            
            if responses and counter < len(responses):
                response = responses[counter]
                self.response_counters[table_name] = counter + 1
                return response
        
        return None
    
    def reset(self):
        """重置所有記錄和計數器"""
        self.insert_calls.clear()
        self.update_calls.clear()
        self.delete_calls.clear()
        self.select_calls.clear()
        self.response_counters.clear()
    
    def get_last_insert(self, table_name: str = None) -> Optional[Dict]:
        """獲取最後一次 insert 調用"""
        if table_name:
            for call in reversed(self.insert_calls):
                if call["table"] == table_name:
                    return call
        elif self.insert_calls:
            return self.insert_calls[-1]
        return None
    
    def get_last_update(self, table_name: str = None) -> Optional[Dict]:
        """獲取最後一次 update 調用"""
        if table_name:
            for call in reversed(self.update_calls):
                if call["table"] == table_name:
                    return call
        elif self.update_calls:
            return self.update_calls[-1]
        return None
    
    def get_call_count(self, operation: str, table_name: str = None) -> int:
        """獲取特定操作的調用次數"""
        calls = getattr(self, f"{operation}_calls", [])
        if table_name:
            return sum(1 for call in calls if call["table"] == table_name)
        return len(calls)


# 便利函數
def create_mock_response(data=None, count=None, error=None) -> MockSupabaseResponse:
    """創建模擬響應的便利函數"""
    return MockSupabaseResponse(data=data, count=count, error=error)


def create_reminder_data(id="test-id", description="Test reminder", **kwargs) -> Dict[str, Any]:
    """創建提醒數據的便利函數"""
    default_data = {
        "id": id,
        "user_id": "test-user",
        "description": description,
        "remind_at": "2024-12-25T10:00:00Z",
        "method": "notification",
        "is_sent": False,
        "sent_at": None,
        "created_at": "2024-12-20T09:00:00Z",
        "is_recurring": False,
        "recurrence_rule": None,
        "recurrence_exceptions": None,
        "status": "active"
    }
    default_data.update(kwargs)
    return default_data