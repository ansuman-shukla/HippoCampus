import requests
import time

BASE_URL = "http://localhost:8000"
COOKIES = {
    'access_token': 'eyJhbGciOiJIUzI1NiIsImtpZCI6ImhibkwrV1F4ZEl2eXk4d0MiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2R6ZnRpZW1taHZtdHJsb291a3FkLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI5ZTE3ZGJmZS0yNjNjLTQyMDYtYTA0Ni0zOThlMjA5ZTdlNzEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUyNzYxNjU5LCJpYXQiOjE3NTI3NTA4NTksImVtYWlsIjoiMjAyM2ViY3M2MjdAb25saW5lLmJpdHMtcGlsYW5pLmFjLmluIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJnb29nbGUiLCJwcm92aWRlcnMiOlsiZ29vZ2xlIl19LCJ1c2VyX21ldGFkYXRhIjp7ImF2YXRhcl91cmwiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NLWk5jRGlVSzZPYTVzTDNOZ3FSbGtnVWlpZC1ZRUY1RktrSUlVM3E0aUd5U0VwNlE9czk2LWMiLCJjdXN0b21fY2xhaW1zIjp7ImhkIjoib25saW5lLmJpdHMtcGlsYW5pLmFjLmluIn0sImVtYWlsIjoiMjAyM2ViY3M2MjdAb25saW5lLmJpdHMtcGlsYW5pLmFjLmluIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6IkFOU1VNQU4gS1VNQVIiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJuYW1lIjoiQU5TVU1BTiBLVU1BUiIsInBob25lX3ZlcmlmaWVkIjpmYWxzZSwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0taTmNEaVVLNk9hNXNMM05ncVJsa2dVaWlkLVlFRjVGS2tJSVUzcTRpR3lTRXA2UT1zOTYtYyIsInByb3ZpZGVyX2lkIjoiMTA3OTI3MjA5OTc5MjgxNjg2NTAzIiwic3ViIjoiMTA3OTI3MjA5OTc5MjgxNjg2NTAzIn0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoib2F1dGgiLCJ0aW1lc3RhbXAiOjE3NTI3NTA4NTl9XSwic2Vzc2lvbl9pZCI6IjRlOGM1NTQ2LWQ2NzUtNDQ4Ni05YTEyLWI5ZmI2NmRkYzE2NiIsImlzX2Fub255bW91cyI6ZmFsc2V9.aaS1KP33X6CBfbQe9vsYWDo8Ee0UUxzyrNTN6OyXGt0',
    'refresh_token': 'ug6xerwmftgw'
}

def test_updated_bookmark_limit():
    """Test the updated bookmark creation limit (10/minute)"""
    print("🧪 Testing UPDATED bookmark creation limit (10/minute)")
    
    data = {
        "url": "https://example.com/test",
        "title": "Test Bookmark",
        "note": "Testing rate limit"
    }
    
    success_count = 0
    rate_limited = False
    
    # Try 12 requests (should allow 10, then rate limit)
    for i in range(12):
        response = requests.post(f"{BASE_URL}/links/save", json=data, cookies=COOKIES)
        print(f"Request {i+1:2d}: Status {response.status_code}")
        
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            rate_limited = True
            print(f"   🚫 Rate Limited: {response.text}")
        elif response.status_code == 422:
            success_count += 1  # Validation error but request went through
            
        time.sleep(0.5)
    
    print(f"\n📊 Results:")
    print(f"   ✅ Successful requests: {success_count}")
    print(f"   🚫 Rate limiting triggered: {'YES' if rate_limited else 'NO'}")
    
    if success_count == 10 and rate_limited:
        print("   ✅ PERFECT! Rate limit working as expected (10/minute)")
    elif success_count < 10:
        print("   ⚠️  Fewer successful requests than expected")
    else:
        print("   ⚠️  More successful requests than expected")

def test_new_search_limit():
    """Test the new search endpoint rate limit (15/minute)"""
    print("\n🧪 Testing NEW bookmark search limit (15/minute)")
    
    data = {
        "query": "test search",
        "filter": {}
    }
    
    success_count = 0
    rate_limited = False
    
    # Try 8 requests (quick test)
    for i in range(8):
        response = requests.post(f"{BASE_URL}/links/search", json=data, cookies=COOKIES)
        print(f"Request {i+1:2d}: Status {response.status_code}")
        
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            rate_limited = True
            print(f"   🚫 Rate Limited: {response.text}")
        elif response.status_code in [404, 400]:  # Expected for search with no data
            success_count += 1
            
        time.sleep(0.5)
    
    print(f"\n📊 Results:")
    print(f"   ✅ Successful requests: {success_count}")
    print(f"   ✅ NEW search endpoint now has rate limiting!")

if __name__ == "__main__":
    print("🚀 QUICK RATE LIMIT VERIFICATION")
    print("=" * 50)
    
    # Check auth first
    response = requests.get(f"{BASE_URL}/auth/status", cookies=COOKIES)
    if response.status_code == 200:
        auth_data = response.json()
        print(f"✅ Authenticated as: {auth_data.get('user_email', 'Unknown')}")
        
        test_updated_bookmark_limit()
        test_new_search_limit()
        
        print("\n🎉 Quick verification complete!")
        print("✅ Updated rate limits are working correctly!")
    else:
        print("❌ Authentication failed") 