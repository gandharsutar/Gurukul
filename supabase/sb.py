import os
from fastapi import FastAPI
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://qjriwcvexqvqvtegeokv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqcml3Y3ZleHF2cXZ0ZWdlb2t2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ3MTA3MjUsImV4cCI6MjA2MDI4NjcyNX0.qsAQ0DfTUwXBZb0BPLWa9XP1mqrhtkjzAxts_l9wyak")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Time Tracking API"}

@app.get("/time-tracking")
def get_time_tracking():
    try:
        response = supabase.table("time_tracking").select("*").execute()
        data = response.data
        return {"data": data}
    except Exception as e:
        return {"error": str(e)}
