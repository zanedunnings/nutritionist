from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import json
from replit import db
import anthropic
from get_todays_plan import get_meal_plan_for_today, format_meal_plan_for_sms, send_meal_plan_sms
from create_weekly_plans import get_week_key

def get_current_context() -> Optional[Dict[str, Any]]:
    """Get the current meal plan context if it exists"""
    week_key = get_week_key()
    print(week_key)
    print(list(db.keys()))

    if week_key not in db:
        return None

    # Get the stored meal plan data
    meal_plan_data = db[week_key]

    # If it's a string, try to parse it as JSON
    if isinstance(meal_plan_data, str):
        try:
            meal_plan = json.loads(meal_plan_data)
        except json.JSONDecodeError:
            return None
    else:
        # If it's already a dictionary, use it directly
        meal_plan = meal_plan_data

    # Check if we have a valid meal plan structure
    if "meal_plan" not in meal_plan:
        return None

    if "daily_plans" not in meal_plan["meal_plan"]:
        return None

    # Get today's day of the week in lowercase
    today = datetime.now().strftime("%A").lower()

    # Check if today's plan exists
    if today not in meal_plan["meal_plan"]["daily_plans"]:
        return None

    today_plan = meal_plan["meal_plan"]["daily_plans"][today]

    return {
        'week_key': week_key,
        'current_plan': meal_plan["meal_plan"],
        'today_plan': today_plan,
        'day': today,
        'overview': meal_plan["meal_plan"].get("overview", {}),
        'meal_prep': meal_plan["meal_plan"].get("meal_prep", {}),
        'grocery_lists': meal_plan["meal_plan"].get("grocery_lists", {})
    }

def format_meal_for_claude(meal):
    """Format a meal object into a string for Claude prompt"""
    if not meal:
        return "Not specified"

    result = f"{meal['description']}\n"
    result += f"  Protein: {meal['protein']}g, Carbs: {meal['carbs']}g, "
    result += f"Fats: {meal['fats']}g, Calories: {meal['calories']}"
    return result

def handle_meal_interaction(phone_number: str, message: str, claude_api_key: str) -> bool:
    """
    Handle meal plan interactions using Claude for natural language understanding
    """
    # Get current context
    context = get_current_context()
    print(context)

    if not context:
        send_meal_plan_sms(phone_number, "I couldn't find your current meal plan. Please make sure one is generated first.")
        return False

    # Format the meals for the prompt
    today_plan = context['today_plan']
    breakfast = format_meal_for_claude(today_plan.get('breakfast'))
    am_snack = format_meal_for_claude(today_plan.get('am_snack'))
    lunch = format_meal_for_claude(today_plan.get('lunch'))
    pm_snack = format_meal_for_claude(today_plan.get('pm_snack'))
    dinner = format_meal_for_claude(today_plan.get('dinner'))

    # Get daily totals
    try:
        total_protein = sum(today_plan[meal]['protein'] for meal in ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner'])
        total_carbs = sum(today_plan[meal]['carbs'] for meal in ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner'])
        total_fats = sum(today_plan[meal]['fats'] for meal in ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner'])
        total_calories = sum(today_plan[meal]['calories'] for meal in ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner'])

        daily_totals = f"Total Protein: {total_protein}g, Total Carbs: {total_carbs}g, Total Fats: {total_fats}g, Total Calories: {total_calories}"
    except:
        daily_totals = "Unable to calculate totals"

    # Create prompt for Claude that includes context and handling instructions
    prompt = f"""Current meal plan for {context['day'].capitalize()}:

Breakfast: {breakfast}

AM Snack: {am_snack}

Lunch: {lunch}

PM Snack: {pm_snack}

Dinner: {dinner}

Daily Totals: {daily_totals}

User message: {message}

Please help with this meal plan request. You can:
1. Suggest alternative meals
2. Provide recipes and cooking instructions
3. Handle meal substitutions and recommend adjustments
4. Answer questions about the meal plan

Keep responses concise and actionable since they'll be sent via SMS.
If the user's request isn't related to these categories, politely explain what you can help with.
Ensure all responses and answers approximately follow the calories and macros in the meal plan, unless specified they want to be different.
If the user's request is not related to the meal plan, politely explain you cannot answer.
If this is a meal substitution, include "SUBSTITUTION_RECORDED" at the start of your response so I know to update the database.
"""

    # Call Claude API
    client = anthropic.Client(api_key=claude_api_key)
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=500,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )
    response_text = response.content[0].text

    # Check if this was a substitution that needs recording
    if response_text.startswith("SUBSTITUTION_RECORDED"):
        response_text = response_text.replace("SUBSTITUTION_RECORDED", "").strip()
        # Record the modification
        modifications_key = f"{context['week_key']}_modifications"
        modifications = db.get(modifications_key, [])
        modifications.append({
            'day': context['day'],
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'response': response_text
        })
        db[modifications_key] = modifications

    cleaned_text = response_text.replace("SUBSTITUTION_RECORDED", "").strip()

    # Send response
    send_meal_plan_sms(phone_number, cleaned_text)
    return True