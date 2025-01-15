from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .LLM_logic import process_message

# Define the request model for the message
class MessageRequest(BaseModel):
    text: str

class MessageResponse(BaseModel):
    message: str
    is_final: bool

# Create a FastAPI router instance
router = APIRouter()

@router.post("/message", response_model=MessageResponse)
async def send_message(request: MessageRequest):
    """
    Process incoming messages and return the next question or final response.
    
    Args:
        request: MessageRequest containing the user's message
        
    Returns:
        MessageResponse containing:
        - message: next question or final LLM response
        - is_final: boolean indicating if this is the final response
        
    Raises:
        HTTPException: If there's an error processing the message
    """
    try:
        if not request.text.strip():
            raise ValueError("Message cannot be empty")
            
        response, is_final = process_message(request.text)
        return MessageResponse(message=response, is_final=is_final)
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
