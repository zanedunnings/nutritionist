#!/usr/bin/env python3
"""
Test script for the nutrition analysis endpoint
Usage: python test_nutrition_endpoint.py <image_path> [username] [password]
"""

import requests
import sys
import os
import json
from pathlib import Path

# Server configuration
BASE_URL = "http://5.161.86.187"
LOGIN_URL = f"{BASE_URL}/auth/login"
NUTRITION_URL = f"{BASE_URL}/api/nutrition/analyze-image"

def login(username: str, password: str) -> str:
    """
    Login to the server and get an access token
    
    Args:
        username: User's username
        password: User's password
        
    Returns:
        Access token string
    """
    login_data = {
        "username": username,
        "password": password
    }
    
    print(f"🔐 Logging in as {username}...")
    
    # Try JSON format first
    try:
        response = requests.post(LOGIN_URL, json=login_data, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if access_token:
                print("✅ Login successful!")
                return access_token
    except Exception as e:
        print(f"JSON login failed: {e}")
    
    # Try form data format as fallback
    try:
        response = requests.post(LOGIN_URL, data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if access_token:
                print("✅ Login successful!")
                return access_token
    except Exception as e:
        print(f"Form data login failed: {e}")
    
    # If both methods fail, show error
    print(f"❌ Login failed: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Try to get more info about available endpoints
    try:
        # Check if the auth endpoint exists at all
        test_response = requests.get(f"{BASE_URL}/auth/")
        print(f"Auth endpoint test: {test_response.status_code}")
        
        # Try alternative login paths
        alt_login_url = f"{BASE_URL}/token"
        alt_response = requests.post(alt_login_url, data=login_data)
        print(f"Alternative login (/token): {alt_response.status_code}")
        
    except Exception as e:
        print(f"Endpoint discovery failed: {e}")
    
    sys.exit(1)

def test_nutrition_endpoint(image_path: str, access_token: str):
    """
    Test the nutrition analysis endpoint
    
    Args:
        image_path: Path to the image file
        access_token: JWT access token
    """
    # Check if image file exists
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        sys.exit(1)
    
    # Prepare headers with authentication
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # Prepare the image file
    with open(image_path, 'rb') as image_file:
        files = {
            'image': (os.path.basename(image_path), image_file, 'image/jpeg')
        }
        
        print(f"📸 Analyzing image: {image_path}")
        print(f"🚀 Sending request to: {NUTRITION_URL}")
        
        # Make the request
        response = requests.post(NUTRITION_URL, files=files, headers=headers)
    
    # Process the response
    print(f"\n📊 Response Status: {response.status_code}")
    print(f"📊 Response Headers: {dict(response.headers)}")
    
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
    if len(sys.argv) < 2:
        print("Usage: python test_nutrition_endpoint.py <image_path> [username] [password]")
        print("\nSupported image formats: JPEG, PNG, GIF, WebP")
        print("Maximum file size: 5MB")
        print("\nExample:")
        print("  python test_nutrition_endpoint.py food_image.jpg myuser mypassword")
        print("  python test_nutrition_endpoint.py food_image.jpg  # Will prompt for credentials")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Get credentials
    if len(sys.argv) >= 4:
        username = sys.argv[2]
        password = sys.argv[3]
    else:
        username = input("Username: ")
        password = input("Password: ")
    
    print("🧪 Testing Nutrition Analysis Endpoint")
    print("=" * 40)
    
    # Login and get token
    access_token = login(username, password)
    
    # Test the endpoint
    test_nutrition_endpoint(image_path, access_token)

if __name__ == "__main__":
    main() 