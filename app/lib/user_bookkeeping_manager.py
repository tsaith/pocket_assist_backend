
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
        print(f"Creating bookkeeping category: Name {name}, Type {type}")
        try:
            # Validate type
            if type not in ['income', 'expense']:
                return f"Type must be 'income' or 'expense', current type: {type}"
            
            # Check if category already exists
            response = supabase_admin.from_("bookkeeping_categories").select("*").eq("user_id", self.user_id).eq("name", name).eq("type", type).execute()
            
            if response.data:
                return f"Bookkeeping category already exists: {name} ({type})"
            
            # Insert new record
            result = supabase_admin.from_("bookkeeping_categories").insert({
                "user_id": self.user_id,
                "name": name,
                "type": type
            }).execute()
            
            if result.data:
                new_record = result.data[0]
                return f"Successfully created bookkeeping category, ID: {new_record.get('id', '')}, Name: {name}, Type: {type}"
            else:
                return "Failed to create bookkeeping category"
                
        except Exception as e:
            error_msg = f"Error occurred while creating bookkeeping category: {str(e)}"
            print(error_msg)
            return error_msg
    
    def read_bookkeeping_categories(self) -> str:
        """
        Read all bookkeeping categories
        
        Returns:
            str: Formatted categories list or error message
        """
        print(f"Reading bookkeeping categories for user: {self.user_id}")
        try:
            response = supabase_admin.from_("bookkeeping_categories").select("id, name, type").eq("user_id", self.user_id).execute()
            if response.data:
                categories_list = []
                for category_data in response.data:
                    category_info = f"ID: {category_data.get('id', '')}, Name: {category_data.get('name', '')}, Type: {category_data.get('type', '')}"
                    categories_list.append(category_info)
                content = "\n".join(categories_list)
                
                print(f"Bookkeeping categories content: {content}")
                return content
            else:
                return "No bookkeeping categories found"
        except Exception as e:
            print(f"Error occurred while reading bookkeeping categories: {str(e)}")
            return ""
    
    def read_bookkeeping_category(self, id: str) -> str:
        """
        Read a single bookkeeping category
        
        Args:
            id: Category ID
            
        Returns:
            str: Category information or error message
        """
        print(f"Reading bookkeeping category for user: {self.user_id}, category_id: {id}")
        try:
            response = supabase_admin.from_("bookkeeping_categories").select("id, name, type").eq("id", id).eq("user_id", self.user_id).execute()
            
            if response.data:
                category_data = response.data[0]
                category_info = f"ID: {category_data.get('id', '')}, Name: {category_data.get('name', '')}, Type: {category_data.get('type', '')}"
                
                print(f"Bookkeeping category content: {category_info}")
                return category_info
            else:
                return f"Bookkeeping category with ID {id} not found"
        except Exception as e:
            print(f"Error occurred while reading bookkeeping category: {str(e)}")
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
        print(f"Updating bookkeeping category: ID {id}, Name {name}, Type {type}")
        try:
            # Validate type
            if type not in ['income', 'expense']:
                print(f"Type must be 'income' or 'expense', current type: {type}")
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
                print(f"Bookkeeping category with ID {id} not found")
                return False
                
        except Exception as e:
            print(f"Error occurred while updating bookkeeping category: {str(e)}")
            return False
    
    def delete_bookkeeping_category(self, id: str) -> str:
        """
        Delete a bookkeeping category
        
        Args:
            id: Category ID
            
        Returns:
            str: Success or error message
        """
        print(f"Deleting bookkeeping category: ID {id}")
        try:
            # Check if record exists
            response = supabase_admin.from_("bookkeeping_categories").select("*").eq("id", id).eq("user_id", self.user_id).execute()
            
            if not response.data:
                return f"Bookkeeping category with ID {id} not found"
            
            # Delete record
            result = supabase_admin.from_("bookkeeping_categories").delete().eq("id", id).eq("user_id", self.user_id).execute()
            
            if result.data:
                return f"Successfully deleted bookkeeping category, ID: {id}"
            else:
                return "Failed to delete bookkeeping category"
                
        except Exception as e:
            error_msg = f"Error occurred while deleting bookkeeping category: {str(e)}"
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
        print(f"Creating bookkeeping transaction: Category ID {category_id}, Amount {amount}, Description {description}, Date {date}, Payment Method {payment_method}")
        try:
            # Check if category exists
            category_response = supabase_admin.from_("bookkeeping_categories").select("*").eq("id", category_id).eq("user_id", self.user_id).execute()
            
            if not category_response.data:
                return f"Bookkeeping category with ID {category_id} not found"
            
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
                return f"Successfully created bookkeeping transaction, ID: {new_record.get('id', '')}, Amount: {amount}, Description: {description}{payment_info}"
            else:
                return "Failed to create bookkeeping transaction"
                
        except Exception as e:
            error_msg = f"Error occurred while creating bookkeeping transaction: {str(e)}"
            print(error_msg)
            return error_msg
    
    def read_bookkeeping_transactions(self) -> str:
        """
        Read all bookkeeping transactions with category information
        
        Returns:
            str: Formatted transactions list with category info or error message
        """
        print(f"Reading bookkeeping transactions from user_id: {self.user_id}")
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
                    type_display = "Income" if category_type == 'income' else "Expense" if category_type == 'expense' else category_type
                    
                    transaction_info = f"ID: {transaction_data.get('id', '')}, Category: {category_name} ({type_display}), Amount: {transaction_data.get('amount', '')}, Description: {transaction_data.get('description', '')}{payment_info}, Date: {transaction_data.get('date', '')}, Created: {transaction_data.get('created_at', '')}, Updated: {transaction_data.get('updated_at', '')}"
                    transactions_list.append(transaction_info)
                content = "\n".join(transactions_list)
                
                print(f"Bookkeeping transaction content: {content}")
                return content
            else:
                return "No bookkeeping transactions found"
        except Exception as e:
            print(f"Error occurred while reading bookkeeping transactions: {str(e)}")
            return ""
    
    def read_bookkeeping_transaction(self, id: str) -> str:
        """
        Read a single bookkeeping transaction with category information
        
        Args:
            id: Transaction ID
            
        Returns:
            str: Transaction information with category info or error message
        """
        print(f"Reading bookkeeping transactions from user_id: {self.user_id}, transaction_id: {id}")
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
                type_display = "Income" if category_type == 'income' else "Expense" if category_type == 'expense' else category_type
                
                transaction_info = f"ID: {transaction_data.get('id', '')}, Category: {category_name} ({type_display}), Amount: {transaction_data.get('amount', '')}, Description: {transaction_data.get('description', '')}{payment_info}, Date: {transaction_data.get('date', '')}, Created: {transaction_data.get('created_at', '')}, Updated: {transaction_data.get('updated_at', '')}"
                
                print(f"Bookkeeping transaction content: {transaction_info}")
                return transaction_info
            else:
                return f"Bookkeeping transaction with ID {id} not found"
        except Exception as e:
            print(f"Error occurred while reading bookkeeping transactions: {str(e)}")
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
        print(f"Updating bookkeeping transaction: ID {id}, Category ID {category_id}, Amount {amount}, Description {description}, Date {date}, Payment Method {payment_method}")
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
                print(f"Bookkeeping transaction with ID {id} not found")
                return False
                
        except Exception as e:
            print(f"Error occurred while updating bookkeeping transaction: {str(e)}")
            return False
    
    def delete_bookkeeping_transaction(self, id: str) -> str:
        """
        Delete a bookkeeping transaction
        
        Args:
            id: Transaction ID
            
        Returns:
            str: Success or error message
        """
        print(f"Deleting bookkeeping transaction: ID {id}")
        try:
            # Check if record exists
            response = supabase_admin.from_("bookkeeping_transactions").select("*").eq("id", id).eq("user_id", self.user_id).execute()
            
            if not response.data:
                return f"Bookkeeping transaction with ID {id} not found"
            
            # Delete record
            result = supabase_admin.from_("bookkeeping_transactions").delete().eq("id", id).eq("user_id", self.user_id).execute()
            
            if result.data:
                return f"Successfully deleted bookkeeping transaction, ID: {id}"
            else:
                return "Failed to delete bookkeeping transaction"
                
        except Exception as e:
            error_msg = f"Error occurred while deleting bookkeeping transaction: {str(e)}"
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
        print(f"Searching bookkeeping transactions from user_id: {self.user_id}, keyword: {keyword}")
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
                    type_display = "Income" if category_type == 'income' else "Expense" if category_type == 'expense' else category_type
                    
                    transaction_info = f"ID: {transaction_data.get('id', '')}, Category: {category_name} ({type_display}), Amount: {transaction_data.get('amount', '')}, Description: {transaction_data.get('description', '')}{payment_info}, Date: {transaction_data.get('date', '')}, Created: {transaction_data.get('created_at', '')}, Updated: {transaction_data.get('updated_at', '')}"
                    transactions_list.append(transaction_info)
                content = "\n".join(transactions_list)
                
                print(f"Search results: found {len(response.data)} bookkeeping transactions")
                return content
            else:
                return f"No bookkeeping transactions found containing keyword '{keyword}'"
        except Exception as e:
            print(f"Error occurred while searching bookkeeping transactions: {str(e)}")
            return f"Error occurred while searching bookkeeping transactions: {str(e)}"
    
    def search_bookkeeping_transactions_by_date(self, start_date: str, end_date: str) -> str:
        """
        Search bookkeeping transactions by date range with category information
        
        Args:
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            
        Returns:
            str: Formatted transactions list with category info or error message
        """
        print(f"Searching bookkeeping transactions by date range from user_id: {self.user_id}, start_date: {start_date}, end_date: {end_date}")
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
                    type_display = "Income" if category_type == 'income' else "Expense" if category_type == 'expense' else category_type
                    
                    transaction_info = f"ID: {transaction_data.get('id', '')}, Category: {category_name} ({type_display}), Amount: {transaction_data.get('amount', '')}, Description: {transaction_data.get('description', '')}{payment_info}, Date: {transaction_data.get('date', '')}, Created: {transaction_data.get('created_at', '')}, Updated: {transaction_data.get('updated_at', '')}"
                    transactions_list.append(transaction_info)
                content = "\n".join(transactions_list)
                
                print(f"Date range search results: found {len(response.data)} bookkeeping transactions")
                print(f"Search results: {content}")
                return content
            else:
                return f"No bookkeeping transactions found in date range '{start_date}' to '{end_date}'"
        except Exception as e:
            print(f"Error occurred while searching bookkeeping transactions by date range: {str(e)}")
            return f"Error occurred while searching bookkeeping transactions by date range: {str(e)}"
