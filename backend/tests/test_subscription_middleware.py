import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request, HTTPException
from app.middleware.subscription_middleware import (
    require_memory_limit,
    require_summary_limit,
    require_pro_subscription,
    check_memory_middleware,
    check_summary_middleware,
    create_upgrade_response
)


class TestSubscriptionMiddleware:
    """Test cases for subscription middleware decorators and functions"""
    
    def setup_method(self):
        """Setup method to create mock request objects"""
        self.mock_request = Mock(spec=Request)
        self.mock_request.state = Mock()
        self.mock_request.state.user_id = "test_user_123"
    
    def test_create_upgrade_response_basic(self):
        """Test upgrade response creation with basic message"""
        message = "Test upgrade message"
        response = create_upgrade_response(message)
        
        assert response["error"] == "Subscription limit exceeded"
        assert response["message"] == message
        assert response["action_required"] == "upgrade"
        assert response["upgrade_url"] == "/subscription/upgrade"
        assert "subscription_info" in response
        assert response["subscription_info"]["current_tier"] == "free"
        assert len(response["subscription_info"]["upgrade_benefits"]) == 3
    
    def test_create_upgrade_response_with_pages(self):
        """Test upgrade response creation with page count"""
        message = "Test message"
        pages = 5
        response = create_upgrade_response(message, pages_requested=pages)
        
        assert response["pages_requested"] == pages
        assert response["message"] == message


class TestRequireMemoryLimit:
    """Test cases for require_memory_limit decorator"""
    
    def setup_method(self):
        """Setup method to create mock request and decorated function"""
        self.mock_request = Mock(spec=Request)
        self.mock_request.state = Mock()
        self.mock_request.state.user_id = "test_user_123"
        
        # Create a simple async function to decorate
        @require_memory_limit
        async def test_endpoint(request: Request):
            return {"success": True}
        
        self.decorated_function = test_endpoint
    
    @pytest.mark.asyncio
    @patch('app.middleware.subscription_middleware.check_memory_limit')
    async def test_memory_limit_blocks_free_user_at_limit(self, mock_check_memory):
        """Unit test: Middleware blocks free user at memory limit"""
        # Setup: User at memory limit (check_memory_limit returns False)
        mock_check_memory.return_value = False
        
        # Execute & Assert: Should raise 402 error
        with pytest.raises(HTTPException) as exc_info:
            await self.decorated_function(self.mock_request)
        
        assert exc_info.value.status_code == 402
        assert exc_info.value.detail["error"] == "Subscription limit exceeded"
        assert "reached your memory save limit" in exc_info.value.detail["message"]
        assert exc_info.value.detail["action_required"] == "upgrade"
        mock_check_memory.assert_called_once_with("test_user_123")
    
    @pytest.mark.asyncio
    @patch('app.middleware.subscription_middleware.check_memory_limit')
    async def test_memory_limit_allows_free_user_under_limit(self, mock_check_memory):
        """Unit test: Middleware allows free user under memory limit"""
        # Setup: User under memory limit (check_memory_limit returns True)
        mock_check_memory.return_value = True
        
        # Execute: Should succeed
        result = await self.decorated_function(self.mock_request)
        
        # Assert: Function executes successfully
        assert result == {"success": True}
        mock_check_memory.assert_called_once_with("test_user_123")
    
    @pytest.mark.asyncio
    async def test_memory_limit_requires_authentication(self):
        """Unit test: Middleware requires authentication (user_id in request state)"""
        # Setup: No user_id in request state
        self.mock_request.state.user_id = None
        
        # Execute & Assert: Should raise 401 error
        with pytest.raises(HTTPException) as exc_info:
            await self.decorated_function(self.mock_request)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authentication required"
    
    @pytest.mark.asyncio
    async def test_memory_limit_handles_missing_request(self):
        """Unit test: Middleware handles missing Request object gracefully"""
        # Create decorated function with wrong argument type
        @require_memory_limit
        async def bad_endpoint(not_a_request):
            return {"success": True}
        
        # Execute & Assert: Should raise 500 error
        with pytest.raises(HTTPException) as exc_info:
            await bad_endpoint("not a request")
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Internal server error"


class TestRequireSummaryLimit:
    """Test cases for require_summary_limit decorator"""
    
    def setup_method(self):
        """Setup method to create mock request and decorated functions"""
        self.mock_request = Mock(spec=Request)
        self.mock_request.state = Mock()
        self.mock_request.state.user_id = "test_user_123"
    
    @pytest.mark.asyncio
    @patch('app.middleware.subscription_middleware.check_summary_limit')
    async def test_summary_limit_blocks_free_user_at_limit(self, mock_check_summary):
        """Unit test: Middleware blocks free user at summary limit"""
        # Setup: User would exceed summary limit (check_summary_limit returns False)
        mock_check_summary.return_value = False
        
        # Create decorated function with specific page count
        @require_summary_limit(pages_requested=3)
        async def test_endpoint(request: Request):
            return {"success": True}
        
        # Execute & Assert: Should raise 402 error
        with pytest.raises(HTTPException) as exc_info:
            await test_endpoint(self.mock_request)
        
        assert exc_info.value.status_code == 402
        assert exc_info.value.detail["error"] == "Subscription limit exceeded"
        assert "exceed your monthly limit" in exc_info.value.detail["message"]
        assert exc_info.value.detail["pages_requested"] == 3
        mock_check_summary.assert_called_once_with("test_user_123", 3)
    
    @pytest.mark.asyncio
    @patch('app.middleware.subscription_middleware.check_summary_limit')
    async def test_summary_limit_allows_free_user_under_limit(self, mock_check_summary):
        """Unit test: Middleware allows free user under summary limit"""
        # Setup: User under summary limit (check_summary_limit returns True)
        mock_check_summary.return_value = True
        
        # Create decorated function
        @require_summary_limit(pages_requested=2)
        async def test_endpoint(request: Request):
            return {"success": True}
        
        # Execute: Should succeed
        result = await test_endpoint(self.mock_request)
        
        # Assert: Function executes successfully
        assert result == {"success": True}
        mock_check_summary.assert_called_once_with("test_user_123", 2)
    
    @pytest.mark.asyncio
    @patch('app.middleware.subscription_middleware.estimate_content_pages')
    @patch('app.middleware.subscription_middleware.check_summary_limit')
    async def test_summary_limit_estimates_pages_from_content(self, mock_check_summary, mock_estimate):
        """Unit test: Middleware estimates pages when content is available"""
        # Setup: Content in request state, estimation returns 4 pages
        self.mock_request.state.content = "This is some test content for page estimation"
        mock_estimate.return_value = 4
        mock_check_summary.return_value = True
        
        # Create decorated function without specific page count
        @require_summary_limit()
        async def test_endpoint(request: Request):
            return {"success": True}
        
        # Execute
        result = await test_endpoint(self.mock_request)
        
        # Assert: Uses estimated page count
        assert result == {"success": True}
        mock_estimate.assert_called_once_with("This is some test content for page estimation")
        mock_check_summary.assert_called_once_with("test_user_123", 4)
    
    @pytest.mark.asyncio
    @patch('app.middleware.subscription_middleware.check_summary_limit')
    async def test_summary_limit_defaults_to_one_page(self, mock_check_summary):
        """Unit test: Middleware defaults to 1 page when no content or page count"""
        # Setup: No content in request state, no pages_requested
        # Explicitly set content to None (not Mock)
        self.mock_request.state.content = None
        mock_check_summary.return_value = True
        
        # Create decorated function without page count
        @require_summary_limit()
        async def test_endpoint(request: Request):
            return {"success": True}
        
        # Execute
        result = await test_endpoint(self.mock_request)
        
        # Assert: Uses default 1 page
        assert result == {"success": True}
        mock_check_summary.assert_called_once_with("test_user_123", 1)


class TestRequireProSubscription:
    """Test cases for require_pro_subscription decorator"""
    
    def setup_method(self):
        """Setup method to create mock request and decorated function"""
        self.mock_request = Mock(spec=Request)
        self.mock_request.state = Mock()
        self.mock_request.state.user_id = "test_user_123"
        
        # Create a simple async function to decorate
        @require_pro_subscription
        async def test_endpoint(request: Request):
            return {"success": True}
        
        self.decorated_function = test_endpoint
    
    @pytest.mark.asyncio
    @patch('app.services.subscription_service.get_user_subscription')
    async def test_pro_subscription_allows_pro_user(self, mock_get_subscription):
        """Unit test: Middleware allows pro user unlimited access"""
        # Setup: User has pro subscription
        mock_get_subscription.return_value = {
            "user_id": "test_user_123",
            "subscription_tier": "pro",
            "subscription_status": "active"
        }
        
        # Execute: Should succeed
        result = await self.decorated_function(self.mock_request)
        
        # Assert: Function executes successfully
        assert result == {"success": True}
        mock_get_subscription.assert_called_once_with("test_user_123")
    
    @pytest.mark.asyncio
    @patch('app.services.subscription_service.get_user_subscription')
    async def test_pro_subscription_blocks_free_user(self, mock_get_subscription):
        """Unit test: Middleware blocks free user from pro features"""
        # Setup: User has free subscription
        mock_get_subscription.return_value = {
            "user_id": "test_user_123",
            "subscription_tier": "free",
            "subscription_status": "active"
        }
        
        # Execute & Assert: Should raise 402 error
        with pytest.raises(HTTPException) as exc_info:
            await self.decorated_function(self.mock_request)
        
        assert exc_info.value.status_code == 402
        assert exc_info.value.detail["error"] == "Subscription limit exceeded"
        assert "only available to Pro subscribers" in exc_info.value.detail["message"]
        mock_get_subscription.assert_called_once_with("test_user_123")
    
    @pytest.mark.asyncio
    @patch('app.services.subscription_service.get_user_subscription')
    async def test_pro_subscription_handles_missing_user(self, mock_get_subscription):
        """Unit test: Middleware handles missing user subscription data"""
        # Setup: User not found in database
        mock_get_subscription.return_value = None
        
        # Execute & Assert: Should raise 500 error
        with pytest.raises(HTTPException) as exc_info:
            await self.decorated_function(self.mock_request)
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Could not verify subscription status"


class TestMiddlewareFunctions:
    """Test cases for middleware functions (non-decorator approach)"""
    
    def setup_method(self):
        """Setup method to create mock request"""
        self.mock_request = Mock(spec=Request)
        self.mock_request.state = Mock()
        self.mock_request.state.user_id = "test_user_123"
    
    @pytest.mark.asyncio
    @patch('app.middleware.subscription_middleware.check_memory_limit')
    async def test_check_memory_middleware_success(self, mock_check_memory):
        """Unit test: check_memory_middleware passes when under limit"""
        # Setup: User under memory limit
        mock_check_memory.return_value = True
        
        # Execute: Should not raise exception
        await check_memory_middleware(self.mock_request)
        
        # Assert: check_memory_limit was called
        mock_check_memory.assert_called_once_with("test_user_123")
    
    @pytest.mark.asyncio
    @patch('app.middleware.subscription_middleware.check_memory_limit')
    async def test_check_memory_middleware_blocks_at_limit(self, mock_check_memory):
        """Unit test: check_memory_middleware blocks when at limit"""
        # Setup: User at memory limit
        mock_check_memory.return_value = False
        
        # Execute & Assert: Should raise 402 error
        with pytest.raises(HTTPException) as exc_info:
            await check_memory_middleware(self.mock_request)
        
        assert exc_info.value.status_code == 402
        assert exc_info.value.detail["error"] == "Subscription limit exceeded"
    
    @pytest.mark.asyncio
    @patch('app.middleware.subscription_middleware.check_summary_limit')
    async def test_check_summary_middleware_success(self, mock_check_summary):
        """Unit test: check_summary_middleware passes when under limit"""
        # Setup: User under summary limit
        mock_check_summary.return_value = True
        
        # Execute: Should not raise exception
        await check_summary_middleware(self.mock_request, pages_requested=3)
        
        # Assert: check_summary_limit was called with correct parameters
        mock_check_summary.assert_called_once_with("test_user_123", 3)
    
    @pytest.mark.asyncio
    @patch('app.middleware.subscription_middleware.check_summary_limit')
    async def test_check_summary_middleware_blocks_at_limit(self, mock_check_summary):
        """Unit test: check_summary_middleware blocks when at limit"""
        # Setup: User would exceed summary limit
        mock_check_summary.return_value = False
        
        # Execute & Assert: Should raise 402 error
        with pytest.raises(HTTPException) as exc_info:
            await check_summary_middleware(self.mock_request, pages_requested=6)
        
        assert exc_info.value.status_code == 402
        assert exc_info.value.detail["pages_requested"] == 6


class TestMiddleware402ErrorFormat:
    """Test cases for proper 402 error format"""
    
    def test_proper_402_error_format_memory(self):
        """Unit test: Middleware returns proper 402 error format for memory"""
        message = "Memory limit exceeded"
        response = create_upgrade_response(message)
        
        # Assert proper error structure
        assert isinstance(response, dict)
        assert response["error"] == "Subscription limit exceeded"
        assert response["message"] == message
        assert response["action_required"] == "upgrade"
        assert response["upgrade_url"] == "/subscription/upgrade"
        
        # Assert subscription info structure
        assert "subscription_info" in response
        sub_info = response["subscription_info"]
        assert sub_info["current_tier"] == "free"
        assert isinstance(sub_info["upgrade_benefits"], list)
        assert len(sub_info["upgrade_benefits"]) > 0
        
        # Check specific benefits
        benefits = sub_info["upgrade_benefits"]
        assert "Unlimited memory saves" in benefits
        assert "100 summary pages per month" in benefits
        assert "AI-powered dashboard queries" in benefits
    
    def test_proper_402_error_format_summary(self):
        """Unit test: Middleware returns proper 402 error format for summary"""
        message = "Summary limit exceeded"
        pages = 7
        response = create_upgrade_response(message, pages_requested=pages)
        
        # Assert all required fields present
        required_fields = ["error", "message", "action_required", "upgrade_url", "subscription_info"]
        for field in required_fields:
            assert field in response
        
        # Assert pages_requested is included
        assert response["pages_requested"] == pages
        
        # Assert error structure is consistent
        assert response["error"] == "Subscription limit exceeded"
        assert response["action_required"] == "upgrade"


class TestIntegrationWithAuthFlow:
    """Integration tests for middleware working with auth flow"""
    
    def setup_method(self):
        """Setup method to create realistic request mock"""
        self.mock_request = Mock(spec=Request)
        self.mock_request.state = Mock()
    
    @pytest.mark.asyncio
    async def test_middleware_integrates_with_auth_flow(self):
        """Integration test: Middleware integrates with existing auth flow"""
        # Setup: Simulate auth middleware setting user_id in request state
        self.mock_request.state.user_id = "authenticated_user_123"
        
        with patch('app.middleware.subscription_middleware.check_memory_limit') as mock_check:
            mock_check.return_value = True
            
            # Create decorated endpoint
            @require_memory_limit
            async def protected_endpoint(request: Request):
                # This simulates how real endpoints access user data
                user_id = request.state.user_id
                return {"user_id": user_id, "success": True}
            
            # Execute: Should work seamlessly with auth flow
            result = await protected_endpoint(self.mock_request)
            
            # Assert: User data from auth flow is accessible
            assert result["user_id"] == "authenticated_user_123"
            assert result["success"] is True
            mock_check.assert_called_once_with("authenticated_user_123")
    
    @pytest.mark.asyncio
    async def test_middleware_requires_auth_middleware_first(self):
        """Integration test: Middleware requires auth middleware to run first"""
        # Setup: Simulate missing auth middleware (no user_id set)
        self.mock_request.state.user_id = None
        
        @require_memory_limit
        async def protected_endpoint(request: Request):
            return {"success": True}
        
        # Execute & Assert: Should fail because auth middleware didn't run
        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(self.mock_request)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authentication required"
    
    @pytest.mark.asyncio
    @patch('app.middleware.subscription_middleware.check_memory_limit')
    async def test_middleware_preserves_request_state(self, mock_check):
        """Integration test: Middleware preserves other request state data"""
        # Setup: Auth middleware would set additional state
        self.mock_request.state.user_id = "test_user"
        self.mock_request.state.user_payload = {"sub": "test_user", "email": "test@example.com"}
        self.mock_request.state.some_other_data = "preserved"
        
        mock_check.return_value = True
        
        @require_memory_limit
        async def endpoint_with_state_access(request: Request):
            # Access all request state like a real endpoint would
            return {
                "user_id": request.state.user_id,
                "email": request.state.user_payload.get("email"),
                "other_data": request.state.some_other_data
            }
        
        # Execute
        result = await endpoint_with_state_access(self.mock_request)
        
        # Assert: All request state is preserved and accessible
        assert result["user_id"] == "test_user"
        assert result["email"] == "test@example.com"
        assert result["other_data"] == "preserved" 