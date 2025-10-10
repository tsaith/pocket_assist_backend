from typing import List, Tuple
from langchain_core.tools import StructuredTool

from app.lib.supabase import supabase_admin
from app.lib.chatbot.utils import (
    convert_utc_to_taiwan_time,
    convert_taiwan_to_utc_time
)

def create_create_bookkeeping_category_tool(user_id: str) -> StructuredTool:
    """創建添加記帳類別工具"""

    def create_bookkeeping_category(name: str, type: str) -> str:
        """添加新的記帳類別"""

        print(f"添加記帳類別：Name {name}, Type {type}")
        try:
            # 驗證類型
            if type not in ['income', 'expense']:
                return f"類型必須是 'income' 或 'expense'，當前類型：{type}"
            
            # 檢查是否已存在相同的 name 和 type 組合
            response = supabase_admin.from_("bookkeeping_categories").select("*").eq("user_id", user_id).eq("name", name).eq("type", type).execute()
            
            if response.data:
                return f"已存在相同的記帳類別：{name} ({type})"
            
            # 添加新記錄
            result = supabase_admin.from_("bookkeeping_categories").insert({
                "user_id": user_id,
                "name": name,
                "type": type
            }).execute()
            
            if result.data:
                new_record = result.data[0]
                return f"成功添加記帳類別，ID: {new_record.get('id', '')}, Name: {name}, Type: {type}"
            else:
                return "添加記帳類別失敗"
                
        except Exception as e:
            error_msg = f"添加記帳類別時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg

    create_bookkeeping_category_tool = StructuredTool.from_function(
        func=create_bookkeeping_category,
        name="create_bookkeeping_category",
        description="添加新的記帳類別，需要提供 name 和 type 參數，type 必須是 'income' 或 'expense'",
    )

    return create_bookkeeping_category_tool


def create_read_bookkeeping_categories_tool(user_id: str) -> StructuredTool:
    """創建讀取記帳類別工具"""

    def read_bookkeeping_categories() -> str:
        """讀取所有記帳類別"""

        print(f"讀取記帳類別 from user_id：{user_id}")
        content = ""
        try:
            response = supabase_admin.from_("bookkeeping_categories").select("id, name, type").eq("user_id", user_id).execute()
            if response.data:
                categories_list = []
                for category_data in response.data:
                    category_info = f"ID: {category_data.get('id', '')}, Name: {category_data.get('name', '')}, Type: {category_data.get('type', '')}"
                    categories_list.append(category_info)
                content = "\n".join(categories_list)

                print(f"記帳類別內容：{content}")
                return content
            else:
                return "No bookkeeping categories found"
        except Exception as e:
            print(f"讀取記帳類別時發生錯誤：{str(e)}")
            return ""

    read_bookkeeping_categories_tool = StructuredTool.from_function(
        func=read_bookkeeping_categories,
        name="read_bookkeeping_categories",
        description="讀取目前存在的記帳類別，返回所有類別的詳細資訊",
    )

    return read_bookkeeping_categories_tool


def create_read_bookkeeping_category_tool(user_id: str) -> StructuredTool:
    """創建讀取單個記帳類別工具"""

    def read_bookkeeping_category(id: str) -> str:
        """讀取單個記帳類別"""

        print(f"讀取記帳類別 from user_id：{user_id}, category_id：{id}")
        try:
            response = supabase_admin.from_("bookkeeping_categories").select("id, name, type").eq("id", id).eq("user_id", user_id).execute()
            
            if response.data:
                category_data = response.data[0]
                category_info = f"ID: {category_data.get('id', '')}, Name: {category_data.get('name', '')}, Type: {category_data.get('type', '')}"
                
                print(f"記帳類別內容：{category_info}")
                return category_info
            else:
                return f"找不到 ID {id} 的記帳類別"
        except Exception as e:
            print(f"讀取記帳類別時發生錯誤：{str(e)}")
            return ""

    read_bookkeeping_category_tool = StructuredTool.from_function(
        func=read_bookkeeping_category,
        name="read_bookkeeping_category",
        description="讀取單個記帳類別，需要提供 id 參數",
    )

    return read_bookkeeping_category_tool


def create_update_bookkeeping_category_tool(user_id: str) -> StructuredTool:
    """創建更新記帳類別工具"""

    def update_bookkeeping_category(id: str, name: str, type: str) -> bool:
        """更新記帳類別"""

        print(f"更新記帳類別：ID {id}, Name {name}, Type {type}")
        is_updated = False
        try:
            # 驗證類型
            if type not in ['income', 'expense']:
                print(f"類型必須是 'income' 或 'expense'，當前類型：{type}")
                return False
            
            # 檢查指定 ID 的記錄是否存在
            response = supabase_admin.from_("bookkeeping_categories").select("*").eq("id", id).eq("user_id", user_id).execute()
            
            if response.data:
                # 如果記錄存在，更新內容
                supabase_admin.from_("bookkeeping_categories").update({
                    "name": name,
                    "type": type
                }).eq("id", id).eq("user_id", user_id).execute()
                is_updated = True
            else:
                print(f"找不到 ID {id} 的記帳類別")
                is_updated = False
                
        except Exception as e:
            is_updated = False
            print(f"更新記帳類別時發生錯誤：{str(e)}")

        return is_updated

    update_bookkeeping_category_tool = StructuredTool.from_function(
        func=update_bookkeeping_category,
        name="update_bookkeeping_category",
        description="更新記帳類別，需要提供 id、name 和 type 參數，type 必須是 'income' 或 'expense'",
    )

    return update_bookkeeping_category_tool


def create_delete_bookkeeping_category_tool(user_id: str) -> StructuredTool:
    """創建刪除記帳類別工具"""

    def delete_bookkeeping_category(id: str) -> str:
        """刪除指定的記帳類別"""

        print(f"刪除記帳類別：ID {id}")
        try:
            # 檢查指定 ID 的記錄是否存在且屬於該 chatbot
            response = supabase_admin.from_("bookkeeping_categories").select("*").eq("id", id).eq("user_id", user_id).execute()
            
            if not response.data:
                return f"找不到 ID {id} 的記帳類別"
            
            # 刪除記錄
            result = supabase_admin.from_("bookkeeping_categories").delete().eq("id", id).eq("user_id", user_id).execute()
            
            if result.data:
                return f"成功刪除記帳類別，ID: {id}"
            else:
                return "刪除記帳類別失敗"
                
        except Exception as e:
            error_msg = f"刪除記帳類別時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg

    delete_bookkeeping_category_tool = StructuredTool.from_function(
        func=delete_bookkeeping_category,
        name="delete_bookkeeping_category",
        description="刪除指定的記帳類別，需要提供 id 參數",
    )

    return delete_bookkeeping_category_tool


def create_create_bookkeeping_transaction_tool(user_id: str) -> StructuredTool:
    """創建添加記帳交易工具"""

    def create_bookkeeping_transaction(category_id: str, amount: float, description: str, date: str = None, payment_method: str = None) -> str:
        """添加新的記帳交易"""

        print(f"添加記帳交易：Category ID {category_id}, Amount {amount}, Description {description}, Date {date}, Payment Method {payment_method}")
        try:
            # 檢查類別是否存在
            category_response = supabase_admin.from_("bookkeeping_categories").select("*").eq("id", category_id).eq("user_id", user_id).execute()
            
            if not category_response.data:
                return f"找不到 ID {category_id} 的記帳類別"
            
            # 準備交易資料
            transaction_data = {
                "user_id": user_id,
                "category_id": category_id,
                "amount": amount,
                "description": description
            }
            
            # 如果有提供日期，則使用提供的日期
            if date:
                transaction_data["date"] = date
            
            # 如果有提供支付方式，則使用提供的支付方式
            if payment_method:
                transaction_data["payment_method"] = payment_method
            
            # 添加新記錄
            result = supabase_admin.from_("bookkeeping_transactions").insert(transaction_data).execute()
            
            if result.data:
                new_record = result.data[0]
                payment_info = f", Payment Method: {payment_method}" if payment_method else ""
                return f"成功添加記帳交易，ID: {new_record.get('id', '')}, Amount: {amount}, Description: {description}{payment_info}"
            else:
                return "添加記帳交易失敗"
                
        except Exception as e:
            error_msg = f"添加記帳交易時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg

    create_bookkeeping_transaction_tool = StructuredTool.from_function(
        func=create_bookkeeping_transaction,
        name="create_bookkeeping_transaction",
        description="添加新的記帳交易，需要提供 category_id、amount 和 description 參數，可選 date 參數（格式：YYYY-MM-DD）和 payment_method 參數（支付方式，如：現金、信用卡、轉帳等）",
    )

    return create_bookkeeping_transaction_tool


def create_read_bookkeeping_transactions_tool(user_id: str) -> StructuredTool:
    """創建讀取記帳交易工具"""

    def read_bookkeeping_transactions() -> str:
        """讀取所有記帳交易"""

        print(f"讀取記帳交易 from user_id：{user_id}")
        content = ""
        try:
            response = supabase_admin.from_("bookkeeping_transactions").select("id, category_id, amount, description, payment_method, date, created_at, updated_at").eq("user_id", user_id).execute()
            if response.data:
                transactions_list = []
                for transaction_data in response.data:
                    payment_method = transaction_data.get('payment_method', '')
                    payment_info = f", Payment Method: {payment_method}" if payment_method else ""
                    transaction_info = f"ID: {transaction_data.get('id', '')}, Category ID: {transaction_data.get('category_id', '')}, Amount: {transaction_data.get('amount', '')}, Description: {transaction_data.get('description', '')}{payment_info}, Date: {transaction_data.get('date', '')}, Created: {transaction_data.get('created_at', '')}, Updated: {transaction_data.get('updated_at', '')}"
                    transactions_list.append(transaction_info)
                content = "\n".join(transactions_list)

                print(f"記帳交易內容：{content}")
                return content
            else:
                return "No bookkeeping transactions found"
        except Exception as e:
            print(f"讀取記帳交易時發生錯誤：{str(e)}")
            return ""

    read_bookkeeping_transactions_tool = StructuredTool.from_function(
        func=read_bookkeeping_transactions,
        name="read_bookkeeping_transactions",
        description="讀取所有記帳交易，返回所有交易的詳細信息",
    )

    return read_bookkeeping_transactions_tool


def create_read_bookkeeping_transaction_tool(user_id: str) -> StructuredTool:
    """創建讀取單個記帳交易工具"""

    def read_bookkeeping_transaction(id: str) -> str:
        """讀取單個記帳交易"""

        print(f"讀取記帳交易 from user_id：{user_id}, transaction_id：{id}")
        try:
            response = supabase_admin.from_("bookkeeping_transactions").select("id, category_id, amount, description, payment_method, date, created_at, updated_at").eq("id", id).eq("user_id", user_id).execute()
            
            if response.data:
                transaction_data = response.data[0]
                payment_method = transaction_data.get('payment_method', '')
                payment_info = f", Payment Method: {payment_method}" if payment_method else ""
                transaction_info = f"ID: {transaction_data.get('id', '')}, Category ID: {transaction_data.get('category_id', '')}, Amount: {transaction_data.get('amount', '')}, Description: {transaction_data.get('description', '')}{payment_info}, Date: {transaction_data.get('date', '')}, Created: {transaction_data.get('created_at', '')}, Updated: {transaction_data.get('updated_at', '')}"
                
                print(f"記帳交易內容：{transaction_info}")
                return transaction_info
            else:
                return f"找不到 ID {id} 的記帳交易"
        except Exception as e:
            print(f"讀取記帳交易時發生錯誤：{str(e)}")
            return ""

    read_bookkeeping_transaction_tool = StructuredTool.from_function(
        func=read_bookkeeping_transaction,
        name="read_bookkeeping_transaction",
        description="讀取單個記帳交易，需要提供 id 參數",
    )

    return read_bookkeeping_transaction_tool


def create_update_bookkeeping_transaction_tool(user_id: str) -> StructuredTool:
    """創建更新記帳交易工具"""

    def update_bookkeeping_transaction(id: str, category_id: str, amount: float, description: str, date: str = None, payment_method: str = None) -> bool:
        """更新記帳交易"""

        print(f"更新記帳交易：ID {id}, Category ID {category_id}, Amount {amount}, Description {description}, Date {date}, Payment Method {payment_method}")
        is_updated = False
        try:
            # 檢查指定 ID 的記錄是否存在
            response = supabase_admin.from_("bookkeeping_transactions").select("*").eq("id", id).eq("user_id", user_id).execute()
            
            if response.data:
                # 準備更新資料
                update_data = {
                    "category_id": category_id,
                    "amount": amount,
                    "description": description
                }
                
                # 如果有提供日期，則更新日期
                if date:
                    update_data["date"] = date
                
                # 如果有提供支付方式，則更新支付方式
                if payment_method is not None:  # 允許設置為空字串
                    update_data["payment_method"] = payment_method
                
                # 更新記錄
                supabase_admin.from_("bookkeeping_transactions").update(update_data).eq("id", id).eq("user_id", user_id).execute()
                is_updated = True
            else:
                print(f"找不到 ID {id} 的記帳交易")
                is_updated = False
                
        except Exception as e:
            is_updated = False
            print(f"更新記帳交易時發生錯誤：{str(e)}")

        return is_updated

    update_bookkeeping_transaction_tool = StructuredTool.from_function(
        func=update_bookkeeping_transaction,
        name="update_bookkeeping_transaction",
        description="更新記帳交易，需要提供 id、category_id、amount 和 description 參數，可選提供 date 參數（格式：YYYY-MM-DD）和 payment_method 參數（支付方式，如：現金、信用卡、轉帳等）",
    )

    return update_bookkeeping_transaction_tool


def create_delete_bookkeeping_transaction_tool(user_id: str) -> StructuredTool:
    """創建刪除記帳交易工具"""

    def delete_bookkeeping_transaction(id: str) -> str:
        """刪除指定的記帳交易"""

        print(f"刪除記帳交易：ID {id}")
        try:
            # 檢查指定 ID 的記錄是否存在且屬於該用戶
            response = supabase_admin.from_("bookkeeping_transactions").select("*").eq("id", id).eq("user_id", user_id).execute()
            
            if not response.data:
                return f"找不到 ID {id} 的記帳交易"
            
            # 刪除記錄
            result = supabase_admin.from_("bookkeeping_transactions").delete().eq("id", id).eq("user_id", user_id).execute()
            
            if result.data:
                return f"成功刪除記帳交易，ID: {id}"
            else:
                return "刪除記帳交易失敗"
                
        except Exception as e:
            error_msg = f"刪除記帳交易時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg

    delete_bookkeeping_transaction_tool = StructuredTool.from_function(
        func=delete_bookkeeping_transaction,
        name="delete_bookkeeping_transaction",
        description="刪除指定的記帳交易，需要提供 id 參數",
    )

    return delete_bookkeeping_transaction_tool


def create_search_bookkeeping_transactions_tool(user_id: str) -> StructuredTool:
    """創建搜尋記帳交易工具"""

    def search_bookkeeping_transactions(keyword: str) -> str:
        """搜尋記帳交易，根據關鍵字搜尋描述和支付方式"""

        print(f"搜尋記帳交易 from user_id：{user_id}, keyword：{keyword}")
        content = ""
        try:
            # 使用 or_ 條件進行模糊搜尋，搜尋描述或支付方式包含關鍵字的交易
            response = supabase_admin.from_("bookkeeping_transactions").select("id, category_id, amount, description, payment_method, date, created_at, updated_at").eq("user_id", user_id).or_(f"description.ilike.%{keyword}%,payment_method.ilike.%{keyword}%").execute()
            
            if response.data:
                transactions_list = []
                for transaction_data in response.data:
                    payment_method = transaction_data.get('payment_method', '')
                    payment_info = f", Payment Method: {payment_method}" if payment_method else ""
                    transaction_info = f"ID: {transaction_data.get('id', '')}, Category ID: {transaction_data.get('category_id', '')}, Amount: {transaction_data.get('amount', '')}, Description: {transaction_data.get('description', '')}{payment_info}, Date: {transaction_data.get('date', '')}, Created: {transaction_data.get('created_at', '')}, Updated: {transaction_data.get('updated_at', '')}"
                    transactions_list.append(transaction_info)
                content = "\n".join(transactions_list)

                print(f"搜尋結果：找到 {len(response.data)} 個記帳交易")
                return content
            else:
                return f"沒有找到包含關鍵字 '{keyword}' 的記帳交易"
        except Exception as e:
            print(f"搜尋記帳交易時發生錯誤：{str(e)}")
            return f"搜尋記帳交易時發生錯誤：{str(e)}"

    search_bookkeeping_transactions_tool = StructuredTool.from_function(
        func=search_bookkeeping_transactions,
        name="search_bookkeeping_transactions",
        description="搜尋記帳交易，根據關鍵字搜尋描述和支付方式，需要提供 keyword 參數",
    )

    return search_bookkeeping_transactions_tool


def create_search_bookkeeping_transactions_by_date_tool(user_id: str) -> StructuredTool:
    """創建根據日期範圍搜尋記帳交易工具"""

    def search_bookkeeping_transactions_by_date(start_date: str, end_date: str) -> str:
        """搜尋記帳交易，根據日期範圍搜尋"""

        print(f"根據日期範圍搜尋記帳交易 from user_id：{user_id}, start_date：{start_date}, end_date：{end_date}")
        content = ""
        try:
            # 使用 gte 和 lte 進行日期範圍搜尋
            response = supabase_admin.from_("bookkeeping_transactions").select("id, category_id, amount, description, payment_method, date, created_at, updated_at").eq("user_id", user_id).gte("date", start_date).lte("date", end_date).execute()
            
            if response.data:
                transactions_list = []
                for transaction_data in response.data:
                    payment_method = transaction_data.get('payment_method', '')
                    payment_info = f", Payment Method: {payment_method}" if payment_method else ""
                    transaction_info = f"ID: {transaction_data.get('id', '')}, Category ID: {transaction_data.get('category_id', '')}, Amount: {transaction_data.get('amount', '')}, Description: {transaction_data.get('description', '')}{payment_info}, Date: {transaction_data.get('date', '')}, Created: {transaction_data.get('created_at', '')}, Updated: {transaction_data.get('updated_at', '')}"
                    transactions_list.append(transaction_info)
                content = "\n".join(transactions_list)

                print(f"日期範圍搜尋結果：找到 {len(response.data)} 個記帳交易")
                print(f"搜尋結果：{content}")
                return content
            else:
                return f"沒有找到在日期範圍 '{start_date}' 到 '{end_date}' 之間的記帳交易"
        except Exception as e:
            print(f"根據日期範圍搜尋記帳交易時發生錯誤：{str(e)}")
            return f"根據日期範圍搜尋記帳交易時發生錯誤：{str(e)}"

    search_bookkeeping_transactions_by_date_tool = StructuredTool.from_function(
        func=search_bookkeeping_transactions_by_date,
        name="search_bookkeeping_transactions_by_date",
        description=
        """
        使用這工具前必須先查詢今天的日期;
        搜尋記帳紀錄，根據日期範圍搜尋，
        需要提供本地時間的 start_date 和 end_date 參數
        （格式：YYYY-MM-DD）";
        """
    )

    return search_bookkeeping_transactions_by_date_tool
