from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
import os
import json
from datetime import datetime, timedelta
from replit import db
import anthropic

# Flask application setup
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'meal-planner-secret')

# ---------- Utility Functions ----------

def get_week_key():
    """Generate the key for the current week's meal plan"""
    today = datetime.now()
    sunday = today - timedelta(days=today.weekday() + 1)  # Find the most recent Sunday
    return f"meal_plan_{sunday.strftime('%Y-%m-%d')}"

def call_claude(prompt, model="claude-3-5-sonnet-20241022", max_tokens=8000, temperature=0.7):
    """Call Claude API with function calling for structured meal plan output with portion sizes"""
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=anthropic_api_key)

    # Define the meal plan schema for structured output
    meal_plan_schema = {
        "name": "generate_meal_plan",
        "description": "Generate a structured 7-day meal plan with daily meals, nutritional info, and portion sizes",
        "input_schema": get_meal_plan_schema()
    }

    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
            tools=[meal_plan_schema]
        )

        # Extract the structured meal plan from the tool calls
        for content in response.content:
            if content.type == "tool_use" and content.name == "generate_meal_plan":
                return content.input

        # Fallback to text response if no tool call is found
        return {"error": "No structured meal plan found in the response"}

    except Exception as e:
        return {"error": str(e)}

def create_meal_schema():
    """Create the schema for a meal with portion sizes"""
    return {
        "description": {"type": "string"},
        "protein": {"type": "number"},
        "carbs": {"type": "number"},
        "fats": {"type": "number"},
        "calories": {"type": "number"},
        "portion_sizes": {
            "type": "object",
            "properties": {
                "meat": {"type": "string"},
                "carbs": {"type": "string"},
                "vegetables": {"type": "string"}
            }
        }
    }

def create_day_schema():
    """Create the schema for a day's meals"""
    return {
        "breakfast": {
            "type": "object",
            "properties": create_meal_schema(),
            "required": ["description", "protein", "carbs", "fats", "calories", "portion_sizes"]
        },
        "am_snack": {
            "type": "object",
            "properties": create_meal_schema(),
            "required": ["description", "protein", "carbs", "fats", "calories", "portion_sizes"]
        },
        "lunch": {
            "type": "object",
            "properties": create_meal_schema(),
            "required": ["description", "protein", "carbs", "fats", "calories", "portion_sizes"]
        },
        "pm_snack": {
            "type": "object",
            "properties": create_meal_schema(),
            "required": ["description", "protein", "carbs", "fats", "calories", "portion_sizes"]
        },
        "dinner": {
            "type": "object",
            "properties": create_meal_schema(),
            "required": ["description", "protein", "carbs", "fats", "calories", "portion_sizes"]
        },
        "is_prep_day": {"type": "boolean"},
        "is_no_cook_dinner": {"type": "boolean"}
    }

def get_meal_plan_schema():
    """Returns the JSON schema for the meal plan with portion sizes"""
    return {
        "type": "object",
        "properties": {
            "meal_plan": {
                "type": "object",
                "properties": {
                    "overview": {
                        "type": "object",
                        "properties": {
                            "calorie_goal": {"type": "string"},
                            "protein_goal": {"type": "string"},
                            "summary": {"type": "string"}
                        },
                        "required": ["calorie_goal", "protein_goal", "summary"]
                    },
                    "daily_plans": {
                        "type": "object",
                        "properties": {
                            "sunday": {
                                "type": "object",
                                "properties": create_day_schema(),
                                "required": ["breakfast", "am_snack", "lunch", "pm_snack", "dinner", "is_prep_day", "is_no_cook_dinner"]
                            },
                            "monday": {
                                "type": "object",
                                "properties": create_day_schema(),
                                "required": ["breakfast", "am_snack", "lunch", "pm_snack", "dinner", "is_prep_day", "is_no_cook_dinner"]
                            },
                            "tuesday": {
                                "type": "object", 
                                "properties": create_day_schema(),
                                "required": ["breakfast", "am_snack", "lunch", "pm_snack", "dinner", "is_prep_day", "is_no_cook_dinner"]
                            },
                            "wednesday": {
                                "type": "object",
                                "properties": create_day_schema(),
                                "required": ["breakfast", "am_snack", "lunch", "pm_snack", "dinner", "is_prep_day", "is_no_cook_dinner"]
                            },
                            "thursday": {
                                "type": "object",
                                "properties": create_day_schema(),
                                "required": ["breakfast", "am_snack", "lunch", "pm_snack", "dinner", "is_prep_day", "is_no_cook_dinner"]
                            },
                            "friday": {
                                "type": "object",
                                "properties": create_day_schema(),
                                "required": ["breakfast", "am_snack", "lunch", "pm_snack", "dinner", "is_prep_day", "is_no_cook_dinner"]
                            },
                            "saturday": {
                                "type": "object",
                                "properties": create_day_schema(),
                                "required": ["breakfast", "am_snack", "lunch", "pm_snack", "dinner", "is_prep_day", "is_no_cook_dinner"]
                            }
                        },
                        "required": ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
                    },
                    "meal_prep": {
                        "type": "object",
                        "properties": {
                            "sunday": {"type": "string"},
                            "wednesday": {"type": "string"}
                        },
                        "required": ["sunday", "wednesday"]
                    },
                    "grocery_lists": {
                        "type": "object",
                        "properties": {
                            "sunday": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "wednesday": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["sunday", "wednesday"]
                    }
                },
                "required": ["overview", "daily_plans", "meal_prep", "grocery_lists"]
            }
        },
        "required": ["meal_plan"]
    }

def get_meal_prompt():
    """Get the meal plan prompt for Claude with portion size requirements"""
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

def get_today_meal_plan():
    """Get today's meal plan with portion sizes"""
    week_key = get_week_key()

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

    return meal_plan["meal_plan"]["daily_plans"][today]

from replit.database import to_primitive

def convert_observed_dict(obj):
    """
    Recursively convert ObservedDict objects to regular dictionaries.
    Also handles lists and other nested structures.
    """
    if hasattr(obj, "items"):  # Dict-like object (including ObservedDict)
        return {k: convert_observed_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_observed_dict(item) for item in obj]
    else:
        return obj

def get_weekly_meal_plan():
    """Get the weekly meal plan ensuring JSON serializable data"""
    week_key = get_week_key()

    if week_key not in db:
        return None

    # Get the stored meal plan data
    meal_plan_data = db[week_key]

    prim = to_primitive(meal_plan_data)
    print(prim)

    # If it's a string, try to parse it as JSON
    if isinstance(meal_plan_data, str):
        try:
            meal_plan = json.loads(meal_plan_data)
        except json.JSONDecodeError:
            return None
    else:
        # Convert the ObservedDict to a regular dict (recursively)
        meal_plan = to_primitive(meal_plan_data)

    # Check if we have a valid meal plan structure
    if "meal_plan" not in meal_plan:
        return None

    return meal_plan["meal_plan"]

def generate_meal_plan():
    """Generate a new meal plan with portion sizes"""
    meal_plan = call_claude(get_meal_prompt())

    if "error" in meal_plan:
        return None

    # Store the plan in the database
    week_key = get_week_key()
    db[week_key] = meal_plan

    # Also save to a JSON file
    with open(f"meal_plan_{get_week_key()[10:]}.json", "w") as f:
        json.dump(meal_plan, f, indent=2)

    return meal_plan

# ---------- Flask Routes ----------

@app.route('/')
def index():
    """Serve the single page Evangelion-styled app"""
    week_key = get_week_key()
    has_plan = week_key in db

    return render_template('index.html', has_plan=has_plan)

# ---------- API Routes ----------

import json
from flask import jsonify
import traceback

def convert_replit_objects(obj):
    """
    Recursively convert Replit DB objects (ObservedDict, ObservedList)
    to standard Python types that are JSON serializable.
    """
    # For ObservedDict
    if hasattr(obj, "keys") and callable(getattr(obj, "keys", None)):
        return {str(k): convert_replit_objects(v) for k, v in obj.items()}

    # For ObservedList and other iterables
    elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes, bytearray)):
        return [convert_replit_objects(item) for item in list(obj)]

    # Return all other objects as is
    else:
        return obj

@app.route('/api/weekly', methods=['GET'])
def api_weekly():
    """API endpoint to get the weekly meal plan with proper error handling"""
    try:
        week_key = get_week_key()
        print(f"Accessing key: {week_key}")

        if week_key not in db:
            print(f"Key {week_key} not found")
            return jsonify({"status": "error", "message": "No meal plan found"})

        # Get the stored meal plan data
        meal_plan_data = db[week_key]
        print(f"Data type: {type(meal_plan_data)}")

        # Force conversion to Python standard types
        try:
            # Convert data to standard Python types
            converted_data = to_primitive(meal_plan_data)
            print(f"Data type: {type(converted_data)}")

            # Verify it's serializable by doing a round-trip through JSON
            # This will break if there are any non-serializable objects left
            meal_plan = json.loads(converted_data)

            print("Data successfully converted and serialized")
        except Exception as e:
            print(f"Error during conversion: {str(e)}")
            traceback.print_exc()

            # Last resort: try to store as string and reparse
            try:
                print("Attempting to store and reparse as string")
                # Store as string in DB
                db[week_key] = json.dumps(to_primitive(meal_plan_data))
                # Read it back
                meal_plan = json.loads(db[week_key])
                print("String storage and reparsing successful")
            except Exception as e2:
                print(f"String storage attempt failed: {str(e2)}")
                return jsonify({
                    "status": "error",
                    "message": f"Could not process meal plan data: {str(e)} then {str(e2)}"
                }), 500

        # Check if we have a valid meal plan structure
        if "meal_plan" not in meal_plan:
            print("'meal_plan' key not found")
            return jsonify({"status": "error", "message": "Invalid meal plan structure: 'meal_plan' key missing"})

        return jsonify({"status": "success", "plan": meal_plan["meal_plan"]})

    except Exception as e:
        print(f"Unhandled error in api_weekly: {str(e)}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"An error occurred retrieving the meal plan: {str(e)}"}), 500

@app.route('/api/today', methods=['GET'])
def api_today():
    """API endpoint to get today's meal plan with proper error handling"""
    try:
        week_key = get_week_key()
        today = datetime.now().strftime("%A").lower()
        print(f"Accessing today's plan for {today} from key: {week_key}")

        if week_key not in db:
            print(f"Key {week_key} not found")
            return jsonify({"status": "error", "message": "No meal plan found"})

        # Get the stored meal plan data
        meal_plan_data = db[week_key]
        print(f"Data type: {type(meal_plan_data)}")

        # Force conversion to Python standard types
        try:
            # Convert data to standard Python types
            converted_data = to_primitive(meal_plan_data)
            print(f"Converted data type: {type(converted_data)}")

            # Verify it's serializable by doing a round-trip through JSON
            # This will break if there are any non-serializable objects left
            if isinstance(converted_data, str):
                meal_plan = json.loads(converted_data)
            else:
                # Serialize and deserialize to ensure clean JSON
                serialized = json.dumps(converted_data)
                meal_plan = json.loads(serialized)

            print("Data successfully converted and serialized")
        except Exception as e:
            print(f"Error during conversion: {str(e)}")
            traceback.print_exc()

            # Last resort: try to store as string and reparse
            try:
                print("Attempting to store and reparse as string")
                # Store as string in DB
                db[week_key] = json.dumps(to_primitive(meal_plan_data))
                # Read it back
                meal_plan = json.loads(db[week_key])
                print("String storage and reparsing successful")
            except Exception as e2:
                print(f"String storage attempt failed: {str(e2)}")
                return jsonify({
                    "status": "error",
                    "message": f"Could not process meal plan data: {str(e)} then {str(e2)}"
                }), 500

        # Check if we have a valid meal plan structure
        if "meal_plan" not in meal_plan:
            print("'meal_plan' key not found")
            return jsonify({"status": "error", "message": "Invalid meal plan structure: 'meal_plan' key missing"})

        if "daily_plans" not in meal_plan["meal_plan"]:
            print("'daily_plans' key not found in meal_plan")
            return jsonify({"status": "error", "message": "Invalid meal plan structure: 'daily_plans' key missing"})

        # Check if today's plan exists
        if today not in meal_plan["meal_plan"]["daily_plans"]:
            print(f"No meal plan found for {today}")
            return jsonify({"status": "error", "message": f"No meal plan found for {today}"})

        # Get today's plan and ensure it's properly serialized
        today_plan = meal_plan["meal_plan"]["daily_plans"][today]
        print(f"Successfully retrieved today's plan for {today}")
        
        return jsonify({"status": "success", "plan": today_plan})

    except Exception as e:
        print(f"Unhandled error in api_today: {str(e)}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"An error occurred retrieving today's meal plan: {str(e)}"}), 500

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """API endpoint to generate a new meal plan with proper error handling"""
    try:
        # Generate meal plan
        prompt = get_meal_prompt()
        response = call_claude(prompt)

        if "error" in response:
            return jsonify({"status": "error", "message": response["error"]})

        # Store the plan in the database (as a JSON string to avoid serialization issues)
        week_key = get_week_key()
        # Convert to standard Python types and then to a JSON string
        db[week_key] = json.dumps(convert_replit_objects(response))

        # Also save to a JSON file for backup
        try:
            with open(f"meal_plan_{week_key[10:]}.json", "w") as f:
                json.dump(response, f, indent=2)
        except Exception as file_error:
            print(f"Warning: Could not save meal plan to file: {str(file_error)}")

        return jsonify({"status": "success", "message": "Meal plan generated successfully"})

    except Exception as e:
        print(f"Error in api_generate: {str(e)}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"An error occurred generating the meal plan: {str(e)}"}), 500

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint for chat functionality"""
    try:
        # Get request data
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"status": "error", "message": "No message provided"}), 400

        message = data['message']
        context = data.get('context', 'general')
        history = data.get('history', [])

        # Get current meal plan
        week_key = get_week_key()

        if week_key not in db:
            return jsonify({"status": "error", "message": "No meal plan found"}), 404

        # Get meal plan data with error handling
        try:
            meal_plan_data = db[week_key]

            if isinstance(meal_plan_data, str):
                try:
                    meal_plan = json.loads(meal_plan_data)
                except json.JSONDecodeError:
                    return jsonify({"status": "error", "message": "Invalid meal plan data"}), 500
            else:
                # For Replit ObservedDict/ObservedList objects
                try:
                    # Convert to regular Python objects
                    meal_plan = json.loads(json.dumps(dict(meal_plan_data)))
                except:
                    return jsonify({"status": "error", "message": "Failed to process meal plan data"}), 500
        except Exception as e:
            return jsonify({"status": "error", "message": f"Error accessing meal plan: {str(e)}"}), 500

        # Check meal plan structure
        if "meal_plan" not in meal_plan:
            return jsonify({"status": "error", "message": "Invalid meal plan structure"}), 500

        # Build prompt for Claude based on context
        prompt = ""

        # Today's meal plan context
        today = datetime.now().strftime("%A").lower()

        if today not in meal_plan["meal_plan"]["daily_plans"]:
            return jsonify({"status": "error", "message": f"No meal plan found for {today}"}), 404

        today_plan = meal_plan["meal_plan"]["daily_plans"][today]

        # Format the prompt for today's plan
        prompt = build_today_prompt(today_plan, today, message, meal_plan["meal_plan"])


        # Call Anthropic API
        response = call_anthropic(prompt)

        # Check for plan modification
        plan_updated = False
        if "PLAN_UPDATE:" in response:
            # Process plan update
            plan_updated = process_plan_update(meal_plan, response, context, today if context == "today" else None)

            # Clean response to remove the update marker
            response = response.replace("PLAN_UPDATE:", "").strip()

        return jsonify({
            "status": "success",
            "message": response,
            "plan_updated": plan_updated
        })

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500

def build_today_prompt(today_plan, day, message, full_plan):
    """Build a prompt for today's meal plan context"""
    prompt = f"""You are MAGI, an AI assistant for a meal planning application in the style of NERV terminals from Evangelion.

Current meal plan for {day.capitalize()}:

BREAKFAST:
{today_plan['breakfast']['description']}
Protein: {today_plan['breakfast']['protein']}g, Carbs: {today_plan['breakfast']['carbs']}g, Fats: {today_plan['breakfast']['fats']}g, Calories: {today_plan['breakfast']['calories']}

AM SNACK:
{today_plan['am_snack']['description']}
Protein: {today_plan['am_snack']['protein']}g, Carbs: {today_plan['am_snack']['carbs']}g, Fats: {today_plan['am_snack']['fats']}g, Calories: {today_plan['am_snack']['calories']}

LUNCH:
{today_plan['lunch']['description']}
Protein: {today_plan['lunch']['protein']}g, Carbs: {today_plan['lunch']['carbs']}g, Fats: {today_plan['lunch']['fats']}g, Calories: {today_plan['lunch']['calories']}

PM SNACK:
{today_plan['pm_snack']['description']}
Protein: {today_plan['pm_snack']['protein']}g, Carbs: {today_plan['pm_snack']['carbs']}g, Fats: {today_plan['pm_snack']['fats']}g, Calories: {today_plan['pm_snack']['calories']}

DINNER:
{today_plan['dinner']['description']}
Protein: {today_plan['dinner']['protein']}g, Carbs: {today_plan['dinner']['carbs']}g, Fats: {today_plan['dinner']['fats']}g, Calories: {today_plan['dinner']['calories']}

USER QUERY: {message}

You are an assistant helping with this meal plan. You can:
1. Answer questions about the meals, recipes, ingredients, or cooking instructions
2. Suggest modifications or alternatives to meals
3. Provide nutritional information and advice

If the user wants to modify the plan (like changing a meal or adjusting portions), preface your response with "PLAN_UPDATE:" (on the same line as your response).

Keep your responses concise and in the style of a NERV terminal from Evangelion (technical, precise, somewhat formal).
"""

    return prompt

def build_weekly_prompt(meal_plan, message):
    """Build a prompt for weekly meal plan context"""
    # Get overview information
    overview = meal_plan.get("overview", {})
    calorie_goal = overview.get("calorie_goal", "Not specified")
    protein_goal = overview.get("protein_goal", "Not specified")

    # Get meal prep information
    meal_prep = meal_plan.get("meal_prep", {})
    sunday_prep = meal_prep.get("sunday", "Not specified")
    wednesday_prep = meal_prep.get("wednesday", "Not specified")

    prompt = f"""You are MAGI, an AI assistant for a meal planning application in the style of NERV terminals from Evangelion.

WEEKLY MEAL PLAN OVERVIEW:
- Calorie Goal: {calorie_goal}
- Protein Goal: {protein_goal}
- Meal Prep (Sunday): {sunday_prep[:200]}...
- Meal Prep (Wednesday): {wednesday_prep[:200]}...

USER QUERY: {message}

You are an assistant helping with this weekly meal plan. You can:
1. Answer questions about the overall meal structure, meal prep, or grocery planning
2. Provide advice on meal preparation, batch cooking, or food storage
3. Suggest modifications to the meal plan structure

If the user wants to modify the plan (like changing meal prep instructions or grocery lists), preface your response with "PLAN_UPDATE:" (on the same line as your response).

Keep your responses concise and in the style of a NERV terminal from Evangelion (technical, precise, somewhat formal).
"""

    return prompt

def build_general_prompt(meal_plan, message):
    """Build a prompt for general meal plan context"""
    overview = meal_plan.get("overview", {})
    calorie_goal = overview.get("calorie_goal", "Not specified")
    protein_goal = overview.get("protein_goal", "Not specified")

    prompt = f"""You are MAGI, an AI assistant for a meal planning application in the style of NERV terminals from Evangelion.

NUTRITIONAL PROGRAM PARAMETERS:
- Calorie Goal: {calorie_goal}
- Protein Goal: {protein_goal}

USER QUERY: {message}

You are an assistant helping with nutritional planning. You can:
1. Provide general nutrition advice
2. Answer questions about dietary concepts, meal planning, or food preparation
3. Offer general suggestions for nutritional optimization

Keep your responses concise and in the style of a NERV terminal from Evangelion (technical, precise, somewhat formal).
"""

    return prompt

def call_anthropic(prompt):
    """Call Anthropic API to get response from Claude"""
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "ERROR: API key not configured. Contact system administrator."

        client = anthropic.Client(api_key=api_key)
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text
    except Exception as e:
        print(f"Error calling Anthropic API: {str(e)}")
        return f"ERROR: Communication failure with language model. Details: {str(e)}"

def process_plan_update(meal_plan, response, context, day=None):
    """Process a plan update request"""
    try:
        # Record the modification request
        week_key = get_week_key()
        modifications_key = f"{week_key}_modifications"

        if modifications_key not in db:
            db[modifications_key] = []

        modifications = db[modifications_key]

        # Add the new modification
        modification = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "day": day,
            "response": response
        }

        modifications.append(modification)
        db[modifications_key] = modifications

        # For now, we're just tracking the modifications
        # To actually implement changes to the meal plan, you would need to 
        # parse the response and modify the meal_plan structure accordingly

        # In a full implementation, you would:
        # 1. Parse the response to determine what changes are needed
        # 2. Update the appropriate part of the meal_plan structure
        # 3. Save the updated meal_plan back to the database

        return True
    except Exception as e:
        print(f"Error processing plan update: {str(e)}")
        return False

# ---------- Run App ----------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
    