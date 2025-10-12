
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.lib.supabase import supabase_admin


class UserBookkeepingManager:
    """Manager class for user bookkeeping operations"""
    
    def __init__(self, user_id: str):
        """
        Initialize UserBookkeepingManager
        
        Args:
            user_id: The user's ID
        """
        self.user_id = user_id
    
    # ==================== Category Methods ====================
    
    def create_bookkeeping_category(self, name: str, type: str) -> str:
        """
        Create a new bookkeeping category
        
        Args:
            name: Category name
            type: Category type ('income' or 'expense')
            
        Returns:
            str: Success or error message
        """
        print(f"添加記帳類別：Name {name}, Type {type}")
        try:
            # Validate type
            if type not in ['income', 'expense']:
                return f"類型必須是 'income' 或 'expense'，當前類型：{type}"
            
            # Check if category already exists
            response = supabase_admin.from_("bookkeeping_categories").select("*").eq("user_id", self.user_id).eq("name", name).eq("type", type).execute()
            
            if response.data:
                return f"已存在相同的記帳類別：{name} ({type})"
            
            # Insert new record
            result = supabase_admin.from_("bookkeeping_categories").insert({
                "user_id": self.user_id,
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
    
    def read_bookkeeping_categories(self) -> str:
        """
        Read all bookkeeping categories
        
        Returns:
            str: Formatted categories list or error message
        """
        print(f"讀取記帳類別 from user_id：{self.user_id}")
        try:
            response = supabase_admin.from_("bookkeeping_categories").select("id, name, type").eq("user_id", self.user_id).execute()
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
    
    def read_bookkeeping_category(self, id: str) -> str:
        """
        Read a single bookkeeping category
        
        Args:
            id: Category ID
            
        Returns:
            str: Category information or error message
        """
        print(f"讀取記帳類別 from user_id：{self.user_id}, category_id：{id}")
        try:
            response = supabase_admin.from_("bookkeeping_categories").select("id, name, type").eq("id", id).eq("user_id", self.user_id).execute()
            
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
    
    def update_bookkeeping_category(self, id: str, name: str, type: str) -> bool:
        """
        Update a bookkeeping category
        
        Args:
            id: Category ID
            name: New category name
            type: New category type ('income' or 'expense')
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        print(f"更新記帳類別：ID {id}, Name {name}, Type {type}")
        try:
            # Validate type
            if type not in ['income', 'expense']:
                print(f"類型必須是 'income' 或 'expense'，當前類型：{type}")
                return False
            
            # Check if record exists
            response = supabase_admin.from_("bookkeeping_categories").select("*").eq("id", id).eq("user_id", self.user_id).execute()
            
            if response.data:
                # Update record
                supabase_admin.from_("bookkeeping_categories").update({
                    "name": name,
                    "type": type
                }).eq("id", id).eq("user_id", self.user_id).execute()
                return True
            else:
                print(f"找不到 ID {id} 的記帳類別")
                return False
                
        except Exception as e:
            print(f"更新記帳類別時發生錯誤：{str(e)}")
            return False
    
    def delete_bookkeeping_category(self, id: str) -> str:
        """
        Delete a bookkeeping category
        
        Args:
            id: Category ID
            
        Returns:
            str: Success or error message
        """
        print(f"刪除記帳類別：ID {id}")
        try:
            # Check if record exists
            response = supabase_admin.from_("bookkeeping_categories").select("*").eq("id", id).eq("user_id", self.user_id).execute()
            
            if not response.data:
                return f"找不到 ID {id} 的記帳類別"
            
            # Delete record
            result = supabase_admin.from_("bookkeeping_categories").delete().eq("id", id).eq("user_id", self.user_id).execute()
            
            if result.data:
                return f"成功刪除記帳類別，ID: {id}"
            else:
                return "刪除記帳類別失敗"
                
        except Exception as e:
            error_msg = f"刪除記帳類別時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg
    
    # ==================== Transaction Methods ====================
    
    def create_bookkeeping_transaction(self, category_id: str, amount: float, description: str, 
                                      date: Optional[str] = None, payment_method: Optional[str] = None) -> str:
        """
        Create a new bookkeeping transaction
        
        Args:
            category_id: Category ID
            amount: Transaction amount
            description: Transaction description
            date: Transaction date (YYYY-MM-DD format), optional
            payment_method: Payment method, optional
            
        Returns:
            str: Success or error message
        """
        print(f"添加記帳交易：Category ID {category_id}, Amount {amount}, Description {description}, Date {date}, Payment Method {payment_method}")
        try:
            # Check if category exists
            category_response = supabase_admin.from_("bookkeeping_categories").select("*").eq("id", category_id).eq("user_id", self.user_id).execute()
            
            if not category_response.data:
                return f"找不到 ID {category_id} 的記帳類別"
            
            # Prepare transaction data
            transaction_data = {
                "user_id": self.user_id,
                "category_id": category_id,
                "amount": amount,
                "description": description
            }
            
            # Add optional fields
            if date:
                transaction_data["date"] = date
            
            if payment_method:
                transaction_data["payment_method"] = payment_method
            
            # Insert new record
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
    
    def read_bookkeeping_transactions(self) -> str:
        """
        Read all bookkeeping transactions with category information
        
        Returns:
            str: Formatted transactions list with category info or error message
        """
        print(f"讀取記帳交易 from user_id：{self.user_id}")
        try:
            # Query transactions with category info using foreign key relationship
            response = supabase_admin.from_("bookkeeping_transactions").select(
                "id, category_id, amount, description, payment_method, date, created_at, updated_at, bookkeeping_categories(name, type)"
            ).eq("user_id", self.user_id).execute()
            
            if response.data:
                transactions_list = []
                for transaction_data in response.data:
                    payment_method = transaction_data.get('payment_method', '')
                    payment_info = f", Payment Method: {payment_method}" if payment_method else ""
                    
                    # Get category info
                    category_info = transaction_data.get('bookkeeping_categories', {})
                    category_name = category_info.get('name', 'Unknown') if category_info else 'Unknown'
                    category_type = category_info.get('type', 'unknown') if category_info else 'unknown'
                    type_display = "收入" if category_type == 'income' else "支出" if category_type == 'expense' else category_type
                    
                    transaction_info = f"ID: {transaction_data.get('id', '')}, Category: {category_name} ({type_display}), Amount: {transaction_data.get('amount', '')}, Description: {transaction_data.get('description', '')}{payment_info}, Date: {transaction_data.get('date', '')}, Created: {transaction_data.get('created_at', '')}, Updated: {transaction_data.get('updated_at', '')}"
                    transactions_list.append(transaction_info)
                content = "\n".join(transactions_list)
                
                print(f"記帳交易內容：{content}")
                return content
            else:
                return "No bookkeeping transactions found"
        except Exception as e:
            print(f"讀取記帳交易時發生錯誤：{str(e)}")
            return ""
    
    def read_bookkeeping_transaction(self, id: str) -> str:
        """
        Read a single bookkeeping transaction with category information
        
        Args:
            id: Transaction ID
            
        Returns:
            str: Transaction information with category info or error message
        """
        print(f"讀取記帳交易 from user_id：{self.user_id}, transaction_id：{id}")
        try:
            # Query transaction with category info
            response = supabase_admin.from_("bookkeeping_transactions").select(
                "id, category_id, amount, description, payment_method, date, created_at, updated_at, bookkeeping_categories(name, type)"
            ).eq("id", id).eq("user_id", self.user_id).execute()
            
            if response.data:
                transaction_data = response.data[0]
                payment_method = transaction_data.get('payment_method', '')
                payment_info = f", Payment Method: {payment_method}" if payment_method else ""
                
                # Get category info
                category_info = transaction_data.get('bookkeeping_categories', {})
                category_name = category_info.get('name', 'Unknown') if category_info else 'Unknown'
                category_type = category_info.get('type', 'unknown') if category_info else 'unknown'
                type_display = "收入" if category_type == 'income' else "支出" if category_type == 'expense' else category_type
                
                transaction_info = f"ID: {transaction_data.get('id', '')}, Category: {category_name} ({type_display}), Amount: {transaction_data.get('amount', '')}, Description: {transaction_data.get('description', '')}{payment_info}, Date: {transaction_data.get('date', '')}, Created: {transaction_data.get('created_at', '')}, Updated: {transaction_data.get('updated_at', '')}"
                
                print(f"記帳交易內容：{transaction_info}")
                return transaction_info
            else:
                return f"找不到 ID {id} 的記帳交易"
        except Exception as e:
            print(f"讀取記帳交易時發生錯誤：{str(e)}")
            return ""
    
    def update_bookkeeping_transaction(self, id: str, category_id: str, amount: float, 
                                      description: str, date: Optional[str] = None, 
                                      payment_method: Optional[str] = None) -> bool:
        """
        Update a bookkeeping transaction
        
        Args:
            id: Transaction ID
            category_id: New category ID
            amount: New amount
            description: New description
            date: New date (YYYY-MM-DD format), optional
            payment_method: New payment method, optional
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        print(f"更新記帳交易：ID {id}, Category ID {category_id}, Amount {amount}, Description {description}, Date {date}, Payment Method {payment_method}")
        try:
            # Check if record exists
            response = supabase_admin.from_("bookkeeping_transactions").select("*").eq("id", id).eq("user_id", self.user_id).execute()
            
            if response.data:
                # Prepare update data
                update_data = {
                    "category_id": category_id,
                    "amount": amount,
                    "description": description
                }
                
                # Add optional fields
                if date:
                    update_data["date"] = date
                
                if payment_method is not None:  # Allow setting to empty string
                    update_data["payment_method"] = payment_method
                
                # Update record
                supabase_admin.from_("bookkeeping_transactions").update(update_data).eq("id", id).eq("user_id", self.user_id).execute()
                return True
            else:
                print(f"找不到 ID {id} 的記帳交易")
                return False
                
        except Exception as e:
            print(f"更新記帳交易時發生錯誤：{str(e)}")
            return False
    
    def delete_bookkeeping_transaction(self, id: str) -> str:
        """
        Delete a bookkeeping transaction
        
        Args:
            id: Transaction ID
            
        Returns:
            str: Success or error message
        """
        print(f"刪除記帳交易：ID {id}")
        try:
            # Check if record exists
            response = supabase_admin.from_("bookkeeping_transactions").select("*").eq("id", id).eq("user_id", self.user_id).execute()
            
            if not response.data:
                return f"找不到 ID {id} 的記帳交易"
            
            # Delete record
            result = supabase_admin.from_("bookkeeping_transactions").delete().eq("id", id).eq("user_id", self.user_id).execute()
            
            if result.data:
                return f"成功刪除記帳交易，ID: {id}"
            else:
                return "刪除記帳交易失敗"
                
        except Exception as e:
            error_msg = f"刪除記帳交易時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg
    
    # ==================== Search Methods ====================
    
    def search_bookkeeping_transactions(self, keyword: str) -> str:
        """
        Search bookkeeping transactions by keyword with category information
        
        Args:
            keyword: Search keyword
            
        Returns:
            str: Formatted transactions list with category info or error message
        """
        print(f"搜尋記帳交易 from user_id：{self.user_id}, keyword：{keyword}")
        try:
            # Search in description and payment_method fields with category info
            response = supabase_admin.from_("bookkeeping_transactions").select(
                "id, category_id, amount, description, payment_method, date, created_at, updated_at, bookkeeping_categories(name, type)"
            ).eq("user_id", self.user_id).or_(f"description.ilike.%{keyword}%,payment_method.ilike.%{keyword}%").execute()
            
            if response.data:
                transactions_list = []
                for transaction_data in response.data:
                    payment_method = transaction_data.get('payment_method', '')
                    payment_info = f", Payment Method: {payment_method}" if payment_method else ""
                    
                    # Get category info
                    category_info = transaction_data.get('bookkeeping_categories', {})
                    category_name = category_info.get('name', 'Unknown') if category_info else 'Unknown'
                    category_type = category_info.get('type', 'unknown') if category_info else 'unknown'
                    type_display = "收入" if category_type == 'income' else "支出" if category_type == 'expense' else category_type
                    
                    transaction_info = f"ID: {transaction_data.get('id', '')}, Category: {category_name} ({type_display}), Amount: {transaction_data.get('amount', '')}, Description: {transaction_data.get('description', '')}{payment_info}, Date: {transaction_data.get('date', '')}, Created: {transaction_data.get('created_at', '')}, Updated: {transaction_data.get('updated_at', '')}"
                    transactions_list.append(transaction_info)
                content = "\n".join(transactions_list)
                
                print(f"搜尋結果：找到 {len(response.data)} 個記帳交易")
                return content
            else:
                return f"沒有找到包含關鍵字 '{keyword}' 的記帳交易"
        except Exception as e:
            print(f"搜尋記帳交易時發生錯誤：{str(e)}")
            return f"搜尋記帳交易時發生錯誤：{str(e)}"
    
    def search_bookkeeping_transactions_by_date(self, start_date: str, end_date: str) -> str:
        """
        Search bookkeeping transactions by date range with category information
        
        Args:
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            
        Returns:
            str: Formatted transactions list with category info or error message
        """
        print(f"根據日期範圍搜尋記帳交易 from user_id：{self.user_id}, start_date：{start_date}, end_date：{end_date}")
        try:
            # Search by date range with category info
            response = supabase_admin.from_("bookkeeping_transactions").select(
                "id, category_id, amount, description, payment_method, date, created_at, updated_at, bookkeeping_categories(name, type)"
            ).eq("user_id", self.user_id).gte("date", start_date).lte("date", end_date).execute()
            
            if response.data:
                transactions_list = []
                for transaction_data in response.data:
                    payment_method = transaction_data.get('payment_method', '')
                    payment_info = f", Payment Method: {payment_method}" if payment_method else ""
                    
                    # Get category info
                    category_info = transaction_data.get('bookkeeping_categories', {})
                    category_name = category_info.get('name', 'Unknown') if category_info else 'Unknown'
                    category_type = category_info.get('type', 'unknown') if category_info else 'unknown'
                    type_display = "收入" if category_type == 'income' else "支出" if category_type == 'expense' else category_type
                    
                    transaction_info = f"ID: {transaction_data.get('id', '')}, Category: {category_name} ({type_display}), Amount: {transaction_data.get('amount', '')}, Description: {transaction_data.get('description', '')}{payment_info}, Date: {transaction_data.get('date', '')}, Created: {transaction_data.get('created_at', '')}, Updated: {transaction_data.get('updated_at', '')}"
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
