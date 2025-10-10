from typing import List, Dict, Any, Tuple, Optional, Callable
import json

from langchain_core.tools import tool, StructuredTool
from langchain_core.messages import (
    HumanMessage, AIMessage, SystemMessage
)
from langchain_core.messages.utils import trim_messages, count_tokens_approximately
from langchain_core.documents import Document

from langchain_openai import OpenAIEmbeddings
from langchain.chat_models import init_chat_model

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

from langchain_core.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from app.lib.supabase import supabase_admin
from app.core.config import settings
from app.lib.chatbot.tools import (
    create_get_current_time_tool, 
    create_get_weekday_tool,
    get_city_time_tool,
    create_get_current_timezone_tool,
    create_get_user_current_time_tool,
    create_get_user_weekday_tool,
    create_get_current_city_tool,
    create_get_user_timezone_tool,
    create_set_user_timezone_tool,
    create_create_note_tool,
    create_read_note_tool,
    create_read_notes_tool,
    create_search_notes_tool,
    create_search_notes_by_time_tool,
    create_update_note_tool,
    create_delete_note_tool,
    create_search_notes_tool,
    create_search_memory_tool,
    create_create_bookkeeping_category_tool,
    create_read_bookkeeping_categories_tool,
    create_read_bookkeeping_category_tool,
    create_update_bookkeeping_category_tool,
    create_delete_bookkeeping_category_tool,
    create_create_bookkeeping_transaction_tool,
    create_read_bookkeeping_transactions_tool,
    create_read_bookkeeping_transaction_tool,
    create_update_bookkeeping_transaction_tool,
    create_delete_bookkeeping_transaction_tool,
    create_search_bookkeeping_transactions_tool,
    create_search_bookkeeping_transactions_by_date_tool,
    create_get_help_tool,
    create_get_user_language_tool,
    create_get_user_reminder_method_tool,
    create_set_user_language_tool,
    create_set_user_reminder_method_tool,
    create_create_reminder_tool,
    create_read_reminder_tool,
    create_read_reminders_tool,
    create_search_reminders_by_keyword_tool,
    create_search_reminder_by_time_tool,
    create_update_reminder_tool,
    create_delete_reminder_tool
)


class ChatbotBase:
    """
    基礎 Chatbot 類，封裝 langchain 相關邏輯
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
    #def __init__(self, model: str = "gpt-4o"):
        """
        初始化 Agent
        
        Args:
            model: 使用的模型名稱，支援 "gpt-4o-mini", "gpt-4o", "grok-beta"
        """

        self.user_id = None

        # 初始化 LLM
        self._init_llm(model)
        
        # 初始化 embeddings
        self._init_embeddings()
        
        # Agent 相關屬性
        self.tools: List[Any] = []
        self.checkpointer: Optional[InMemorySaver] = None
        self.agent: Optional[Any] = None
        self.prompt: Optional[str] = None
        self.response: Optional[Dict[str, Any]] = None

    def _init_llm(self, model: str) -> None:
        """
        初始化語言模型
        
        Args:
            model: 模型名稱
        """
        if model.startswith("gpt"):
            model_provider = "openai"
            api_key = settings.OPENAI_API_KEY
        else:
            raise ValueError(f"不支持的模型: {model}")

        self.llm = init_chat_model(
            model=model,
            model_provider=model_provider,
            api_key=api_key,
            #temperature=0.0,
            max_tokens=1000,  # For the response
            timeout=30,  # 30 seconds
            max_retries=3,  # 3 retries
        )

    def _init_embeddings(self) -> None:
        """初始化嵌入模型"""
        embedding_model = "text-embedding-ada-002"
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            openai_api_key=settings.OPENAI_API_KEY
        )

    def setup_agent(self, user_id: str, chatbot_name: str = "AI助手", 
        character_traits: str = None) -> None:
        """
        設置 Agent
        
        Args:
            user_id: 用戶ID
            chatbot_id: 聊天機器人ID
            chatbot_name: 聊天機器人名稱
            character_traits: 性格特徵
        """

        self.user_id = user_id

        # 創建獲取用戶時區工具
        get_user_timezone_tool = create_get_user_timezone_tool(user_id)

        # 創建設定用戶時區工具
        set_user_timezone_tool = create_set_user_timezone_tool(user_id)

        # 創建獲取用戶目前時間工具
        get_user_current_time_tool = create_get_user_current_time_tool(user_id)

        # 創建獲取用戶今天是禮拜幾工具
        get_user_weekday_tool = create_get_user_weekday_tool(user_id)

        # 創建新增提醒工具
        create_reminder_tool = create_create_reminder_tool(user_id)
        
        # 創建讀取單個提醒工具
        read_reminder_tool = create_read_reminder_tool(user_id)
        
        # 創建讀取提醒工具
        read_reminders_tool = create_read_reminders_tool(user_id)
        
        # 創建搜尋提醒工具
        search_reminders_by_keyword_tool = create_search_reminders_by_keyword_tool(user_id)
        
        # 創建根據時間範圍搜尋提醒工具
        search_reminders_by_time_tool = create_search_reminder_by_time_tool(user_id)
        
        # 創建更新提醒工具
        update_reminder_tool = create_update_reminder_tool(user_id)
        
        # 創建刪除提醒工具
        delete_reminder_tool = create_delete_reminder_tool(user_id)
        
        # 創建新增筆記工具
        create_note_tool = create_create_note_tool(user_id)

        # 創建讀取單個筆記工具
        read_note_tool = create_read_note_tool(user_id)
        
        # 創建讀取筆記工具
        read_notes_tool = create_read_notes_tool(user_id)
        
        # 創建搜尋筆記工具
        search_notes_tool = create_search_notes_tool(user_id)
        
        # 創建根據時間範圍搜尋筆記工具
        search_notes_by_time_tool = create_search_notes_by_time_tool(user_id)

        # 創建更新筆記工具
        update_note_tool = create_update_note_tool(user_id)
        
        # 創建刪除筆記工具
        delete_note_tool = create_delete_note_tool(user_id)
        
        # 創建搜索記憶體工具
        search_memory_tool = create_search_memory_tool(user_id)
        
        # 創建新增記帳類別工具
        create_bookkeeping_category_tool = create_create_bookkeeping_category_tool(user_id)
        
        # 創建讀取記帳類別工具
        read_bookkeeping_categories_tool = create_read_bookkeeping_categories_tool(user_id)
        
        # 創建讀取單個記帳類別工具
        read_bookkeeping_category_tool = create_read_bookkeeping_category_tool(user_id)
        
        # 創建更新記帳類別工具
        update_bookkeeping_category_tool = create_update_bookkeeping_category_tool(user_id)
        
        # 創建刪除記帳類別工具
        delete_bookkeeping_category_tool = create_delete_bookkeeping_category_tool(user_id)
        
        # 創建新增記帳交易工具
        create_bookkeeping_transaction_tool = create_create_bookkeeping_transaction_tool(user_id)
        
        # 創建讀取記帳交易工具
        read_bookkeeping_transactions_tool = create_read_bookkeeping_transactions_tool(user_id)
        
        # 創建讀取單個記帳交易工具
        read_bookkeeping_transaction_tool = create_read_bookkeeping_transaction_tool(user_id)
        
        # 創建更新記帳交易工具
        update_bookkeeping_transaction_tool = create_update_bookkeeping_transaction_tool(user_id)
        
        # 創建刪除記帳交易工具
        delete_bookkeeping_transaction_tool = create_delete_bookkeeping_transaction_tool(user_id)
        
        # 創建搜尋記帳交易工具
        search_bookkeeping_transactions_tool = create_search_bookkeeping_transactions_tool(user_id)
        
        # 創建根據日期範圍搜尋記帳交易工具
        search_bookkeeping_transactions_by_date_tool = create_search_bookkeeping_transactions_by_date_tool(user_id)
        
        # 創建幫助工具
        help_tool = create_get_help_tool()
        
        # 創建獲取目前所在城市工具
        get_current_city_tool = create_get_current_city_tool()
        
        # 創建獲取用戶語言工具
        get_user_language_tool = create_get_user_language_tool(user_id)

        # 創建獲取用戶提醒方式工具
        get_user_reminder_method_tool = create_get_user_reminder_method_tool(user_id)

        # 創建設定用戶語言工具
        set_user_language_tool = create_set_user_language_tool(user_id)

        # 創建設定用戶提醒方式工具
        set_user_reminder_method_tool = create_set_user_reminder_method_tool(user_id)

        # 設置工具列表
        self.tools = [
            get_user_language_tool,
            get_user_reminder_method_tool,
            set_user_language_tool,
            set_user_reminder_method_tool,
            get_user_timezone_tool,
            set_user_timezone_tool,
            get_user_current_time_tool,
            get_user_weekday_tool,
            read_reminder_tool,
            read_reminders_tool,
            search_reminders_by_keyword_tool,
            search_reminders_by_time_tool,
            create_reminder_tool,
            update_reminder_tool,
            delete_reminder_tool,
            search_memory_tool,
            read_note_tool,
            read_notes_tool,
            search_notes_tool,
            search_notes_by_time_tool,
            create_note_tool,
            update_note_tool,
            delete_note_tool,
            read_bookkeeping_category_tool,
            read_bookkeeping_categories_tool,
            create_bookkeeping_category_tool,
            update_bookkeeping_category_tool,
            delete_bookkeeping_category_tool,
            read_bookkeeping_transaction_tool,
            read_bookkeeping_transactions_tool,
            create_bookkeeping_transaction_tool,
            update_bookkeeping_transaction_tool,
            delete_bookkeeping_transaction_tool,
            search_bookkeeping_transactions_tool,
            search_bookkeeping_transactions_by_date_tool,
            get_current_city_tool,
            get_city_time_tool,
            help_tool
        ]

        # 設置提示詞
        self.prompt = f"""
        你的名字是：{chatbot_name}，
        你現在扮演的是一位智能助理，與主人進行對話，並回答主人提出的問題，
        ，給予最精確的回覆。

        你的記憶庫儲存著主人所有的筆記資料，當你無法回答主人的問題時，
        必須要先查詢記憶庫（使用 search_memory 工具），然後再進行回答。
        倘若在記憶庫中沒有找到相關資訊，那就誠實回答我不知道。
        在回答不知道前，必須先確認記憶庫中沒有記載相關資訊，然後再進行回答。
        請確保你的回答基於檢索到的記憶內容，不要編造信息。

        當主人說，某個東西，這代表他要你查詢記憶庫中的那個東西，
        例如，當他說，父親的生日，這代表他要你查詢父親的生日。

        處理時間相關的問題前，必須先查詢目前的時區，然後再查詢現在時間以及今天是禮拜幾。

        請用目前時區的時間回答主人和呼叫工具，絕對不可以使用 UTC 時間。 

        新增/修改/查詢/刪除事件時，都必須先查詢目前的時間和今天是禮拜幾，
        這樣才能判斷主人說的今天或明天所對應的確切日期。

        查詢事件時，需要實際查詢資料庫，不可以光靠過去的對話歷史來回答。

        妳只能說實話。不可以因為主人的質疑而扭曲妳的回答，
        但在回答前，必須先查詢資料已確認妳的回答是正確的。

        當要進行的動作與時間相關時，必須先確認目前的時間。  

        新增提醒時，需要先獲取目前用戶的提醒方法設定。
        新增提醒後，只需要回覆主人，敘述和提醒時間，除非主人有特別要求，不然請勿提到提醒的方法。

        當主人請你幫忙紀錄某件事時，除非有明確要求不然你需要自行判斷是要紀錄在筆記，
        或是提醒事件或是記帳。

        當主人說"多久後提醒我做某事"時，這代表要新增提醒。

        新增提醒時，需要先判斷是單次提醒或是重複性提醒。
        當主人希望新增重複性活動的提醒時，你可以使用 is_recurring=true 並設定 recurrence_rule 來建立重複性提醒。
        重複規則使用 iCalendar RRULE 格式：
        - 每日：FREQ=DAILY
        - 每週：FREQ=WEEKLY
        - 每月：FREQ=MONTHLY  
        - 每年：FREQ=YEARLY
        - 每週一到週五：FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR
        - 每週一、三、五：FREQ=WEEKLY;BYDAY=MO,WE,FR

        新增或刪除提醒時，不需要告訴主人該提醒的 id。

        當需要搜尋提醒紀錄時，必須提供搜尋的時間範圍。
        當主人要搜尋提醒時，你需要先確定搜尋的時間範圍，
        然後才可以開始搜尋提醒紀錄。

        不可以新增已經過去時間的提醒。

        呼叫工具時若得到的資料中包含UTC時間，需要自動轉換為主人的當地時間。
        
        當需要對筆記內容做更新時，需要保留原來不相關的部份，只做需要的更正，然後更新筆記內容。 

        當新增記帳交易時，需要先查詢目前可用的類別，
        然後從現有類別中選擇或需要新增類別，自動決定收支type，自動設定交易日期，
        並且可以設定支付方式，預設是不設定支付方式。
        新增或修改記帳紀錄時，倘若 payment_method 的值是英文，請使用英文小寫去紀錄。
        查詢記帳紀錄前，必須先查詢目前的時間和今天是禮拜幾，

        當主人要刪除任何紀錄時，必須要跟主人確認，確認後才可以進行刪除。

        當你需要呈現標題或表示重點時，請使用 ✅ 來顯示標題或重點，
        絕對不要使用 ** 的符號來表示標題或重點。

        當呼叫時間相關工具時，使用的參數必須是英文或數字，不要使用中文。

        """

        # 設置記憶體
        self.checkpointer = InMemorySaver()

        # 定義預處理鉤子
        def pre_model_hook(state):
            trimmed_messages = trim_messages(
                state["messages"],
                strategy="last",
                token_counter=count_tokens_approximately,
                include_system=True,
                max_tokens=2000,
                start_on="human",
                end_on=("human", "tool"),
            )

            return {"messages": [RemoveMessage(REMOVE_ALL_MESSAGES)] + trimmed_messages}

        # 創建 react agent
        self.agent = create_react_agent(
            model=self.llm, 
            tools=self.tools, 
            prompt=self.prompt, 
            checkpointer=self.checkpointer,
            pre_model_hook=pre_model_hook,
            debug=False
        )

    def invoke(self, user_message: str, thread_id: str = "default") -> Dict[str, Any]:
        """
        處理用戶問題並返回回應
        
        Args:
            user_message: 用戶消息
            thread_id: 對話線程ID
            
        Returns:
            包含回答、token使用量和來源的字典
            
        Raises:
            ValueError: 當 agent 尚未初始化時
        """
        if not self.agent:
            raise ValueError("Agent 尚未初始化，請先調用 setup_agent() 方法")
        
        # 設置配置（包含線程ID）
        config = {"configurable": {"thread_id": thread_id}}
        
        # 調用 agent 
        self.response = self.agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]}, 
            config=config
        )
        
        messages = self.response["messages"]
        token_usage = messages[-1].usage_metadata

        # 獲取 AI 回應
        ai_msg = self.response["messages"][-1].content
        
        # 構建結果
        result = {
            "result": ai_msg,
            "token_usage": token_usage
        }
                
        return result

    def add_tool(self, tool_func: Callable) -> None:
        """
        添加自定義工具
        
        Args:
            tool_func: 工具函數
        """
        self.tools.append(tool_func)

    def set_prompt(self, prompt: str) -> None:
        """
        設置自定義提示詞
        
        Args:
            prompt: 提示詞字符串
        """
        self.prompt = prompt

    def is_ready(self) -> bool:
        """
        檢查 agent 是否已準備就緒
        
        Returns:
            bool: agent 是否已初始化
        """
        return self.agent is not None

    def get_last_response(self) -> Optional[Dict[str, Any]]:
        """
        獲取最後一次回應的完整數據
        
        Returns:
            最後一次回應的數據，如果沒有則返回 None
        """
        return self.response
