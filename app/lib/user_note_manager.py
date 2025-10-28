
from typing import Optional, List, Dict, Any

from app.lib.supabase import supabase_admin
from app.lib.utils.time_utils import (
    convert_user_local_to_utc_time,
    convert_utc_to_user_local_time
)

from app.core.constants import Constants

class UserNoteManager:
    """Manager class for user note operations"""
    
    def __init__(self, user_id: str):
        """
        Initialize UserNoteManager
        
        Args:
            user_id: The user's ID
        """
        self.user_id = user_id
    
    def get_note_count(self) -> int:
        """
        Get the count of user's notes
        
        Returns:
            int: Number of notes for the user
        """
        print(f"Getting note count for user_id: {self.user_id}")
        try:
            response = supabase_admin.from_("notes").select("*", count="exact").eq("user_id", self.user_id).execute()
            count = response.count if response.count is not None else 0
            print(f"Note count: {count}")
            return count
        except Exception as e:
            print(f"Error occurred while getting note count: {str(e)}")
            return 0
    
    def create_note(self, title: str, content: str) -> str:
        """
        Create a new note with subscription limit check
        
        Args:
            title: Note title
            content: Note content
            
        Returns:
            str: Success or error message
        """
        print(f"Creating note: Title {title}, Content {content}")
        try:
            # Get current notes count
            current_notes_count = self.get_note_count()
            
            if current_notes_count >= Constants.NOTES_MAX:
                print(f"Maximum notes limit exceeded: {Constants.NOTES_MAX}")
                return f"Cannot create note: maximum notes limit reached, can only create up to {Constants.NOTES_MAX} notes"
                
            # Check if note with same title already exists
            response = supabase_admin.from_("notes").select("*").eq("user_id", self.user_id).eq("title", title).execute()
            
            if response.data:
                return f"Note with same title already exists: {title}"
            
            # Insert new record
            result = supabase_admin.from_("notes").insert({
                "user_id": self.user_id,
                "title": title,
                "content": content
            }).execute()
            
            if result.data:
                new_record = result.data[0]
                return f"Successfully created note, ID: {new_record.get('id', '')}, Title: {title}, Content: {content}"
            else:
                return "Failed to create note"
                
        except Exception as e:
            error_msg = f"Error occurred while creating note: {str(e)}"
            print(error_msg)
            return error_msg
    
    def read_notes(self) -> str:
        """
        Read all notes
        
        Returns:
            str: Formatted notes list or error message
        """
        print(f"Reading all notes for user: {self.user_id}")
        try:
            response = supabase_admin.from_("notes").select("id, title, content, created_at, updated_at").eq("user_id", self.user_id).execute()
            if response.data:
                notes_list = []
                for note_data in response.data:
                    note_info = f"ID: {note_data.get('id', '')}, Title: {note_data.get('title', '')}, Content: {note_data.get('content', '')}, Created: {note_data.get('created_at', '')}, Updated: {note_data.get('updated_at', '')}"
                    notes_list.append(note_info)
                content = "\n".join(notes_list)
                
                print(f"Note content: {content}")
                return content
            else:
                return "No notes found"
        except Exception as e:
            print(f"Error occurred while reading notes: {str(e)}")
            return ""
    
    def read_note(self, id: str) -> str:
        """
        Read a single note
        
        Args:
            id: Note ID
            
        Returns:
            str: Note information or error message
        """
        print(f"Reading single note for user: {self.user_id}, note_id: {id}")
        try:
            response = supabase_admin.from_("notes").select("id, title, content, created_at, updated_at").eq("id", id).eq("user_id", self.user_id).execute()
            
            if response.data:
                note_data = response.data[0]
                note_info = f"ID: {note_data.get('id', '')}, Title: {note_data.get('title', '')}, Content: {note_data.get('content', '')}, Created: {note_data.get('created_at', '')}, Updated: {note_data.get('updated_at', '')}"
                
                print(f"Note content: {note_info}")
                return note_info
            else:
                return f"Note with ID {id} not found"
        except Exception as e:
            print(f"Error occurred while reading note: {str(e)}")
            return ""
    
    def update_note(self, id: str, title: str, content: str) -> bool:
        """
        Update a note
        
        Args:
            id: Note ID
            title: New title
            content: New content
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        print(f"Updating note: ID {id}, Title {title}, Content {content}")
        try:
            # Check if record exists
            response = supabase_admin.from_("notes").select("*").eq("id", id).eq("user_id", self.user_id).execute()
            
            if response.data:
                # Update record
                supabase_admin.from_("notes").update({
                    "title": title,
                    "content": content,
                    "updated_at": "now()"
                }).eq("id", id).eq("user_id", self.user_id).execute()
                return True
            else:
                print(f"Note with ID {id} not found")
                return False
                
        except Exception as e:
            print(f"Error occurred while updating note: {str(e)}")
            return False
    
    def delete_note(self, id: str) -> str:
        """
        Delete a note
        
        Args:
            id: Note ID
            
        Returns:
            str: Success or error message
        """
        print(f"Deleting note: ID {id}")
        try:
            # Check if record exists
            response = supabase_admin.from_("notes").select("*").eq("id", id).eq("user_id", self.user_id).execute()
            
            if not response.data:
                return f"Note with ID {id} not found"
            
            # Delete record
            result = supabase_admin.from_("notes").delete().eq("id", id).eq("user_id", self.user_id).execute()
            
            if result.data:
                return f"Successfully deleted note, ID: {id}"
            else:
                return "Failed to delete note"
                
        except Exception as e:
            error_msg = f"Error occurred while deleting note: {str(e)}"
            print(error_msg)
            return error_msg
    
    def search_notes(self, keyword: str) -> str:
        """
        Search notes by keyword in title or content
        
        Args:
            keyword: Search keyword
            
        Returns:
            str: Formatted notes list or error message
        """
        print(f"Searching notes for user: {self.user_id}, keyword: {keyword}")
        try:
            # Search in title and content fields
            response = supabase_admin.from_("notes").select("id, title, content, created_at, updated_at").eq("user_id", self.user_id).or_(f"title.ilike.%{keyword}%,content.ilike.%{keyword}%").execute()
            
            if response.data:
                notes_list = []
                for note_data in response.data:
                    note_info = f"ID: {note_data.get('id', '')}, Title: {note_data.get('title', '')}, Content: {note_data.get('content', '')}, Created: {note_data.get('created_at', '')}, Updated: {note_data.get('updated_at', '')}"
                    notes_list.append(note_info)
                content = "\n".join(notes_list)
                
                print(f"Search results: found {len(response.data)} notes")
                return content
            else:
                return f"No notes found containing keyword '{keyword}'"
        except Exception as e:
            print(f"Error occurred while searching notes: {str(e)}")
            return f"Error occurred while searching notes: {str(e)}"
    
    def search_notes_by_time(self, start_at: str, end_at: str) -> str:
        """
        Search notes by time range
        
        Args:
            start_at: Start time (user local time, format: YYYY-MM-DD HH:MM:SS)
            end_at: End time (user local time, format: YYYY-MM-DD HH:MM:SS)
            
        Returns:
            str: Formatted notes list or error message
        """
        print(f"Searching notes by time range for user: {self.user_id}, start_at: {start_at}, end_at: {end_at}")
        try:
            # Convert user local time to UTC
            start_at_utc, start_info = convert_user_local_to_utc_time(self.user_id, start_at)
            end_at_utc, end_info = convert_user_local_to_utc_time(self.user_id, end_at)
            
            # Check if conversion was successful
            if "error" in start_info or "error" in end_info:
                return f"Time conversion failed, please check time format"
            
            print(f"start_at_utc: {start_at_utc}, end_at_utc: {end_at_utc}")
            
            # Search by time range
            response = supabase_admin.from_("notes").select("id, title, content, created_at, updated_at").eq("user_id", self.user_id).or_(f"created_at.gte.{start_at_utc},created_at.lte.{end_at_utc},updated_at.gte.{start_at_utc},updated_at.lte.{end_at_utc}").execute()
            
            if response.data:
                notes_list = []
                for note_data in response.data:
                    note_info = f"ID: {note_data.get('id', '')}, Title: {note_data.get('title', '')}, Content: {note_data.get('content', '')}, Created: {note_data.get('created_at', '')}, Updated: {note_data.get('updated_at', '')}"
                    notes_list.append(note_info)
                content = "\n".join(notes_list)
                
                print(f"Time range search results: found {len(response.data)} notes")
                return content
            else:
                return f"No notes found in time range '{start_at}' to '{end_at}'"
        except Exception as e:
            print(f"Error occurred while searching notes by time range: {str(e)}")
            return f"Error occurred while searching notes by time range: {str(e)}"
