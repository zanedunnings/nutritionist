from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
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
from models.meal_plan import MealPlan, MealPlanCreate, MealPlanResponse, Macros, Meal, DailyPlan, GroceryList

router = APIRouter()

def get_week_key() -> str:
    """Get the current week key in YYYY-MM-DD format."""
    today = datetime.now()
    # Get the start of the week (Monday)
    start_of_week = today - timedelta(days=today.weekday())
    return start_of_week.strftime("%Y-%m-%d")

def create_meal_from_dict(meal_dict: Any) -> Meal:
    """Create a Meal object from a dictionary or string."""
    if isinstance(meal_dict, str):
        # If it's a string, treat it as a description
        return Meal(
            description=meal_dict,
            ingredients=[],
            macros=Macros(calories=0, protein=0, carbs=0, fat=0)
        )
    
    # If it's a dictionary, extract the values
    return Meal(
        description=meal_dict.get("description", ""),
        ingredients=meal_dict.get("ingredients", []),
        macros=Macros(
            calories=meal_dict.get("macros", {}).get("calories", 0),
            protein=meal_dict.get("macros", {}).get("protein", 0),
            carbs=meal_dict.get("macros", {}).get("carbs", 0),
            fat=meal_dict.get("macros", {}).get("fat", 0)
        )
    )

def create_daily_plan_from_dict(day_dict: Dict[str, Any]) -> DailyPlan:
    """Create a DailyPlan object from a dictionary."""
    return DailyPlan(
        breakfast=create_meal_from_dict(day_dict.get("breakfast", {})),
        lunch=create_meal_from_dict(day_dict.get("lunch", {})),
        dinner=create_meal_from_dict(day_dict.get("dinner", {}))
    )

def create_grocery_list_from_dict(grocery_dict: Dict[str, List[str]]) -> GroceryList:
    """Create a GroceryList object from a dictionary."""
    return GroceryList(
        proteins=grocery_dict.get("proteins", []),
        vegetables=grocery_dict.get("vegetables", []),
        grains=grocery_dict.get("grains", []),
        fats=grocery_dict.get("fats", []),
        condiments=grocery_dict.get("condiments", [])
    )

@router.get("/meal-plan", response_model=MealPlanResponse)
async def get_meal_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current meal plan for the user"""
    meal_plan = db.query(MealPlan).filter(
        MealPlan.user_id == current_user.id
    ).order_by(MealPlan.created_at.desc()).first()
    
    if not meal_plan:
        raise HTTPException(status_code=404, detail="No meal plan found")
    
    try:
        plan_data = json.loads(meal_plan.plan_data)
    except json.JSONDecodeError:
        # If the plan_data is not valid JSON, create a default structure
        plan_data = {
            "daily_plans": {},
            "grocery_list": {
                "proteins": [],
                "vegetables": [],
                "grains": [],
                "fats": [],
                "condiments": []
            }
        }
    
    # Convert the plan data to the proper structure
    daily_plans = {
        day: create_daily_plan_from_dict(meals)
        for day, meals in plan_data.get("daily_plans", {}).items()
    }
    
    grocery_list = create_grocery_list_from_dict(plan_data.get("grocery_list", {}))
    
    return MealPlanResponse(
        id=meal_plan.id,
        user_id=meal_plan.user_id,
        created_at=meal_plan.created_at,
        daily_plans=daily_plans,
        grocery_list=grocery_list
    )

@router.post("/meal-plan/generate", response_model=MealPlanResponse)
async def generate_meal_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a new meal plan for the user"""
    # Example meal plan with nutrition facts
    example_plan = {
        "daily_plans": {
            "monday": {
                "breakfast": {
                    "description": "Scrambled eggs with whole wheat toast and avocado",
                    "ingredients": [
                        "2 large eggs",
                        "1 slice whole wheat bread",
                        "1/2 avocado",
                        "1 tsp olive oil",
                        "Salt and pepper to taste"
                    ],
                    "macros": {
                        "calories": 350,
                        "protein": 18,
                        "carbs": 25,
                        "fat": 22
                    }
                },
                "lunch": {
                    "description": "Grilled chicken salad with mixed greens",
                    "ingredients": [
                        "4 oz grilled chicken breast",
                        "2 cups mixed greens",
                        "1/4 cup cherry tomatoes",
                        "1/4 cup cucumber",
                        "1 tbsp olive oil",
                        "1 tbsp balsamic vinegar"
                    ],
                    "macros": {
                        "calories": 320,
                        "protein": 30,
                        "carbs": 12,
                        "fat": 18
                    }
                },
                "dinner": {
                    "description": "Baked salmon with quinoa and steamed broccoli",
                    "ingredients": [
                        "5 oz salmon fillet",
                        "1/2 cup cooked quinoa",
                        "1 cup steamed broccoli",
                        "1 tsp olive oil",
                        "Lemon wedges"
                    ],
                    "macros": {
                        "calories": 450,
                        "protein": 35,
                        "carbs": 35,
                        "fat": 20
                    }
                }
            }
        },
        "grocery_list": {
            "proteins": ["Eggs", "Chicken breast", "Salmon fillet"],
            "vegetables": ["Mixed greens", "Cherry tomatoes", "Cucumber", "Broccoli"],
            "grains": ["Whole wheat bread", "Quinoa"],
            "fats": ["Avocado", "Olive oil"],
            "condiments": ["Balsamic vinegar", "Salt", "Pepper", "Lemon"]
        }
    }
    
    # Create new meal plan
    meal_plan = MealPlan(
        user_id=current_user.id,
        week_key=get_week_key(),
        plan_data=json.dumps(example_plan),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(meal_plan)
    db.commit()
    db.refresh(meal_plan)
    
    # Convert the plan data to the proper structure
    daily_plans = {
        day: create_daily_plan_from_dict(meals)
        for day, meals in example_plan["daily_plans"].items()
    }
    
    grocery_list = create_grocery_list_from_dict(example_plan["grocery_list"])
    
    return MealPlanResponse(
        id=meal_plan.id,
        user_id=meal_plan.user_id,
        created_at=meal_plan.created_at,
        daily_plans=daily_plans,
        grocery_list=grocery_list
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