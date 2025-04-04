from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base

class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    week_key = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    plan_data = Column(Text, nullable=False)  # JSON string of meal plan data
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="meal_plans")
    modifications = relationship("Modification", back_populates="meal_plan", cascade="all, delete-orphan")

class Modification(Base):
    __tablename__ = "modifications"

    id = Column(Integer, primary_key=True, index=True)
    meal_plan_id = Column(Integer, ForeignKey("meal_plans.id"), nullable=False)
    day = Column(String(10), nullable=False)  # e.g., "Monday", "Tuesday"
    meal_type = Column(String(20), nullable=False)  # e.g., "breakfast", "lunch", "dinner"
    original_meal = Column(Text, nullable=False)  # Original meal description
    modified_meal = Column(Text, nullable=False)  # Modified meal description
    reason = Column(Text)  # Optional reason for modification
    created_at = Column(DateTime, nullable=False)

    # Relationships
    meal_plan = relationship("MealPlan", back_populates="modifications") 