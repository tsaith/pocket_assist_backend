from datetime import datetime
import pytz

from typing import List, Tuple
from langchain_core.tools import StructuredTool

from app.lib.supabase import supabase_admin
from app.lib.chatbot.utils import (
    convert_utc_to_taiwan_time,
    convert_taiwan_to_utc_time
)

def create_create_calendar_event_tool(user_id: str) -> StructuredTool:
    """創建添加行事曆事件工具"""

    def create_calendar_event(title: str, description: str, location: str, start_time: str, end_time: str, is_all_day: bool = False, timezone: str = 'UTC', is_recurring: bool = False, recurrence_rule: str = None, status: str = 'active', color: str = '#3b82f6') -> str:
        """添加新的行事曆事件"""

        print(f"添加行事曆事件：Title {title}, Start {start_time}, End {end_time}")
        try:
            # 檢查是否已存在相同的 title 和 start_time 組合
            response = supabase_admin.from_("calendar_events").select("*").eq("user_id", user_id).eq("title", title).eq("start_time", start_time).execute()
            
            if response.data:
                return f"已存在相同的 Title: {title} 和 Start Time: {start_time} 記錄"
            
            # 添加新記錄
            result = supabase_admin.from_("calendar_events").insert({
                "user_id": user_id,
                "title": title,
                "description": description,
                "location": location,
                "start_time": start_time,
                "end_time": end_time,
                "is_all_day": is_all_day,
                "timezone": timezone,
                "is_recurring": is_recurring,
                "recurrence_rule": recurrence_rule,
                "status": status,
                "color": color
            }).execute()
            
            if result.data:

                print(f"result.data: {result.data}")
                new_record = result.data[0]
                content = f"成功添加行事曆事件，ID: {new_record.get('id', '')}, Title: {title}, Start: {start_time}, End: {end_time}"
                print(f"content: {content}")
                return f"成功添加行事曆事件，ID: {new_record.get('id', '')}, Title: {title}, Start: {start_time}, End: {end_time}"
            else:
                return "添加行事曆事件失敗"
                
        except Exception as e:
            error_msg = f"添加行事曆事件時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg

    create_calendar_event_tool = StructuredTool.from_function(
        func=create_calendar_event,
        name="create_calendar_event",
        description="添加新的行事曆事件(calendar event)，需要提供 title、description、location、start_time、end_time 等參數，請用台灣時間設定 start_time 和 end_time",
    )

    return create_calendar_event_tool


def create_read_calendar_event_tool(user_id: str) -> StructuredTool:
    """創建讀取單個行事曆事件工具"""

    def read_calendar_event(id: str) -> str:
        """讀取智能助理的單個行事曆事件內容"""

        print(f"讀取行事曆事件內容：ID {id}")
        try:
            response = supabase_admin.from_("calendar_events").select("id, title, description, location, start_time, end_time, is_all_day, timezone, is_recurring, recurrence_rule, status, color, created_at, updated_at").eq("id", id).eq("user_id", user_id).execute()
            
            if response.data:
                event_data = response.data[0]
                start_time = convert_utc_to_taiwan_time(event_data.get('start_time', ''))
                end_time = convert_utc_to_taiwan_time(event_data.get('end_time', ''))
                event_info = f"ID: {event_data.get('id', '')}, Title: {event_data.get('title', '')}, Description: {event_data.get('description', '')}, Location: {event_data.get('location', '')}, Start: {start_time}, End: {end_time}, All Day: {event_data.get('is_all_day', '')}, Timezone: {event_data.get('timezone', '')}, Recurring: {event_data.get('is_recurring', '')}, Status: {event_data.get('status', '')}, Color: {event_data.get('color', '')}, Created: {event_data.get('created_at', '')}, Updated: {event_data.get('updated_at', '')}"
                
                print(f"行事曆事件內容：{event_info}")
                return event_info
            else:
                return f"找不到 ID {id} 的行事曆事件記錄"
        except Exception as e:
            print(f"讀取行事曆事件內容時發生錯誤：{str(e)}")
            return ""

    read_calendar_event_tool = StructuredTool.from_function(
        func=read_calendar_event,
        name="read_calendar_event",
        description="讀取智能助理的單個行事曆事件內容，需要提供 id 參數",
    )

    return read_calendar_event_tool


def create_read_calendar_events_tool(user_id: str) -> StructuredTool:
    """創建讀取行事曆事件工具"""

    def read_calendar_events() -> str:
        """讀取智能助理的行事曆事件內容"""

        print(f"讀取單一行事曆事件內容：{user_id}")
        content = ""
        try:
            response = supabase_admin.from_("calendar_events").select("id, title, description, location, start_time, end_time, is_all_day, timezone, is_recurring, recurrence_rule, status, color, created_at, updated_at").eq("user_id", user_id).execute()
            if response.data:
                events_list = []
                for event_data in response.data:
                    start_time = convert_utc_to_taiwan_time(event_data.get('start_time', ''))
                    end_time = convert_utc_to_taiwan_time(event_data.get('end_time', ''))
                    event_info = f"ID: {event_data.get('id', '')}, Title: {event_data.get('title', '')}, Description: {event_data.get('description', '')}, Location: {event_data.get('location', '')}, Start: {start_time}, End: {end_time}, All Day: {event_data.get('is_all_day', '')}, Timezone: {event_data.get('timezone', '')}, Recurring: {event_data.get('is_recurring', '')}, Status: {event_data.get('status', '')}, Color: {event_data.get('color', '')}, Created: {event_data.get('created_at', '')}, Updated: {event_data.get('updated_at', '')}"
                    events_list.append(event_info)
                content = "\n".join(events_list)

                print(f"行事曆事件內容：{content}")
                return content
            else:
                return "No calendar events found"
        except Exception as e:
            print(f"讀取行事曆事件內容時發生錯誤：{str(e)}")
            return ""

    read_calendar_events_tool = StructuredTool.from_function(
        func=read_calendar_events,
        name="read_calendar_events",
        description="讀取智能助理的行事曆事件內容，返回所有記錄的詳細信息",
    )

    return read_calendar_events_tool


def create_update_calendar_event_tool(user_id: str) -> StructuredTool:
    """創建更新行事曆事件工具"""

    def update_calendar_event(id: str, title: str, description: str, location: str, start_time: str, end_time: str, is_all_day: bool = False, timezone: str = 'UTC', is_recurring: bool = False, recurrence_rule: str = None, status: str = 'active', color: str = '#3b82f6') -> bool:
        """更新智能助理的行事曆事件內容"""

        print(f"更新行事曆事件內容：ID {id}, Title {title}, Start {start_time}, End {end_time}")
        is_updated = False
        try:
            # 檢查指定 ID 的記錄是否存在
            response = supabase_admin.from_("calendar_events").select("*").eq("id", id).eq("user_id", user_id).execute()
            
            if response.data:
                # 如果記錄存在，更新內容
                supabase_admin.from_("calendar_events").update({
                    "title": title,
                    "description": description,
                    "location": location,
                    "start_time": start_time,
                    "end_time": end_time,
                    "is_all_day": is_all_day,
                    "timezone": timezone,
                    "is_recurring": is_recurring,
                    "recurrence_rule": recurrence_rule,
                    "status": status,
                    "color": color,
                    "updated_at": "now()"
                }).eq("id", id).eq("user_id", user_id).execute()
                is_updated = True
            else:
                print(f"找不到 ID {id} 的行事曆事件記錄")
                is_updated = False
                
        except Exception as e:
            is_updated = False
            print(f"更新行事曆事件內容時發生錯誤：{str(e)}")

        return is_updated

    update_calendar_event_tool = StructuredTool.from_function(
        func=update_calendar_event,
        name="update_calendar_event",
        description="更新智能助理的行事曆事件內容，需要提供 id、title、description、location、start_time、end_time 等參數，請用 UTC 時間設定 start_time 和 end_time "
    )

    return update_calendar_event_tool


def create_delete_calendar_event_tool(user_id: str) -> StructuredTool:
    """創建刪除行事曆事件工具"""

    def delete_calendar_event(id: str) -> str:
        """刪除指定的行事曆事件記錄"""

        print(f"刪除行事曆事件：ID {id}")
        try:
            # 檢查指定 ID 的記錄是否存在且屬於該 user
            response = supabase_admin.from_("calendar_events").select("*").eq("id", id).eq("user_id", user_id).execute()
            
            if not response.data:
                return f"找不到 ID {id} 的行事曆事件記錄"
            
            # 刪除記錄
            result = supabase_admin.from_("calendar_events").delete().eq("id", id).eq("user_id", user_id).execute()
            
            if result.data:
                return f"成功刪除行事曆事件記錄，ID: {id}"
            else:
                return "刪除行事曆事件記錄失敗"
                
        except Exception as e:
            error_msg = f"刪除行事曆事件時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg

    delete_calendar_event_tool = StructuredTool.from_function(
        func=delete_calendar_event,
        name="delete_calendar_event",
        description="刪除指定的行事曆事件記錄，需要提供 id 參數",
    )

    return delete_calendar_event_tool

def create_search_calendar_events_tool(user_id: str) -> StructuredTool:
    """創建搜尋行事曆事件工具"""

    def search_calendar_events(keyword: str) -> str:
        """搜尋智能助理的行事曆事件內容，根據關鍵字搜尋標題或敘述"""

        print(f"搜尋行事曆事件 from user_id：{user_id}, keyword：{keyword}")
        content = ""
        try:
            # 使用 ilike 進行模糊搜尋，搜尋標題或敘述包含關鍵字的事件
            response = supabase_admin.from_("calendar_events").select("id, title, description, location, start_time, end_time, is_all_day, timezone, is_recurring, recurrence_rule, status, color, created_at, updated_at").eq("user_id", user_id).or_(f"title.ilike.%{keyword}%,description.ilike.%{keyword}%").execute()
            
            if response.data:
                events_list = []
                for event_data in response.data:
                    start_time = convert_utc_to_taiwan_time(event_data.get('start_time', ''))
                    end_time = convert_utc_to_taiwan_time(event_data.get('end_time', ''))
                    event_info = f"ID: {event_data.get('id', '')}, Title: {event_data.get('title', '')}, Description: {event_data.get('description', '')}, Location: {event_data.get('location', '')}, Start: {start_time}, End: {end_time}, All Day: {event_data.get('is_all_day', '')}, Timezone: {event_data.get('timezone', '')}, Recurring: {event_data.get('is_recurring', '')}, Status: {event_data.get('status', '')}, Color: {event_data.get('color', '')}, Created: {event_data.get('created_at', '')}, Updated: {event_data.get('updated_at', '')}"
                    events_list.append(event_info)
                content = "\n".join(events_list)

                print(f"搜尋結果：找到 {len(response.data)} 個行事曆事件")
                return content
            else:
                return f"沒有找到包含關鍵字 '{keyword}' 的行事曆事件"
        except Exception as e:
            print(f"搜尋行事曆事件時發生錯誤：{str(e)}")
            return f"搜尋行事曆事件時發生錯誤：{str(e)}"

    search_calendar_events_tool = StructuredTool.from_function(
        func=search_calendar_events,
        name="search_calendar_events",
        description="搜尋智能助理的行事曆事件內容，根據關鍵字搜尋標題或敘述，需要提供 keyword 參數; 關鍵字不可以是日期。",
    )

    return search_calendar_events_tool

def create_search_calendar_events_by_time_tool(user_id: str) -> StructuredTool:
    """創建根據時間範圍搜尋行事曆事件工具"""

    def search_calendar_events_by_time(start_at: str, end_at: str) -> str:
        """搜尋智能助理的行事曆事件內容，根據時間範圍搜尋 start_time 介於指定時間之間的事件"""

        start_at_utc = convert_taiwan_to_utc_time(start_at)
        end_at_utc = convert_taiwan_to_utc_time(end_at)

        print(f"根據時間範圍搜尋行事曆事件 from user_id：{user_id}, start_at：{start_at}, end_at：{end_at}")
        content = ""
        try:
            # 使用 gte 和 lte 進行時間範圍搜尋，搜尋 start_time 介於指定時間之間的事件
            response = supabase_admin.from_("calendar_events").select("id, title, description, location, start_time, end_time, is_all_day, timezone, is_recurring, recurrence_rule, status, color, created_at, updated_at").eq("user_id", user_id).gte("start_time", start_at_utc).lte("start_time", end_at_utc).execute()
            
            if response.data:
                events_list = []
                for event_data in response.data:
                    start_time_taiwan = convert_utc_to_taiwan_time(event_data.get('start_time', ''))
                    end_time_taiwan = convert_utc_to_taiwan_time(event_data.get('end_time', ''))
                    event_info = f"ID: {event_data.get('id', '')}, Title: {event_data.get('title', '')}, Description: {event_data.get('description', '')}, Location: {event_data.get('location', '')}, Start: {start_time_taiwan}, End: {end_time_taiwan}, All Day: {event_data.get('is_all_day', '')}, Timezone: {event_data.get('timezone', '')}, Recurring: {event_data.get('is_recurring', '')}, Status: {event_data.get('status', '')}, Color: {event_data.get('color', '')}, Created: {event_data.get('created_at', '')}, Updated: {event_data.get('updated_at', '')}"
                    events_list.append(event_info)
                content = "\n".join(events_list)

                print(f"時間範圍搜尋結果：找到 {len(response.data)} 個行事曆事件")
                return content
            else:
                return f"沒有找到在時間範圍 '{start_at}' 到 '{end_at}' 之間的行事曆事件"
        except Exception as e:
            print(f"根據時間範圍搜尋行事曆事件時發生錯誤：{str(e)}")
            return f"根據時間範圍搜尋行事曆事件時發生錯誤：{str(e)}"

    search_calendar_events_by_time_tool = StructuredTool.from_function(
        func=search_calendar_events_by_time,
        name="search_calendar_events_by_time",
        description="搜尋智能助理的行事曆事件內容，根據時間範圍搜尋 start_time 介於指定時間之間的事件，需要提供 start_at 和 end_at 參數（請使用台灣時間）",
    ) 

    return search_calendar_events_by_time_tool

def create_create_calendar_event_and_reminder_tool(user_id: str) -> StructuredTool:
    """創建添加行事曆事件和對應提醒工具"""

    def create_calendar_event_and_reminder(title: str, description: str, location: str, start_time: str, end_time: str, is_all_day: bool = False, timezone: str = 'UTC', is_recurring: bool = False, recurrence_rule: str = None, status: str = 'active', color: str = '#3b82f6', remind_at: str = None, reminder_method: str = 'notification', reminder_description: str = None) -> str:
        """添加新的行事曆事件和對應的提醒"""

        print(f"添加行事曆事件和提醒：Title {title}, Start {start_time}, End {end_time}, Remind At {remind_at}")
        try:
            # 檢查是否已存在相同的 title 和 start_time 組合
            response = supabase_admin.from_("calendar_events").select("*").eq("user_id", user_id).eq("title", title).eq("start_time", start_time).execute()
            
            if response.data:
                return f"已存在相同的 Title: {title} 和 Start Time: {start_time} 記錄"
            
            # 第一步：添加行事曆事件
            result = supabase_admin.from_("calendar_events").insert({
                "user_id": user_id,
                "title": title,
                "description": description,
                "location": location,
                "start_time": start_time,
                "end_time": end_time,
                "is_all_day": is_all_day,
                "timezone": timezone,
                "is_recurring": is_recurring,
                "recurrence_rule": recurrence_rule,
                "status": status,
                "color": color
            }).execute()
            
            if not result.data:
                return "添加行事曆事件失敗，無法繼續建立提醒"
            
            # 獲取新建立的行事曆事件 ID
            new_event = result.data[0]
            event_id = new_event.get('id', '')
            
            print(f"成功建立行事曆事件，ID: {event_id}")
            
            # 第二步：建立對應的提醒事件
            if remind_at:
                # 如果沒有指定提醒描述，使用行事曆事件的標題
                if not reminder_description:
                    reminder_description = f"提醒：{title}"
                
                # 檢查是否已存在相同的 event_id、user_id、reminder_method 組合
                reminder_check = supabase_admin.from_("reminders").select("*").eq("event_id", event_id).eq("user_id", user_id).eq("method", reminder_method).execute()
                
                if reminder_check.data:
                    print(f"已存在相同的提醒記錄，跳過建立提醒")
                else:
                    # 建立新的提醒記錄
                    reminder_result = supabase_admin.from_("reminders").insert({
                        "event_id": event_id,
                        "user_id": user_id,
                        "description": reminder_description,
                        "remind_at": remind_at,
                        "method": reminder_method
                    }).execute()
                    
                    if reminder_result.data:
                        new_reminder = reminder_result.data[0]
                        reminder_id = new_reminder.get('id', '')
                        print(f"成功建立提醒，ID: {reminder_id}")
                        
                        return f"成功添加行事曆事件和提醒！\n- 行事曆事件 ID: {event_id}, Title: {title}, Start: {start_time}, End: {end_time}\n- 提醒 ID: {reminder_id}, Remind At: {remind_at}, Method: {reminder_method}"
                    else:
                        print(f"建立提醒失敗，但行事曆事件已成功建立")
                        return f"成功添加行事曆事件，ID: {event_id}, Title: {title}, Start: {start_time}, End: {end_time}\n⚠️ 建立提醒失敗"
            else:
                # 如果沒有指定提醒時間，只建立行事曆事件
                print(f"未指定提醒時間，只建立行事曆事件")
                return f"成功添加行事曆事件，ID: {event_id}, Title: {title}, Start: {start_time}, End: {end_time}\nℹ️ 未建立提醒（未指定提醒時間）"
                
        except Exception as e:
            error_msg = f"添加行事曆事件和提醒時發生錯誤：{str(e)}"
            print(error_msg)
            return error_msg

    create_calendar_event_and_reminder_tool = StructuredTool.from_function(
        func=create_calendar_event_and_reminder,
        name="create_calendar_event_and_reminder",
        description="添加新的行事曆事件和對應的提醒，需要提供 title、description、location、start_time、end_time 等參數，可選提供 remind_at（提醒時間）、reminder_method（提醒方式）、reminder_description（提醒描述）。請用台灣時間設定 start_time、end_time 和 remind_at。",
    )

    return create_calendar_event_and_reminder_tool
