
import re
import os
from datetime import datetime
from replit import db
from twilio.rest import Client
from create_weekly_plans import get_week_key

def parse_meal_plan(raw_text):
    """ Parses the raw text and extracts meal plans by day. """
    meal_plan = {}
    current_day = None
    current_meals = {}
    in_meal_plan_section = False

    lines = raw_text.split("\n")

    for line in lines:
        line = line.strip()

        if line.startswith("MEAL PLAN:"):
            in_meal_plan_section = True
            continue

        if not in_meal_plan_section:
            continue

        day_match = re.match(r"^(SUNDAY|MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY)(?:\s*\(.*?\))?:?$", line, re.IGNORECASE)
        if day_match:
            if current_day:
                meal_plan[current_day] = current_meals
            current_day = day_match.group(1).capitalize()
            current_meals = {}
            continue

        meal_match = re.match(r"^(Breakfast|AM Snack|Lunch|PM Snack|Dinner):\s*(.*)$", line, re.IGNORECASE)
        if meal_match and current_day:
            meal_type = meal_match.group(1)
            meal_desc = meal_match.group(2)
            current_meals[meal_type] = meal_desc
            continue

        if line.startswith("Prep:") and current_day:
            prep_steps = []
            for prep_line in lines[lines.index(line) + 1:]:
                prep_line = prep_line.strip()
                if not prep_line or re.match(r"^(SUNDAY|MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY)", prep_line, re.IGNORECASE):
                    break
                prep_steps.append(prep_line)
            current_meals["Prep Instructions"] = prep_steps

    if current_day:
        meal_plan[current_day] = current_meals

    return meal_plan

def format_meal_plan_for_sms(meal_plan):
    """Format meal plan into a concise SMS message"""
    message = f"Meal Plan for {datetime.now().strftime('%A')}:\n\n"
    for meal, description in meal_plan.items():
        if meal != "Prep Instructions":
            message += f"{meal}: {description}\n"
    if "Prep Instructions" in meal_plan:
        message += "\nPrep Steps:\n"
        for step in meal_plan["Prep Instructions"]:
            message += f"- {step}\n"
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

def get_meal_plan_for_today():
    week_key = get_week_key()

    if week_key not in db:
        print("No meal plan found for this week. Run `weekly_plan.py` first.")
        return None

    raw_text = db[week_key]
    today = datetime.now().strftime("%A")
    meal_plan = parse_meal_plan(raw_text)

    return meal_plan.get(today, {"error": f"No meal plan found for {today}"})

if __name__ == "__main__":
    today_plan = get_meal_plan_for_today()
    if today_plan:
        # Format meal plan for display
        print(f"Today's Meal Plan ({datetime.now().strftime('%A')}):\n")
        for meal, description in today_plan.items():
            print(f"{meal}: {description}")
        
        # Send SMS if phone number is provided
        phone_number = os.environ.get('TARGET_PHONE_NUMBER')
        if phone_number:
            message = format_meal_plan_for_sms(today_plan)
            if send_meal_plan_sms(phone_number, message):
                print("\nMeal plan sent via SMS successfully!")
            else:
                print("\nFailed to send SMS")
