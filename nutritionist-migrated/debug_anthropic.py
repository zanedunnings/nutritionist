#!/usr/bin/env python3
"""
Debug script to test Anthropic client initialization
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_anthropic_client():
    """Test Anthropic client initialization and basic functionality"""
    
    print("🔍 Testing Anthropic client...")
    
    # Check if API key is set
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not set")
        return False
    
    print(f"✅ ANTHROPIC_API_KEY found (length: {len(api_key)})")
    
    # Try to import anthropic
    try:
        import anthropic
        print(f"✅ Anthropic library imported successfully (version: {anthropic.__version__})")
    except ImportError as e:
        print(f"❌ Failed to import anthropic: {e}")
        return False
    
    # Try to initialize client
    try:
        client = anthropic.Anthropic(api_key=api_key)
        print("✅ Anthropic client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Anthropic client: {e}")
        return False
    
    # Try a simple API call (without image)
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=50,
            messages=[
                {
                    "role": "user",
                    "content": "Hello, can you respond with just 'Hello world'?"
                }
            ]
        )
        print("✅ Simple API call successful")
        
        # Check response format
        if hasattr(response, 'content') and response.content:
            if isinstance(response.content, list) and len(response.content) > 0:
                content = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
                print(f"✅ Response content: {content}")
            else:
                content = str(response.content)
                print(f"✅ Response content (alt format): {content}")
        elif hasattr(response, 'completion'):
            print(f"✅ Response completion (old format): {response.completion}")
        else:
            print(f"❌ Unexpected response format: {type(response)}")
            print(f"Response attributes: {dir(response)}")
            return False
            
    except Exception as e:
        print(f"❌ API call failed: {e}")
        print(f"Error type: {type(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_anthropic_client()
    sys.exit(0 if success else 1) 