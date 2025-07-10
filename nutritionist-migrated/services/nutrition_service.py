import anthropic
import base64
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from PIL import Image
import io

from config import ANTHROPIC_API_KEY

# Set up logging
logger = logging.getLogger(__name__)

# Global client variable to avoid repeated initialization
_anthropic_client = None

def get_anthropic_client():
    """Get Anthropic client instance with proper error handling for modern API"""
    global _anthropic_client
    if _anthropic_client is None:
        try:
            if not ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            # Modern Anthropic client initialization
            _anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise
    return _anthropic_client

class NutritionAnalysisError(Exception):
    """Custom exception for nutrition analysis errors"""
    def __init__(self, message: str, code: str = "ANALYSIS_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

async def analyze_food_image(image_data: bytes, content_type: str) -> Dict[str, Any]:
    """
    Analyze a food image using Anthropic Claude Vision API (modern format)
    
    Args:
        image_data: Binary image data
        content_type: MIME type of the image
        
    Returns:
        Dict containing calories, description, and timestamp
        
    Raises:
        NutritionAnalysisError: If analysis fails
    """
    try:
        # Validate image size (5MB limit for Claude)
        if len(image_data) > 5 * 1024 * 1024:
            raise NutritionAnalysisError(
                "File too large. Maximum size is 5MB for Claude Vision", 
                "FILE_TOO_LARGE"
            )
        
        # Convert to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Determine media type for Claude
        media_type = content_type
        if media_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
            media_type = "image/jpeg"  # Default fallback
        
        # Get client instance
        client = get_anthropic_client()
        
        # Call Anthropic Claude Vision API using the modern Messages API
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """I'm going to show you an image of food. Please analyze it and return ONLY a JSON response with the following structure:
{
    "calories": <number>,
    "description": "<detailed description of the food and estimated portion size>",
    "protein": <grams of protein>,
    "carbs": <grams of carbohydrates>,
    "fat": <grams of fat>
}

Be as accurate as possible with portion size estimation. If you can't clearly identify the food, return calories as 0 and describe what you can see. Return ONLY the JSON, no other text."""
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_image
                            }
                        }
                    ]
                }
            ]
        )
        
        # Parse response from modern API
        content = None
        if hasattr(response, 'content') and response.content:
            if isinstance(response.content, list) and len(response.content) > 0:
                content = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
            else:
                content = str(response.content)
        
        if not content:
            raise NutritionAnalysisError("No response from AI model", "AI_NO_RESPONSE")
        
        # Parse JSON response
        try:
            analysis_result = json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from AI: {content}")
            raise NutritionAnalysisError("Invalid response format from AI model", "AI_INVALID_FORMAT")
        
        # Validate required fields
        required_fields = ["calories", "description"]
        for field in required_fields:
            if field not in analysis_result:
                raise NutritionAnalysisError(f"Missing required field: {field}", "AI_INCOMPLETE_RESULT")
        
        # Ensure numeric fields are integers/floats
        try:
            analysis_result["calories"] = int(analysis_result["calories"])
            analysis_result["protein"] = float(analysis_result.get("protein", 0))
            analysis_result["carbs"] = float(analysis_result.get("carbs", 0))
            analysis_result["fat"] = float(analysis_result.get("fat", 0))
        except (ValueError, TypeError):
            raise NutritionAnalysisError("Invalid numeric values in analysis result", "AI_INVALID_NUMBERS")
        
        # Add timestamp
        analysis_result["timestamp"] = datetime.now().isoformat()
        
        return analysis_result
        
    except anthropic.RateLimitError:
        raise NutritionAnalysisError("API quota exceeded", "QUOTA_EXCEEDED")
    except anthropic.AuthenticationError:
        raise NutritionAnalysisError("Invalid API key", "INVALID_API_KEY")
    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        raise NutritionAnalysisError("Anthropic API error", "ANTHROPIC_ERROR")
    except Exception as e:
        logger.error(f"Unexpected error in nutrition analysis: {e}")
        raise NutritionAnalysisError("Internal server error during image analysis", "ANALYSIS_ERROR")

def validate_image_file(content_type: str, file_size: int) -> None:
    """
    Validate image file type and size
    
    Args:
        content_type: MIME type of the file
        file_size: Size of the file in bytes
        
    Raises:
        NutritionAnalysisError: If validation fails
    """
    # Check file type
    if not content_type.startswith('image/'):
        raise NutritionAnalysisError("Only image files are allowed", "INVALID_FILE_TYPE")
    
    # Check file size (5MB limit for Claude)
    if file_size > 5 * 1024 * 1024:
        raise NutritionAnalysisError("File too large. Maximum size is 5MB", "FILE_TOO_LARGE")

async def save_nutrition_analysis(user_id: int, analysis_result: Dict[str, Any], filename: str = None) -> None:
    """
    Save nutrition analysis result to database (placeholder for future implementation)
    
    Args:
        user_id: ID of the user
        analysis_result: Analysis result from Anthropic
        filename: Original filename of the image
    """
    # TODO: Implement database storage for nutrition analysis history
    # This would create a new table for storing food analysis results
    logger.info(f"Saving nutrition analysis for user {user_id}: {analysis_result}")
    pass 