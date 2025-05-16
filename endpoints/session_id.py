# Import required modules and libraries
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from supabase import create_client
import os
import uvicorn

# Initialize FastAPI app
app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
load_dotenv()
    
# Initialize Supabase client with service role key for bypassing RLS
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Using service role key for bypassing RLS
)

# Define the endpoint and its behavior
@app.get("/agent-snapshot/{session_id}")
async def get_agent_snapshot(session_id: str, timestamp: str = None):
    """
    Returns session state for a specific session_id
    - If timestamp is provided: returns state at that exact time
    - If no timestamp: returns the latest state
    
    Response format:
    {
        "session_id": "string",
        "timestamp": "datetime",
        "state": {json_object},
        ...other_fields
    }
    """
    try:
        # Build the base query
        query = supabase.table("agent_logs").select("*").eq("id", session_id)
        
        # Apply timestamp filter if provided
        if timestamp:
            query = query.eq("timestamp", timestamp)
        else:
            query = query.order("timestamp", desc=True).limit(1)
        
        # Execute query
        response = query.execute()
        
        # Handle response
        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=f"No snapshot found for session {session_id}" + 
                      (f" at timestamp {timestamp}" if timestamp else "")
            )
            
        return JSONResponse(content=response.data[0])
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch session state: {str(e)}"
        )

# Run the app if this file is executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="192.168.0.94", port=8000)