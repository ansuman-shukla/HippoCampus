#!/usr/bin/env python3
"""
Debug script for the specific refresh token issue
"""
import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_specific_refresh_token():
    """Test the specific refresh token that's failing"""
    
    refresh_token = "c4h7lbg5m7bm"
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    
    print("🔍 Testing specific refresh token...")
    print(f"📝 Refresh token: {refresh_token}")
    print(f"📝 Supabase URL: {supabase_url}")
    print(f"📝 Anon key length: {len(supabase_anon_key) if supabase_anon_key else 'NOT SET'}")
    
    # Test 1: Direct call to Supabase API
    print("\n--- Test 1: Direct Supabase API Call ---")
    url = f"{supabase_url}/auth/v1/token"
    headers = {
        "apikey": supabase_anon_key,
        "Content-Type": "application/json"
    }
    data = {
        "grant_type": "refresh_token", 
        "refresh_token": refresh_token
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, headers=headers, json=data)
            print(f"📝 Status Code: {response.status_code}")
            print(f"📝 Response Headers: {dict(response.headers)}")
            print(f"📝 Response Body: {response.text}")
            
            if response.status_code != 200:
                print("❌ Direct Supabase API call failed")
                
                # Try to parse error details
                try:
                    error_data = response.json()
                    print(f"📝 Error Details: {json.dumps(error_data, indent=2)}")
                except:
                    print("📝 Could not parse error response as JSON")
            else:
                print("✅ Direct Supabase API call succeeded")
                token_data = response.json()
                print(f"📝 Token Data Keys: {list(token_data.keys())}")
                
        except Exception as e:
            print(f"❌ Exception during direct API call: {e}")
    
    # Test 2: Call through our FastAPI endpoint
    print("\n--- Test 2: FastAPI Endpoint Call ---")
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Test if server is running
            health_response = await client.get(f"{base_url}/health")
            if health_response.status_code != 200:
                print("❌ FastAPI server not running")
                return
            
            print("✅ FastAPI server is running")
            
            # Test refresh endpoint
            response = await client.post(
                f"{base_url}/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            
            print(f"📝 FastAPI Status Code: {response.status_code}")
            print(f"📝 FastAPI Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ FastAPI refresh endpoint succeeded")
            else:
                print("❌ FastAPI refresh endpoint failed")
                
        except httpx.ConnectError:
            print("❌ Could not connect to FastAPI server (not running?)")
        except Exception as e:
            print(f"❌ Exception during FastAPI call: {e}")

    # Test 3: Validate refresh token format
    print("\n--- Test 3: Refresh Token Validation ---")
    print(f"📝 Token length: {len(refresh_token)}")
    print(f"📝 Token characters: {set(refresh_token)}")
    print(f"📝 Is alphanumeric: {refresh_token.isalnum()}")
    
    # Check if token looks like a typical Supabase refresh token
    if len(refresh_token) < 10:
        print("⚠️ Token seems too short for a Supabase refresh token")
    elif not refresh_token.isalnum():
        print("⚠️ Token contains non-alphanumeric characters")
    else:
        print("✅ Token format looks reasonable")

if __name__ == "__main__":
    asyncio.run(test_specific_refresh_token())
