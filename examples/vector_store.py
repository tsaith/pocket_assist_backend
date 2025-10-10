#!/usr/bin/env python
"""
測試 Supabase 的 match_sections 函數和SupabaseVectorStore檢索器
"""

import os
import sys
from pprint import pprint
from dotenv import load_dotenv

# 從父目錄導入模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot_service.lib.supabase.admin import supabase_admin
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.supabase import SupabaseVectorStore

def main():
    # 加載環境變數
    load_dotenv()
    
    # 從環境變數中獲取 chatbot_id
    chatbot_id = os.environ.get("TEST_CHATBOT_ID")
    
    if not chatbot_id:
        print("錯誤: 環境變數中不存在 TEST_CHATBOT_ID")
        print("請在.env文件或環境變數中設置 TEST_CHATBOT_ID")
        sys.exit(1)
        
    print(f"正在測試 match_sections 函數 (chatbot_id: {chatbot_id})...")
    
    try:
        # 創建嵌入模型
        embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        
        # 測試查詢
        query = "Assistbot 的創始人是誰?"
        print(f"查詢: {query}")
        
        # 測試 1: 直接調用 match_sections 函數
        print("\n=== 測試 1: 直接調用 match_sections 函數 ===")
        # 生成查詢的嵌入向量
        query_embedding = embeddings.embed_query(query)
        print(f"生成的嵌入向量長度: {len(query_embedding)}")
        
        # 直接調用 match_sections 函數
        print("調用 match_sections 函數...")
        response = supabase_admin.rpc(
            "match_sections", 
            {
                "query_embedding": query_embedding,
                "chatbot_id": chatbot_id,
                "match_count": 5
            }
        ).execute()
        
        # 檢查回應
        if response.data:
            print(f"找到 {len(response.data)} 個匹配結果:")
            for i, item in enumerate(response.data, 1):
                print(f"\n結果 {i}:")
                print(f"內容: {item.get('content', '')[:150]}..." if len(item.get('content', '')) > 150 else f"內容: {item.get('content', '')}")
                print(f"元數據: {item.get('metadata', {})}")
                print(f"相似度: {item.get('similarity', 0)}")
        else:
            print("沒有找到匹配結果")
            
        # 測試 2: 使用 SupabaseVectorStore 和檢索器
        print("\n=== 測試 2: 使用 SupabaseVectorStore 和檢索器 ===")
        # 初始化 Supabase 向量存儲
        vector_store = SupabaseVectorStore(
            embedding=embeddings,
            client=supabase_admin,
            table_name="document_sections",
            query_name="match_sections",
        )
        
        # 使用過濾器創建檢索器
        retriever = vector_store.as_retriever(
            search_kwargs={
                "k": 5,
                "filter": {"chatbot_id": chatbot_id}
            }
        )
        
        # 執行檢索
        print("使用檢索器進行搜索...")
        docs = retriever.get_relevant_documents(query)
        
        # 檢查結果
        if docs:
            print(f"找到 {len(docs)} 個匹配結果:")
            for i, doc in enumerate(docs, 1):
                print(f"\n結果 {i}:")
                print(f"內容: {doc.page_content[:150]}..." if len(doc.page_content) > 150 else f"內容: {doc.page_content}")
                print(f"元數據: {doc.metadata}")
        else:
            print("沒有找到匹配結果")
            
    except Exception as e:
        print(f"錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 