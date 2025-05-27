<<<<<<< HEAD
# Import required modules and libraries
import os
from supabase import create_client
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app and configure CORS middleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables and initialize Supabase client with service role key for bypassing RLS
load_dotenv()

# Initialize client
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

def diagnose_table(table_name: str):
    print(f"\nDiagnosing table: {table_name}")
    
    try:
        data = supabase.table(table_name).select("*").execute()
        print(f"Data: {data.data}")
        return data.data
    except:
        print("Couldn't get query data")

@app.get("/agent-log/timeline")
def get_agent_log():
    table_name = "agent_logs"  # Replace with your table name
    data = diagnose_table(table_name)
    return JSONResponse(content=data)

if __name__ == "__main__":
    table_name = "agent_logs"  # Replace with your table name
    query = diagnose_table(table_name)
    
    # Alternative direct access
    print("\nDirect query results:")
    print(query)
    
import uvicorn
uvicorn.run(app, host="192.168.0.71", port=8000)
=======
# Import required modules and libraries
import os
from supabase import create_client
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app and configure CORS middleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables and initialize Supabase client with service role key for bypassing RLS
load_dotenv()

# Initialize client
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

def diagnose_table(table_name: str):
    print(f"\nDiagnosing table: {table_name}")
    
    try:
        data = supabase.table(table_name).select("*").execute()
        print(f"Data: {data.data}")
        return data.data
    except:
        print("Couldn't get query data")

@app.get("/agent-log/timeline")
def get_agent_log():
    table_name = "agent_logs"  # Replace with your table name
    data = diagnose_table(table_name)
    return JSONResponse(content=data)

@app.post("/agent-log/save")
async def save_agent_log(request: Request):
    try:
        data = await request.json()
        response = supabase.table("agent_logs").insert(data).execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    table_name = "agent_logs"  # Replace with your table name
    query = diagnose_table(table_name)
    
    # Alternative direct access
    print("\nDirect query results:")
    print(query)
    
import uvicorn
uvicorn.run(app, host="192.168.1.19", port=8501)
>>>>>>> 10bd3819fec539bdc1992505f9a5b8ef7bbbbe6a
