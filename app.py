import os
import json
import sqlite3
import traceback
from datetime import datetime, timedelta
import jwt
from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

import anthropic
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import random

# ---------- Authentication Functions ----------
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-here")  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(authorization: str = Header(...)):
    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Verify user exists in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {"user_id": user_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------- SQLite Helper Functions ----------
DATABASE = "meal_plans.db"
OTP_EXPIRATION_MINUTES = 5

AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
if not AUTH_SECRET_KEY:
    raise ValueError("AUTH_SECRET_KEY environment variable is not set")

ALGORITHM = "HS256"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create meal_plans table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS meal_plans (
        week_key TEXT PRIMARY KEY,
        plan TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create modifications table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS modifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        week_key TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        context TEXT,
        day TEXT,
        response TEXT NOT NULL,
        FOREIGN KEY (week_key) REFERENCES meal_plans(week_key)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

def save_meal_plan(week_key: str, plan: dict):
    plan_json = json.dumps(plan)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO meal_plans (week_key, plan)
        VALUES (?, ?)
    ''', (week_key, plan_json))
    conn.commit()
    conn.close()

def get_meal_plan(week_key: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT plan FROM meal_plans WHERE week_key = ?', (week_key,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return json.loads(row["plan"])

def add_modification(week_key: str, modification: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO modifications (week_key, timestamp, context, day, response)
        VALUES (?, ?, ?, ?, ?)
    ''', (week_key, modification["timestamp"], modification.get("context"), modification.get("day"), modification["response"]))
    conn.commit()
    conn.close()

# ---------- Utility Functions ----------
def get_week_key():
    today = datetime.now()
    # Compute the most recent Sunday
    sunday = today - timedelta(days=today.weekday() + 1)
    return f"meal_plan_{sunday.strftime('%Y-%m-%d')}"

def create_meal_schema():
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
                            "sunday": {"type": "object", "properties": create_day_schema(), "required": ["breakfast", "am_snack", "lunch", "pm_snack", "dinner", "is_prep_day", "is_no_cook_dinner"]},
                            "monday": {"type": "object", "properties": create_day_schema(), "required": ["breakfast", "am_snack", "lunch", "pm_snack", "dinner", "is_prep_day", "is_no_cook_dinner"]},
                            "tuesday": {"type": "object", "properties": create_day_schema(), "required": ["breakfast", "am_snack", "lunch", "pm_snack", "dinner", "is_prep_day", "is_no_cook_dinner"]},
                            "wednesday": {"type": "object", "properties": create_day_schema(), "required": ["breakfast", "am_snack", "lunch", "pm_snack", "dinner", "is_prep_day", "is_no_cook_dinner"]},
                            "thursday": {"type": "object", "properties": create_day_schema(), "required": ["breakfast", "am_snack", "lunch", "pm_snack", "dinner", "is_prep_day", "is_no_cook_dinner"]},
                            "friday": {"type": "object", "properties": create_day_schema(), "required": ["breakfast", "am_snack", "lunch", "pm_snack", "dinner", "is_prep_day", "is_no_cook_dinner"]},
                            "saturday": {"type": "object", "properties": create_day_schema(), "required": ["breakfast", "am_snack", "lunch", "pm_snack", "dinner", "is_prep_day", "is_no_cook_dinner"]}
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
                            "sunday": {"type": "array", "items": {"type": "string"}},
                            "wednesday": {"type": "array", "items": {"type": "string"}}
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

# ---------- Anthropic API Call Functions ----------
def call_claude(prompt, model="claude-3-5-sonnet-20241022", max_tokens=8000, temperature=0.7):
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    client = anthropic.Anthropic(api_key=anthropic_api_key)
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
        for content in response.content:
            if content.type == "tool_use" and content.name == "generate_meal_plan":
                return content.input
        return {"error": "No structured meal plan found in the response"}
    except Exception as e:
        return {"error": str(e)}

def call_anthropic(prompt):
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "ERROR: API key not configured."
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
        return f"ERROR: {str(e)}"

# ---------- Meal Plan Functions ----------
def get_today_meal_plan():
    week_key = get_week_key()
    meal_plan = get_meal_plan(week_key)
    if not meal_plan or "meal_plan" not in meal_plan or "daily_plans" not in meal_plan["meal_plan"]:
        return None
    today = datetime.now().strftime("%A").lower()
    return meal_plan["meal_plan"]["daily_plans"].get(today)

def get_weekly_meal_plan():
    week_key = get_week_key()
    meal_plan = get_meal_plan(week_key)
    if not meal_plan or "meal_plan" not in meal_plan:
        return None
    return meal_plan["meal_plan"]

def generate_meal_plan():
    try:
        print("Starting meal plan generation...")
        
        print("Calling Claude API to generate meal plan...")
        meal_plan = call_claude(get_meal_prompt())
        
        if "error" in meal_plan:
            print(f"Error generating meal plan: {meal_plan['error']}")
            raise HTTPException(status_code=500, detail=meal_plan["error"])
        
        # Validate meal plan structure
        if not isinstance(meal_plan, dict):
            print("Error: Meal plan is not a dictionary")
            raise HTTPException(status_code=500, detail="Invalid meal plan format")
        
        if "meal_plan" not in meal_plan:
            print("Error: No 'meal_plan' key in response")
            raise HTTPException(status_code=500, detail="Invalid meal plan structure")
        
        if "daily_plans" not in meal_plan["meal_plan"]:
            print("Error: No 'daily_plans' key in meal plan")
            raise HTTPException(status_code=500, detail="Invalid meal plan structure")
        
        print("Meal plan generated successfully, saving to database...")
        # Save the meal plan
        week_key = get_week_key()
        save_meal_plan(week_key, meal_plan)
        print("Meal plan saved successfully")
        
        return {"status": "success", "plan": meal_plan}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in generate_meal_plan: {str(e)}")
        print(f"Error traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

def process_plan_update(meal_plan, response, context, day=None):
    try:
        week_key = get_week_key()
        modification = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "day": day,
            "response": response
        }
        add_modification(week_key, modification)
        return True
    except Exception as e:
        print(f"Error processing plan update: {str(e)}")
        return False

def build_today_prompt(today_plan, day, message, full_plan):
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

You are an assistant helping with this meal plan. Respond concisely in a technical, precise style.
"""
    return prompt

def build_weekly_prompt(meal_plan, message):
    overview = meal_plan.get("overview", {})
    calorie_goal = overview.get("calorie_goal", "Not specified")
    protein_goal = overview.get("protein_goal", "Not specified")
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

Respond concisely in a technical and precise style.
"""
    return prompt

def build_general_prompt(meal_plan, message):
    overview = meal_plan.get("overview", {})
    calorie_goal = overview.get("calorie_goal", "Not specified")
    protein_goal = overview.get("protein_goal", "Not specified")
    prompt = f"""You are MAGI, an AI assistant for a meal planning application in the style of NERV terminals from Evangelion.

NUTRITIONAL PARAMETERS:
- Calorie Goal: {calorie_goal}
- Protein Goal: {protein_goal}

USER QUERY: {message}

Respond concisely in a technical, precise style.
"""
    return prompt

# ---------- Phone Number Authentication Models & Endpoints ----------

class RequestOTP(BaseModel):
    phone: str

class VerifyOTP(BaseModel):
    phone: str
    otp: str

class Token(BaseModel):
    access_token: str
    token_type: str

def send_sms(phone: str, otp: str):
    # Replace with an actual SMS API integration in production
    print(f"Sending OTP {otp} to phone {phone}")

def generate_otp():
    return f"{random.randint(100000, 999999)}"


# ---------- FastAPI Application ----------
app = FastAPI()
templates = Jinja2Templates(directory="templates")  # Optional if you use templates


@app.post("/auth/request-otp")
def request_otp(data: RequestOTP):
    phone = data.phone

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create a user record if it doesn't exist
    cursor.execute("SELECT * FROM users WHERE phone = ?", (phone,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (phone) VALUES (?)", (phone,))
        conn.commit()  # commit the new user
    
    # Generate OTP and store it
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRATION_MINUTES)
    cursor.execute(
        "INSERT INTO otps (phone, otp, expires_at) VALUES (?, ?, ?)",
        (phone, otp, expires_at.isoformat())
    )
    conn.commit()
    conn.close()
    
    send_sms(phone, otp)  # Replace this with actual SMS sending in production
    return {"message": "OTP sent"}


@app.post("/auth/verify-otp", response_model=Token)
def verify_otp(data: VerifyOTP):
    phone = data.phone
    otp = data.otp
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM otps WHERE phone = ? AND otp = ? AND used = 0", (phone, otp))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    expires_at = datetime.fromisoformat(row["expires_at"])
    if datetime.utcnow() > expires_at:
        conn.close()
        raise HTTPException(status_code=400, detail="OTP expired")
    
    cursor.execute("UPDATE otps SET used = 1 WHERE id = ?", (row["id"],))
    cursor.execute("SELECT * FROM users WHERE phone = ?", (phone,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (phone) VALUES (?)", (phone,))
        conn.commit()
        user_id = cursor.lastrowid
    else:
        user_id = user["id"]
    conn.commit()
    conn.close()
    
    payload = {
        "sub": phone,
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, AUTH_SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

http_bearer = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, AUTH_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/users/me")
def get_profile(current_user: dict = Depends(get_current_user)):
    return {"phone": current_user["sub"], "user_id": current_user["user_id"]}




@app.get("/")
def index(request: Request):
    """Index route to serve the main app page."""
    week_key = get_week_key()
    plan_exists = get_meal_plan(week_key) is not None
    # If you have templates, you could render one:
    return templates.TemplateResponse("index.html", {"request": request, "has_plan": plan_exists})

@app.get("/landing")
def index(request: Request, theme: str = None):
    """Index route to serve the main app page with optional theme parameter."""
    week_key = get_week_key()
    plan_exists = get_meal_plan(week_key) is not None
    
    # Pass the theme parameter to the template
    return templates.TemplateResponse(
        "landing.html", 
        {"request": request, "theme": theme}
    )

@app.get("/api/weekly")
def api_weekly():
    try:
        week_key = get_week_key()
        meal_plan = get_meal_plan(week_key)
        if not meal_plan or "meal_plan" not in meal_plan:
            return {
                "status": "success",
                "plan": None,
                "message": "No meal plan found. Please generate one first."
            }
        return {"status": "success", "plan": meal_plan["meal_plan"]}
    except Exception as e:
        print(f"Error in api_weekly: {str(e)}")
        print(f"Error traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/today")
def api_today():
    try:
        week_key = get_week_key()
        today = datetime.now().strftime("%A").lower()
        meal_plan = get_meal_plan(week_key)
        if not meal_plan or "meal_plan" not in meal_plan or "daily_plans" not in meal_plan["meal_plan"]:
            raise HTTPException(status_code=404, detail="No meal plan found")
        if today not in meal_plan["meal_plan"]["daily_plans"]:
            raise HTTPException(status_code=404, detail=f"No meal plan found for {today}")
        today_plan = meal_plan["meal_plan"]["daily_plans"][today]
        return {"status": "success", "plan": today_plan}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def api_chat(data: dict):
    try:
        if "message" not in data:
            raise HTTPException(status_code=400, detail="No message provided")
        message = data["message"]
        context = data.get("context", "general")
        week_key = get_week_key()
        meal_plan = get_meal_plan(week_key)
        if not meal_plan:
            raise HTTPException(status_code=404, detail="No meal plan found")
        if "meal_plan" not in meal_plan:
            raise HTTPException(status_code=500, detail="Invalid meal plan structure")
        today = datetime.now().strftime("%A").lower()
        if today not in meal_plan["meal_plan"]["daily_plans"]:
            raise HTTPException(status_code=404, detail=f"No meal plan found for {today}")
        today_plan = meal_plan["meal_plan"]["daily_plans"][today]
        prompt = build_today_prompt(today_plan, today, message, meal_plan["meal_plan"])
        response = call_anthropic(prompt)
        print("Recieved update from anthropic")
        plan_updated = False
        if "PLAN_UPDATE:" in response:
            plan_updated = process_plan_update(meal_plan, response, context, today if context=="today" else None)
            response = response.replace("PLAN_UPDATE:", "").strip()
        return {"status": "success", "message": response, "plan_updated": plan_updated}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/request-otp")
async def request_otp(phone_number: str):
    try:
        # In a real application, you would send an OTP via SMS
        # For development, we'll just create a user and return a token
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT user_id FROM users WHERE phone_number = ?", (phone_number,))
        user = cursor.fetchone()
        
        if not user:
            # Create new user
            cursor.execute("INSERT INTO users (phone_number) VALUES (?)", (phone_number,))
            user_id = cursor.lastrowid
            conn.commit()
        else:
            user_id = user["user_id"]
        
        conn.close()
        
        # Create access token
        access_token = create_access_token({"user_id": user_id})
        
        return {
            "status": "success",
            "message": "OTP sent successfully",
            "access_token": access_token
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/verify-otp")
async def verify_otp(phone_number: str, otp: str):
    try:
        # In a real application, you would verify the OTP
        # For development, we'll just return a token
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id FROM users WHERE phone_number = ?", (phone_number,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        conn.close()
        
        # Create access token
        access_token = create_access_token({"user_id": user["user_id"]})
        
        return {
            "status": "success",
            "message": "OTP verified successfully",
            "access_token": access_token
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
async def generate_meal_plan_endpoint():
    try:
        print("Starting meal plan generation...")
        
        print("Calling Claude API to generate meal plan...")
        meal_plan = call_claude(get_meal_prompt())
        
        if "error" in meal_plan:
            print(f"Error generating meal plan: {meal_plan['error']}")
            raise HTTPException(status_code=500, detail=meal_plan["error"])
        
        # Validate meal plan structure
        if not isinstance(meal_plan, dict):
            print("Error: Meal plan is not a dictionary")
            raise HTTPException(status_code=500, detail="Invalid meal plan format")
        
        if "meal_plan" not in meal_plan:
            print("Error: No 'meal_plan' key in response")
            raise HTTPException(status_code=500, detail="Invalid meal plan structure")
        
        if "daily_plans" not in meal_plan["meal_plan"]:
            print("Error: No 'daily_plans' key in meal plan")
            raise HTTPException(status_code=500, detail="Invalid meal plan structure")
        
        print("Meal plan generated successfully, saving to database...")
        # Save the meal plan
        week_key = get_week_key()
        save_meal_plan(week_key, meal_plan)
        print("Meal plan saved successfully")
        
        return {"status": "success", "plan": meal_plan}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in generate_meal_plan: {str(e)}")
        print(f"Error traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Run the Application ----------
# Use: uvicorn main:app --host 0.0.0.0 --port 8080

