"""
Test Supabase Connection Script
-------------------------------
This script tests the connection to Supabase and verifies that 
the imports and code structure are working correctly.
"""

try:
    # Test importing the Supabase client
    from backend.supabase import supabase, get_all_users
    
    # Test importing functions from supabase_utils
    from backend.supabase_utils import (
        get_user_profile,
        get_lesson_completion_records,
        get_user_details
    )
    
    print("✅ Imports successful!")
    
    # Test Supabase connection
    try:
        print("\nTesting Supabase connection...")
        # A simple query that should work even if no data exists
        response = supabase.from_("user_profiles").select("count", count="exact").execute()
        print(f"✅ Connection successful! Found {response.count} user profiles.")
        
        # Test auth
        try:
            user = supabase.auth.get_user()
            if user and hasattr(user, 'user') and user.user:
                print(f"✅ Current user: {user.user.get('email', 'Unknown')}")
            else:
                print("ℹ️ No user is currently logged in. This is expected if you haven't authenticated.")
        except Exception as e:
            print(f"⚠️ Auth check warning: {str(e)}")
        
        # Test getting users
        try:
            users = get_all_users()
            print(f"✅ Found {len(users)} users in the profiles table.")
        except Exception as e:
            print(f"⚠️ Users query warning: {str(e)}")
            
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\nPossible issues:")
        print("1. Supabase URL or API key might be incorrect")
        print("2. Network connectivity issues")
        print("3. Supabase service might be down")
        
except ImportError as e:
    print(f"❌ Import error: {str(e)}")
    print("\nPossible issues:")
    print("1. Make sure the 'backend' directory is in your Python path")
    print("2. Verify that you have installed the supabase package: pip install supabase")
    print("3. Check that all files (__init__.py, supabase.py, etc.) exist in the correct locations")

except Exception as e:
    print(f"❌ Unexpected error: {str(e)}")
    
print("\nTest complete!") 