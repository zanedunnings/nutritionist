from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from replit import db
import os
import anthropic
from datetime import datetime
from get_todays_plan import parse_meal_plan, send_meal_plan_sms
from create_weekly_plans import get_week_key

app = Flask(__name__)



def get_current_context():
    """Get the current meal plan context if it exists"""
    week_key = get_week_key()
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

@app.route('/webhook', methods=['POST'])
def webhook():
    # Get incoming message details from Twilio's request
    incoming_msg = request.values.get('Body', '').strip()
    phone_number = request.values.get('From', '')

    # Create TwiML response
    resp = MessagingResponse()

    try:
        # Get current context
        context = get_current_context()
        if not context:
            resp.message("I couldn't find your current meal plan. Please make sure one is generated first.")
            return str(resp)

        # Get Claude API key
        claude_api_key = os.environ.get('CLAUDE_API_KEY')
        if not claude_api_key:
            resp.message("Sorry, I'm not configured correctly right now. Please try again later.")
            return str(resp)

        # Create prompt for Claude
        prompt = f"""Current meal plan for {context['day']}:
{context['today_plan']}

User message: {incoming_msg}

Please help with this meal plan request. You can:
1. Suggest alternative meals
2. Provide recipes and cooking instructions
3. Handle meal substitutions and recommend adjustments
4. Answer questions about the meal plan

Keep responses concise and actionable since they'll be sent via SMS.

If the user's request isn't related to these categories, politely explain what you can help with.

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

        # Handle substitution recording
        if response_text.startswith("SUBSTITUTION_RECORDED"):
            response_text = response_text.replace("SUBSTITUTION_RECORDED", "").strip()
            modifications_key = f"{context['week_key']}_modifications"
            modifications = db.get(modifications_key, [])
            modifications.append({
                'day': context['day'],
                'message': incoming_msg,
                'timestamp': datetime.now().isoformat(),
                'response': response_text
            })
            db[modifications_key] = modifications

        # Send response back through Twilio
        resp.message(response_text)
        return str(resp)

    except Exception as e:
        resp.message("Sorry, I encountered an error. Please try again.")
        return str(resp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)