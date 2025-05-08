import os
import logging
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Set up logging
def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Create a log filename with timestamp
    log_filename = f"logs/supabase_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger()

# Main function
def main():
    logger = setup_logging()
    logger.info("Script started")
    
    try:
        # Load environment variables from .env file
        load_dotenv()
        logger.info("Environment variables loaded")
        
        # Set up Supabase using environment variables
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase URL or Key not found in environment variables")
            
        logger.info("Initializing Supabase client")
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Query the database
        logger.info("Querying learning_history table")
        response = supabase.table("learning_history").select("*").execute()
        
        # Process and log the response
        data = response.data
        logger.info(f"Retrieved {len(data)} records from learning_history table")
        logger.debug(f"Data: {data}")
        
        # Print data to console
        print("Retrieved data:")
        print(data)
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        raise
    finally:
        logger.info("Script completed")

if __name__ == "__main__":
    main()