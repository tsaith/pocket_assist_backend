from langchain_core.tools import StructuredTool

from app.lib.user_bookkeeping_manager import UserBookkeepingManager


def create_create_bookkeeping_category_tool(user_id: str) -> StructuredTool:
    """創建添加記帳類別工具"""

    def create_bookkeeping_category(name: str, type: str) -> str:
        """添加新的記帳類別"""
        manager = UserBookkeepingManager(user_id)
        return manager.create_bookkeeping_category(name, type)

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
        manager = UserBookkeepingManager(user_id)
        return manager.read_bookkeeping_categories()

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
        manager = UserBookkeepingManager(user_id)
        return manager.read_bookkeeping_category(id)

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
        manager = UserBookkeepingManager(user_id)
        return manager.update_bookkeeping_category(id, name, type)

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
        manager = UserBookkeepingManager(user_id)
        return manager.delete_bookkeeping_category(id)

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
        manager = UserBookkeepingManager(user_id)
        return manager.create_bookkeeping_transaction(category_id, amount, description, date, payment_method)

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
        manager = UserBookkeepingManager(user_id)
        return manager.read_bookkeeping_transactions()

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
        manager = UserBookkeepingManager(user_id)
        return manager.read_bookkeeping_transaction(id)

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
        manager = UserBookkeepingManager(user_id)
        return manager.update_bookkeeping_transaction(id, category_id, amount, description, date, payment_method)

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
        manager = UserBookkeepingManager(user_id)
        return manager.delete_bookkeeping_transaction(id)

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
        manager = UserBookkeepingManager(user_id)
        return manager.search_bookkeeping_transactions(keyword)

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
        manager = UserBookkeepingManager(user_id)
        return manager.search_bookkeeping_transactions_by_date(start_date, end_date)

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
