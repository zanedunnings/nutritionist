# Add this to your existing app.py or create a new router file

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
import openai
import base64
import json
import os
from typing import Optional
from datetime import datetime
import io
from PIL import Image

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

# Add this to your existing FastAPI app or router
@app.post("/api/nutrition/analyze-image")
async def analyze_food_image(
    image: UploadFile = File(...),
    # user: dict = Depends(get_current_user)  # Uncomment if you have auth
):
    """
    Analyze a food image and return calorie and nutrition information
    """
    try:
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail={"error": "Only image files are allowed", "code": "INVALID_FILE_TYPE"}
            )
        
        # Check file size (10MB limit)
        contents = await image.read()
        if len(contents) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=400,
                detail={"error": "File too large. Maximum size is 10MB", "code": "FILE_TOO_LARGE"}
            )
        
        # Convert image to base64
        base64_image = base64.b64encode(contents).decode('utf-8')
        
        # Call OpenAI Vision API
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this food image and return ONLY a JSON response with 'calories' (number) and 'description' (string describing the food and portion size). Example: {\"calories\": 350, \"description\": \"Grilled chicken breast with steamed broccoli, approximately 6oz chicken and 1 cup broccoli\"}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image.content_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        
        # Parse the response
        content = response.choices[0].message.content
        if not content:
            raise HTTPException(
                status_code=500,
                detail={"error": "No response from AI model", "code": "AI_NO_RESPONSE"}
            )
        
        # Parse JSON response from AI
        try:
            analysis_result = json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500,
                detail={"error": "Invalid response format from AI model", "code": "AI_INVALID_FORMAT"}
            )
        
        # Validate required fields
        if not analysis_result.get("calories") or not analysis_result.get("description"):
            raise HTTPException(
                status_code=500,
                detail={"error": "Incomplete analysis result", "code": "AI_INCOMPLETE_RESULT"}
            )
        
        # Optional: Save to database
        # await save_food_analysis(user["id"], analysis_result, image.filename)
        
        # Return successful response
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "analysis": {
                    "calories": int(analysis_result["calories"]),
                    "description": analysis_result["description"],
                    "timestamp": datetime.now().isoformat()
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Image analysis error: {e}")
        
        # Handle specific OpenAI errors
        if "insufficient_quota" in str(e):
            raise HTTPException(
                status_code=429,
                detail={"error": "API quota exceeded", "code": "QUOTA_EXCEEDED"}
            )
        
        if "invalid_api_key" in str(e):
            raise HTTPException(
                status_code=401,
                detail={"error": "Invalid API key", "code": "INVALID_API_KEY"}
            )
        
        # Generic error response
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error during image analysis", "code": "ANALYSIS_ERROR"}
        )

# Optional: Add database models if you want to store analysis results
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FoodAnalysis(Base):
    __tablename__ = "food_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    calories = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    image_filename = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

async def save_food_analysis(user_id: int, analysis_result: dict, filename: str):
    # Add database save logic here
    pass
""" 