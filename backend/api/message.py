from fastapi import APIRouter
from pydantic import BaseModel

# Define the request model for the message
class MessageRequest(BaseModel):
    text: str

# Create a FastAPI router instance
router = APIRouter()

@router.post("/message")
async def send_message(request: MessageRequest):
    """
    Dummy message endpoint that simulates backend processing.
    Returns a response with the message received.
    """
    return {"message": f"Message received: {request.text}"}
