from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.meal_plan import MealPlan, Modification
from config import MEAL_PLAN_DB
import json
import anthropic
import os
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get meal plan database path
MEAL_PLAN_DB = os.getenv("MEAL_PLAN_DB", "data/meal_plans.db")

# Global client variable to avoid repeated initialization
_anthropic_client = None

def get_anthropic_client():
    """Get Anthropic client instance with proper error handling"""
    global _anthropic_client
    if _anthropic_client is None:
        try:
            anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            _anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize Anthropic client: {e}")
    return _anthropic_client

def get_week_key():
    today = datetime.now()
    sunday = today - timedelta(days=today.weekday() + 1)
    return f"meal_plan_{sunday.strftime('%Y-%m-%d')}"

def save_meal_plan(db: Session, week_key: str, plan: dict):
    plan_json = json.dumps(plan)
    meal_plan = MealPlan(week_key=week_key, plan=plan)
    db.merge(meal_plan)
    db.commit()

def get_meal_plan(db: Session, user_id: int, week_key: str) -> Optional[Dict[str, Any]]:
    """Get the meal plan for a specific user and week."""
    meal_plan = db.query(MealPlan).filter(
        MealPlan.user_id == user_id,
        MealPlan.week_key == week_key
    ).first()
    
    if meal_plan:
        return meal_plan
    return None

def add_modification(db: Session, week_key: str, modification: dict):
    mod = Modification(
        week_key=week_key,
        timestamp=datetime.now(),
        context=modification.get("context"),
        day=modification.get("day"),
        response=modification["response"]
    )
    db.add(mod)
    db.commit()

def call_claude(prompt, model="claude-3-5-sonnet-20241022", max_tokens=8000, temperature=0.7):
    """Call Claude with proper error handling and client initialization"""
    try:
        client = get_anthropic_client()
        
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return {"error": str(e)}

def get_meal_prompt():
    return """
System:
You are a nutritionist AI.

Use the following details to create a structured 7-day meal plan:
Goal & Macros:
- Daily Calories: ~1,900–2,200
- Daily Protein: ~200g
- 5 meals per day: Breakfast (~35g protein, ~350 kcal), AM Snack (~30g protein, ~250 kcal), Lunch (~45g protein, ~450 kcal), PM Snack (~30g protein, ~250 kcal), Dinner (~60g protein, ~600–700 kcal)
- Must be gluten-free (use GF alternatives: bread, pasta, sauces, etc.)
Lifestyle Details:
- Meal prep on Sunday and Wednesday
- No-cook dinners on Monday and Wednesday (use leftovers from Sunday or Wednesday's prep)
- 2 grocery runs: Sunday and Wednesday
- Include: premade salad bags for quick veggies, premade protein shakes (e.g. Fairlife), leftover proteins (e.g. rotisserie chicken, ground turkey) to minimize effort.

Plan Format:
- Overview of the 7-day plan and calorie/protein goals
- Day-by-Day breakdown (Sunday to Saturday), highlighting:
  - Which days I'm cooking fresh vs. using leftovers
  - Which days are "no-cook" dinners (Monday & Wednesday)
- Meal Prep instructions:
  - On Sunday: specify proteins, carbs, veggies to cook in bulk for Mon/Tue/(Wed)
  - On Wednesday: specify proteins, carbs, veggies to cook for Thu/Fri/(Sat)
- Grocery Lists:
  - A Sunday grocery list
  - A Wednesday grocery list
- Suggestions for flavor combos, leftover usage, optional ingredients (like avocado, hummus, cheese if tolerated)
- Format the plan with approximate protein/cals for each meal

IMPORTANT DETAILS:
- Include specific portion sizes for all meat (e.g., "6oz chicken breast", "4oz ground turkey")
- Include portion sizes for carbs and vegetables where applicable
- Be precise about quantities to help with meal prep and shopping

Other Notes:
- Adjust if weight loss is <1 lb/week or >2 lbs/week by tweaking calories as needed.
- Keep it interesting, flexible, and seasonally varied.
- I like most food types. Asian and medeterranian food are favorites.
- Summarize clearly so it's easy to follow.
- assume for fish it's hard to have left overs unless its from meal prepping

Include each meal for every day of the week. Also include a list of groceries and what I should do for prep days.
Ensure any meals provided have ingredients from a prior day of shopping for groceries. Don't include meals if the item wasn't included in groceries.

Meals should vary in cuisine and use little "hacks" to make the macro nutrients work in my favor. 
Here are some example meals to give you ideas:
 - Stuffed Peppers w/ Ground Turkey (6oz) & Cauliflower Rice (1 cup)
 - Asian Beef Bowl w/ Lean Ground Beef (5oz), Kimchi (1/2 cup) & Brown Rice (3/4 cup)
 - Spaghetti w/ Turkey Meat (4oz) & Lentil Pasta (2oz dry)
 - Thai Red Curry Shrimp (6oz) w/ Light Coconut Milk & Rice (3/4 cup)
 - New York Strip Steak (5oz) & Bagged Salad (2 cups)
 - Ground Chicken Lettuce Wraps (6oz chicken, 6 lettuce leaves)
"""

def get_all_meal_plans(db: Session, user_id: int, week_key: str) -> List[Dict[str, Any]]:
    """Get all meal plans for a specific user and week."""
    meal_plans = db.query(MealPlan).filter(
        MealPlan.user_id == user_id,
        MealPlan.week_key == week_key
    ).all()
    
    return meal_plans

def generate_meal_plan_data() -> Dict[str, Any]:
    """Generate a sample meal plan with overview and grocery list."""
    return {
        "overview": """
        This meal plan is designed to provide balanced nutrition throughout the week.
        It includes a variety of proteins, vegetables, and healthy carbohydrates.
        Meals are planned to be easy to prepare and can be batch cooked for efficiency.
        """,
        "daily_plans": {
            "monday": {
                "breakfast": "Oatmeal with berries and nuts (1 cup oats, 1/2 cup berries, 1/4 cup nuts)",
                "lunch": "Grilled chicken salad (6oz chicken, mixed greens, 1/4 avocado, balsamic vinaigrette)",
                "dinner": "Baked salmon with roasted vegetables (6oz salmon, 1 cup mixed vegetables)"
            },
            "tuesday": {
                "breakfast": "Greek yogurt with granola and honey (1 cup yogurt, 1/2 cup granola, 1 tbsp honey)",
                "lunch": "Turkey and avocado wrap (4oz turkey, 1/4 avocado, whole wheat wrap)",
                "dinner": "Beef stir-fry with brown rice (6oz beef, 1 cup vegetables, 1/2 cup rice)"
            },
            "wednesday": {
                "breakfast": "Scrambled eggs with spinach (3 eggs, 1 cup spinach, 1 slice whole wheat toast)",
                "lunch": "Quinoa bowl with roasted vegetables (1 cup quinoa, 1 cup vegetables, 1/4 cup feta)",
                "dinner": "Grilled chicken with sweet potato (6oz chicken, 1 medium sweet potato)"
            },
            "thursday": {
                "breakfast": "Smoothie bowl (1 banana, 1 cup berries, 1 scoop protein powder, 1/4 cup granola)",
                "lunch": "Tuna salad with crackers (5oz tuna, mixed greens, 10 whole grain crackers)",
                "dinner": "Pork tenderloin with roasted Brussels sprouts (6oz pork, 1 cup Brussels sprouts)"
            },
            "friday": {
                "breakfast": "Avocado toast with eggs (2 slices whole wheat bread, 1/2 avocado, 2 eggs)",
                "lunch": "Chicken and vegetable soup (6oz chicken, 1 cup vegetables, 1 cup broth)",
                "dinner": "Grilled shrimp with quinoa (6oz shrimp, 1 cup quinoa, 1 cup vegetables)"
            }
        },
        "grocery_list": {
            "Produce": [
                "Mixed greens",
                "Berries (strawberries, blueberries)",
                "Avocado",
                "Mixed vegetables",
                "Spinach",
                "Sweet potatoes",
                "Brussels sprouts",
                "Bananas"
            ],
            "Protein": [
                "Chicken breast",
                "Salmon fillets",
                "Ground turkey",
                "Beef strips",
                "Pork tenderloin",
                "Shrimp",
                "Eggs",
                "Greek yogurt"
            ],
            "Pantry": [
                "Oats",
                "Granola",
                "Quinoa",
                "Brown rice",
                "Whole wheat bread",
                "Whole wheat wraps",
                "Crackers",
                "Nuts"
            ],
            "Dairy": [
                "Feta cheese",
                "Milk",
                "Butter"
            ]
        }
    }

def create_meal_plan(db: Session, user_id: int, week_key: str, plan_data: Optional[Dict[str, Any]] = None) -> MealPlan:
    """Create a new meal plan for a user."""
    if plan_data is None:
        plan_data = generate_meal_plan_data()
    
    meal_plan = MealPlan(
        user_id=user_id,
        week_key=week_key,
        plan_data=json.dumps(plan_data)
    )
    db.add(meal_plan)
    db.commit()
    db.refresh(meal_plan)
    return meal_plan

def update_meal_plan(db: Session, user_id: int, week_key: str, plan_data: Dict[str, Any]) -> Optional[MealPlan]:
    """Update an existing meal plan."""
    meal_plan = db.query(MealPlan).filter(
        MealPlan.user_id == user_id,
        MealPlan.week_key == week_key
    ).first()
    
    if meal_plan:
        meal_plan.plan_data = json.dumps(plan_data)
        db.commit()
        db.refresh(meal_plan)
        return meal_plan
    return None

def delete_meal_plan(db: Session, user_id: int, week_key: str) -> bool:
    """Delete a meal plan."""
    meal_plan = db.query(MealPlan).filter(
        MealPlan.user_id == user_id,
        MealPlan.week_key == week_key
    ).first()
    
    if meal_plan:
        db.delete(meal_plan)
        db.commit()
        return True
    return False

def generate_grocery_list(meal_plan: Dict[str, Any]) -> Dict[str, List[str]]:
    """Generate a grocery list from a meal plan."""
    if not meal_plan:
        return {}
    
    grocery_list = {
        "Produce": [],
        "Dairy": [],
        "Meat": [],
        "Pantry": []
    }
    
    # Example implementation - in a real app, this would analyze the meal plan
    # and extract ingredients based on recipes
    for day, meals in meal_plan.get("daily_plans", {}).items():
        for meal, details in meals.items():
            # Add example ingredients based on meal type
            if "breakfast" in meal.lower():
                grocery_list["Dairy"].append("Milk")
                grocery_list["Pantry"].append("Cereal")
            elif "lunch" in meal.lower():
                grocery_list["Produce"].append("Lettuce")
                grocery_list["Meat"].append("Chicken")
            elif "dinner" in meal.lower():
                grocery_list["Produce"].append("Potatoes")
                grocery_list["Meat"].append("Beef")
    
    # Remove duplicates
    for category in grocery_list:
        grocery_list[category] = list(set(grocery_list[category]))
    
    return grocery_list 