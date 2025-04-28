from fastapi import FastAPI
from supabase import create_client, Client

app = FastAPI()

SUPABASE_URL = "https://qjriwcvexqvqvtegeokv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqcml3Y3ZleHF2cXZ0ZWdlb2t2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ3MTA3MjUsImV4cCI6MjA2MDI4NjcyNX0.qsAQ0DfTUwXBZb0BPLWa9XP1mqrhtkjzAxts_l9wyak"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/users")
def get_users():
    response = supabase.table('users').select('*').execute()
    return response.data

@app.post("/users")
def create_user(user: dict):
    response = supabase.table('users').insert(user).execute()
    return response.data
