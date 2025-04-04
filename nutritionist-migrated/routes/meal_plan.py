from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json
import os

from services.meal_plan_service import (
    get_meal_plan,
    create_meal_plan,
    update_meal_plan,
    delete_meal_plan,
    get_all_meal_plans,
    call_claude,
    get_meal_prompt,
    get_week_key,
    generate_grocery_list
)
from models.database import get_db
from routes.auth import get_current_user
from models.user import User
from models.meal_plan import MealPlan

router = APIRouter()

def get_week_key() -> str:
    """Get the current week key in YYYY-MM-DD format."""
    today = datetime.now()
    # Get the start of the week (Monday)
    start_of_week = today - timedelta(days=today.weekday())
    return start_of_week.strftime("%Y-%m-%d")

@router.get("/meal-plan")
async def read_meal_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the meal plan for the current user and week."""
    week_key = get_week_key()
    meal_plan = get_meal_plan(db, current_user.id, week_key)
    if meal_plan:
        return json.loads(meal_plan.plan_data)
    return None

@router.post("/meal-plan/generate")
async def generate_meal_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a new meal plan for the current user."""
    try:
        week_key = get_week_key()
        # Generate a sample meal plan (replace with actual generation logic)
        plan_data = {
            "overview": "A balanced meal plan for the week with a variety of healthy options.",
            "daily_plans": {
                "monday": {
                    "breakfast": "Oatmeal with berries",
                    "lunch": "Chicken salad",
                    "dinner": "Grilled salmon with vegetables"
                },
                "tuesday": {
                    "breakfast": "Greek yogurt with granola",
                    "lunch": "Turkey sandwich",
                    "dinner": "Beef stir-fry"
                },
                "wednesday": {
                    "breakfast": "Scrambled eggs with toast",
                    "lunch": "Quinoa bowl with vegetables",
                    "dinner": "Grilled chicken with sweet potatoes"
                },
                "thursday": {
                    "breakfast": "Smoothie bowl",
                    "lunch": "Tuna salad wrap",
                    "dinner": "Vegetable stir-fry with tofu"
                },
                "friday": {
                    "breakfast": "Avocado toast",
                    "lunch": "Grilled cheese and tomato soup",
                    "dinner": "Baked salmon with asparagus"
                },
                "saturday": {
                    "breakfast": "Pancakes with fruit",
                    "lunch": "Caesar salad with chicken",
                    "dinner": "Beef tacos with all the fixings"
                },
                "sunday": {
                    "breakfast": "French toast",
                    "lunch": "Turkey and cheese sandwich",
                    "dinner": "Roast chicken with vegetables"
                }
            },
            "grocery_list": {
                "Produce": [
                    "Berries",
                    "Salmon",
                    "Vegetables",
                    "Sweet potatoes",
                    "Asparagus",
                    "Fruit",
                    "Chicken"
                ],
                "Dairy": [
                    "Greek yogurt",
                    "Cheese",
                    "Milk",
                    "Eggs"
                ],
                "Meat": [
                    "Chicken breast",
                    "Ground beef",
                    "Turkey",
                    "Salmon"
                ],
                "Pantry": [
                    "Oatmeal",
                    "Granola",
                    "Quinoa",
                    "Bread",
                    "Rice",
                    "Tortillas"
                ]
            }
        }
        
        # Create the meal plan with timestamps
        meal_plan = MealPlan(
            user_id=current_user.id,
            week_key=week_key,
            plan_data=json.dumps(plan_data),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(meal_plan)
        db.commit()
        db.refresh(meal_plan)
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=plan_data
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Failed to generate meal plan: {str(e)}"}
        )

@router.get("/meal-plan/{week_key}")
async def get_meal_plan_by_week(
    week_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific meal plan by week key."""
    meal_plan = get_meal_plan(db, current_user.id, week_key)
    if meal_plan:
        return json.loads(meal_plan.plan_data)
    raise HTTPException(status_code=404, detail="Meal plan not found")

@router.post("/meal-plan/{week_key}")
async def create_meal_plan_by_week(
    week_key: str,
    plan_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a meal plan for a specific week."""
    meal_plan = create_meal_plan(db, current_user.id, week_key, plan_data)
    return json.loads(meal_plan.plan_data)

@router.put("/meal-plan/{week_key}")
async def update_meal_plan_by_week(
    week_key: str,
    plan_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a meal plan for a specific week."""
    meal_plan = update_meal_plan(db, current_user.id, week_key, plan_data)
    if meal_plan:
        return json.loads(meal_plan.plan_data)
    raise HTTPException(status_code=404, detail="Meal plan not found")

@router.delete("/meal-plan/{week_key}")
async def delete_meal_plan_by_week(
    week_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a meal plan for a specific week."""
    success = delete_meal_plan(db, current_user.id, week_key)
    if not success:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return {"message": "Meal plan deleted successfully"}

@router.get("/meal-plan/{week_key}/grocery-list")
async def get_grocery_list(
    week_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the grocery list for a specific meal plan."""
    meal_plan = get_meal_plan(db, current_user.id, week_key)
    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    plan_data = json.loads(meal_plan.plan_data)
    return generate_grocery_list(plan_data)

@router.get("/")
async def read_meal_plans_old(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    week_key = get_week_key()
    meal_plans = get_all_meal_plans(db, current_user.id, week_key)
    return meal_plans

@router.get("/{meal_plan_id}")
async def read_meal_plan(
    meal_plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    meal_plan = get_meal_plan(db, meal_plan_id)
    if meal_plan is None:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return meal_plan

@router.post("/")
async def create_meal_plan_endpoint(
    meal_plan: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_meal_plan(db, meal_plan)

@router.put("/{meal_plan_id}")
async def update_meal_plan_endpoint(
    meal_plan_id: int,
    meal_plan: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated_meal_plan = update_meal_plan(db, meal_plan_id, meal_plan)
    if updated_meal_plan is None:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return updated_meal_plan

@router.delete("/{meal_plan_id}")
async def delete_meal_plan_endpoint(
    meal_plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = delete_meal_plan(db, meal_plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return {"status": "success"}

@router.post("/generate")
async def generate_meal_plan_old(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Get the current week key
        week_key = get_week_key()
        
        # Generate meal plan using Claude
        prompt = get_meal_prompt()
        response = call_claude(prompt)
        
        if isinstance(response, dict) and "error" in response:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate meal plan: {response['error']}"
            )
        
        # Parse the response into a structured format
        try:
            plan_data = json.loads(response)
        except json.JSONDecodeError:
            # If response is not JSON, create a structured format
            plan_data = {
                "overview": response,
                "daily_plans": {},
                "grocery_list": {
                    "sunday": [],
                    "wednesday": []
                }
            }
        
        # Save the meal plan
        meal_plan = create_meal_plan(
            db=db,
            user_id=current_user.id,
            week_key=week_key,
            plan_data=plan_data
        )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Meal plan generated successfully",
                "meal_plan": meal_plan
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate meal plan: {str(e)}"
        ) 