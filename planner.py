from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict
from replit import db
import anthropic
from get_todays_plan import parse_meal_plan, send_meal_plan_sms
from create_weekly_plans import get_week_key

def get_current_context() -> Optional[Dict]:
    """Get the current meal plan context if it exists"""
    week_key = get_week_key()
    print(week_key)
    print(list(db.keys()))
    if week_key not in db:
        return None

    current_plan = parse_meal_plan(db[week_key])
    today = datetime.now().strftime("%A")

    return {
        'week_key': week_key,
        'current_plan': current_plan,
        'today_plan': current_plan.get(today, {}),
        'day': today
    }

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

    # Create prompt for Claude that includes context and handling instructions
    prompt = f"""Current meal plan for {context['day']}:
{context['today_plan']}

User message: {message}

Please help with this meal plan request. You can:
1. Suggest alternative meals
2. Provide recipes and cooking instructions
3. Handle meal substitutions and recommend adjustments
4. Answer questions about the meal plan

Keep responses concise and actionable since they'll be sent via SMS.

If the user's request isn't related to these categories, politely explain what you can help with.

Ensure all responses and answers approximately follow the calories in the meal plan, unless specified they want to be different.

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