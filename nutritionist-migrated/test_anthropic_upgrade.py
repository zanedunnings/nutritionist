#!/usr/bin/env python3
"""
Test script to verify Anthropic vision upgrade works locally
Usage: python test_anthropic_upgrade.py <image_path>
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.nutrition_service import analyze_food_image, NutritionAnalysisError

async def test_anthropic_vision(image_path: str):
    """Test the upgraded Anthropic vision functionality"""
    print(f"🧪 Testing Anthropic Vision Upgrade")
    print("=" * 40)
    print(f"📸 Image: {image_path}")
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return False
    
    # Read image data
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Determine content type
        content_type = "image/jpeg"
        if image_path.lower().endswith('.png'):
            content_type = "image/png"
        elif image_path.lower().endswith('.gif'):
            content_type = "image/gif"
        elif image_path.lower().endswith('.webp'):
            content_type = "image/webp"
        
        print(f"📊 Image size: {len(image_data)} bytes")
        print(f"📊 Content type: {content_type}")
        print(f"🚀 Calling Anthropic Vision API...")
        
        # Test the nutrition analysis
        result = await analyze_food_image(image_data, content_type)
        
        print("\n✅ SUCCESS! Anthropic Vision Analysis Result:")
        print("=" * 50)
        print(f"🍽️  Description: {result.get('description', 'N/A')}")
        print(f"🔥 Calories: {result.get('calories', 'N/A')}")
        print(f"🥩 Protein: {result.get('protein', 'N/A')}g")
        print(f"🍞 Carbs: {result.get('carbs', 'N/A')}g")
        print(f"🥑 Fat: {result.get('fat', 'N/A')}g")
        print(f"⏰ Timestamp: {result.get('timestamp', 'N/A')}")
        
        return True
        
    except NutritionAnalysisError as e:
        print(f"❌ Nutrition Analysis Error: {e.message} (Code: {e.code})")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_anthropic_upgrade.py <image_path>")
        print("\nSupported image formats: JPEG, PNG, GIF, WebP")
        print("Maximum file size: 5MB")
        print("\nExample:")
        print("  python test_anthropic_upgrade.py sandwich.jpeg")
        print("\nThis will test the upgraded Anthropic vision functionality locally!")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Run the async test
    success = asyncio.run(test_anthropic_vision(image_path))
    
    if success:
        print("\n🎉 Anthropic Vision Upgrade Test PASSED!")
        print("✅ Ready to deploy to server!")
    else:
        print("\n💥 Anthropic Vision Upgrade Test FAILED!")
        print("❌ Fix issues before deploying!")
        sys.exit(1)

if __name__ == "__main__":
    main() 