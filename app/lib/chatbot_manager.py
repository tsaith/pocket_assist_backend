import time
import threading
from typing import Dict, Optional
from datetime import datetime, timedelta

from app.lib.chatbot import Chatbot
from app.lib.supabase import supabase_admin
from app.core.config import settings

class ChatbotManager:
    """
    Class for managing multiple chatbot instances, providing get, create, and cleanup functions
    """
    def __init__(self):
        """Initialize ChatbotManager"""
        # key: chatbot_id, value: (chatbot instance, last_used_time)
        self.chatbots: Dict[str, tuple] = {}
        
        # Thread lock to ensure thread safety
        self.lock = threading.RLock()
        
        # Cleanup configuration
        self.max_idle_time = 86400  # Instances unused for 24 hours will be cleaned up
        self.cleanup_interval = 3600  # Cleanup thread checks every 1 hour
        
        # Cleanup thread control
        self._cleanup_thread = None
        self._stop_cleanup_thread = threading.Event()
        
        # Automatically start cleanup thread
        self.start_cleanup_thread()

    def get_chatbot_id_by_linebot_id(self, linebot_id: str) -> Optional[str]:
        """
        Get corresponding chatbot_id through linebot_id
        
        Args:
            linebot_id: LINE bot ID
            
        Returns:
            str: chatbot_id, returns None if not found
        """
        try:
            response = supabase_admin.table('linebots').select('chatbot_id').eq('id', linebot_id).single().execute()
            
            if not response.data:
                print(f"Cannot find corresponding chatbot, linebot_id: {linebot_id}")
                return None
                
            return str(response.data['chatbot_id'])
            
        except Exception as e:
            print(f"Error occurred while getting chatbot_id through linebot_id: {str(e)}")
            return None

    def get_linebot_id_by_chatbot_id(self, chatbot_id: str) -> Optional[str]:
        """
        Get corresponding linebot_id through chatbot_id
        
        Args:
            chatbot_id: Chatbot ID
            
        Returns:
            str: linebot_id, returns None if not found
        """
        try:
            response = supabase_admin.table('linebots').select('id').eq('chatbot_id', chatbot_id).single().execute()
            
            if not response.data:
                print(f"Cannot find corresponding linebot, chatbot_id: {chatbot_id}")
                return None
                
            return str(response.data['id'])
            
        except Exception as e:
            print(f"Error occurred while getting linebot_id through chatbot_id: {str(e)}")
            return None

    def get_user_id_by_chatbot_id(self, chatbot_id: str) -> Optional[str]:
        """
        Get corresponding user_id through chatbot_id
        
        Args:
            chatbot_id: Chatbot ID
            
        Returns:
            str: user_id, returns None if not found
        """
        try:
            response = supabase_admin.table('chatbots').select('user_id').eq('id', chatbot_id).single().execute()
            
            if not response.data:
                print(f"Cannot find corresponding user_id, chatbot_id: {chatbot_id}")
                return None
                
            return str(response.data['user_id'])
            
        except Exception as e:
            print(f"Error occurred while getting user_id through chatbot_id: {str(e)}")
            return None

    def get_chatbot(self, chatbot_id: str) -> Chatbot:
        """
        Get chatbot instance with specified ID, create new instance if not exists
        
        Args:
            chatbot_id: Chatbot ID
            
        Returns:
            Chatbot: Chatbot instance
            
        Raises:
            ValueError: If creating chatbot instance fails
        """
        current_time = time.time()
        
        with self.lock:
            # Check if chatbot with this ID already exists
            if chatbot_id in self.chatbots:
                chatbot, _ = self.chatbots[chatbot_id]
                # Update last used time
                self.chatbots[chatbot_id] = (chatbot, current_time)
                return chatbot
            
            # Create new chatbot instance
            try:
                print(f"Creating new chatbot instance (ID: {chatbot_id})")
                chatbot = Chatbot()
                chatbot.init(chatbot_id)
                self.chatbots[chatbot_id] = (chatbot, current_time)
                return chatbot
            except Exception as e:
                error_msg = f"Failed to create chatbot instance (ID: {chatbot_id}): {str(e)}"
                print(error_msg)
                raise ValueError(error_msg)

    def remove_chatbot(self, chatbot_id: str) -> bool:
        """
        Remove chatbot with specified ID from manager
        
        Args:
            chatbot_id: Chatbot ID
            
        Returns:
            bool: Whether removal was successful
        """
        with self.lock:
            if chatbot_id in self.chatbots:
                del self.chatbots[chatbot_id]
                print(f"Removed chatbot (ID: {chatbot_id})")
                return True
            return False

    def reset_chatbot(self, chatbot_id: str) -> bool:
        """
        Reinitialize specified chatbot
        
        Args:
            chatbot_id: Chatbot ID
            
        Returns:
            bool: Whether reinitialization was successful
        """
        with self.lock:
            if chatbot_id in self.chatbots:
                try:
                    print(f"Reinitializing chatbot (ID: {chatbot_id})")
                    chatbot, _ = self.chatbots[chatbot_id]
                    chatbot.init(chatbot_id)
                    current_time = time.time()
                    self.chatbots[chatbot_id] = (chatbot, current_time)
                    print(f"Chatbot reinitialization successful (ID: {chatbot_id})")
                    return True
                except Exception as e:
                    error_msg = f"Failed to reinitialize chatbot (ID: {chatbot_id}): {str(e)}"
                    print(error_msg)
                    return False
            else:
                # Chatbot doesn't exist, no operation performed
                return False

    def cleanup_idle_chatbots(self):
        """
        Clean up idle chatbot instances
        
        Returns:
            int: Number of chatbots cleaned up
        """
        current_time = time.time()
        chatbot_ids_to_remove = []
        
        with self.lock:
            for chatbot_id, (_, last_used_time) in self.chatbots.items():
                # If exceeds maximum idle time, mark for removal
                if current_time - last_used_time > self.max_idle_time:
                    chatbot_ids_to_remove.append(chatbot_id)
            
            # Remove idle instances
            for chatbot_id in chatbot_ids_to_remove:
                del self.chatbots[chatbot_id]
                print(f"Cleaned up idle chatbot (ID: {chatbot_id})")
        
        if chatbot_ids_to_remove:
            print(f"Cleaned up {len(chatbot_ids_to_remove)} idle chatbot instances")
            
        return len(chatbot_ids_to_remove)

    def _cleanup_thread_task(self):
        """Cleanup thread task function"""
        while not self._stop_cleanup_thread.is_set():
            # Execute cleanup
            self.cleanup_idle_chatbots()
            # Wait for specified interval while checking stop signal
            self._stop_cleanup_thread.wait(self.cleanup_interval)

    def start_cleanup_thread(self):
        """Start automatic cleanup thread"""
        if self._cleanup_thread is not None and self._cleanup_thread.is_alive():
            print("Cleanup thread is already running")
            return
        
        self._stop_cleanup_thread.clear()
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_thread_task,
            daemon=True,
            name="ChatbotCleanupThread"
        )
        self._cleanup_thread.start()
        print("Started chatbot automatic cleanup thread")

    def stop_cleanup_thread(self):
        """Stop automatic cleanup thread"""
        if self._cleanup_thread is not None and self._cleanup_thread.is_alive():
            self._stop_cleanup_thread.set()
            self._cleanup_thread.join(timeout=2.0)
            print("Stopped chatbot automatic cleanup thread")
        else:
            print("Cleanup thread is not running")

    def get_status(self) -> Dict:
        """Get manager status information"""
        with self.lock:
            return {
                "active_chatbots": len(self.chatbots),
                "chatbot_ids": list(self.chatbots.keys()),
                "cleanup_thread_active": self._cleanup_thread is not None and self._cleanup_thread.is_alive()
            }

    def __del__(self):
        """Destructor to ensure cleanup thread stops"""
        self.stop_cleanup_thread()

# Singleton pattern
chatbot_manager = ChatbotManager()