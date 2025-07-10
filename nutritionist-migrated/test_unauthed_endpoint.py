#!/usr/bin/env python3
"""
Simple test script for the unauthed nutrition endpoint
Usage: python test_unauthed_endpoint.py <image_path>
"""

import requests
import sys
import os
import json

# Server configuration
BASE_URL = "http://5.161.86.187"
NUTRITION_URL = f"{BASE_URL}/api/nutrition/analyze-image"

def test_unauthed_nutrition_endpoint(image_path: str):
    """Test the unauthed nutrition analysis endpoint"""
    print(f"🧪 Testing Unauthed Nutrition Endpoint")
    print("=" * 40)
    print(f"🌐 Server: {BASE_URL}")
    print(f"📸 Image: {image_path}")
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return False
    
    # Prepare the image file
    try:
        with open(image_path, 'rb') as image_file:
            files = {
                'image': (os.path.basename(image_path), image_file, 'image/jpeg')
            }
            
            print(f"🚀 Sending request to: {NUTRITION_URL}")
            print("📊 No authentication required!")
            
            # Make the request (no auth headers needed)
            response = requests.post(NUTRITION_URL, files=files)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("\n✅ SUCCESS! Nutrition Analysis Result:")
                print("=" * 50)
                
                # Handle the response format
                if "analysis" in result:
                    analysis = result["analysis"]
                    print(f"🍽️  Description: {analysis.get('description', 'N/A')}")
                    print(f"🔥 Calories: {analysis.get('calories', 'N/A')}")
                    print(f"🥩 Protein: {analysis.get('protein', 'N/A')}g")
                    print(f"🍞 Carbs: {analysis.get('carbs', 'N/A')}g")
                    print(f"🥑 Fat: {analysis.get('fat', 'N/A')}g")
                    print(f"⏰ Timestamp: {analysis.get('timestamp', 'N/A')}")
                else:
                    # Direct format fallback
                    print(f"🍽️  Description: {result.get('description', 'N/A')}")
                    print(f"🔥 Calories: {result.get('calories', 'N/A')}")
                    print(f"🥩 Protein: {result.get('protein', 'N/A')}g")
                    print(f"🍞 Carbs: {result.get('carbs', 'N/A')}g")
                    print(f"🥑 Fat: {result.get('fat', 'N/A')}g")
                    print(f"⏰ Timestamp: {result.get('timestamp', 'N/A')}")
                
                print(f"\n📋 Full Response:")
                print(json.dumps(result, indent=2))
                return True
                
            except json.JSONDecodeError:
                print("❌ Invalid JSON response")
                print(f"Raw response: {response.text}")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"❌ Error during request: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_unauthed_endpoint.py <image_path>")
        print("\nSupported image formats: JPEG, PNG, GIF, WebP")
        print("Maximum file size: 5MB")
        print("\nExample:")
        print("  python test_unauthed_endpoint.py sandwich.jpeg")
        print("\nThis will test the unauthed nutrition endpoint with Anthropic vision!")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Test the unauthed endpoint
    success = test_unauthed_nutrition_endpoint(image_path)
    
    if success:
        print("\n🎉 Unauthed Nutrition Endpoint Test PASSED!")
        print("✅ Anthropic vision upgrade is working!")
    else:
        print("\n💥 Unauthed Nutrition Endpoint Test FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main() 