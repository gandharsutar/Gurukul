import os
from fastapi import FastAPI
from supabase import create_client, Client
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

# Set up Supabase using environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


response=supabase.table("learning_history").select("*").execute()
data=response.data
print(data)

