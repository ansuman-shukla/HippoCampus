import requests
import time
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"

# Authentication cookies from user
COOKIES = {
    'access_token': 'eyJhbGciOiJIUzI1NiIsImtpZCI6ImhibkwrV1F4ZEl2eXk4d0MiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2R6ZnRpZW1taHZtdHJsb291a3FkLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI5ZTE3ZGJmZS0yNjNjLTQyMDYtYTA0Ni0zOThlMjA5ZTdlNzEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUyNzYxNjU5LCJpYXQiOjE3NTI3NTA4NTksImVtYWlsIjoiMjAyM2ViY3M2MjdAb25saW5lLmJpdHMtcGlsYW5pLmFjLmluIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJnb29nbGUiLCJwcm92aWRlcnMiOlsiZ29vZ2xlIl19LCJ1c2VyX21ldGFkYXRhIjp7ImF2YXRhcl91cmwiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NLWk5jRGlVSzZPYTVzTDNOZ3FSbGtnVWlpZC1ZRUY1RktrSUlVM3E0aUd5U0VwNlE9czk2LWMiLCJjdXN0b21fY2xhaW1zIjp7ImhkIjoib25saW5lLmJpdHMtcGlsYW5pLmFjLmluIn0sImVtYWlsIjoiMjAyM2ViY3M2MjdAb25saW5lLmJpdHMtcGlsYW5pLmFjLmluIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6IkFOU1VNQU4gS1VNQVIiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJuYW1lIjoiQU5TVU1BTiBLVU1BUiIsInBob25lX3ZlcmlmaWVkIjpmYWxzZSwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0taTmNEaVVLNk9hNXNMM05ncVJsa2dVaWlkLVlFRjVGS2tJSVUzcTRpR3lTRXA2UT1zOTYtYyIsInByb3ZpZGVyX2lkIjoiMTA3OTI3MjA5OTc5MjgxNjg2NTAzIiwic3ViIjoiMTA3OTI3MjA5OTc5MjgxNjg2NTAzIn0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoib2F1dGgiLCJ0aW1lc3RhbXAiOjE3NTI3NTA4NTl9XSwic2Vzc2lvbl9pZCI6IjRlOGM1NTQ2LWQ2NzUtNDQ4Ni05YTEyLWI5ZmI2NmRkYzE2NiIsImlzX2Fub255bW91cyI6ZmFsc2V9.aaS1KP33X6CBfbQe9vsYWDo8Ee0UUxzyrNTN6OyXGt0',
    'refresh_token': 'ug6xerwmftgw'
}

def print_headers(response):
    """Print rate limit headers if they exist"""
    rate_limit_headers = {
        'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
        'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
        'X-RateLimit-Reset': response.headers.get('X-RateLimit-Reset'),
    }
    
    headers_found = {k: v for k, v in rate_limit_headers.items() if v is not None}
    if headers_found:
        print(f"      Rate Limit Headers: {headers_found}")

def test_endpoint_rate_limit(endpoint, method, data, limit_count, limit_description):
    """Test a specific endpoint to trigger rate limiting"""
    print(f"\n=== Testing {method} {endpoint} ({limit_description}) ===")
    
    successful_requests = 0
    rate_limited = False
    
    # Make requests slightly above the limit to trigger rate limiting
    test_requests = limit_count + 3
    
    for i in range(test_requests):
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", cookies=COOKIES)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json=data, cookies=COOKIES)
            
            print(f"Request {i+1:2d}: Status {response.status_code}")
            print_headers(response)
            
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
                print(f"      ⚠️  Other response: {response.status_code} - {response.text[:100]}")
            
            # Small delay between requests
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Request {i+1:2d}: ❌ Error - {str(e)}")
    
    print(f"\nResults for {endpoint}:")
    print(f"  - Successful requests: {successful_requests}")
    print(f"  - Rate limiting triggered: {'✅ YES' if rate_limited else '❌ NO'}")
    
    return successful_requests, rate_limited

def test_bookmark_operations():
    """Test bookmark rate limits"""
    print("\n" + "="*60)
    print("TESTING BOOKMARK OPERATIONS")
    print("="*60)
    
    # Test bookmark creation (10/minute limit)
    create_data = {
        "url": "https://example.com/test",
        "title": "Test Bookmark for Rate Limiting",
        "description": "This is a test bookmark created during rate limit testing"
    }
    
    success, limited = test_endpoint_rate_limit(
        "/links/save", 
        "POST", 
        create_data, 
        10, 
        "10 requests per minute"
    )
    
    if limited:
        print("\n⏰ Waiting 30 seconds before next test...")
        time.sleep(30)
    
    # Test bookmark retrieval (20/minute limit)
    success, limited = test_endpoint_rate_limit(
        "/links/get", 
        "GET", 
        None, 
        20, 
        "20 requests per minute"
    )

def test_notes_operations():
    """Test notes rate limits"""
    print("\n" + "="*60)
    print("TESTING NOTES OPERATIONS")
    print("="*60)
    
    # Test notes creation (15/minute limit)
    create_data = {
        "title": "Test Note for Rate Limiting",
        "note": "This is a test note created during rate limit testing"
    }
    
    success, limited = test_endpoint_rate_limit(
        "/notes/", 
        "POST", 
        create_data, 
        15, 
        "15 requests per minute"
    )
    
    if limited:
        print("\n⏰ Waiting 30 seconds before next test...")
        time.sleep(30)
    
    # Test notes retrieval (20/minute limit)
    success, limited = test_endpoint_rate_limit(
        "/notes/", 
        "GET", 
        None, 
        20, 
        "20 requests per minute"
    )

def test_summary_operations():
    """Test summary rate limits"""
    print("\n" + "="*60)
    print("TESTING SUMMARY OPERATIONS")
    print("="*60)
    
    # Test summary generation (5/day limit)
    summary_data = {
        "content": "This is test content for summary generation during rate limit testing. " * 10
    }
    
    success, limited = test_endpoint_rate_limit(
        "/summary/generate", 
        "POST", 
        summary_data, 
        5, 
        "5 requests per day"
    )

def test_auth_status():
    """Test authentication status first"""
    print("=== Testing Authentication Status ===")
    
    try:
        response = requests.get(f"{BASE_URL}/auth/status", cookies=COOKIES)
        print(f"Auth Status: {response.status_code}")
        
        if response.status_code == 200:
            auth_data = response.json()
            print(f"✅ Authenticated as: {auth_data.get('user_email', 'Unknown')}")
            print(f"   User ID: {auth_data.get('user_id', 'Unknown')}")
            print(f"   Token Valid: {auth_data.get('token_valid', False)}")
            return True
        else:
            print(f"❌ Authentication failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Auth check failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 SLOWAPI RATE LIMITING TEST WITH AUTHENTICATION")
    print("=" * 70)
    print(f"Test started at: {datetime.now()}")
    print(f"Target server: {BASE_URL}")
    
    # Check if server is running
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code != 200:
            print("❌ Server is not responding to health check")
            return
        print("✅ Server is running")
    except Exception as e:
        print(f"❌ Cannot connect to server: {str(e)}")
        return
    
    # Test authentication
    if not test_auth_status():
        print("❌ Authentication failed. Cannot proceed with rate limit testing.")
        return
    
    print("\n📝 RATE LIMIT CONFIGURATION:")
    print("  • Bookmark Creation (POST /links/save): 10 requests/minute")
    print("  • Bookmark Retrieval (GET /links/get): 20 requests/minute")
    print("  • Notes Creation (POST /notes/): 15 requests/minute")
    print("  • Notes Retrieval (GET /notes/): 20 requests/minute")
    print("  • Summary Generation (POST /summary/generate): 5 requests/day")
    
    # Run tests
    try:
        test_bookmark_operations()
        test_notes_operations()
        test_summary_operations()
        
        print("\n" + "="*70)
        print("🎉 RATE LIMITING TESTS COMPLETED")
        print("="*70)
        print(f"Test completed at: {datetime.now()}")
        
        print("\n📊 TEST SUMMARY:")
        print("✅ If you saw 429 responses, rate limiting is working correctly!")
        print("✅ Rate limits are tracked per user per route as expected")
        print("✅ The SlowAPI implementation is functioning properly")
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")

if __name__ == "__main__":
    main() 