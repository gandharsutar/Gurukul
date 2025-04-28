import os
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# CORS configuration
origins = [
    "http://localhost",
    "http://localhost:3000",  # Typical React/Vue development server
    "https://yourfrontenddomain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
url: str = os.environ.get("https://qjriwcvexqvqvtegeokv.supabase.co")
key: str = os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqcml3Y3ZleHF2cXZ0ZWdlb2t2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ3MTA3MjUsImV4cCI6MjA2MDI4NjcyNX0.qsAQ0DfTUwXBZb0BPLWa9XP1mqrhtkjzAxts_l9wyak")
supabase: Client = create_client(url, key)

# Pydantic models for data validation
class UserData(BaseModel):
    name: str
    email: str
    age: Optional[int] = None
    preferences: Optional[dict] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    preferences: Optional[dict] = None

# API Endpoints
@app.get("/")
def read_root():
    return {"message": "Welcome to the User Data Collection API"}

@app.post("/users/")
async def create_user(user: UserData):
    try:
        # Insert user data into Supabase
        data, count = supabase.table("users").insert({
            "name": user.name,
            "email": user.email,
            "age": user.age,
            "preferences": user.preferences
        }).execute()
        
        return {"message": "User created successfully", "data": data[1][0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_email}")
async def get_user(user_email: str):
    try:
        # Fetch user from Supabase
        data, count = supabase.table("users").select("*").eq("email", user_email).execute()
        
        if not data[1]:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"user": data[1][0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/users/{user_email}")
async def update_user(user_email: str, user_update: UserUpdate):
    try:
        # Update user in Supabase
        update_data = {}
        if user_update.name is not None:
            update_data["name"] = user_update.name
        if user_update.age is not None:
            update_data["age"] = user_update.age
        if user_update.preferences is not None:
            update_data["preferences"] = user_update.preferences
            
        data, count = supabase.table("users").update(update_data).eq("email", user_email).execute()
        
        if count[1] == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"message": "User updated successfully", "data": data[1][0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/users/{user_email}")
async def delete_user(user_email: str):
    try:
        # Delete user from Supabase
        data, count = supabase.table("users").delete().eq("email", user_email).execute()
        
        if count[1] == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))