import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict, Optional

# Load environment variables from .env file
load_dotenv()

# Set up Supabase using environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class LearningAnalyzerAgent:
    def __init__(self):
        self.today = datetime.now().date()
    
    def get_all_student_ids(self) -> List[str]:
        """Get all student IDs from the database"""
        try:
            response = supabase.table("learning_history").select("student_id").execute()
            if response.data:
                # Use set to get unique IDs, then convert back to list
                return list({item["student_id"] for item in response.data})
            return []
        except Exception as e:
            print(f"Error fetching student IDs: {str(e)}")
            return []
    
    def get_learning_history(self, student_id: str) -> List[Dict]:
        """Fetch learning history for a specific student"""
        try:
            response = supabase.table("learning_history").select("*").eq("student_id", student_id).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching learning history: {str(e)}")
            return []
    
    def generate_feedback(self, student_id: str) -> str:
        """Generate simple feedback about completed lessons"""
        history = self.get_learning_history(student_id)
        
        if not history:
            return "No learning history found. Would you like to start learning?"
        
        completed_lessons = sum(1 for item in history if item.get("status") == "completed")
        total_lessons = len(history)
        
        if completed_lessons == 0:
            return "You haven't completed any lessons yet. Would you like to start learning?"
        elif completed_lessons < total_lessons:
            return f"You've completed {completed_lessons} lessons. Want to continue or revise?"
        else:
            return f"Congratulations! You've completed all {total_lessons} lessons. Would you like to revise any topics?"

def select_student_id(student_ids: List[str]) -> Optional[str]:
    """Allow user to select a student ID from the list"""
    if not student_ids:
        print("No students found in the database.")
        return None
    
    print("\nAvailable Student IDs:")
    for i, student_id in enumerate(student_ids, 1):
        print(f"{i}. {student_id}")
    
    while True:
        try:
            choice = input("\nSelect a student by number (or 'q' to quit): ")
            if choice.lower() == 'q':
                return None
            choice_num = int(choice)
            if 1 <= choice_num <= len(student_ids):
                return student_ids[choice_num - 1]
            print(f"Please enter a number between 1 and {len(student_ids)}")
        except ValueError:
            print("Please enter a valid number or 'q' to quit.")

def main():
    analyzer = LearningAnalyzerAgent()
    
    # Get all student IDs from the database
    student_ids = analyzer.get_all_student_ids()
    
    # Let user select a student ID
    student_id = select_student_id(student_ids)
    
    if not student_id:
        print("No student selected.")
        return
    
    # Generate feedback for the selected student
    feedback = analyzer.generate_feedback(student_id)
    print(f"\nStudent ID: {student_id}")
    print(f"Feedback: {feedback}")

if __name__ == "__main__":
    main()