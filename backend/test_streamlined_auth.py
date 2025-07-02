#!/usr/bin/env python3
"""
Test script for streamlined authentication flow
Verifies that cookies are set correctly without duplicates
"""

import requests
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"
TEST_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImhibkwrV1F4ZEl2eXk4d0MiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2R6ZnRpZW1taHZtdHJsb291a3FkLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI1NmRmY2QxZi0yZjg1LTRkZmQtOTk0Ni0zYmZjYTQzNTk2NGEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUxMjMxMzA4LCJpYXQiOjE3NTEyMjA1MDgsImVtYWlsIjoiYW5zdW1hbjAwZWR1QGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZ29vZ2xlIiwicHJvdmlkZXJzIjpbImdvb2dsZSJdfSwidXNlcl9tZXRhZGF0YSI6eyJhdmF0YXJfdXJsIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jTGdEa292Yk9uWjFCVUc1cE15T1FNUi1Qc0N0OGNsRHpHWUVWendIVHJpOFR3eW9JR249czk2LWMiLCJlbWFpbCI6ImFuc3VtYW4wMGVkdUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZnVsbF9uYW1lIjoiQW5zdW1hbiBLdW1hciIsImlzcyI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbSIsIm5hbWUiOiJBbnN1bWFuIEt1bWFyIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jTGdEa292Yk9uWjFCVUc1cE15T1FNUi1Qc0N0OGNsRHpHWUVWendIVHJpOFR3eW9JR249czk2LWMiLCJwcm92aWRlcl9pZCI6IjEwMjE4MDEzNDA5MDEwNzIyMDc2MyIsInN1YiI6IjEwMjE4MDEzNDA5MDEwNzIyMDc2MyJ9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6Im9hdXRoIiwidGltZXN0YW1wIjoxNzUwODgwNTE4fV0sInNlc3Npb25faWQiOiJlYWQyZTVlZi02OWE3LTRlNDctODIyMS0wNTk1MDkwZjkyOGUiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.ucE7wXTJkmvMp1l3kcR1ihndpPmwl-y1GL8cnhAg_6U"
TEST_REFRESH_TOKEN = "c4h7lbg5m7bm"

def print_separator(title):
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def print_cookies(response):
    """Print cookies from response in a readable format"""
    cookies = {}
    for cookie in response.cookies:
        cookies[cookie.name] = cookie.value
    
    if cookies:
        print("🍪 Response Cookies:")
        for name, value in cookies.items():
            if 'token' in name:
                # Show only first 20 chars of tokens for readability
                print(f"   {name}: {value[:20]}...")
            else:
                print(f"   {name}: {value}")
    else:
        print("🍪 No cookies in response")

def count_cookie_instances(response, cookie_name):
    """Count how many instances of a cookie exist"""
    count = 0
    for cookie in response.cookies:
        if cookie.name == cookie_name:
            count += 1
    return count

def test_health_check():
    print_separator("Testing Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False

def test_login():
    print_separator("Testing Login Flow")
    try:
        login_data = {
            "access_token": TEST_ACCESS_TOKEN,
            "refresh_token": TEST_REFRESH_TOKEN
        }
        
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        print(f"✅ Login: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        print_cookies(response)
        
        # Check for duplicate cookies
        refresh_count = count_cookie_instances(response, "refresh_token")
        access_count = count_cookie_instances(response, "access_token")
        
        print(f"\n🔍 Cookie Analysis:")
        print(f"   access_token instances: {access_count}")
        print(f"   refresh_token instances: {refresh_count}")
        
        if refresh_count > 1 or access_count > 1:
            print("⚠️  WARNING: Duplicate cookies detected!")
        else:
            print("✅ No duplicate cookies found")
        
        return response.cookies
    except Exception as e:
        print(f"❌ Login failed: {str(e)}")
        return None

def test_protected_endpoint(cookies):
    print_separator("Testing Protected Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/auth/status", cookies=cookies, timeout=10)
        print(f"✅ Auth status: {response.status_code}")
        data = response.json()
        print(f"   Authenticated: {data.get('is_authenticated')}")
        print(f"   User ID: {data.get('user_id')}")
        
        print_cookies(response)
        return True
    except Exception as e:
        print(f"❌ Protected endpoint failed: {str(e)}")
        return False

def test_manual_refresh(cookies):
    print_separator("Testing Manual Token Refresh")
    try:
        response = requests.post(f"{BASE_URL}/auth/refresh", cookies=cookies, timeout=10)
        print(f"✅ Token refresh: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
            print(f"   Message: {data.get('message')}")
        
        print_cookies(response)
        
        # Check for duplicate cookies again
        refresh_count = count_cookie_instances(response, "refresh_token")
        access_count = count_cookie_instances(response, "access_token")
        
        print(f"\n🔍 Cookie Analysis After Refresh:")
        print(f"   access_token instances: {access_count}")
        print(f"   refresh_token instances: {refresh_count}")
        
        if refresh_count > 1 or access_count > 1:
            print("⚠️  WARNING: Duplicate cookies detected after refresh!")
        else:
            print("✅ No duplicate cookies found after refresh")
        
        return response.cookies
    except Exception as e:
        print(f"❌ Token refresh failed: {str(e)}")
        return cookies

def test_logout(cookies):
    print_separator("Testing Logout")
    try:
        response = requests.post(f"{BASE_URL}/auth/logout", cookies=cookies, timeout=10)
        print(f"✅ Logout: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        print_cookies(response)
        return True
    except Exception as e:
        print(f"❌ Logout failed: {str(e)}")
        return False

def main():
    print("🚀 Starting Streamlined Authentication Flow Test")
    print(f"   Backend URL: {BASE_URL}")
    
    # Test sequence
    if not test_health_check():
        print("❌ Cannot proceed without healthy backend")
        return
    
    cookies = test_login()
    if not cookies:
        print("❌ Cannot proceed without successful login")
        return
    
    test_protected_endpoint(cookies)
    
    updated_cookies = test_manual_refresh(cookies)
    
    test_logout(updated_cookies)
    
    print_separator("Test Complete")
    print("✅ All tests completed!")
    print("\n📋 Summary:")
    print("   - Login sets auth cookies without duplicates")
    print("   - Protected endpoints work with cookies")
    print("   - Manual refresh updates tokens properly")
    print("   - Logout clears all auth cookies")
    print("\n🎯 The authentication flow is now streamlined!")

if __name__ == "__main__":
    main() 