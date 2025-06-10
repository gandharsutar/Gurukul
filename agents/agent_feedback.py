import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict, Optional, Union
from enum import Enum
import logging

# Configure logging
def setup_logging():
    """Configure logging for the application"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"learning_analyzer_{current_time}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

# Load environment variables from .env file
load_dotenv()

# Set up Supabase using environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class MediaType(Enum):
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"

class LearningAnalyzerAgent:
    def __init__(self):
        self.today = datetime.now().date()
        self.tables_checked = False
        self.tables_exist = {
            'learning_history': False,
            'media_interactions': False,
            'processed_media': False
        }
        logger.info("LearningAnalyzerAgent initialized")
    
    def check_tables_exist(self) -> None:
        """Check which tables exist in the database"""
        if self.tables_checked:
            return
            
        logger.info("Checking database tables existence")
        try:
            # Check learning_history table
            supabase.table("learning_history").select("count", count="exact").limit(1).execute()
            self.tables_exist['learning_history'] = True
            logger.debug("learning_history table exists")
        except Exception as e:
            self.tables_exist['learning_history'] = False
            logger.warning(f"learning_history table does not exist: {str(e)}")
            
        try:
            # Check media_interactions table
            supabase.table("media_interactions").select("count", count="exact").limit(1).execute()
            self.tables_exist['media_interactions'] = True
            logger.debug("media_interactions table exists")
        except Exception as e:
            self.tables_exist['media_interactions'] = False
            logger.warning(f"media_interactions table does not exist: {str(e)}")
            
        try:
            # Check processed_media table
            supabase.table("processed_media").select("count", count="exact").limit(1).execute()
            self.tables_exist['processed_media'] = True
            logger.debug("processed_media table exists")
        except Exception as e:
            self.tables_exist['processed_media'] = False
            logger.warning(f"processed_media table does not exist: {str(e)}")
            
        self.tables_checked = True
        logger.info(f"Table existence check completed: {self.tables_exist}")
    
    def get_all_student_ids(self) -> List[str]:
        """Get all student IDs from the database"""
        self.check_tables_exist()
        
        if not self.tables_exist['learning_history']:
            logger.warning("Cannot get student IDs - learning_history table does not exist")
            return []
            
        try:
            logger.info("Fetching all student IDs from learning_history")
            response = supabase.table("learning_history").select("student_id").execute()
            if response.data:
                # Use set to get unique IDs, then convert back to list
                student_ids = list({item["student_id"] for item in response.data})
                logger.info(f"Found {len(student_ids)} unique student IDs")
                return student_ids
            logger.info("No student IDs found in learning_history")
            return []
        except Exception as e:
            logger.error(f"Error fetching student IDs: {str(e)}")
            return []
    
    def get_learning_history(self, student_id: str) -> List[Dict]:
        """Fetch learning history for a specific student"""
        self.check_tables_exist()
        
        if not self.tables_exist['learning_history']:
            logger.warning(f"Cannot get learning history for {student_id} - table doesn't exist")
            return []
            
        try:
            logger.info(f"Fetching learning history for student {student_id}")
            response = supabase.table("learning_history").select("*").eq("student_id", student_id).execute()
            logger.debug(f"Retrieved {len(response.data)} learning history records")
            return response.data
        except Exception as e:
            logger.error(f"Error fetching learning history for {student_id}: {str(e)}")
            return []
    
    def get_media_interactions(self, student_id: str) -> Dict[str, Dict]:
        """Get all media interactions for a student"""
        self.check_tables_exist()
        
        if not self.tables_exist['media_interactions']:
            logger.warning(f"Cannot get media interactions for {student_id} - table doesn't exist")
            return {}
            
        try:
            logger.info(f"Fetching media interactions for student {student_id}")
            response = supabase.table("media_interactions") \
                .select("*") \
                .eq("student_id", student_id) \
                .execute()
            
            interactions = {}
            for item in response.data:
                media_id = item["media_id"]
                if media_id not in interactions:
                    interactions[media_id] = {
                        "type": item["media_type"],
                        "views": 0,
                        "completion_rate": 0,
                        "interactions": []
                    }
                interactions[media_id]["interactions"].append(item)
                interactions[media_id]["views"] += 1
                interactions[media_id]["completion_rate"] = max(
                    interactions[media_id]["completion_rate"],
                    item.get("completion_percentage", 0)
                )
            
            logger.debug(f"Processed {len(interactions)} media interactions")
            return interactions
        except Exception as e:
            logger.error(f"Error fetching media interactions for {student_id}: {str(e)}")
            return {}
    
    def get_processed_media(self, media_id: str) -> Optional[Dict]:
        """Get processed media data from storage"""
        self.check_tables_exist()
        
        if not self.tables_exist['processed_media']:
            logger.warning(f"Cannot get processed media {media_id} - table doesn't exist")
            return None
            
        try:
            logger.info(f"Fetching processed media data for {media_id}")
            response = supabase.table("processed_media") \
                .select("*") \
                .eq("media_id", media_id) \
                .single() \
                .execute()
            logger.debug(f"Retrieved processed media data for {media_id}")
            return response.data
        except Exception as e:
            logger.error(f"Error fetching processed media {media_id}: {str(e)}")
            return None
    
    def generate_media_feedback(self, media_type: MediaType, interactions: List[Dict]) -> str:
        """Generate feedback specific to media type"""
        if not interactions:
            logger.debug(f"No interactions found for {media_type.value} media")
            return f"No interactions with {media_type.value} content found."
        
        last_interaction = interactions[-1]
        completion = last_interaction.get("completion_percentage", 0)
        
        if media_type == MediaType.TEXT:
            if completion < 50:
                feedback = "You haven't completed most of the reading material. Would you like to revisit it?"
            else:
                feedback = f"You've read {completion}% of the text. Great progress!"
        
        elif media_type == MediaType.AUDIO:
            if completion < 30:
                feedback = "You've listened to a small portion of the audio. Would you like to continue?"
            else:
                feedback = f"You've listened to {completion}% of the audio material. Keep it up!"
        
        elif media_type == MediaType.VIDEO:
            if completion < 40:
                feedback = "You've watched part of the video. Would you like to finish watching?"
            else:
                feedback = f"You've watched {completion}% of the video. Good job!"
        
        elif media_type == MediaType.IMAGE:
            view_duration = last_interaction.get("view_duration", 0)
            if view_duration < 10:
                feedback = "You've briefly viewed the image. Would you like to examine it more closely?"
            else:
                feedback = "You've spent good time analyzing the image. Well done!"
        
        logger.debug(f"Generated {media_type.value} feedback: {feedback}")
        return feedback
    
    def generate_comprehensive_feedback(self, student_id: str) -> str:
        """Generate comprehensive feedback including media interactions"""
        self.check_tables_exist()
        logger.info(f"Generating comprehensive feedback for student {student_id}")
        
        history = []
        if self.tables_exist['learning_history']:
            history = self.get_learning_history(student_id)
        
        media_interactions = {}
        if self.tables_exist['media_interactions']:
            media_interactions = self.get_media_interactions(student_id)
        
        if not history and not media_interactions:
            if not self.tables_exist['learning_history'] and not self.tables_exist['media_interactions']:
                feedback = "No learning tables found in the database. Please set up the required tables."
                logger.warning(feedback)
                return feedback
            feedback = "No learning history or media interactions found. Would you like to start learning?"
            logger.info(feedback)
            return feedback
        
        # Basic lesson completion feedback
        completed_lessons = sum(1 for item in history if item.get("status") == "completed")
        total_lessons = len(history)
        lesson_feedback = ""
        
        if total_lessons > 0:
            if completed_lessons == 0:
                lesson_feedback = "You haven't completed any lessons yet. "
            elif completed_lessons < total_lessons:
                lesson_feedback = f"You've completed {completed_lessons} of {total_lessons} lessons. "
            else:
                lesson_feedback = f"Congratulations! You've completed all {total_lessons} lessons. "
        
        logger.debug(f"Lesson feedback: {lesson_feedback}")
        
        # Media interaction feedback
        media_feedback = []
        media_stats = {
            MediaType.TEXT: {"count": 0, "completion": 0},
            MediaType.AUDIO: {"count": 0, "completion": 0},
            MediaType.VIDEO: {"count": 0, "completion": 0},
            MediaType.IMAGE: {"count": 0, "duration": 0}
        }
        
        for media_id, data in media_interactions.items():
            media_type = MediaType(data["type"])
            media_stats[media_type]["count"] += 1
            if media_type != MediaType.IMAGE:
                media_stats[media_type]["completion"] += data["completion_rate"]
            else:
                total_duration = sum(i.get("view_duration", 0) for i in data["interactions"])
                media_stats[media_type]["duration"] += total_duration
            
            # Get specific feedback for this media item
            specific_feedback = self.generate_media_feedback(media_type, data["interactions"])
            media_feedback.append(f"• {media_type.value.capitalize()} '{media_id}': {specific_feedback}")
        
        # Generate summary statistics
        summary = []
        for media_type, stats in media_stats.items():
            if stats["count"] > 0:
                if media_type != MediaType.IMAGE:
                    avg_completion = stats["completion"] / stats["count"]
                    summary.append(f"{stats['count']} {media_type.value}s (avg. {avg_completion:.0f}% completion)")
                else:
                    avg_duration = stats["duration"] / stats["count"]
                    summary.append(f"{stats['count']} images (avg. {avg_duration:.1f}s viewing)")
        
        summary_text = "You've interacted with: " + ", ".join(summary) if summary else ""
        logger.debug(f"Media summary: {summary_text}")
        
        # Combine all feedback
        full_feedback = lesson_feedback + summary_text
        if media_feedback:
            full_feedback += "\n\nDetailed feedback:\n" + "\n".join(media_feedback)
        
        # Add database status information if tables are missing
        missing_tables = [name for name, exists in self.tables_exist.items() if not exists]
        if missing_tables:
            full_feedback += f"\n\nNote: Some functionality limited - missing tables: {', '.join(missing_tables)}"
            logger.warning(f"Missing tables affecting feedback: {missing_tables}")
        
        logger.info(f"Feedback generation completed for student {student_id}")
        return full_feedback if full_feedback else "Keep up the good work with your learning!"

    def print_database_setup_instructions(self) -> None:
        """Print instructions for setting up the required database tables"""
        logger.info("Displaying database setup instructions")
        print("\nDatabase Setup Instructions:")
        print("=" * 40)
        print("To use all features, you need to create the following tables in your Supabase database:")
        
        print("\n1. learning_history table:")
        print("""CREATE TABLE learning_history (
    id SERIAL PRIMARY KEY,
    student_id TEXT NOT NULL,
    lesson_id TEXT NOT NULL,
    status TEXT,
    completion_percentage INTEGER,
    last_accessed TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);""")

        print("\n2. media_interactions table:")
        print("""CREATE TABLE media_interactions (
    id SERIAL PRIMARY KEY,
    student_id TEXT NOT NULL,
    media_id TEXT NOT NULL,
    media_type TEXT NOT NULL,
    interaction_type TEXT,
    completion_percentage INTEGER,
    view_duration INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);""")

        print("\n3. processed_media table:")
        print("""CREATE TABLE processed_media (
    media_id TEXT PRIMARY KEY,
    media_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    metadata JSONB,
    processed_at TIMESTAMP DEFAULT NOW()
);""")
        print("=" * 40)

def select_student_id(student_ids: List[str]) -> Optional[str]:
    """Allow user to select a student ID from the list"""
    if not student_ids:
        logger.warning("No students found for selection")
        print("No students found in the database.")
        return None
    
    logger.info("Displaying student ID selection menu")
    print("\nAvailable Student IDs:")
    for i, student_id in enumerate(student_ids, 1):
        print(f"{i}. {student_id}")
    
    while True:
        try:
            choice = input("\nSelect a student by number (or 'q' to quit): ")
            if choice.lower() == 'q':
                logger.info("User quit student selection")
                return None
            choice_num = int(choice)
            if 1 <= choice_num <= len(student_ids):
                selected_id = student_ids[choice_num - 1]
                logger.info(f"User selected student ID: {selected_id}")
                return selected_id
            print(f"Please enter a number between 1 and {len(student_ids)}")
            logger.warning(f"Invalid selection: {choice}")
        except ValueError:
            print("Please enter a valid number or 'q' to quit.")
            logger.warning("Invalid input in student selection")

def main():
    try:
        logger.info("Starting Learning Analyzer application")
        analyzer = LearningAnalyzerAgent()
        
        # Print database setup instructions if tables are missing
        analyzer.check_tables_exist()
        if not all(analyzer.tables_exist.values()):
            logger.warning("Some required tables are missing")
            analyzer.print_database_setup_instructions()
        
        # Get all student IDs from the database
        student_ids = analyzer.get_all_student_ids()
        
        # Let user select a student ID
        student_id = select_student_id(student_ids)
        
        if not student_id:
            logger.info("No student selected - exiting")
            print("No student selected.")
            return
        
        # Generate comprehensive feedback for the selected student
        feedback = analyzer.generate_comprehensive_feedback(student_id)
        print(f"\nStudent ID: {student_id}")
        print("Learning Analysis Report:")
        print("=" * 40)
        print(feedback)
        print("=" * 40)
        
        logger.info("Application completed successfully")
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        print("An error occurred. Please check the logs for details.")

if __name__ == "__main__":
    main()