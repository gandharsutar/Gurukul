from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import os
from dotenv import load_dotenv

# Import our models and utility functions
from backend.models.lectures_api import Lecture, get_all_lectures, get_lecture_by_id
from backend.supabase import supabase

load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def root():
    return {"message": "Welcome to Gurukul API"}

@app.get("/lectures", response_model=List[dict])
async def read_lectures():
    """
    Get all lectures
    """
    try:
        lectures = await get_all_lectures()
        return lectures
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/lectures/{lecture_id}", response_model=dict)
async def read_lecture(lecture_id: int):
    """
    Get a specific lecture by ID
    """
    lecture = await get_lecture_by_id(lecture_id)
    if lecture is None:
        raise HTTPException(status_code=404, detail=f"Lecture with ID {lecture_id} not found")
    return lecture

@app.get("/users")
async def get_users():
    """
    Get all users from Supabase profiles table
    """
    try:
        response = supabase.table("profiles").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api:app", host="0.0.0.0", port=8000, reload=True) 