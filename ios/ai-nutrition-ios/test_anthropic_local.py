#!/usr/bin/env python3
"""
Local test script for upgraded Anthropic vision functionality
Usage: python test_anthropic_local.py <image_path>
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the services directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from nutrition_service import analyze_food_image, NutritionAnalysisError

async def test_anthropic_vision(image_path: str):
    """Test the upgraded Anthropic vision functionality locally"""
    
    print(f"🧪 Testing Anthropic Vision Upgrade")
    print("=" * 40)
    print(f"📸 Image: {image_path}")
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return False
    
    try:
        # Read image file
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Determine content type
        file_ext = Path(image_path).suffix.lower()
        content_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        content_type = content_type_map.get(file_ext, 'image/jpeg')
        
        print(f"📄 Content-Type: {content_type}")
        print(f"📏 File size: {len(image_data)} bytes")
        print(f"🔍 Analyzing with Anthropic Claude Vision...")
        
        # Call the nutrition analysis function
        result = await analyze_food_image(image_data, content_type)
        
        print("\n✅ SUCCESS! Analysis Result:")
        print("=" * 50)
        print(f"🍽️  Description: {result.get('description', 'N/A')}")
        print(f"🔥 Calories: {result.get('calories', 'N/A')}")
        print(f"🥩 Protein: {result.get('protein', 'N/A')}g")
        print(f"🍞 Carbs: {result.get('carbs', 'N/A')}g")
        print(f"🥑 Fat: {result.get('fat', 'N/A')}g")
        print(f"⏰ Timestamp: {result.get('timestamp', 'N/A')}")
        
        return True
        
    except NutritionAnalysisError as e:
        print(f"❌ Nutrition Analysis Error: {e.message}")
        print(f"Error Code: {e.code}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")
        print(f"Error Type: {type(e).__name__}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_anthropic_local.py <image_path>")
        print("\nSupported image formats: JPEG, PNG, GIF, WebP")
        print("Maximum file size: 5MB")
        print("\nExample:")
        print("  python test_anthropic_local.py food_image.jpg")
        print("\nMake sure you have ANTHROPIC_API_KEY set in your environment:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Check if API key is set
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY environment variable not set!")
        print("Please set it with: export ANTHROPIC_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    # Run the test
    success = asyncio.run(test_anthropic_vision(image_path))
    
    if success:
        print("\n🎉 Anthropic vision upgrade test PASSED!")
    else:
        print("\n💥 Anthropic vision upgrade test FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main() 