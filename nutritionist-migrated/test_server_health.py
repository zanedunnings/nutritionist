#!/usr/bin/env python3
"""
Simple health check script for the nutritionist server
Usage: python test_server_health.py
"""

import requests
import sys
import json

# Server configuration
BASE_URL = "http://5.161.86.187"
HEALTH_URL = f"{BASE_URL}/health"
NUTRITION_HEALTH_URL = f"{BASE_URL}/api/nutrition/health"

def test_server_health():
    """Test the server health endpoints"""
    print("🏥 Testing Server Health")
    print("=" * 30)
    
    # Test main health endpoint
    try:
        print(f"🚀 Testing main health endpoint: {HEALTH_URL}")
        response = requests.get(HEALTH_URL, timeout=10)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Main health check: {result}")
        else:
            print(f"❌ Main health check failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Main health check error: {e}")
        return False
    
    # Test nutrition health endpoint
    try:
        print(f"\n🚀 Testing nutrition health endpoint: {NUTRITION_HEALTH_URL}")
        response = requests.get(NUTRITION_HEALTH_URL, timeout=10)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Nutrition health check: {result}")
        else:
            print(f"❌ Nutrition health check failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Nutrition health check error: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("🧪 Server Health Check")
    print("=" * 25)
    print(f"🌐 Server: {BASE_URL}")
    
    success = test_server_health()
    
    if success:
        print("\n🎉 Server Health Check PASSED!")
        print("✅ Server is running properly!")
    else:
        print("\n💥 Server Health Check FAILED!")
        print("❌ Server may be down or experiencing issues!")
        sys.exit(1)

if __name__ == "__main__":
    main() 