import requests
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"

# Authentication cookies
COOKIES = {
    'access_token': 'eyJhbGciOiJIUzI1NiIsImtpZCI6ImhibkwrV1F4ZEl2eXk4d0MiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2R6ZnRpZW1taHZtdHJsb291a3FkLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI5ZTE3ZGJmZS0yNjNjLTQyMDYtYTA0Ni0zOThlMjA5ZTdlNzEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUyNzYxNjU5LCJpYXQiOjE3NTI3NTA4NTksImVtYWlsIjoiMjAyM2ViY3M2MjdAb25saW5lLmJpdHMtcGlsYW5pLmFjLmluIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJnb29nbGUiLCJwcm92aWRlcnMiOlsiZ29vZ2xlIl19LCJ1c2VyX21ldGFkYXRhIjp7ImF2YXRhcl91cmwiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NLWk5jRGlVSzZPYTVzTDNOZ3FSbGtnVWlpZC1ZRUY1RktrSUlVM3E0aUd5U0VwNlE9czk2LWMiLCJjdXN0b21fY2xhaW1zIjp7ImhkIjoib25saW5lLmJpdHMtcGlsYW5pLmFjLmluIn0sImVtYWlsIjoiMjAyM2ViY3M2MjdAb25saW5lLmJpdHMtcGlsYW5pLmFjLmluIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6IkFOU1VNQU4gS1VNQVIiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJuYW1lIjoiQU5TVU1BTiBLVU1BUiIsInBob25lX3ZlcmlmaWVkIjpmYWxzZSwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0taTmNEaVVLNk9hNXNMM05ncVJsa2dVaWlkLVlFRjVGS2tJSVUzcTRpR3lTRXA2UT1zOTYtYyIsInByb3ZpZGVyX2lkIjoiMTA3OTI3MjA5OTc5MjgxNjg2NTAzIiwic3ViIjoiMTA3OTI3MjA5OTc5MjgxNjg2NTAzIn0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoib2F1dGgiLCJ0aW1lc3RhbXAiOjE3NTI3NTA4NTl9XSwic2Vzc2lvbl9pZCI6IjRlOGM1NTQ2LWQ2NzUtNDQ4Ni05YTEyLWI5ZmI2NmRkYzE2NiIsImlzX2Fub255bW91cyI6ZmFsc2V9.aaS1KP33X6CBfbQe9vsYWDo8Ee0UUxzyrNTN6OyXGt0',
    'refresh_token': 'ug6xerwmftgw'
}

def test_bookmark_creation_rate_limit():
    """Test the updated 10/minute rate limit for bookmark creation"""
    print("🧪 TESTING BOOKMARK CREATION RATE LIMIT (10/minute)")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    
    # Valid bookmark data that should pass validation
    bookmark_data = {
        "url": "https://example.com/test-bookmark",
        "title": "Test Bookmark for Rate Limiting",
        "note": "This is a test bookmark created during rate limit testing"
    }
    
    successful_requests = 0
    rate_limited = False
    
    # Test 13 requests (should hit rate limit after 10)
    for i in range(13):
        try:
            response = requests.post(
                f"{BASE_URL}/links/save", 
                json=bookmark_data, 
                cookies=COOKIES
            )
            
            print(f"Request {i+1:2d}: Status {response.status_code}")
            
            if response.status_code == 200:
                successful_requests += 1
                print(f"      ✅ Success")
            elif response.status_code == 429:
                rate_limited = True
                print(f"      🚫 Rate Limited! {response.text}")
                try:
                    error_data = response.json()
                    print(f"      Error details: {error_data}")
                except:
                    pass
            else:
                print(f"      ⚠️  Status {response.status_code}: {response.text[:100]}")
            
            # Rate limit headers
            if 'X-RateLimit-Limit' in response.headers:
                limit = response.headers.get('X-RateLimit-Limit')
                remaining = response.headers.get('X-RateLimit-Remaining')
                reset = response.headers.get('X-RateLimit-Reset')
                print(f"      📊 Limit: {limit}, Remaining: {remaining}, Reset: {reset}")
            
            time.sleep(1)  # 1 second delay between requests
            
        except Exception as e:
            print(f"Request {i+1:2d}: ❌ Error - {str(e)}")
    
    print(f"\n📊 TEST RESULTS:")
    print(f"  ✅ Successful requests: {successful_requests}")
    print(f"  🚫 Rate limiting triggered: {'YES' if rate_limited else 'NO'}")
    
    if successful_requests == 10 and rate_limited:
        print(f"  🎉 PERFECT! Rate limit working exactly as expected (10/minute)")
    elif rate_limited:
        print(f"  ✅ Rate limiting is working, but got {successful_requests} successful requests instead of 10")
    else:
        print(f"  ❌ Rate limiting not triggered - this needs investigation")
    
    print(f"\nTest completed at: {datetime.now()}")

if __name__ == "__main__":
    # Check server health first
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code == 200:
            print("✅ Server is running")
            test_bookmark_creation_rate_limit()
        else:
            print("❌ Server health check failed")
    except Exception as e:
        print(f"❌ Cannot connect to server: {str(e)}") 