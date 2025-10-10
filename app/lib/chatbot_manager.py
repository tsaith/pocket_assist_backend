import time
import threading
from typing import Dict, Optional
from datetime import datetime, timedelta

from app.lib.chatbot import Chatbot
from app.lib.supabase import supabase_admin
from app.core.config import settings

class ChatbotManager:
    """
    管理多個聊天機器人實例的類，提供獲取、創建、回收等功能
    """
    def __init__(self):
        """初始化ChatbotManager"""
        # key: chatbot_id, value: (chatbot instance, last_used_time)
        self.chatbots: Dict[str, tuple] = {}
        
        # 線程鎖，保證線程安全
        self.lock = threading.RLock()
        
        # 清理配置
        self.max_idle_time = 1800  # 0.5 小時未使用的實例將被清理
        self.cleanup_interval = 600  # 清理線程每10分鐘檢查一次
        
        # 清理線程控制
        self._cleanup_thread = None
        self._stop_cleanup_thread = threading.Event()
        
        # 自動啟動清理線程
        self.start_cleanup_thread()

    def get_chatbot_id_by_linebot_id(self, linebot_id: str) -> Optional[str]:
        """
        通過 linebot_id 獲取對應的 chatbot_id
        
        Args:
            linebot_id: LINE 機器人ID
            
        Returns:
            str: chatbot_id，如果找不到則返回 None
        """
        try:
            response = supabase_admin.table('linebots').select('chatbot_id').eq('id', linebot_id).single().execute()
            
            if not response.data:
                print(f"找不到對應的 chatbot，linebot_id: {linebot_id}")
                return None
                
            return str(response.data['chatbot_id'])
            
        except Exception as e:
            print(f"通過 linebot_id 獲取 chatbot_id 時發生錯誤: {str(e)}")
            return None

    def get_linebot_id_by_chatbot_id(self, chatbot_id: str) -> Optional[str]:
        """
        通過 chatbot_id 獲取對應的 linebot_id
        
        Args:
            chatbot_id: 聊天機器人ID
            
        Returns:
            str: linebot_id，如果找不到則返回 None
        """
        try:
            response = supabase_admin.table('linebots').select('id').eq('chatbot_id', chatbot_id).single().execute()
            
            if not response.data:
                print(f"找不到對應的 linebot，chatbot_id: {chatbot_id}")
                return None
                
            return str(response.data['id'])
            
        except Exception as e:
            print(f"通過 chatbot_id 獲取 linebot_id 時發生錯誤: {str(e)}")
            return None

    def get_user_id_by_chatbot_id(self, chatbot_id: str) -> Optional[str]:
        """
        通過 chatbot_id 獲取對應的 user_id
        
        Args:
            chatbot_id: 聊天機器人ID
            
        Returns:
            str: user_id，如果找不到則返回 None
        """
        try:
            response = supabase_admin.table('chatbots').select('user_id').eq('id', chatbot_id).single().execute()
            
            if not response.data:
                print(f"找不到對應的 user_id，chatbot_id: {chatbot_id}")
                return None
                
            return str(response.data['user_id'])
            
        except Exception as e:
            print(f"通過 chatbot_id 獲取 user_id 時發生錯誤: {str(e)}")
            return None

    def get_chatbot(self, chatbot_id: str) -> Chatbot:
        """
        獲取指定ID的聊天機器人實例，如果不存在則創建新實例
        
        Args:
            chatbot_id: 聊天機器人ID
            
        Returns:
            Chatbot: 聊天機器人實例
            
        Raises:
            ValueError: 如果創建聊天機器人實例失敗
        """
        current_time = time.time()
        
        with self.lock:
            # 檢查是否已存在此ID的聊天機器人
            if chatbot_id in self.chatbots:
                chatbot, _ = self.chatbots[chatbot_id]
                # 更新最後使用時間
                self.chatbots[chatbot_id] = (chatbot, current_time)
                return chatbot
            
            # 創建新的聊天機器人實例
            try:
                print(f"創建新的聊天機器人實例 (ID: {chatbot_id})")
                chatbot = Chatbot()
                chatbot.init(chatbot_id)
                self.chatbots[chatbot_id] = (chatbot, current_time)
                return chatbot
            except Exception as e:
                error_msg = f"創建聊天機器人實例失敗 (ID: {chatbot_id}): {str(e)}"
                print(error_msg)
                raise ValueError(error_msg)

    def remove_chatbot(self, chatbot_id: str) -> bool:
        """
        從管理器中移除指定ID的聊天機器人
        
        Args:
            chatbot_id: 聊天機器人ID
            
        Returns:
            bool: 是否成功移除
        """
        with self.lock:
            if chatbot_id in self.chatbots:
                del self.chatbots[chatbot_id]
                print(f"已移除聊天機器人 (ID: {chatbot_id})")
                return True
            return False

    def reset_chatbot(self, chatbot_id: str) -> bool:
        """
        重新初始化指定的聊天機器人
        
        Args:
            chatbot_id: 聊天機器人ID
            
        Returns:
            bool: 是否成功重新初始化
        """
        with self.lock:
            if chatbot_id in self.chatbots:
                try:
                    print(f"重新初始化聊天機器人 (ID: {chatbot_id})")
                    chatbot, _ = self.chatbots[chatbot_id]
                    chatbot.init(chatbot_id)
                    current_time = time.time()
                    self.chatbots[chatbot_id] = (chatbot, current_time)
                    print(f"聊天機器人重新初始化成功 (ID: {chatbot_id})")
                    return True
                except Exception as e:
                    error_msg = f"重新初始化聊天機器人失敗 (ID: {chatbot_id}): {str(e)}"
                    print(error_msg)
                    return False
            else:
                # 聊天機器人不存在，不進行任何操作
                return False

    def cleanup_idle_chatbots(self):
        """
        清理閒置的聊天機器人實例
        
        Returns:
            int: 清理的聊天機器人數量
        """
        current_time = time.time()
        chatbot_ids_to_remove = []
        
        with self.lock:
            for chatbot_id, (_, last_used_time) in self.chatbots.items():
                # 如果超過最大閒置時間，則標記為待移除
                if current_time - last_used_time > self.max_idle_time:
                    chatbot_ids_to_remove.append(chatbot_id)
            
            # 移除閒置實例
            for chatbot_id in chatbot_ids_to_remove:
                del self.chatbots[chatbot_id]
                print(f"已清理閒置的聊天機器人 (ID: {chatbot_id})")
        
        if chatbot_ids_to_remove:
            print(f"清理了 {len(chatbot_ids_to_remove)} 個閒置的聊天機器人實例")
            
        return len(chatbot_ids_to_remove)

    def _cleanup_thread_task(self):
        """清理線程的任務函數"""
        while not self._stop_cleanup_thread.is_set():
            # 執行清理
            self.cleanup_idle_chatbots()
            # 等待指定間隔時間，同時檢查停止信號
            self._stop_cleanup_thread.wait(self.cleanup_interval)

    def start_cleanup_thread(self):
        """啟動自動清理線程"""
        if self._cleanup_thread is not None and self._cleanup_thread.is_alive():
            print("清理線程已在運行中")
            return
        
        self._stop_cleanup_thread.clear()
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_thread_task,
            daemon=True,
            name="ChatbotCleanupThread"
        )
        self._cleanup_thread.start()
        print("已啟動聊天機器人自動清理線程")

    def stop_cleanup_thread(self):
        """停止自動清理線程"""
        if self._cleanup_thread is not None and self._cleanup_thread.is_alive():
            self._stop_cleanup_thread.set()
            self._cleanup_thread.join(timeout=2.0)
            print("已停止聊天機器人自動清理線程")
        else:
            print("清理線程未運行")

    def get_status(self) -> Dict:
        """獲取管理器的狀態信息"""
        with self.lock:
            return {
                "active_chatbots": len(self.chatbots),
                "chatbot_ids": list(self.chatbots.keys()),
                "cleanup_thread_active": self._cleanup_thread is not None and self._cleanup_thread.is_alive()
            }

    def __del__(self):
        """析構函數，確保清理線程停止"""
        self.stop_cleanup_thread()

# 單例模式
chatbot_manager = ChatbotManager()