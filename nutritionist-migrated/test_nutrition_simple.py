#!/usr/bin/env python3
"""
Simple test script for the nutrition analysis endpoint (no auth required)
Usage: python test_nutrition_simple.py <image_path>
"""

import requests
import sys
import os
import json

# Server configuration
BASE_URL = "http://5.161.86.187"
NUTRITION_URL = f"{BASE_URL}/api/nutrition/analyze-image"

def test_nutrition_endpoint(image_path: str):
    """
    Test the nutrition analysis endpoint without authentication
    
    Args:
        image_path: Path to the image file
    """
    # Check if image file exists
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        sys.exit(1)
    
    # Prepare the image file
    with open(image_path, 'rb') as image_file:
        files = {
            'image': (os.path.basename(image_path), image_file, 'image/jpeg')
        }
        
        print(f"📸 Analyzing image: {image_path}")
        print(f"🚀 Sending request to: {NUTRITION_URL}")
        
        # Make the request (no authentication headers needed)
        response = requests.post(NUTRITION_URL, files=files)
    
    # Process the response
    print(f"\n📊 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            result = response.json()
            print("\n✅ SUCCESS! Nutrition Analysis Result:")
            print("=" * 50)
            
            analysis = result.get("analysis", {})
            print(f"🍽️  Description: {analysis.get('description', 'N/A')}")
            print(f"🔥 Calories: {analysis.get('calories', 'N/A')}")
            print(f"🥩 Protein: {analysis.get('protein', 'N/A')}g")
            print(f"🍞 Carbs: {analysis.get('carbs', 'N/A')}g")
            print(f"🥑 Fat: {analysis.get('fat', 'N/A')}g")
            print(f"⏰ Timestamp: {analysis.get('timestamp', 'N/A')}")
            
            print("\n📋 Full Response:")
            print(json.dumps(result, indent=2))
            
        except json.JSONDecodeError:
            print("❌ Invalid JSON response")
            print(f"Raw response: {response.text}")
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(f"Error response: {response.text}")
        
        # Try to parse error details
        try:
            error_data = response.json()
            print(f"Error details: {json.dumps(error_data, indent=2)}")
        except:
            pass

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python test_nutrition_simple.py <image_path>")
        print("\nSupported image formats: JPEG, PNG, GIF, WebP")
        print("Maximum file size: 5MB")
        print("\nExample:")
        print("  python test_nutrition_simple.py food_image.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    print("🧪 Testing Nutrition Analysis Endpoint (No Auth)")
    print("=" * 45)
    
    # Test the endpoint
    test_nutrition_endpoint(image_path)

if __name__ == "__main__":
    main() 