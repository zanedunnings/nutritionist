import re
from datetime import datetime
from replit import db
from create_weekly_plans import get_week_key  # Import function to get the week key

# Parse meal plan from raw text
def parse_meal_plan(raw_text):
    """ Parses the raw text and extracts meal plans by day. """
    meal_plan = {}
    current_day = None
    current_meals = {}
    in_meal_plan_section = False  # Track when we've reached "MEAL PLAN"

    lines = raw_text.split("\n")

    for line in lines:
        line = line.strip()

        # Start capturing meal plan once we reach "MEAL PLAN:"
        if line.startswith("MEAL PLAN:"):
            in_meal_plan_section = True
            continue

        # Ignore everything before "MEAL PLAN"
        if not in_meal_plan_section:
            continue

        # Detect day headers (e.g., "SUNDAY (Prep Day):", "MONDAY:")
        day_match = re.match(r"^(SUNDAY|MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY)(?:\s*\(.*?\))?:?$", line, re.IGNORECASE)
        if day_match:
            if current_day:  # Save previous day's data
                meal_plan[current_day] = current_meals
            current_day = day_match.group(1).capitalize()
            current_meals = {}
            continue

        # Detect meal entries (e.g., "Breakfast: Egg white omelette")
        meal_match = re.match(r"^(Breakfast|AM Snack|Lunch|PM Snack|Dinner):\s*(.*)$", line, re.IGNORECASE)
        if meal_match and current_day:
            meal_type = meal_match.group(1)
            meal_desc = meal_match.group(2)
            current_meals[meal_type] = meal_desc
            continue

        # Detect "Prep:" section under a specific day and collect multi-line instructions
        if line.startswith("Prep:") and current_day:
            prep_steps = []
            for prep_line in lines[lines.index(line) + 1:]:
                prep_line = prep_line.strip()
                if not prep_line or re.match(r"^(SUNDAY|MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY)", prep_line, re.IGNORECASE):
                    break  # Stop when reaching the next day's section
                prep_steps.append(prep_line)
            current_meals["Prep Instructions"] = prep_steps

    # Save the last day's data
    if current_day:
        meal_plan[current_day] = current_meals

    return meal_plan

# Get today's meal plan
def get_meal_plan_for_today():
    week_key = get_week_key()

    if week_key not in db:
        print("No meal plan found for this week. Run `weekly_plan.py` first.")
        return None

    raw_text = db[week_key]
    today = datetime.now().strftime("%A")
    meal_plan = parse_meal_plan(raw_text)

    return meal_plan.get(today, {"error": f"No meal plan found for {today}"})

# Run the script
if __name__ == "__main__":
    today_plan = get_meal_plan_for_today()
    if today_plan:
        print(f"Today's Meal Plan ({datetime.now().strftime('%A')}):\n")
        for meal, description in today_plan.items():
            print(f"{meal}: {description}")
