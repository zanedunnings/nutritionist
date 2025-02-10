import os
import requests
import json

# 1. Claude API Key
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# 2. Claude API function
def call_claude(prompt, model="claude-3-5-sonnet-20241022", max_tokens=8000, temperature=0.7):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }

    # Format the messages according to the Messages API structure
    data = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for bad status codes
        result = response.json()

        # Extract the content from the response
        if 'content' in result and len(result['content']) > 0:
            return result['content'][0]['text']
        else:
            return "No content received from the API"

    except requests.exceptions.RequestException as e:
        print(f"Error calling Claude API: {e}")
        return str(e)

# 3. The Prompt
prompt_text = """
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
Other Notes:
- Adjust if weight loss is <1 lb/week or >2 lbs/week by tweaking calories as needed.
- Keep it interesting, flexible, and seasonally varied.
- I like most food types. Asian and medeterranian food are favorites.
- Summarize clearly so it's easy to follow.
- assume for fish it's hard to have left overs unless its from meal prepping

Please provide a detailed 7 day meal plan.
Include each meal for every day of the week.
Also include a list of groceries and what I should do for prep days.
Ensure any meals provided have ingredients from a prior day of shopping for groceries. Don't include meals if the item wasn't included in groceries.

Meals should vary in cuisine and use little "hacks" to make the macro nutrients work in my favor. 
Here are some example meals. Don't only use these meal, but these should help you see what I mean:
 - Stuffed Peppers w/ Ground Turkey & Cauliflower Rice
 - Asian Beef Bowl w/ Lean Ground Beef, Kimchi & Brown Rice
 - Spaghetti w/ Turkey Meat & Lentil Pasta
 - Thai Red Curry Shrimp w/ Light Coconut Milk & Rice
 - New York Strip Steak & Bagged Salad
 - Ground Chicken Lettuce Wraps (Asian Style)
 - Greek Chicken Bowl
 - Tuna Steaks & Roasted Veggies
 - Chicken Fajitas on GF Tortillas
 - Turkey Meatloaf Muffins & Mashed Cauliflower
 - Baked Cod w/ Lemon & Spinach Orzo
 - Shrimp “Pad Thai” w/ Rice Noodles
 - Chicken Tikka Masala w/ Light Sauce
 - Lean Ground Beef “Shepherd’s Pie”
 - Salmon Teriyaki Bowl (Light Sauce) & Brown Rice
 - Turkey Chili (Beans Optional) & GF Cornbread
 - Pork Tenderloin w/ Apple Slaw & Sweet Potato
 - Baked Chicken Parmesan (Low-Fat Cheese) & Zucchini Noodles
 - “Sushi” Bowl w/ Salmon &  Rice
 - Chicken & Waffle (GF)
 - Turkey Burgers (Lettuce Wrap or GF Bun) & Oven Fries
 - Miso Glazed Cod & Bok Choy
 - Taco Salad Bowl w/ 90% Lean Beef
 - Chicken Stir-Fry w/ Sweet Sauce & Veggies
 - Blackened Tilapia & Quinoa w/ Veggies


Human:

Please provide a detailed 7 day meal plan.
Include each meal for every day of the week.
Also include a list of groceries and what I should do for prep days.

Assistant:
"""

from replit import db
from datetime import datetime, timedelta

def get_week_key():
    # Get current date
    today = datetime.now()
    # Find the most recent Sunday
    sunday = today - timedelta(days=today.weekday() + 1)
    # Format as YYYY-MM-DD
    return f"meal_plan_{sunday.strftime('%Y-%m-%d')}"

# 4. Call the Claude API with the above prompt
response = call_claude(prompt_text)

# 5. Store the response in the database with the week's date as key
week_key = get_week_key()
db[week_key] = response

# 6. Print out the plan
print(f"Claude's Meal Plan for week starting {week_key[10:]}:\n")
print(response)

# Optional: Print all stored meal plans
print("\nStored meal plans:")
for key in db.prefix("meal_plan_"):
    print(f"- Week of {key[10:]}")