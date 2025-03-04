
# import re
# import os
# from datetime import datetime
# from replit import db
# from twilio.rest import Client
# from create_weekly_plans import get_week_key

# def parse_meal_plan(raw_text):
#     """ Parses the raw text and extracts meal plans by day. """
#     meal_plan = {}
#     current_day = None
#     current_meals = {}
#     in_meal_plan_section = False

#     lines = raw_text.split("\n")

#     for line in lines:
#         line = line.strip()

#         if "MEAL PLAN:" in line:
#             in_meal_plan_section = True
#             continue

#         if not in_meal_plan_section:
#             continue

#         day_match = re.match(r"^(SUNDAY|MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY)(?:\s*\(.*?\))?:?$", line, re.IGNORECASE)
#         if day_match:
#             if current_day:
#                 meal_plan[current_day] = current_meals
#             current_day = day_match.group(1).capitalize()
#             current_meals = {}
#             continue

#         meal_match = re.match(r"^(Breakfast|AM Snack|Lunch|PM Snack|Dinner):\s*(.*)$", line, re.IGNORECASE)
#         if meal_match and current_day:
#             meal_type = meal_match.group(1)
#             meal_desc = meal_match.group(2)
#             current_meals[meal_type] = meal_desc
#             continue

#         if line.startswith("Prep:") and current_day:
#             prep_steps = []
#             for prep_line in lines[lines.index(line) + 1:]:
#                 prep_line = prep_line.strip()
#                 if not prep_line or re.match(r"^(SUNDAY|MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY)", prep_line, re.IGNORECASE):
#                     break
#                 prep_steps.append(prep_line)
#             current_meals["Prep Instructions"] = prep_steps

#     if current_day:
#         meal_plan[current_day] = current_meals

#     return meal_plan

# def format_meal_plan_for_sms(meal_plan):
#     """Format meal plan into a concise SMS message"""
#     message = f"Meal Plan for {datetime.now().strftime('%A')}:\n\n"
#     for meal, description in meal_plan.items():
#         if meal != "Prep Instructions":
#             message += f"{meal}: {description}\n"
#     if "Prep Instructions" in meal_plan:
#         message += "\nPrep Steps:\n"
#         for step in meal_plan["Prep Instructions"]:
#             message += f"- {step}\n"
#     return message

# def send_meal_plan_sms(phone_number, message):
#     """Send meal plan via SMS using Twilio"""
#     account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
#     auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
#     from_number = os.environ.get('TWILIO_PHONE_NUMBER')
    
#     if not all([account_sid, auth_token, from_number]):
#         print("Twilio credentials not found in environment variables")
#         return False
    
#     client = Client(account_sid, auth_token)
#     try:
#         # Split message into chunks (max 1600 chars per SMS)
#         chunk_size = 1500
#         message_chunks = [message[i:i+chunk_size] for i in range(0, len(message), chunk_size)]
        
#         # Send each chunk with a counter
#         for i, chunk in enumerate(message_chunks, 1):
#             prefix = f"({i}/{len(message_chunks)}) "
#             client.messages.create(
#                 body=prefix + chunk,
#                 from_=from_number,
#                 to=phone_number
#             )
#         return True
#     except Exception as e:
#         print(f"Error sending SMS: {e}")
#         return False

# def get_meal_plan_for_today():
#     week_key = get_week_key()

#     if week_key not in db:
#         print(week_key)
#         print(db["meal_plan_2025-02-23"])
#         print("No meal plan found for this week. Run `weekly_plan.py` first.")
#         return None

#     raw_text = db[week_key]
#     today = datetime.now().strftime("%A")
#     meal_plan = parse_meal_plan(raw_text)

#     return meal_plan.get(today, {"error": f"No meal plan found for {today}"})

# if __name__ == "__main__":
#     today_plan = get_meal_plan_for_today()
#     if today_plan:
#         # Format meal plan for display
#         print(f"Today's Meal Plan ({datetime.now().strftime('%A')}):\n")
#         for meal, description in today_plan.items():
#             print(f"{meal}: {description}")
        
#         # Send SMS if phone number is provided
#         phone_number = os.environ.get('TARGET_PHONE_NUMBER')
#         if phone_number:
#             message = format_meal_plan_for_sms(today_plan)
#             if send_meal_plan_sms(phone_number, message):
#                 print("\nMeal plan sent via SMS successfully!")
#             else:
#                 print("\nFailed to send SMS")
import os
import json
from datetime import datetime
from replit import db
from twilio.rest import Client
from create_weekly_plans import get_week_key

def get_meal_plan_for_today():
    """Gets today's meal plan from the stored JSON data"""
    week_key = get_week_key()

    if week_key not in db:
        print(f"No meal plan found for this week ({week_key}). Run `weekly_plan.py` first.")
        return None

    # Get the stored JSON meal plan
    stored_data = db[week_key]

    # If the stored data is a string, try to parse it as JSON
    if isinstance(stored_data, str):
        try:
            meal_plan = json.loads(stored_data)
        except json.JSONDecodeError:
            print(f"Error: Stored meal plan is not valid JSON")
            return None
    else:
        # If it's already a dictionary, use it directly
        meal_plan = stored_data

    # Get today's day of the week in lowercase
    today = datetime.now().strftime("%A").lower()

    # Check if we have a valid meal plan structure
    if "meal_plan" not in meal_plan:
        print("Error: Invalid meal plan structure - missing 'meal_plan' key")
        return None

    if "daily_plans" not in meal_plan["meal_plan"]:
        print("Error: Invalid meal plan structure - missing 'daily_plans' key")
        return None

    if today not in meal_plan["meal_plan"]["daily_plans"]:
        print(f"Error: No meal plan found for {today}")
        return None

    # Return today's meal plan
    return meal_plan["meal_plan"]["daily_plans"][today]

def format_meal_plan_for_sms(meal_plan):
    """Format the JSON meal plan into a concise SMS message"""
    today = datetime.now().strftime("%A")
    message = f"Meal Plan for {today}:\n\n"

    # Format each meal with macros
    try:
        # Breakfast
        message += f"Breakfast: {meal_plan['breakfast']['description']}\n"
        message += f"  Protein: {meal_plan['breakfast']['protein']}g, Carbs: {meal_plan['breakfast']['carbs']}g, "
        message += f"Fats: {meal_plan['breakfast']['fats']}g, Calories: {meal_plan['breakfast']['calories']}\n\n"

        # AM Snack
        message += f"AM Snack: {meal_plan['am_snack']['description']}\n"
        message += f"  Protein: {meal_plan['am_snack']['protein']}g, Carbs: {meal_plan['am_snack']['carbs']}g, "
        message += f"Fats: {meal_plan['am_snack']['fats']}g, Calories: {meal_plan['am_snack']['calories']}\n\n"

        # Lunch
        message += f"Lunch: {meal_plan['lunch']['description']}\n"
        message += f"  Protein: {meal_plan['lunch']['protein']}g, Carbs: {meal_plan['lunch']['carbs']}g, "
        message += f"Fats: {meal_plan['lunch']['fats']}g, Calories: {meal_plan['lunch']['calories']}\n\n"

        # PM Snack
        message += f"PM Snack: {meal_plan['pm_snack']['description']}\n"
        message += f"  Protein: {meal_plan['pm_snack']['protein']}g, Carbs: {meal_plan['pm_snack']['carbs']}g, "
        message += f"Fats: {meal_plan['pm_snack']['fats']}g, Calories: {meal_plan['pm_snack']['calories']}\n\n"

        # Dinner
        message += f"Dinner: {meal_plan['dinner']['description']}\n"
        message += f"  Protein: {meal_plan['dinner']['protein']}g, Carbs: {meal_plan['dinner']['carbs']}g, "
        message += f"Fats: {meal_plan['dinner']['fats']}g, Calories: {meal_plan['dinner']['calories']}\n\n"

        # Add day-specific notes
        if meal_plan.get('is_prep_day', False):
            message += "NOTE: This is a prep day!\n"
        if meal_plan.get('is_no_cook_dinner', False):
            message += "NOTE: Today is a no-cook dinner day - use leftovers.\n"

        # Calculate daily totals
        total_protein = sum(meal_plan[meal]['protein'] for meal in ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner'])
        total_carbs = sum(meal_plan[meal]['carbs'] for meal in ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner'])
        total_fats = sum(meal_plan[meal]['fats'] for meal in ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner'])
        total_calories = sum(meal_plan[meal]['calories'] for meal in ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner'])

        message += f"\nDAILY TOTALS:\n"
        message += f"Protein: {total_protein}g, Carbs: {total_carbs}g, "
        message += f"Fats: {total_fats}g, Calories: {total_calories}"

    except KeyError as e:
        message += f"\nError: Missing data in meal plan: {e}"

    return message

def send_meal_plan_sms(phone_number, message):
    """Send meal plan via SMS using Twilio"""
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_number = os.environ.get('TWILIO_PHONE_NUMBER')

    if not all([account_sid, auth_token, from_number]):
        print("Twilio credentials not found in environment variables")
        return False

    client = Client(account_sid, auth_token)
    try:
        # Split message into chunks (max 1600 chars per SMS)
        chunk_size = 1500
        message_chunks = [message[i:i+chunk_size] for i in range(0, len(message), chunk_size)]

        # Send each chunk with a counter
        for i, chunk in enumerate(message_chunks, 1):
            prefix = f"({i}/{len(message_chunks)}) "
            client.messages.create(
                body=prefix + chunk,
                from_=from_number,
                to=phone_number
            )
        return True
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False

def format_meal_plan_for_display(meal_plan):
    """Format the meal plan for console display"""
    today = datetime.now().strftime("%A")
    output = f"\n===== MEAL PLAN FOR {today.upper()} =====\n\n"

    try:
        # Day-specific flags
        notes = []
        if meal_plan.get('is_prep_day', False):
            notes.append("PREP DAY")
        if meal_plan.get('is_no_cook_dinner', False):
            notes.append("NO-COOK DINNER")

        if notes:
            output += f"NOTE: This is a {' & '.join(notes)}\n\n"

        # Breakfast
        output += "🍳 BREAKFAST\n"
        output += f"{meal_plan['breakfast']['description']}\n"
        output += f"Protein: {meal_plan['breakfast']['protein']}g | "
        output += f"Carbs: {meal_plan['breakfast']['carbs']}g | "
        output += f"Fats: {meal_plan['breakfast']['fats']}g | "
        output += f"Calories: {meal_plan['breakfast']['calories']}\n\n"

        # AM Snack
        output += "🥪 AM SNACK\n"
        output += f"{meal_plan['am_snack']['description']}\n"
        output += f"Protein: {meal_plan['am_snack']['protein']}g | "
        output += f"Carbs: {meal_plan['am_snack']['carbs']}g | "
        output += f"Fats: {meal_plan['am_snack']['fats']}g | "
        output += f"Calories: {meal_plan['am_snack']['calories']}\n\n"

        # Lunch
        output += "🥗 LUNCH\n"
        output += f"{meal_plan['lunch']['description']}\n"
        output += f"Protein: {meal_plan['lunch']['protein']}g | "
        output += f"Carbs: {meal_plan['lunch']['carbs']}g | "
        output += f"Fats: {meal_plan['lunch']['fats']}g | "
        output += f"Calories: {meal_plan['lunch']['calories']}\n\n"

        # PM Snack
        output += "🍎 PM SNACK\n"
        output += f"{meal_plan['pm_snack']['description']}\n"
        output += f"Protein: {meal_plan['pm_snack']['protein']}g | "
        output += f"Carbs: {meal_plan['pm_snack']['carbs']}g | "
        output += f"Fats: {meal_plan['pm_snack']['fats']}g | "
        output += f"Calories: {meal_plan['pm_snack']['calories']}\n\n"

        # Dinner
        output += "🍽️ DINNER\n"
        output += f"{meal_plan['dinner']['description']}\n"
        output += f"Protein: {meal_plan['dinner']['protein']}g | "
        output += f"Carbs: {meal_plan['dinner']['carbs']}g | "
        output += f"Fats: {meal_plan['dinner']['fats']}g | "
        output += f"Calories: {meal_plan['dinner']['calories']}\n\n"

        # Calculate daily totals
        total_protein = sum(meal_plan[meal]['protein'] for meal in ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner'])
        total_carbs = sum(meal_plan[meal]['carbs'] for meal in ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner'])
        total_fats = sum(meal_plan[meal]['fats'] for meal in ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner'])
        total_calories = sum(meal_plan[meal]['calories'] for meal in ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner'])

        output += "📊 DAILY TOTALS\n"
        output += f"Protein: {total_protein}g | Carbs: {total_carbs}g | Fats: {total_fats}g | Calories: {total_calories}\n"

    except KeyError as e:
        output += f"\nError: Missing data in meal plan: {e}\n"

    return output

if __name__ == "__main__":
    today_plan = get_meal_plan_for_today()
    if today_plan:
        # Format and display today's meal plan
        formatted_plan = format_meal_plan_for_display(today_plan)
        print(formatted_plan)

        # Send SMS if phone number is provided
        phone_number = os.environ.get('TARGET_PHONE_NUMBER')
        if phone_number:
            message = format_meal_plan_for_sms(today_plan)
            if send_meal_plan_sms(phone_number, message):
                print("\nMeal plan sent via SMS successfully!")
            else:
                print("\nFailed to send SMS")
    else:
        print("No meal plan available for today.")