
from datetime import datetime
import create_weekly_plans
import get_todays_plan

def should_create_weekly_plan():
    """Check if today is Sunday"""
    return datetime.now().weekday() == 6  # Sunday is 6

if __name__ == "__main__":
    if should_create_weekly_plan():
        print("It's Sunday! Creating weekly meal plan...")
        create_weekly_plans.fetch_meal_plan()
    else:
        print(f"Getting today's meal plan for {datetime.now().strftime('%A')}...")
        today_plan = get_todays_plan.get_meal_plan_for_today()
        if today_plan:
            # Format and send meal plan
            for meal, description in today_plan.items():
                print(f"{meal}: {description}")
            
            # Send SMS if configured
            phone_number = get_todays_plan.os.environ.get('TARGET_PHONE_NUMBER')
            if phone_number:
                message = get_todays_plan.format_meal_plan_for_sms(today_plan)
                if get_todays_plan.send_meal_plan_sms(phone_number, message):
                    print("\nMeal plan sent via SMS successfully!")
                else:
                    print("\nFailed to send SMS")
