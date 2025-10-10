#!/usr/bin/env python
"""
測試 Supabase 中的 match_sections 函數

此腳本用於測試調用 match_sections 存儲過程，該函數用於根據向量相似度檢索文檔片段。
"""

import os
import sys
import json
from typing import List, Dict, Any
import argparse

from langchain_openai import OpenAIEmbeddings
from chatbot_service.lib.supabase.admin import supabase_admin
from dotenv import load_dotenv

def generate_embedding(text: str) -> List[float]:
    """
    使用 OpenAI 的 API 為文本生成嵌入向量
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    return embeddings.embed_query(text)

def test_match_sections(chatbot_id: str, query_text: str, match_count: int = 5) -> List[Dict[str, Any]]:
    """
    測試 match_sections 函數
    
    Args:
        chatbot_id: Chatbot 的 UUID
        query_text: 要搜索的查詢文本
        match_count: 要返回的最大結果數
        
    Returns:
        匹配的部分列表
    """
    try:
        print(f"開始為查詢生成嵌入向量: '{query_text}'")
        query_embedding = generate_embedding(query_text)
        
        print(f"調用 match_sections 函數，chatbot_id: {chatbot_id}")
        response = supabase_admin.rpc(
            "match_sections", 
            {
                "query_embedding": query_embedding,
                "chatbot_id": chatbot_id,
                "match_count": match_count
            }
        ).execute()
        
        if not response.data:
            print("未找到匹配的結果")
            return []
            
        print(f"找到 {len(response.data)} 個匹配的結果")
        return response.data
        
    except Exception as e:
        print(f"調用 match_sections 時發生錯誤: {str(e)}")
        return []

def format_results(results: List[Dict[str, Any]]) -> None:
    """
    格式化並打印結果
    """
    if not results:
        print("\n無匹配結果")
        return
        
    print("\n匹配結果:")
    for idx, result in enumerate(results, 1):
        print(f"\n結果 #{idx}:")
        print(f"ID: {result.get('id')}")
        print(f"Chatbot ID: {result.get('chatbot_id')}")
        
        # 顯示內容，截斷過長的文本
        content = result.get('content', '')
        if len(content) > 150:
            content_preview = content[:147] + "..."
            print(f"內容 (前150字符): {content_preview}")
        else:
            print(f"內容: {content}")
        
        # 顯示元數據
        metadata = result.get('metadata', {})
        if metadata:
            print(f"元數據: {json.dumps(metadata, ensure_ascii=False, indent=2)}")
        
        # 顯示相似度分數
        similarity = result.get('similarity', 0)
        print(f"相似度: {similarity:.6f}")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='測試 Supabase match_sections 函數')
    parser.add_argument('--chatbot_id', type=str, help='Chatbot ID (如果未提供，將使用環境變數中的 TEST_CHATBOT_ID)')
    parser.add_argument('--query', type=str, default="Andrew 如何修行?", help='查詢文本 (默認為 "Andrew 如何修行?")')
    parser.add_argument('--count', type=int, default=5, help='返回的最大結果數 (默認為 5)')
    
    args = parser.parse_args()
    
    # 載入環境變數
    load_dotenv()
    
    # 獲取 chatbot ID
    chatbot_id = args.chatbot_id
    if not chatbot_id:
        chatbot_id = os.environ.get("TEST_CHATBOT_ID")
    
    if not chatbot_id:
        print("錯誤: 未提供 chatbot_id，請通過命令行參數提供或在環境變數中設置 TEST_CHATBOT_ID")
        sys.exit(1)
    
    print(f"使用 Chatbot ID: {chatbot_id}")
    print(f"查詢: '{args.query}'")
    print(f"最大結果數: {args.count}")
    
    # 執行測試並顯示結果
    results = test_match_sections(chatbot_id, args.query, args.count)
    format_results(results)

if __name__ == "__main__":
    main()
