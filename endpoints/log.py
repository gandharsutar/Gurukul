import os
from supabase import create_client
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
uvicorn.run(app, host="192.168.0.94", port=8000)