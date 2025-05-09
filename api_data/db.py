from pymongo import MongoClient
import os

# Use environment variable or hardcode your Mongo URI (use Compass URI)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)

db = client["student_db"]

# Define collections
user_collection = db["chat_collection"]
pdf_collection = db["pdf_collection"]        
image_collection = db["image_collection"]

lecture_collection=db['lectures']
test_collection=db['test']
subject_collection=db['subject']


#frontend change 
# 1. Send Query (POST /chatpost) : This query_id will be used to link the query and its response.

# 2. Fetch Response (GET /chatbot) : You will call the /chatbot endpoint to get the response for the query.
