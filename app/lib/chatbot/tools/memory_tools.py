from typing import List, Tuple
from langchain_core.tools import StructuredTool

from app.lib.supabase import supabase_admin


def create_search_memory_tool(user_id: str) -> StructuredTool:
    """創建搜索記憶體工具，將用戶的所有筆記作為智能助理的記憶體內容"""

    def search_memory() -> str:
        """搜索智能助理的記憶體內容（用戶的筆記），返回所有記憶內容"""

        print(f"搜索記憶體內容 from user_id：{user_id}")
        content = ""
        try:
            # 返回所有筆記作為記憶體內容
            response = supabase_admin.from_("notes").select("id, title, content, created_at, updated_at").eq("user_id", user_id).order("updated_at", desc=True).execute()
            
            if response.data:
                memory_list = []
                for note_data in response.data:
                    # 格式化記憶內容，更符合記憶體的概念
                    memory_info = f"記憶 ID: {note_data.get('id', '')}\n標題: {note_data.get('title', '')}\n內容: {note_data.get('content', '')}\n創建時間: {note_data.get('created_at', '')}\n更新時間: {note_data.get('updated_at', '')}"
                    memory_list.append(memory_info)
                content = "\n" + "="*50 + "\n".join(memory_list) + "\n" + "="*50

                print(f"記憶體搜索結果：找到 {len(response.data)} 個記憶片段")
                return f"智能助理的記憶庫中找到 {len(response.data)} 個記憶：\n{content}"
            else:
                return "記憶庫中目前沒有任何記憶內容"
        except Exception as e:
            error_msg = f"搜索記憶體時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg

    search_memory_tool = StructuredTool.from_function(
        func=search_memory,
        name="search_memory",
        description="當無法回答主人的問題時，必須先搜索記憶庫（裡面有主人的所有筆記資料）。",
    )

    return search_memory_tool
