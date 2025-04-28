import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration class
class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    @classmethod
    def validate(cls):
        if not cls.SUPABASE_URL or not cls.SUPABASE_KEY:
            raise ValueError("Supabase URL and KEY must be set in environment variables")

# Validate configuration
try:
    Config.validate()
except ValueError as e:
    logger.error(f"Configuration error: {str(e)}")
    raise

# Initialize Supabase client
try:
    supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    logger.info("Successfully connected to Supabase")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    raise

# Initialize FastAPI app
app = FastAPI(
    title="Supabase Data API",
    description="API for fetching data from Supabase",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class TimeTrackingRecord(BaseModel):
    id: int
    user_id: str
    project_id: str
    start_time: str
    end_time: str
    description: Optional[str] = None

class ErrorResponse(BaseModel):
    detail: str

@app.get("/", tags=["Root"])
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "Welcome to the Supabase Data API"
    }

@app.get(
    "/time-tracking",
    response_model=List[TimeTrackingRecord],
    responses={500: {"model": ErrorResponse}},
    tags=["Time Tracking"]
)
async def get_all_time_tracking():
    """Fetch all time tracking records"""
    try:
        response = supabase.table("time_tracking").select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching time tracking data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch time tracking records"
        )

@app.get(
    "/time-tracking/{record_id}",
    response_model=TimeTrackingRecord,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    tags=["Time Tracking"]
)
async def get_time_tracking_record(record_id: int):
    """Fetch a specific time tracking record by ID"""
    try:
        response = supabase.table("time_tracking").select("*").eq("id", record_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=f"Time tracking record with ID {record_id} not found"
            )
            
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching time tracking record {record_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch time tracking record"
        )

@app.get(
    "/time-tracking/user/{user_id}",
    response_model=List[TimeTrackingRecord],
    responses={500: {"model": ErrorResponse}},
    tags=["Time Tracking"]
)
async def get_time_tracking_by_user(user_id: str):
    """Fetch all time tracking records for a specific user"""
    try:
        response = supabase.table("time_tracking").select("*").eq("user_id", user_id).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching time tracking data for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch time tracking records for user {user_id}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.0.80", port=8000)