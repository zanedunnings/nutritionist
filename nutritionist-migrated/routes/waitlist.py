from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, EmailStr

from models.database import get_db
from models.waitlist import WaitlistEmail

router = APIRouter()

class WaitlistEmailCreate(BaseModel):
    email: EmailStr

@router.post("/waitlist")
async def add_to_waitlist(
    email_data: WaitlistEmailCreate,
    db: Session = Depends(get_db)
):
    """Add an email to the waitlist."""
    try:
        # Check if email already exists
        existing_email = db.query(WaitlistEmail).filter(WaitlistEmail.email == email_data.email).first()
        if existing_email:
            return {"message": "Email already on waitlist"}
        
        # Create new waitlist entry
        waitlist_email = WaitlistEmail(email=email_data.email)
        db.add(waitlist_email)
        db.commit()
        db.refresh(waitlist_email)
        
        return {"message": "Successfully added to waitlist"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/waitlist/count")
async def get_waitlist_count(
    db: Session = Depends(get_db)
):
    """Get the total number of emails on the waitlist."""
    count = db.query(WaitlistEmail).count()
    return {"count": count} 