#!/usr/bin/env python
"""
測試修改後的Chatbot類的ReAct agent功能
"""

import os
import sys
from dotenv import load_dotenv

# 從父目錄導入模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend_service.app.lib.chatbot.chatbot import Chatbot

def main():
    # 加載環境變數
    load_dotenv()
    
    # 從環境變數中獲取 chatbot_id
    chatbot_id = os.environ.get("TEST_CHATBOT_ID")
    
    if not chatbot_id:
        print("錯誤: 環境變數中不存在 TEST_CHATBOT_ID")
        print("請在.env文件或環境變數中設置 TEST_CHATBOT_ID")
        sys.exit(1)
    
    try:
        # 創建並初始化聊天機器人
        print(f"正在初始化聊天機器人 (ID: {chatbot_id})...")
        chatbot = Chatbot().init(chatbot_id)
        print("聊天機器人初始化完成!")
        
        # 用於存儲對話線程ID
        thread_id = "test-thread-123"
        
        # 向聊天機器人提問
        questions = [
            "Assistbot 的創始人是誰?",
            "你能告訴我關於AI產品的信息嗎?",
            "你是誰開發的?",
        ]
        
        # 與機器人進行多輪對話
        for i, question in enumerate(questions, 1):
            print(f"\n問題 {i}: {question}")
            
            # 獲取回答
            response = chatbot.ask(question, thread_id=thread_id)
            
            # 顯示回答
            print(f"\n回答 {i}:")
            print(response["result"])
            
    except Exception as e:
        print(f"錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 