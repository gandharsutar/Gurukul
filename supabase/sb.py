import os
from fastapi import FastAPI
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Supabase details from environment variables or hardcoded values
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://qjriwcvexqvqvtegeokv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqcml3Y3ZleHF2cXZ0ZWdlb2t2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ3MTA3MjUsImV4cCI6MjA2MDI4NjcyNX0.qsAQ0DfTUwXBZb0BPLWa9XP1mqrhtkjzAxts_l9wyak")

# Create the Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Time Tracking API!"}

@app.get("/time_tracking")
def get_time_tracking():
    try:
        logging.info("Fetching data from time_tracking table...")
        response = supabase.table("time_tracking").select("*").execute()
        
        # The supabase-py client might return data differently
        # Check the actual structure of the response
        if hasattr(response, 'data'):
            data = response.data
        else:
            data = response.get('data', [])
            
        if data:
            logging.info(f"Fetched {len(data)} records.")
            return {"data": data}
        else:
            logging.warning("No records found.")
            return {"message": "No records found in the time_tracking table."}
            
    except Exception as e:
        logging.error(f"Error fetching data: {str(e)}")
        return {"error": f"Error fetching data: {str(e)}", "details": str(e)}