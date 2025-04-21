from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Dict, List, Optional
from .base import Base

class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    week_key = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    plan_data = Column(Text, nullable=False)  # JSON string of meal plan data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="meal_plans")
    modifications = relationship("Modification", back_populates="meal_plan", cascade="all, delete-orphan")

    def get_daily_plans(self) -> dict:
        """Get the daily plans from the plan_data JSON string."""
        import json
        data = json.loads(self.plan_data)
        return data.get("daily_plans", {})

    def get_grocery_list(self) -> dict:
        """Get the grocery list from the plan_data JSON string."""
        import json
        data = json.loads(self.plan_data)
        return data.get("grocery_list", {})

class Modification(Base):
    __tablename__ = "modifications"

    id = Column(Integer, primary_key=True, index=True)
    meal_plan_id = Column(Integer, ForeignKey("meal_plans.id"), nullable=False)
    day = Column(String(10), nullable=False)  # e.g., "Monday", "Tuesday"
    meal_type = Column(String(20), nullable=False)  # e.g., "breakfast", "lunch", "dinner"
    original_meal = Column(Text, nullable=False)  # Original meal description
    modified_meal = Column(Text, nullable=False)  # Modified meal description
    reason = Column(Text)  # Optional reason for modification
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    meal_plan = relationship("MealPlan", back_populates="modifications")

# Pydantic models for API requests/responses
class Macros(BaseModel):
    calories: float
    protein: float
    carbs: float
    fat: float

class Meal(BaseModel):
    description: str
    ingredients: List[str]
    macros: Macros

class DailyPlan(BaseModel):
    breakfast: Meal
    lunch: Meal
    dinner: Meal

class GroceryList(BaseModel):
    proteins: List[str]
    vegetables: List[str]
    grains: List[str]
    fats: List[str]
    condiments: List[str]

class MealPlanCreate(BaseModel):
    daily_plans: Dict[str, DailyPlan]
    grocery_list: GroceryList

class MealPlanResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    daily_plans: Dict[str, DailyPlan]
    grocery_list: GroceryList 