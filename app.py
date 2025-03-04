from flask import Flask, request, jsonify, render_template
from twilio.twiml.messaging_response import MessagingResponse
from replit import db
import os
import anthropic
from datetime import datetime
import create_weekly_plans
import get_todays_plan
from planner import handle_meal_interaction, get_current_context

app = Flask(__name__)

@app.route('/')
def index():
    """Main page showing current meal plan information"""
    context = get_current_context()
    return render_template('index.html', context=context)

@app.route('/api/get_today_plan', methods=['GET'])
def get_today_plan():
    """API endpoint to get today's meal plan"""
    today_plan = get_todays_plan.get_meal_plan_for_today()
    return jsonify(today_plan)

@app.route('/api/get_weekly_plan', methods=['GET'])
def get_weekly_plan():
    """API endpoint to get the full weekly meal plan"""
    week_key = create_weekly_plans.get_week_key()
    if week_key in db:
        raw_text = db[week_key]
        meal_plan = get_todays_plan.parse_meal_plan(raw_text)
        return jsonify(meal_plan)
    return jsonify({"error": "No meal plan found for this week"})

@app.route('/api/create_weekly_plan', methods=['POST'])
def create_weekly_plan():
    """API endpoint to generate a new weekly meal plan"""
    meal_plan = create_weekly_plans.fetch_meal_plan()
    # Send SMS notification if configured
    if request.args.get('send_sms', 'false').lower() == 'true':
        phone_number = os.environ.get('TARGET_PHONE_NUMBER')
        if phone_number and create_weekly_plans.send_weekly_plan_sms(meal_plan):
            return jsonify({"status": "success", "message": "Meal plan created and SMS sent"})
        else:
            return jsonify({"status": "partial", "message": "Meal plan created but SMS failed"})
    return jsonify({"status": "success", "message": "Meal plan created"})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook for handling Twilio SMS interactions"""
    # Get incoming message details from Twilio's request
    incoming_msg = request.values.get('Body', '').strip()
    phone_number = request.values.get('From', '')

    # Create TwiML response
    resp = MessagingResponse()

    try:
        # Get Claude API key
        claude_api_key = os.environ.get('CLAUDE_API_KEY')
        if not claude_api_key:
            resp.message("Sorry, I'm not configured correctly right now. Please try again later.")
            return str(resp)

        # Handle the meal interaction
        if handle_meal_interaction(phone_number, incoming_msg, claude_api_key):
            return str(resp)
        else:
            resp.message("Sorry, I couldn't process your request.")
            return str(resp)

    except Exception as e:
        resp.message(f"Sorry, I encountered an error: {str(e)}")
        return str(resp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)