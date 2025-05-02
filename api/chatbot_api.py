# chatbot_api.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Request schema
class Message(BaseModel):
    user_message: str

# Simple rule-based response
def get_bot_response(user_message: str) -> str:
    if "hello" in user_message.lower():
        return "Hi there! How can I help you today?"
    elif "bye" in user_message.lower():
        return "Goodbye!"
    else:
        return "I'm not sure how to respond to that."

# POST endpoint
@app.post("/chat")
async def chat(msg: Message):
    response = get_bot_response(msg.user_message)
    return {"bot_response": response}
