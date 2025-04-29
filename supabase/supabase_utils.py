import os
from fastapi import FastAPI
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Set up Supabase using environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_feedback(data):
    """Generate feedback based on learning history data"""
    try:
        if not data:
            return "No learning history data available."
        
        # Convert data to DataFrame for easier analysis
        df = pd.DataFrame(data)
        
        # Convert date columns to datetime
        df['start_time'] = pd.to_datetime(df['start_time'])
        df['end_time'] = pd.to_datetime(df['end_time'])
        
        # Calculate session duration in minutes
        df['duration_minutes'] = (df['end_time'] - df['start_time']).dt.total_seconds() / 60
        
        # Group by user_id to analyze individual performance
        feedback_messages = []
        
        for user_id, user_data in df.groupby('user_id'):
            # Calculate user statistics
            total_sessions = len(user_data)
            avg_duration = user_data['duration_minutes'].mean()
            total_time = user_data['duration_minutes'].sum()
            
            # Get the most recent session
            recent_session = user_data.sort_values('start_time').iloc[-1]
            
            # Generate feedback message
            message = f"User {user_id}:\n"
            message += f"- Total learning sessions: {total_sessions}\n"
            message += f"- Average session duration: {avg_duration:.1f} minutes\n"
            message += f"- Total learning time: {total_time:.1f} minutes\n"
            
            # Add specific feedback based on recent activity
            if recent_session['duration_minutes'] > avg_duration:
                message += "- Recent session was longer than average - great dedication!\n"
            elif recent_session['duration_minutes'] < avg_duration:
                message += "- Recent session was shorter than average - consider longer study sessions.\n"
            
            # Add time-based feedback
            if total_time < 60:
                message += "- Consider increasing your study time to see better results.\n"
            elif total_time > 300:
                message += "- Excellent commitment to learning!\n"
            
            feedback_messages.append(message)
        
        return "\n\n".join(feedback_messages)
    
    except Exception as e:
        return f"Error generating feedback: {str(e)}"

def main():
    try:
        # Fetch learning history data
        response = supabase.table("learning_history").select("*").execute()
        data = response.data
        
        if not data:
            print("No learning history data found.")
            return
        
        # Generate and display feedback
        feedback = generate_feedback(data)
        print("\nLearning History Feedback:")
        print(feedback)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()

 