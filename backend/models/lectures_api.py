from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
from backend.supabase import supabase

class Lecture(BaseModel):
    id: int
    title: str
    description: str
    instructor: str
    duration: int
    link_to_lec: Optional[str] = ""
    date_created: datetime

async def get_all_lectures():
    """
    Retrieve all lectures from the Supabase database
    """
    try:
        response = supabase.table('lectures').select('*').execute()
        lectures = response.data
        return lectures
    except Exception as e:
        print(f"Error fetching lectures: {e}")
        return []

async def get_lecture_by_id(lecture_id: int):
    """
    Retrieve a specific lecture by ID from Supabase
    """
    try:
        response = supabase.table('lectures').select('*').eq('id', lecture_id).execute()
        lectures = response.data
        return lectures[0] if lectures else None
    except Exception as e:
        print(f"Error fetching lecture with ID {lecture_id}: {e}")
        return None

async def create_lecture(lecture_data: dict):
    """
    Create a new lecture in Supabase
    """
    try:
        response = supabase.table('lectures').insert(lecture_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error creating lecture: {e}")
        return None 