#!/usr/bin/env python
"""
範例：使用 Chatbot 類建立一個聊天機器人，並使用 RAG 回答問題
"""

import os
import sys

from backend_service.app.lib.chatbot.chatbot import Chatbot
from app.core.config import settings

def main():
    
    # 從設置中獲取 chatbot_id
    chatbot_id = settings.TEST_CHATBOT_ID
    
    if not chatbot_id:
        print("錯誤: 設置中不存在 TEST_CHATBOT_ID")
        print("請在配置中設置 TEST_CHATBOT_ID")
        sys.exit(1)
    
    try:
        # 創建並初始化聊天機器人
        print(f"正在初始化聊天機器人 (ID: {chatbot_id})...")
        chatbot = Chatbot().init(chatbot_id)
        print("聊天機器人初始化完成!")
        
        # 向聊天機器人提問
        question = "Assistbot 的創始人是誰?"
        print(f"\n問題: {question}")
        
        # 獲取回答
        response = chatbot.ask(question)
        
        # 顯示回答
        print("\n回答:")
        print(response["result"])
        
        # 顯示來源(如果有)
        if response["sources"] and len(response["sources"]) > 0:
            print("\n資訊來源:")
            for i, source in enumerate(response["sources"], 1):
                print(f"\n來源 {i}:")
                print(f"內容: {source['content'][:150]}..." if len(source['content']) > 150 else f"內容: {source['content']}")
                print(f"元數據: {source['metadata']}")
        else:
            print("\n沒有找到相關資訊來源")
            
    except Exception as e:
        print(f"錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
