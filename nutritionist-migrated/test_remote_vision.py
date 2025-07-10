#!/usr/bin/env python3
"""
Simple test script for the remote nutrition API with vision
Usage: python test_remote_vision.py <image_path> <username> <password>
"""

import requests
import sys
import os
import json
from pathlib import Path

# Server configuration
BASE_URL = "http://5.161.86.187"
LOGIN_URL = f"{BASE_URL}/token"  # Common FastAPI token endpoint
NUTRITION_URL = f"{BASE_URL}/api/nutrition/analyze-image"

def login(username: str, password: str) -> str:
    """Login and get access token"""
    print(f"🔐 Logging in as {username}...")
    
    # FastAPI typically uses form data for OAuth2 token endpoint
    login_data = {
        "username": username,
        "password": password
    }
    
    # Try the standard /token endpoint first
    try:
        response = requests.post(LOGIN_URL, data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if access_token:
                print("✅ Login successful!")
                return access_token
    except Exception as e:
        print(f"Token endpoint failed: {e}")
    
    # Try alternative auth endpoints
    alt_endpoints = [
        f"{BASE_URL}/auth/login",
        f"{BASE_URL}/login",
        f"{BASE_URL}/api/auth/login"
    ]
    
    for endpoint in alt_endpoints:
        try:
            # Try JSON format
            response = requests.post(endpoint, json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                if access_token:
                    print(f"✅ Login successful via {endpoint}!")
                    return access_token
            
            # Try form data format
            response = requests.post(endpoint, data=login_data)
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                if access_token:
                    print(f"✅ Login successful via {endpoint}!")
                    return access_token
        except Exception as e:
            continue
    
    print("❌ All login attempts failed!")
    print("Available endpoints to try manually:")
    print("- /token (OAuth2 standard)")
    print("- /auth/login")
    print("- /login")
    print("- /api/auth/login")
    sys.exit(1)

def test_nutrition_api(image_path: str, access_token: str):
    """Test the nutrition analysis API"""
    print(f"📸 Testing nutrition analysis with: {image_path}")
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return False
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # Prepare the image file
    try:
        with open(image_path, 'rb') as image_file:
            files = {
                'image': (os.path.basename(image_path), image_file, 'image/jpeg')
            }
            
            print(f"🚀 Sending request to: {NUTRITION_URL}")
            response = requests.post(NUTRITION_URL, files=files, headers=headers)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("\n✅ SUCCESS! Nutrition Analysis Result:")
                print("=" * 50)
                
                # Handle different response formats
                if "analysis" in result:
                    analysis = result["analysis"]
                    print(f"🍽️  Description: {analysis.get('description', 'N/A')}")
                    print(f"🔥 Calories: {analysis.get('calories', 'N/A')}")
                    print(f"🥩 Protein: {analysis.get('protein', 'N/A')}g")
                    print(f"🍞 Carbs: {analysis.get('carbs', 'N/A')}g")
                    print(f"🥑 Fat: {analysis.get('fat', 'N/A')}g")
                    print(f"⏰ Timestamp: {analysis.get('timestamp', 'N/A')}")
                else:
                    # Direct format
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
            return False
            
    except Exception as e:
        print(f"❌ Error during request: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 4:
        print("Usage: python test_remote_vision.py <image_path> <username> <password>")
        print("\nSupported image formats: JPEG, PNG, GIF, WebP")
        print("Maximum file size: 5MB")
        print("\nExample:")
        print("  python test_remote_vision.py food_image.jpg myuser mypass")
        print("\nThis will test the upgraded Anthropic vision functionality on the remote server!")
        sys.exit(1)
    
    image_path = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    
    print("🧪 Testing Remote Nutrition API with Vision")
    print("=" * 45)
    print(f"🌐 Server: {BASE_URL}")
    print(f"📸 Image: {image_path}")
    print(f"👤 User: {username}")
    
    # Login and get token
    access_token = login(username, password)
    
    # Test the nutrition API
    success = test_nutrition_api(image_path, access_token)
    
    if success:
        print("\n🎉 Remote vision API test PASSED!")
        print("✅ Anthropic vision upgrade is working on the server!")
    else:
        print("\n💥 Remote vision API test FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main() 