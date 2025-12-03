"""Chat routes for conversation and message management."""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime
from app.config.database import get_db
from app.models.models import User, Conversation, Message
from app.services.auth_service import verify_token
from app.services.gen_ai_service import gen_ai_service

router = APIRouter(prefix="/chat", tags=["chat"])


class MessageCreate(BaseModel):
    """Schema for creating a message."""
    role: str
    content: str


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: int
    role: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """Schema for creating a conversation."""
    title: str = "New Conversation"


class ConversationResponse(BaseModel):
    """Schema for conversation response."""
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    """Schema for detailed conversation with messages."""
    messages: List[MessageResponse]


class ChatRequest(BaseModel):
    """Schema for chat request."""
    conversation_id: int
    message: str


class ChatResponse(BaseModel):
    """Schema for chat response."""
    assistant_message: str
    message_id: int


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    data: ConversationCreate,
    user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create a new conversation for the user."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    conversation = Conversation(user_id=user_id, title=data.title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """List all conversations for the user."""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(Conversation.updated_at.desc()).all()
    
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get a specific conversation with all messages."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def send_message(
    conversation_id: int,
    chat_request: ChatRequest,
    user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Send a message and get AI response.
    
    Args:
        conversation_id: ID of the conversation
        chat_request: Message content
        user_id: Authenticated user ID
        db: Database session
        
    Returns:
        AI response and message ID
    """
    # Verify conversation ownership
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Save user message
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=chat_request.message
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Get conversation history
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()
    
    # Format for Gen AI
    message_history = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]
    
    # Get AI response
    try:
        ai_response = await gen_ai_service.generate_response(message_history)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating response: {str(e)}"
        )
    
    # Save assistant message
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=ai_response
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    
    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "assistant_message": ai_response,
        "message_id": assistant_message.id
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete a conversation and all its messages."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    db.delete(conversation)
    db.commit()
    
    return {"message": "Conversation deleted successfully"}
