from typing import List, Dict, Any, Tuple, Optional
import asyncio
from datetime import datetime

from app.lib.chatbot.chatbot_base import ChatbotBase
from app.lib.supabase import supabase_admin
from app.lib.chatbot.linebot import Linebot
from app.lib.utils import save_chat_message, save_token_usage
from app.lib.credit_manager import CreditManager

class Chatbot(ChatbotBase):
    """
    Chatbot class that inherits from Agent and adds chatbot-specific functionality
    """

    #def __init__(self, model: str = "gpt-4o"):
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize chatbot
        
        Args:
            chatbot_id: Chatbot ID
            model: Model name to use
        """
        # Initialize parent class Agent
        super().__init__(model)

        self.user_id = None

        # Chatbot-specific attributes
        self.chatbot_id = None
        self.chatbot_data = None

        # Cache attributes
        self.chatbot_info: Optional[Dict[str, Any]] = None
        self.linebot_id: Optional[str] = None
        self.linebot: Optional[Any] = None  # Use Any temporarily to avoid circular import
        self.user_id: Optional[str] = None

    def init(self, chatbot_id: str):
        """
        Initialize chatbot, get related data and set up retriever
        
        Args:
            chatbot_id: Chatbot ID
            
        Returns:
            self: Returns self to support method chaining
        """
        self.chatbot_id = chatbot_id
        # Clear cache since chatbot_id may have changed
        self.clear_cache()

        # Get chatbot data from Supabase
        response = supabase_admin.table('chatbots').select('*').eq('id', chatbot_id).single().execute()

        if not response or not response.data:
            raise ValueError(f"Cannot find chatbot with ID {chatbot_id}")
            
        self.chatbot_data = response.data
        chatbot_name = self.chatbot_data.get('name', 'AI Assistant')
        character_traits = self.chatbot_data.get('character_traits', '')
        
        # Get user_id from chatbot data
        self.user_id = self.chatbot_data.get('user_id')
        if not self.user_id:
            raise ValueError(f"Cannot find user_id for chatbot {chatbot_id}")
        
        print(f"Initializing Chatbot: {chatbot_name}, User ID: {self.user_id}")
        
        self.setup_agent(self.user_id, chatbot_name, character_traits)
        
        return self

    async def invoke(self, user_message: str, thread_id: str = "default", platform: str = "app") -> Dict[str, Any]:
        """
        Process user message and save conversation history
        
        Args:
            user_message: User message
            thread_id: Conversation thread ID
            platform: Platform type (app, line, unknown)
            
        Returns:
            Dict: Contains response result and related information
        """
        
        try:
            # Get user_id corresponding to chatbot
            user_id = self.get_user_id()
            if not user_id:
                raise ValueError('Cannot find corresponding chatbot or user_id')

            # Query credit balance
            credit_balance = await CreditManager.get_credit_balance(user_id)

            print(f"user_id: {user_id}, chatbot_id: {self.chatbot_id}, thread_id: {thread_id}, platform: {platform}")

            # Check balance
            if credit_balance.balance <= 0:
                error_message = 'Sorry, unable to continue providing conversation service due to insufficient Credits.'
                user_message = f'Please reply {error_message}'

            # Call parent class Agent's invoke method
            response = super().invoke(user_message, thread_id)

            # If response is successful, save bot response and consume credits
            if 'result' in response:

                # Consume credits from tokens
                token_usage = response['token_usage']
                total_tokens = token_usage.get('total_tokens', 0)
                    
                try:
                    await CreditManager.consume_credits_from_tokens(user_id, total_tokens)
                except Exception as error:
                    print(f'Failed to consume credits: {error}')
                
                # Save token usage
                input_tokens = token_usage.get('input_tokens', 0)
                output_tokens = token_usage.get('output_tokens', 0)
                total_tokens = token_usage.get('total_tokens', input_tokens + output_tokens)
                input_token_details = token_usage.get('input_token_details', {})
                output_token_details = token_usage.get('output_token_details', {})
                    
                try:
                    await save_token_usage(
                        self.chatbot_id,
                        input_tokens,
                        output_tokens,
                        total_tokens,
                        input_token_details,
                        output_token_details
                    )
                except Exception as error:
                    print(f'Failed to save token usage: {error}')

            return response

        except Exception as error:
            print(f'Error in Chatbot.invoke: {error}')
            raise error
        
    def get_chatbot_info(self) -> Optional[Dict[str, Any]]:
        """
        Get chatbot basic information from Supabase
        
        Returns:
            Dict containing id, name, description, user_id, returns None if not found
        """
        if self.chatbot_info:
            return self.chatbot_info

        if not self.chatbot_id:
            print("Error: chatbot_id not set")
            return None

        try:
            response = supabase_admin.table('chatbots').select(
                'id, user_id, name, character_traits'
            ).eq('id', self.chatbot_id).single().execute()

            if not response.data:
                print(f"Cannot find chatbot_id: {self.chatbot_id}")
                return None

            # Map character_traits to description
            data = response.data
            self.chatbot_info = {
                'id': data['id'],
                'name': data['name'], 
                'description': data['character_traits'],
                'user_id': data['user_id']
            }
            return self.chatbot_info

        except Exception as e:
            print(f"Error occurred while getting chatbot information: {str(e)}")
            return None

    def get_linebot(self):
        """
        Get Linebot instance for this chatbot
        
        Returns:
            Linebot: Linebot instance
            
        Raises:
            ValueError: When associated linebot_id cannot be found
        """
        if self.linebot:
            return self.linebot
            
        linebot_id = self._get_linebot_id()
        if not linebot_id:
            raise ValueError(f'Cannot find linebot_id for chatbot_id {self.chatbot_id}')
        
        # Delayed import to avoid circular dependency
        self.linebot = Linebot(linebot_id)
        return self.linebot

    def _get_linebot_id(self) -> Optional[str]:
        """
        Get linebot_id from Supabase based on chatbot_id
        
        Returns:
            str: linebot_id, returns None if not found
        """
        if self.linebot_id:
            return self.linebot_id

        if not self.chatbot_id:
            return None

        try:
            response = supabase_admin.table('linebots').select(
                'id'
            ).eq('chatbot_id', self.chatbot_id).single().execute()

            if not response.data:
                print(f"Cannot find linebot for chatbot_id {self.chatbot_id}")
                return None

            self.linebot_id = response.data['id']
            return self.linebot_id

        except Exception as e:
            print(f"Error occurred while getting linebot_id: {str(e)}")
            return None

    def has_linebot(self) -> bool:
        """
        Check if this chatbot has an associated linebot
        
        Returns:
            bool: Whether there is an associated linebot
        """
        linebot_id = self._get_linebot_id()
        return linebot_id is not None

    def get_associated_linebot_id(self) -> Optional[str]:
        """
        Get associated linebot_id
        
        Returns:
            str: linebot_id, returns None if not found
        """
        return self._get_linebot_id()

    def is_valid(self) -> bool:
        """
        Check if chatbot exists and is valid
        
        Returns:
            bool: Whether chatbot is valid
        """
        info = self.get_chatbot_info()
        return info is not None

    def get_id(self) -> Optional[str]:
        """
        Get chatbot ID
        
        Returns:
            str: Chatbot ID
        """
        return self.chatbot_id

    def get_user_id(self) -> Optional[str]:
        """
        Get user ID who owns this chatbot
        
        Returns:
            str: User ID, returns None if not found
        """
        if self.user_id:
            return self.user_id

        try:
            chatbot_info = self.get_chatbot_info()
            if chatbot_info and chatbot_info.get('user_id'):
                self.user_id = chatbot_info['user_id']
                return self.user_id
            
            return None
        except Exception as e:
            print(f"Error occurred while getting user_id: {str(e)}")
            return None

    def clear_cache(self) -> None:
        """
        Clear cached data (for testing or when data may have changed)
        """
        self.linebot_id = None
        self.linebot = None
        self.chatbot_info = None
        self.user_id = None

