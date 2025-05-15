from supabase import create_client, Client
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test connection to Supabase and print table structure"""
    try:
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        print(f"Connecting to Supabase with URL: {supabase_url}")
        supabase = create_client(supabase_url, supabase_key)
        
        # Get the agent_logs table structure
        print("\nAttempting to query agent_logs table...")
        response = supabase.table("agent_logs").select("*").limit(1).execute()
        
        if response.data and len(response.data) > 0:
            print("\nSUCCESS: Retrieved data from agent_logs table")
            print("\nTable structure (column names):")
            print(list(response.data[0].keys()))
            
            print("\nSample record:")
            print(json.dumps(response.data[0], indent=2))
        else:
            print("\nTable exists but no records found")
            
            # Try to get table structure by inserting a test record
            print("\nAttempting to get table structure by inserting a test record...")
            test_record = {
                "user_id": "test_user",
                "agent": "test_agent",
                "action": "test_action",
                "details": {"test": "data"}
            }
            
            # Try to insert with different timestamp field names
            for timestamp_field in ["timestamp", "created_at", "time", "date"]:
                try:
                    test_record_with_timestamp = test_record.copy()
                    test_record_with_timestamp[timestamp_field] = "2023-01-01T00:00:00"
                    
                    print(f"\nTrying with timestamp field: {timestamp_field}")
                    insert_response = supabase.table("agent_logs").insert(test_record_with_timestamp).execute()
                    
                    if insert_response.data:
                        print(f"SUCCESS: Record inserted with {timestamp_field}")
                        print("Inserted record structure:")
                        print(list(insert_response.data[0].keys()))
                        break
                except Exception as e:
                    print(f"Failed with {timestamp_field}: {str(e)}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_supabase_connection()
