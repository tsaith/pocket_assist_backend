from typing import Dict, Any, Optional
from datetime import datetime
from app.lib.supabase.admin import supabase_admin

async def get_user_id(chatbot_id: str) -> str:
    try:
        response = supabase_admin.table('chatbots').select('user_id').eq('id', chatbot_id).single().execute()
        return response.data.get('user_id')

    except Exception as error:
        print(f'Error getting user_id: {error}')
        raise error

async def save_chat_message(
    chatbot_id: str,
    user_id: str,
    platform: str,
    sender: str,  # 'human' or 'bot'
    content: str,
    meta_data: Dict[str, Any] = {}
) -> None:
    """
    Save chat message to Supabase chat_messages table
    
    Args:
        chatbot_id: The ID of the chatbot
        user_id: The visitor/thread ID
        platform: The platform (e.g., 'app', 'line', 'unknown')
        sender: The sender type ('human' or 'bot')
        content: The message content
        meta_data: Additional metadata for the message
    """
    try:

        print(f"chatbot_id: {chatbot_id}, user_id: {user_id}, platform: {platform}, sender: {sender}, content: {content}, meta_data: {meta_data}")

        # Insert chat message into database
        response = supabase_admin.table('chat_messages').insert({
            'chatbot_id': chatbot_id,
            'user_id': user_id,
            'platform': platform,
            'sender': sender,
            'content': content,
            'meta_data': meta_data,
            'created_at': datetime.utcnow().isoformat()
        }).execute()

        if not len(response.data) > 0:
            print(f'Error saving chat message!')

    except Exception as error:
        print(f'Error saving chat message: {error}')
        raise error


async def save_token_usage(
    chatbot_id: str,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    input_token_details: Dict[str, Any] = {},
    output_token_details: Dict[str, Any] = {}
) -> None:
    """
    Save token usage to Supabase token_usage table
    
    Args:
        chatbot_id: The ID of the chatbot
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens used
        total_tokens: Total number of tokens used
        input_token_details: Detailed breakdown of input token usage
        output_token_details: Detailed breakdown of output token usage
    """
    try:
        # First get the chatbot info to find the user_id
        response = supabase_admin.table('chatbots').select('user_id').eq('id', chatbot_id).single().execute()
        user_id = response.data.get('user_id')

        # Insert token usage into database
        response = supabase_admin.table('token_usage').insert({
            'user_id': user_id,
            'chatbot_id': chatbot_id,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'input_token_details': input_token_details,
            'output_token_details': output_token_details,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }).execute()

        if not len(response.data) > 0:
            print(f'Error saving token usage!')
            
    except Exception as error:
        print(f'Error saving token usage: {error}')
        raise error
