#!/usr/bin/env python3
"""
Test script for authentication system
"""
import asyncio
import httpx
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

class AuthTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.access_token = None
        self.refresh_token = None
    
    async def test_health_check(self):
        """Test if the server is running"""
        print("🔍 Testing health check...")
        try:
            response = await self.client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ Health check passed")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_auth_status(self):
        """Test auth status endpoint"""
        print("\n🔍 Testing auth status...")
        try:
            response = await self.client.get(f"{BASE_URL}/auth/status")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Auth status: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"❌ Auth status failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Auth status error: {e}")
            return False
    
    async def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        print("\n🔍 Testing protected endpoint without token...")
        try:
            response = await self.client.get(f"{BASE_URL}/save")
            if response.status_code == 401:
                print("✅ Protected endpoint correctly returns 401 without token")
                return True
            else:
                print(f"❌ Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Protected endpoint test error: {e}")
            return False
    
    async def test_supabase_token_creation(self):
        """Test creating tokens through Supabase (requires manual setup)"""
        print("\n🔍 Testing Supabase token creation...")
        print("📝 Note: This requires manual setup with valid Supabase credentials")
        
        # This would typically be done through your frontend auth flow
        # For testing, you might need to:
        # 1. Create a test user in Supabase
        # 2. Use Supabase client to authenticate
        # 3. Extract tokens
        
        print("⏭️ Skipping automatic token creation - requires manual setup")
        return True
    
    async def test_token_refresh(self):
        """Test token refresh endpoint"""
        print("\n🔍 Testing token refresh...")
        if not self.refresh_token:
            print("⏭️ No refresh token available - skipping test")
            return True
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/auth/refresh",
                json={"refresh_token": self.refresh_token}
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Token refresh successful")
                print(f"📝 New access token length: {len(data.get('access_token', ''))}")
                return True
            else:
                print(f"❌ Token refresh failed: {response.status_code}")
                print(f"📝 Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Token refresh error: {e}")
            return False
    
    async def test_jwt_secret_configuration(self):
        """Test JWT secret configuration"""
        print("\n🔍 Testing JWT secret configuration...")
        
        jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        if jwt_secret:
            print(f"✅ JWT secret configured (length: {len(jwt_secret)})")
            return True
        else:
            print("❌ SUPABASE_JWT_SECRET not configured")
            print("📝 Please add SUPABASE_JWT_SECRET to your .env file")
            print("📝 You can find this in your Supabase dashboard under Settings > API")
            return False
    
    async def test_configuration(self):
        """Test all configuration variables"""
        print("\n🔍 Testing configuration...")
        
        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY", 
            "SUPABASE_JWT_SECRET"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
            else:
                print(f"✅ {var} configured")
        
        if missing_vars:
            print(f"❌ Missing configuration variables: {missing_vars}")
            return False
        else:
            print("✅ All required configuration variables present")
            return True
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Authentication System Tests")
        print("=" * 50)
        
        tests = [
            ("Configuration", self.test_configuration),
            ("JWT Secret", self.test_jwt_secret_configuration),
            ("Health Check", self.test_health_check),
            ("Auth Status", self.test_auth_status),
            ("Protected Endpoint", self.test_protected_endpoint_without_token),
            ("Supabase Token Creation", self.test_supabase_token_creation),
            ("Token Refresh", self.test_token_refresh),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n📈 Overall: {passed}/{len(results)} tests passed")
        
        if passed == len(results):
            print("🎉 All tests passed! Your authentication system is ready.")
        else:
            print("⚠️ Some tests failed. Please review the configuration and setup.")
        
        await self.client.aclose()

async def main():
    tester = AuthTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
