import os
import requests
import json
from replit import db
from datetime import datetime, timedelta
import time
# Claude API Key
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


# Claude API function with function calling (Tools API)
def call_claude(prompt,
                model="claude-3-5-sonnet-20241022",
                max_tokens=8000,
                temperature=0.7):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }

    # Define the meal plan schema for structured output
    meal_plan_schema = {
        "name": "generate_meal_plan",
        "description":
        "Generate a structured 7-day meal plan with daily meals and nutritional info",
        "input_schema": {
            "type": "object",
            "properties": {
                "meal_plan": {
                    "type":
                    "object",
                    "properties": {
                        "overview": {
                            "type": "object",
                            "properties": {
                                "calorie_goal": {
                                    "type": "string"
                                },
                                "protein_goal": {
                                    "type": "string"
                                },
                                "summary": {
                                    "type": "string"
                                }
                            },
                            "required":
                            ["calorie_goal", "protein_goal", "summary"]
                        },
                        "daily_plans": {
                            "type":
                            "object",
                            "properties": {
                                "sunday": {
                                    "type":
                                    "object",
                                    "properties":
                                    create_day_schema(),
                                    "required": [
                                        "breakfast", "am_snack", "lunch",
                                        "pm_snack", "dinner", "is_prep_day",
                                        "is_no_cook_dinner"
                                    ]
                                },
                                "monday": {
                                    "type":
                                    "object",
                                    "properties":
                                    create_day_schema(),
                                    "required": [
                                        "breakfast", "am_snack", "lunch",
                                        "pm_snack", "dinner", "is_prep_day",
                                        "is_no_cook_dinner"
                                    ]
                                },
                                "tuesday": {
                                    "type":
                                    "object",
                                    "properties":
                                    create_day_schema(),
                                    "required": [
                                        "breakfast", "am_snack", "lunch",
                                        "pm_snack", "dinner", "is_prep_day",
                                        "is_no_cook_dinner"
                                    ]
                                },
                                "wednesday": {
                                    "type":
                                    "object",
                                    "properties":
                                    create_day_schema(),
                                    "required": [
                                        "breakfast", "am_snack", "lunch",
                                        "pm_snack", "dinner", "is_prep_day",
                                        "is_no_cook_dinner"
                                    ]
                                },
                                "thursday": {
                                    "type":
                                    "object",
                                    "properties":
                                    create_day_schema(),
                                    "required": [
                                        "breakfast", "am_snack", "lunch",
                                        "pm_snack", "dinner", "is_prep_day",
                                        "is_no_cook_dinner"
                                    ]
                                },
                                "friday": {
                                    "type":
                                    "object",
                                    "properties":
                                    create_day_schema(),
                                    "required": [
                                        "breakfast", "am_snack", "lunch",
                                        "pm_snack", "dinner", "is_prep_day",
                                        "is_no_cook_dinner"
                                    ]
                                },
                                "saturday": {
                                    "type":
                                    "object",
                                    "properties":
                                    create_day_schema(),
                                    "required": [
                                        "breakfast", "am_snack", "lunch",
                                        "pm_snack", "dinner", "is_prep_day",
                                        "is_no_cook_dinner"
                                    ]
                                }
                            },
                            "required": [
                                "sunday", "monday", "tuesday", "wednesday",
                                "thursday", "friday", "saturday"
                            ]
                        },
                        "meal_prep": {
                            "type": "object",
                            "properties": {
                                "sunday": {
                                    "type": "string"
                                },
                                "wednesday": {
                                    "type": "string"
                                }
                            },
                            "required": ["sunday", "wednesday"]
                        },
                        "grocery_lists": {
                            "type": "object",
                            "properties": {
                                "sunday": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                },
                                "wednesday": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                }
                            },
                            "required": ["sunday", "wednesday"]
                        }
                    },
                    "required":
                    ["overview", "daily_plans", "meal_prep", "grocery_lists"]
                }
            },
            "required": ["meal_plan"]
        }
    }

    data = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{
            "role": "user",
            "content": prompt
        }],
        "tools": [meal_plan_schema]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        # Extract the structured meal plan from the tool calls
        if "content" in result and len(result["content"]) > 0:
            for content_item in result["content"]:
                if content_item["type"] == "tool_use":
                    # Only return the meal_plan JSON object
                    return content_item["input"]

        # Fallback to text response if no tool call is found
        return {"error": "No structured meal plan found in the response"}
    except requests.exceptions.RequestException as e:
        print(f"Error calling Claude API: {e}")
        return {"error": str(e)}


# Helper function to create meal schema
def create_meal_schema():
    """Create the schema for a meal"""
    return {
        "description": {
            "type": "string"
        },
        "protein": {
            "type": "number"
        },
        "carbs": {
            "type": "number"
        },
        "fats": {
            "type": "number"
        },
        "calories": {
            "type": "number"
        },
        "portion_sizes": {
            "type": "object",
            "properties": {
                "meat": {
                    "type": "string"
                },
                "carbs": {
                    "type": "string"
                },
                "vegetables": {
                    "type": "string"
                }
            }
        }
    }


# Helper function to create day schema
def create_day_schema():
    return {
        "breakfast": {
            "type": "object",
            "properties": create_meal_schema(),
            "required":
            ["description", "protein", "carbs", "fats", "calories"]
        },
        "am_snack": {
            "type": "object",
            "properties": create_meal_schema(),
            "required":
            ["description", "protein", "carbs", "fats", "calories"]
        },
        "lunch": {
            "type": "object",
            "properties": create_meal_schema(),
            "required":
            ["description", "protein", "carbs", "fats", "calories"]
        },
        "pm_snack": {
            "type": "object",
            "properties": create_meal_schema(),
            "required":
            ["description", "protein", "carbs", "fats", "calories"]
        },
        "dinner": {
            "type": "object",
            "properties": create_meal_schema(),
            "required":
            ["description", "protein", "carbs", "fats", "calories"]
        },
        "is_prep_day": {
            "type": "boolean"
        },
        "is_no_cook_dinner": {
            "type": "boolean"
        }
    }


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

IMPORTANT DETAILS:
- Include specific portion sizes for all meat (e.g., "6oz chicken breast", "4oz ground turkey")
- Include portion sizes for carbs and vegetables where applicable
- Be precise about quantities to help with meal prep and shopping

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
 - Shrimp "Pad Thai" w/ Rice Noodles
 - Chicken Tikka Masala w/ Light Sauce
 - Lean Ground Beef "Shepherd's Pie"
 - Salmon Teriyaki Bowl (Light Sauce) & Brown Rice
 - Turkey Chili (Beans Optional) & GF Cornbread
 - Pork Tenderloin w/ Apple Slaw & Sweet Potato
 - Baked Chicken Parmesan (Low-Fat Cheese) & Zucchini Noodles
 - "Sushi" Bowl w/ Salmon &  Rice
 - Chicken & Waffle (GF)
 - Turkey Burgers (Lettuce Wrap or GF Bun) & Oven Fries
 - Miso Glazed Cod & Bok Choy
 - Taco Salad Bowl w/ 90% Lean Beef
 - Chicken Stir-Fry w/ Sweet Sauce & Veggies
 - Blackened Tilapia & Quinoa w/ Veggies


H:

Please provide a detailed 7 day meal plan.
Include each meal for every day of the week.
Also include a list of groceries and what I should do for prep days. ENSURE YOU GIVE ME THE FULL WEEKS PLAN, DO NOT TRUNCATE OR ASK FOR CONFIRMATION IF I WANT THE FULL WEEKS PLAN!!
"""


# Generate the key for the current week's meal plan
def get_week_key():
    today = datetime.now()
    sunday = today - timedelta(
        days=today.weekday() + 1)  # Find the most recent Sunday
    return f"meal_plan_{sunday.strftime('%Y-%m-%d')}"


# Fetch meal plan
def fetch_meal_plan(force_call_claude=False):
    week_key = get_week_key()

    if week_key in db and not force_call_claude:
        print(f"Using stored meal plan for week {week_key[10:]}")
        return db[week_key]

    print("Fetching a new meal plan from Claude...")
    if week_key not in db or force_call_claude:
        print(week_key)
        # Get response from Claude API
        response = call_claude(prompt_text)

        # Ensure we're storing only the JSON
        if isinstance(response, dict):
            # Store the clean JSON in the database
            db[week_key] = response
        else:
            # If it's a string, try to parse it as JSON before storing
            try:
                json_response = json.loads(response)
                db[week_key] = json_response
            except:
                # If parsing fails, store as is
                db[week_key] = response

        return db[week_key]
    else:
        return db[week_key]


def format_meal_plan_for_sms(meal_plan_json):
    """Format the JSON meal plan into a readable SMS text format"""
    try:
        # Access the meal_plan object
        if isinstance(meal_plan_json, str):
            meal_plan = json.loads(meal_plan_json)
        else:
            meal_plan = meal_plan_json

        if "meal_plan" not in meal_plan:
            return "Error: Invalid meal plan format"

        plan = meal_plan["meal_plan"]

        # Format the overview
        output = f"7-DAY MEAL PLAN\n"
        output += f"Goal: {plan['overview']['calorie_goal']} calories, {plan['overview']['protein_goal']} protein\n\n"

        # Format each day
        days = [
            "sunday", "monday", "tuesday", "wednesday", "thursday", "friday",
            "saturday"
        ]
        for day in days:
            day_plan = plan["daily_plans"][day]
            day_title = day.upper()

            if day_plan["is_prep_day"]:
                day_title += " (PREP DAY)"
            if day_plan["is_no_cook_dinner"]:
                day_title += " (NO-COOK DINNER)"

            output += f"{day_title}\n"

            # Format each meal
            output += f"- Breakfast: {day_plan['breakfast']['description']} ({day_plan['breakfast']['protein']}g P, {day_plan['breakfast']['calories']} cal)\n"
            output += f"- AM Snack: {day_plan['am_snack']['description']} ({day_plan['am_snack']['protein']}g P, {day_plan['am_snack']['calories']} cal)\n"
            output += f"- Lunch: {day_plan['lunch']['description']} ({day_plan['lunch']['protein']}g P, {day_plan['lunch']['calories']} cal)\n"
            output += f"- PM Snack: {day_plan['pm_snack']['description']} ({day_plan['pm_snack']['protein']}g P, {day_plan['pm_snack']['calories']} cal)\n"
            output += f"- Dinner: {day_plan['dinner']['description']} ({day_plan['dinner']['protein']}g P, {day_plan['dinner']['calories']} cal)\n\n"

        # Add meal prep instructions
        output += "MEAL PREP INSTRUCTIONS\n"
        output += f"SUNDAY: {plan['meal_prep']['sunday']}\n\n"
        output += f"WEDNESDAY: {plan['meal_prep']['wednesday']}\n\n"

        # Add grocery lists
        output += "GROCERY LISTS\n"
        output += "SUNDAY:\n"
        for item in plan["grocery_lists"]["sunday"]:
            output += f"- {item}\n"
        output += "\nWEDNESDAY:\n"
        for item in plan["grocery_lists"]["wednesday"]:
            output += f"- {item}\n"

        return output
    except Exception as e:
        return f"Error formatting meal plan: {str(e)}"


def send_weekly_plan_sms(meal_plan):
    """Send weekly meal plan via SMS using Twilio"""
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_number = os.environ.get('TWILIO_PHONE_NUMBER')
    to_number = os.environ.get('TARGET_PHONE_NUMBER')

    if not all([account_sid, auth_token, from_number, to_number]):
        print("Twilio credentials not found in environment variables")
        return False

    from twilio.rest import Client
    client = Client(account_sid, auth_token)

    try:
        # Format the JSON meal plan into readable text
        formatted_message = format_meal_plan_for_sms(meal_plan)

        # Format initial message
        full_message = f"Weekly Meal Plan ({get_week_key()[10:]}):\n\n{formatted_message}"

        # Split message into chunks (max 1600 chars per SMS)
        chunk_size = 1500
        message_chunks = [
            full_message[i:i + chunk_size]
            for i in range(0, len(full_message), chunk_size)
        ]

        # Send each chunk with a counter
        for i, chunk in enumerate(message_chunks, 1):
            prefix = f"({i}/{len(message_chunks)}) "
            client.messages.create(body=prefix + chunk,
                                   from_=from_number,
                                   to=to_number)
            time.sleep(.5)

        return True
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False


# Run the script
if __name__ == "__main__":
    meal_plan = fetch_meal_plan(force_call_claude=True)

    # Print JSON meal plan (for debugging)
    print(f"Meal Plan for the week starting {get_week_key()[10:]}:\n")

    # Pretty print if it's a dict, otherwise just print the string
    if isinstance(meal_plan, dict):
        print(json.dumps(meal_plan, indent=2))
    else:
        try:
            # Try to parse and pretty print if it's a JSON string
            print(json.dumps(json.loads(meal_plan), indent=2))
        except:
            # Just print as is if not valid JSON
            print(meal_plan)

    # Save to a JSON file
    with open(f"meal_plan_{get_week_key()[10:]}.json", "w") as f:
        if isinstance(meal_plan, dict):
            json.dump(meal_plan, f, indent=2)
        else:
            try:
                json_data = json.loads(meal_plan)
                json.dump(json_data, f, indent=2)
            except:
                f.write(str(meal_plan))

    print(f"\nMeal plan saved to meal_plan_{get_week_key()[10:]}.json")

    # Send SMS if credentials are configured
    if send_weekly_plan_sms(meal_plan):
        print("\nMeal plan sent via SMS successfully!")
    else:
        print("\nFailed to send SMS")
