#!/usr/bin/env python3
"""
Comprehensive debug script for refresh token issues
"""
import asyncio
import httpx
import json
import os
import sys
from dotenv import load_dotenv
import requests

load_dotenv()

def test_refresh_token_formats():
    """Test different ways to call Supabase refresh token API"""
    
    refresh_token = "c4h7lbg5m7bm"
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    
    print("🔍 Comprehensive Refresh Token Testing")
    print(f"📝 Refresh token: {refresh_token}")
    print(f"📝 Token length: {len(refresh_token)}")
    print(f"📝 Supabase URL: {supabase_url}")
    print(f"📝 Anon key available: {'Yes' if supabase_anon_key else 'No'}")
    
    if not supabase_url or not supabase_anon_key:
        print("❌ Missing environment variables!")
        return
    
    # Test 1: POST with JSON body (most common)
    print("\n--- Test 1: POST with JSON body ---")
    try:
        headers = {
            "apikey": supabase_anon_key,
            "Content-Type": "application/json"
        }
        data = {
            "refresh_token": refresh_token
        }
        
        response = requests.post(
            f"{supabase_url}/auth/v1/token?grant_type=refresh_token",
            headers=headers,
            json=data
        )
        
        print(f"📝 Status: {response.status_code}")
        print(f"📝 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Method 1 SUCCESS!")
            return response.json()
        else:
            print("❌ Method 1 failed")
            
    except Exception as e:
        print(f"❌ Method 1 exception: {e}")
    
    # Test 2: POST with form data
    print("\n--- Test 2: POST with form data ---")
    try:
        headers = {
            "apikey": supabase_anon_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        response = requests.post(
            f"{supabase_url}/auth/v1/token",
            headers=headers,
            data=data
        )
        
        print(f"📝 Status: {response.status_code}")
        print(f"📝 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Method 2 SUCCESS!")
            return response.json()
        else:
            print("❌ Method 2 failed")
            
    except Exception as e:
        print(f"❌ Method 2 exception: {e}")
    
    # Test 3: Different endpoint path
    print("\n--- Test 3: Different endpoint ---")
    try:
        headers = {
            "apikey": supabase_anon_key,
            "Authorization": f"Bearer {supabase_anon_key}",
            "Content-Type": "application/json"
        }
        data = {
            "refresh_token": refresh_token
        }
        
        response = requests.post(
            f"{supabase_url}/auth/v1/refresh",
            headers=headers,
            json=data
        )
        
        print(f"📝 Status: {response.status_code}")
        print(f"📝 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Method 3 SUCCESS!")
            return response.json()
        else:
            print("❌ Method 3 failed")
            
    except Exception as e:
        print(f"❌ Method 3 exception: {e}")
    
    # Test 4: Check token format
    print("\n--- Test 4: Token Analysis ---")
    print(f"📝 Token: '{refresh_token}'")
    print(f"📝 Length: {len(refresh_token)} characters")
    print(f"📝 Is alphanumeric: {refresh_token.isalnum()}")
    print(f"📝 Characters: {set(refresh_token)}")
    
    # Typical Supabase refresh tokens are much longer
    if len(refresh_token) < 50:
        print("⚠️  WARNING: This token seems too short for a Supabase refresh token")
        print("📝 Typical Supabase refresh tokens are 100+ characters long")
        print("📝 This might be a session ID or different type of token")
    
    return None

async def test_fastapi_endpoint():
    """Test our FastAPI refresh endpoint"""
    
    print("\n--- Testing FastAPI Endpoint ---")
    refresh_token = "c4h7lbg5m7bm"
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Check if server is running
            health_check = await client.get(f"{base_url}/")
            print(f"📝 Server status: {health_check.status_code}")
            
            if health_check.status_code != 200:
                print("❌ FastAPI server not accessible")
                return
            
            # Test refresh endpoint
            response = await client.post(
                f"{base_url}/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            
            print(f"📝 FastAPI Status: {response.status_code}")
            print(f"📝 FastAPI Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ FastAPI refresh SUCCESS!")
            else:
                print("❌ FastAPI refresh failed")
                
        except Exception as e:
            print(f"❌ FastAPI test exception: {e}")

def create_test_refresh_token():
    """Create a test with a real refresh token format"""
    
    print("\n--- Creating Test with Proper Token ---")
    print("📝 To test with a real refresh token:")
    print("1. Sign in to your app normally")
    print("2. Check the browser's localStorage or network tab")
    print("3. Look for 'supabase.auth.token' or refresh_token in responses")
    print("4. Real tokens look like: 'M_6Xl2d3nQKK...' (much longer)")
    
    # Generate a mock test
    mock_long_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNjk" + \
                     "0MTM0ODAwLCJpYXQiOjE2OTQxMzEyMDAsInN1YiI6IjEyMzQ1Njc4LTEyMzQtMTIzNC0xMjM0LTEyMzQ1Njc4OTAxMiIsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnt9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNjk0MTMxMjAwfV0sInNlc3Npb25faWQiOiIxMjM0NTY3OC0xMjM0LTEyMzQtMTIzNC0xMjM0NTY3ODkwMTIifQ"
    
    print(f"\n📝 Testing with mock token (length: {len(mock_long_token)})...")
    
    # Test the mock token format
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        headers = {
            "apikey": supabase_anon_key,
            "Content-Type": "application/json"
        }
        data = {
            "refresh_token": mock_long_token
        }
        
        response = requests.post(
            f"{supabase_url}/auth/v1/token?grant_type=refresh_token",
            headers=headers,
            json=data
        )
        
        print(f"📝 Mock token status: {response.status_code}")
        print(f"📝 Mock token response: {response.text}")
        
        if response.status_code != 400:
            print("✅ Mock token got a different response (not 'unsupported_grant_type')")
        else:
            error_data = response.json()
            if error_data.get("msg") != "unsupported_grant_type":
                print("✅ Mock token got a different error message")
            else:
                print("❌ Same error - issue might be with API format, not token")
                
    except Exception as e:
        print(f"❌ Mock token test exception: {e}")

async def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 COMPREHENSIVE REFRESH TOKEN DEBUG")
    print("=" * 60)
    
    # Test 1: Different API call formats
    result = test_refresh_token_formats()
    
    if result:
        print("\n✅ Found working method!")
        return
    
    # Test 2: FastAPI endpoint
    await test_fastapi_endpoint()
    
    # Test 3: Token format analysis
    create_test_refresh_token()
    
    print("\n" + "=" * 60)
    print("🎯 RECOMMENDATIONS:")
    print("1. Your token 'c4h7lbg5m7bm' is likely NOT a Supabase refresh token")
    print("2. Check your frontend auth flow to get the real refresh token")
    print("3. Real tokens are typically 100+ characters and start with 'eyJ' or similar")
    print("4. Check browser localStorage or network tab during login")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
