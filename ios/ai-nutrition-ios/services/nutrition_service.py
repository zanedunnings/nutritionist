import base64
import os
from typing import Dict, Any
import openai
from openai import OpenAI

def get_openai_client():
    """Initialize OpenAI client for vision analysis"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    return OpenAI(api_key=api_key)

def analyze_food_image_with_openai(image_path: str) -> Dict[str, Any]:
    """
    Analyze food image using OpenAI's GPT-4 Vision API
    """
    try:
        client = get_openai_client()
        
        # Encode image to base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this food image and provide detailed nutritional information. 
                            Return the response in JSON format with the following structure:
                            {
                                "food_items": [
                                    {
                                        "name": "food name",
                                        "quantity": "estimated quantity",
                                        "calories": estimated_calories,
                                        "macronutrients": {
                                            "protein": grams,
                                            "carbohydrates": grams,
                                            "fat": grams,
                                            "fiber": grams
                                        },
                                        "micronutrients": {
                                            "vitamin_c": mg,
                                            "iron": mg,
                                            "calcium": mg
                                        }
                                    }
                                ],
                                "total_calories": total_estimated_calories,
                                "confidence": confidence_score
                            }"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        return {
            "success": True,
            "analysis": response.choices[0].message.content,
            "model": "gpt-4-vision-preview"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": "gpt-4-vision-preview"
        }

# Keep the original function for backwards compatibility but use OpenAI
def analyze_food_image(image_path: str) -> Dict[str, Any]:
    """
    Analyze food image using OpenAI GPT-4 Vision (fallback from Anthropic)
    """
    return analyze_food_image_with_openai(image_path) 