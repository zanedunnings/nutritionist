from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from .database import Base
import bcrypt
import logging

logger = logging.getLogger(__name__)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Relationships
    meal_plans = relationship("MealPlan", back_populates="user", cascade="all, delete-orphan")

    def verify_password(self, plain_password: str) -> bool:
        try:
            if not self.hashed_password:
                logger.error("No password hash found for user")
                return False
                
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                self.hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def set_password(self, plain_password: str) -> None:
        try:
            if not plain_password:
                raise ValueError("Password cannot be empty")
                
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
            self.hashed_password = hashed.decode('utf-8')
            logger.debug(f"Password set for user {self.username}")
        except Exception as e:
            logger.error(f"Password hashing error: {e}")
            raise 