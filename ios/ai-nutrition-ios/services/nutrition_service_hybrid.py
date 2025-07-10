import base64
import os
import requests
from typing import Dict, Any
import anthropic

def get_anthropic_client():
    """Initialize Anthropic client (version 0.7.7 compatible)"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")
    return anthropic.Anthropic(api_key=api_key)

def analyze_food_image_logmeal(image_path: str) -> Dict[str, Any]:
    """
    Analyze food image using LogMeal API (specialized for food recognition)
    """
    try:
        api_key = os.getenv("LOGMEAL_API_KEY")
        if not api_key:
            raise ValueError("LOGMEAL_API_KEY environment variable is required")
        
        url = "https://api.logmeal.es/v2/image/segmentation/complete"
        
        with open(image_path, 'rb') as image_file:
            files = {'image': image_file}
            headers = {'Authorization': f'Bearer {api_key}'}
            
            response = requests.post(url, files=files, headers=headers)
            response.raise_for_status()
            
            return {
                "success": True,
                "analysis": response.json(),
                "model": "logmeal-api"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": "logmeal-api"
        }

def generate_nutrition_summary(food_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use Anthropic 0.7.7 to generate a nutrition summary from food analysis data
    """
    try:
        client = get_anthropic_client()
        
        # Format the food analysis data for Anthropic
        analysis_text = str(food_analysis)
        
        prompt = f"""Human: Based on this food analysis data, provide a comprehensive nutrition summary:

{analysis_text}

Please provide:
1. A list of identified food items
2. Estimated calories for each item
3. Total estimated calories
4. Macronutrient breakdown (protein, carbs, fat)
5. Any notable nutritional highlights 