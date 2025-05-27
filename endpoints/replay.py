<<<<<<< HEAD
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from fastapi.responses import JSONResponse
import json
from dotenv import load_dotenv

app=FastAPI()

load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from supabase import create_client
import os

# Initialize Supabase client
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

@app.get("/replay-session/{session_id}")
async def replay_session(session_id: str):
    # Check if the session is closed or terminated
    session_status = supabase.table("agent_logs").select("status").eq("id", session_id).single().execute()
    if session_status.data and session_status.data['status'] in ['closed', 'terminated']:
        # Restart the session
        supabase.table("sessions").update({"status": "active"}).eq("id", session_id).execute()
    try:
        # Fetch session data from Supabase
        session_data = supabase.table("agent_logs").select("*").eq("id", session_id).execute()
        
        if not session_data.data:
            return JSONResponse(content={"error": "Session not found"}, status_code=404)
        
        # Process and return the session data
        return JSONResponse(content={"session": session_data.data[0]})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
=======
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from fastapi.responses import JSONResponse
import json
from dotenv import load_dotenv

app=FastAPI()

load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from supabase import create_client
import os

# Initialize Supabase client
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

@app.get("/replay-session/{session_id}")
async def replay_session(session_id: str):
    # Check if the session is closed or terminated
    session_status = supabase.table("agent_logs").select("status").eq("id", session_id).single().execute()
    if session_status.data and session_status.data['status'] in ['closed', 'terminated']:
        # Restart the session
        supabase.table("sessions").update({"status": "active"}).eq("id", session_id).execute()
    try:
        # Fetch session data from Supabase
        session_data = supabase.table("agent_logs").select("*").eq("id", session_id).execute()
        
        if not session_data.data:
            return JSONResponse(content={"error": "Session not found"}, status_code=404)
        
        # Process and return the session data
        return JSONResponse(content={"session": session_data.data[0]})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
>>>>>>> 10bd3819fec539bdc1992505f9a5b8ef7bbbbe6a
    uvicorn.run(app, host="192.168.0.66", port=8000)