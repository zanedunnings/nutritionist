from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any

from models.database import get_db
from models.user import User
from services.meal_plan_service import get_meal_plan, get_all_meal_plans
from routes.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_week_key() -> str:
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    return start_of_week.strftime("%Y-%m-%d")

@router.get("/")
async def main_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        "main.html",
        {"request": request, "current_user": current_user}
    )

@router.get("/dashboard")
async def dashboard(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "current_user": current_user}
    )

@router.get("/profile")
async def profile(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": current_user}
    )

@router.get("/meal-plan")
async def meal_plan(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    week_key = get_week_key()
    meal_plan = get_meal_plan(db, current_user.id, week_key)
    
    return templates.TemplateResponse(
        "meal_plan.html",
        {"request": request, "current_user": current_user, "meal_plan": meal_plan}
    )

@router.get("/nutrition-stats")
async def nutrition_stats(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get the last 7 days of meal plans
    week_key = get_week_key()
    meal_plans = get_all_meal_plans(db, current_user.id, week_key)
    
    # Calculate nutrition stats
    nutrition_stats = {
        "daily_calories": 2000,  # Example value
        "daily_protein": 150,    # Example value
        "daily_carbs": 250,      # Example value
        "daily_fat": 70,         # Example value
        "weekly_labels": [f"Day {i+1}" for i in range(7)],
        "weekly_calories": [2000] * 7,  # Example values
        "recommendations": [
            "Increase protein intake by 10g per day",
            "Consider adding more vegetables to your meals",
            "Stay hydrated throughout the day"
        ]
    }
    
    return templates.TemplateResponse(
        "nutrition_stats.html",
        {"request": request, "current_user": current_user, "nutrition_stats": nutrition_stats}
    )

@router.get("/grocery-list")
async def grocery_list(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    week_key = get_week_key()
    meal_plan = get_meal_plan(db, current_user.id, week_key)
    
    # Example grocery list structure
    grocery_list = {
        "Produce": ["Apples", "Bananas", "Spinach", "Carrots"],
        "Dairy": ["Milk", "Cheese", "Yogurt"],
        "Meat": ["Chicken breast", "Ground beef", "Salmon"],
        "Pantry": ["Rice", "Pasta", "Olive oil", "Spices"]
    } if meal_plan else None
    
    return templates.TemplateResponse(
        "grocery_list.html",
        {"request": request, "current_user": current_user, "grocery_list": grocery_list}
    ) 