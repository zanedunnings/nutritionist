from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import logging

from services.nutrition_service import (
    analyze_food_image, 
    validate_image_file, 
    save_nutrition_analysis,
    NutritionAnalysisError
)
from models.database import get_db
from routes.auth import get_current_user
from models.user import User

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/analyze-image")
async def analyze_food_image_endpoint(
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Analyze a food image and return calorie and nutrition information
    
    This endpoint accepts an image file and uses Anthropic's Claude Vision API to analyze
    the food content and provide nutritional estimates.
    
    No authentication required - this is a public endpoint.
    """
    try:
        # Read file contents
        contents = await image.read()
        
        # Validate file
        validate_image_file(image.content_type, len(contents))
        
        # Analyze the image
        analysis_result = await analyze_food_image(contents, image.content_type)
        
        # Note: Not saving to database since this is now a public endpoint
        # If you want to save analysis history, you'll need authentication
        
        # Return successful response
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "analysis": {
                    "calories": analysis_result["calories"],
                    "description": analysis_result["description"],
                    "protein": analysis_result.get("protein", 0),
                    "carbs": analysis_result.get("carbs", 0),
                    "fat": analysis_result.get("fat", 0),
                    "timestamp": analysis_result["timestamp"]
                }
            }
        )
        
    except NutritionAnalysisError as e:
        logger.error(f"Nutrition analysis error: {e.message}")
        raise HTTPException(
            status_code=400 if e.code in ["INVALID_FILE_TYPE", "FILE_TOO_LARGE"] else 500,
            detail={"error": e.message, "code": e.code}
        )
    except Exception as e:
        logger.error(f"Unexpected error in nutrition analysis endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "code": "INTERNAL_ERROR"}
        )

@router.get("/health")
async def nutrition_health_check():
    """Health check endpoint for nutrition service"""
    return {"status": "ok", "service": "nutrition"}

# TODO: Add endpoints for nutrition history
# @router.get("/history")
# async def get_nutrition_history(
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get user's nutrition analysis history"""
#     pass

# TODO: Add endpoint for daily nutrition summary
# @router.get("/daily-summary")
# async def get_daily_nutrition_summary(
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get daily nutrition summary for the user"""
#     pass 