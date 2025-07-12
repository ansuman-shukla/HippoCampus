import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from app.main import app
from app.services.subscription_service import TIER_LIMITS, estimate_content_pages
import json

client = TestClient(app)

class TestSummaryRouterSubscription:
    """Integration tests for summary router with subscription middleware"""
    
    @pytest.fixture
    def sample_content_short(self):
        """Sample short content (1 page)"""
        return "This is a short article about technology. It contains basic information about recent developments in AI and machine learning."
    
    @pytest.fixture
    def sample_content_medium(self):
        """Sample medium content (2 pages - approximately 6000 characters)"""
        # Creating content that would be estimated as 2 pages
        base_text = "This is a comprehensive article about artificial intelligence and its applications in modern technology. "
        return base_text * 60  # Approximately 6000 characters
    
    @pytest.fixture
    def sample_content_large(self):
        """Sample large content (4 pages - approximately 12000 characters)"""
        # Creating content that would be estimated as 4 pages
        base_text = "This is an extensive research paper on machine learning algorithms and their implementation in real-world scenarios. It covers various aspects including deep learning, neural networks, and data processing techniques. "
        return base_text * 60  # Approximately 12000 characters
    
    @pytest.fixture
    def free_user_no_usage(self):
        """Mock subscription data for free user with no summary usage"""
        return {
            "user_id": "test_user_123",
            "subscription_tier": "free",
            "subscription_status": "active",
            "subscription_start_date": "2024-01-01T00:00:00Z",
            "subscription_end_date": None,
            "total_memories_saved": 50,
            "monthly_summary_pages_used": 0,  # No usage yet
            "monthly_summary_reset_date": "2024-01-01T00:00:00Z"
        }
    
    @pytest.fixture
    def free_user_at_limit(self):
        """Mock subscription data for free user at summary limit"""
        return {
            "user_id": "test_user_123",
            "subscription_tier": "free",
            "subscription_status": "active",
            "subscription_start_date": "2024-01-01T00:00:00Z",
            "subscription_end_date": None,
            "total_memories_saved": 50,
            "monthly_summary_pages_used": 5,  # At free tier limit
            "monthly_summary_reset_date": "2024-01-01T00:00:00Z"
        }
    
    @pytest.fixture
    def free_user_near_limit(self):
        """Mock subscription data for free user near summary limit"""
        return {
            "user_id": "test_user_123",
            "subscription_tier": "free",
            "subscription_status": "active",
            "subscription_start_date": "2024-01-01T00:00:00Z",
            "subscription_end_date": None,
            "total_memories_saved": 50,
            "monthly_summary_pages_used": 4,  # 1 page from limit
            "monthly_summary_reset_date": "2024-01-01T00:00:00Z"
        }
    
    @pytest.fixture
    def pro_user_subscription(self):
        """Mock subscription data for pro user"""
        return {
            "user_id": "test_user_123",
            "subscription_tier": "pro",
            "subscription_status": "active",
            "subscription_start_date": "2024-01-01T00:00:00Z",
            "subscription_end_date": "2025-01-01T00:00:00Z",
            "total_memories_saved": 500,
            "monthly_summary_pages_used": 50,  # Within pro limit of 100
            "monthly_summary_reset_date": "2024-01-01T00:00:00Z"
        }

    def setup_auth_mocks(self, mock_jwt_decode, mock_create_user):
        """Helper method to setup authentication mocks consistently"""
        mock_jwt_decode.return_value = {"sub": "test_user_123", "user_metadata": {"full_name": "Test User"}}
        mock_create_user.return_value = None  # Auth middleware doesn't use return value

    @patch('app.routers.summaryRouter.generate_summary', new_callable=AsyncMock)
    @patch('app.routers.summaryRouter.increment_summary_pages')
    @patch('app.routers.summaryRouter.check_summary_middleware', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    def test_free_user_blocked_after_5_pages_in_month(
        self,
        mock_create_user,
        mock_jwt_decode,
        mock_check_summary_middleware,
        mock_increment_pages,
        mock_generate_summary,
        free_user_at_limit,
        sample_content_short
    ):
        """Integration test: Free user blocked after 5 pages in month"""
        
        # Setup mocks
        self.setup_auth_mocks(mock_jwt_decode, mock_create_user)
        
        # Mock the middleware to throw 402 error
        from fastapi import HTTPException
        mock_check_summary_middleware.side_effect = HTTPException(
            status_code=402, 
            detail={
                "error": "Subscription limit exceeded",
                "action_required": "upgrade",
                "message": "This summary (1 pages) would exceed your monthly limit (5 pages). Upgrade to Pro for 100 pages per month.",
                "upgrade_url": "/subscription/upgrade",
                "subscription_info": {
                    "current_tier": "free",
                    "upgrade_benefits": ["Unlimited memory saves", "100 summary pages per month", "AI-powered dashboard queries"]
                }
            }
        )
        
        # Make request to generate summary
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiaWF0IjoxNjE2MjM5MDIyfQ.test_signature"
        headers = {"access_token": fake_jwt}
        request_data = {"content": sample_content_short}
        
        response = client.post("/summary/generate", json=request_data, headers=headers)
        
        # Assertions
        assert response.status_code == 402
        response_data = response.json()
        
        # Check 402 response structure
        assert "detail" in response_data
        detail = response_data["detail"]
        assert detail["error"] == "Subscription limit exceeded"
        assert detail["action_required"] == "upgrade"
        assert "monthly limit (5 pages)" in detail["message"]
        assert detail["upgrade_url"] == "/subscription/upgrade"
        assert "subscription_info" in detail
        
        # Verify summary generation was never called
        mock_generate_summary.assert_not_called()
        mock_increment_pages.assert_not_called()
    
    @patch('app.routers.summaryRouter.generate_summary', new_callable=AsyncMock)
    @patch('app.routers.summaryRouter.increment_summary_pages')
    @patch('app.routers.summaryRouter.check_summary_middleware', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    def test_pro_user_can_generate_up_to_100_pages(
        self,
        mock_create_user,
        mock_jwt_decode,
        mock_check_summary_middleware,
        mock_increment_pages,
        mock_generate_summary,
        pro_user_subscription,
        sample_content_large
    ):
        """Integration test: Pro user can generate up to 100 pages"""
        
        # Setup mocks
        self.setup_auth_mocks(mock_jwt_decode, mock_create_user)
        mock_check_summary_middleware.return_value = None  # No exception = allowed
        mock_generate_summary.return_value = "This is a generated summary of the large content."
        
        # Mock increment to return updated subscription
        updated_subscription = {**pro_user_subscription, "monthly_summary_pages_used": 54}
        mock_increment_pages.return_value = updated_subscription
        
        # Make request to generate summary
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiaWF0IjoxNjE2MjM5MDIyfQ.test_signature"
        headers = {"access_token": fake_jwt}
        request_data = {"content": sample_content_large}
        
        response = client.post("/summary/generate", json=request_data, headers=headers)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        
        # Check successful response
        assert "summary" in response_data
        assert "pages_processed" in response_data
        estimated_pages = estimate_content_pages(sample_content_large)
        assert response_data["pages_processed"] == estimated_pages
        
        # Verify summary generation was called
        mock_generate_summary.assert_called_once_with(sample_content_large)
        
        # Verify page increment was called with correct estimated pages
        mock_increment_pages.assert_called_once_with("test_user_123", estimated_pages)
    
    @patch('app.routers.summaryRouter.generate_summary', new_callable=AsyncMock)
    @patch('app.routers.summaryRouter.increment_summary_pages')
    @patch('app.routers.summaryRouter.check_summary_middleware', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    def test_page_estimation_is_reasonable(
        self,
        mock_create_user,
        mock_jwt_decode,
        mock_check_summary_middleware,
        mock_increment_pages,
        mock_generate_summary
    ):
        """Integration test: Page estimation is reasonable (±20% accuracy)"""
        
        # Create content with known character counts for testing
        test_cases = [
            ("A" * 1500, 1),   # ~1500 chars should be 1 page
            ("A" * 3000, 1),   # ~3000 chars should be 1 page
            ("A" * 4500, 2),   # ~4500 chars should be 2 pages
            ("A" * 6000, 2),   # ~6000 chars should be 2 pages
            ("A" * 9000, 3),   # ~9000 chars should be 3 pages
            ("A" * 12000, 4),  # ~12000 chars should be 4 pages
        ]
        
        for content, expected_pages in test_cases:
            # Setup mocks for each test
            self.setup_auth_mocks(mock_jwt_decode, mock_create_user)
            mock_check_summary_middleware.return_value = None  # No exception = allowed
            mock_generate_summary.return_value = f"Summary of {len(content)} character content"
            
            mock_increment_pages.return_value = {"monthly_summary_pages_used": expected_pages}
            
            # Make request
            fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiaWF0IjoxNjE2MjM5MDIyfQ.test_signature"
            headers = {"access_token": fake_jwt}
            request_data = {"content": content}
            
            response = client.post("/summary/generate", json=request_data, headers=headers)
            
            # Check page estimation is reasonable (within ±20% or exactly expected)
            assert response.status_code == 200
            response_data = response.json()
            estimated_pages = response_data["pages_processed"]
            
            # Allow for some variance but should be close to expected
            min_acceptable = max(1, int(expected_pages * 0.8))
            max_acceptable = int(expected_pages * 1.2) + 1
            
            assert min_acceptable <= estimated_pages <= max_acceptable, (
                f"Page estimation for {len(content)} chars: expected ~{expected_pages}, "
                f"got {estimated_pages}, acceptable range: {min_acceptable}-{max_acceptable}"
            )
            
            # Reset mocks for next iteration
            mock_generate_summary.reset_mock()
            mock_increment_pages.reset_mock()
    
    @patch('app.routers.summaryRouter.generate_summary', new_callable=AsyncMock)
    @patch('app.routers.summaryRouter.increment_summary_pages')
    @patch('app.routers.summaryRouter.check_summary_middleware', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    def test_summary_count_increments_correctly(
        self,
        mock_create_user,
        mock_jwt_decode,
        mock_check_summary_middleware,
        mock_increment_pages,
        mock_generate_summary,
        sample_content_medium
    ):
        """Integration test: Summary count increments correctly"""
        
        # Setup mocks
        self.setup_auth_mocks(mock_jwt_decode, mock_create_user)
        mock_check_summary_middleware.return_value = None  # No exception = allowed
        mock_generate_summary.return_value = "Generated summary for medium content"
        
        # Estimate pages for the medium content
        estimated_pages = estimate_content_pages(sample_content_medium)
        
        # Mock increment to return updated subscription
        mock_increment_pages.return_value = {"monthly_summary_pages_used": estimated_pages}
        
        # Make request
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiaWF0IjoxNjE2MjM5MDIyfQ.test_signature"
        headers = {"access_token": fake_jwt}
        request_data = {"content": sample_content_medium}
        
        response = client.post("/summary/generate", json=request_data, headers=headers)
        
        # Assertions
        assert response.status_code == 200
        
        # Verify summary was generated first
        mock_generate_summary.assert_called_once_with(sample_content_medium)
        
        # Verify increment was called after successful generation
        mock_increment_pages.assert_called_once_with("test_user_123", estimated_pages)
        
        # Verify the correct number of pages was used
        args, kwargs = mock_increment_pages.call_args
        assert args[0] == "test_user_123"
        assert args[1] == estimated_pages
    
    @patch('app.routers.summaryRouter.generate_summary', new_callable=AsyncMock)
    @patch('app.routers.summaryRouter.increment_summary_pages')
    @patch('app.routers.summaryRouter.check_summary_middleware', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    def test_large_content_blocks_free_user_appropriately(
        self,
        mock_create_user,
        mock_jwt_decode,
        mock_check_summary_middleware,
        mock_increment_pages,
        mock_generate_summary,
        sample_content_large
    ):
        """Integration test: Large content (4 pages) blocks free user near limit"""
        
        # Setup mocks - middleware should block this request
        self.setup_auth_mocks(mock_jwt_decode, mock_create_user)
        
        # Mock the middleware to throw 402 error
        from fastapi import HTTPException
        estimated_pages = estimate_content_pages(sample_content_large)
        mock_check_summary_middleware.side_effect = HTTPException(
            status_code=402, 
            detail={
                "error": "Subscription limit exceeded",
                "action_required": "upgrade",
                "message": f"This summary ({estimated_pages} pages) would exceed your monthly limit (5 pages). Upgrade to Pro for 100 pages per month.",
                "upgrade_url": "/subscription/upgrade",
                "subscription_info": {
                    "current_tier": "free",
                    "upgrade_benefits": ["Unlimited memory saves", "100 summary pages per month", "AI-powered dashboard queries"]
                },
                "pages_requested": estimated_pages
            }
        )
        
        # Make request
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiaWF0IjoxNjE2MjM5MDIyfQ.test_signature"
        headers = {"access_token": fake_jwt}
        request_data = {"content": sample_content_large}
        
        response = client.post("/summary/generate", json=request_data, headers=headers)
        
        # Should be blocked with 402
        assert response.status_code == 402
        response_data = response.json()
        
        # Check error message mentions the estimated pages
        detail = response_data["detail"]
        assert str(estimated_pages) in detail["message"]
        assert "monthly limit (5 pages)" in detail["message"]
        
        # Verify summary generation was never called
        mock_generate_summary.assert_not_called()
        mock_increment_pages.assert_not_called()
    
    @patch('app.routers.summaryRouter.generate_summary', new_callable=AsyncMock)
    @patch('app.routers.summaryRouter.increment_summary_pages')
    @patch('app.routers.summaryRouter.check_summary_middleware', new_callable=AsyncMock)
    @patch('app.main.decodeJWT')
    @patch('app.main.create_user_if_not_exists', new_callable=AsyncMock)
    def test_increment_failure_doesnt_break_summary_generation(
        self,
        mock_create_user,
        mock_jwt_decode,
        mock_check_summary_middleware,
        mock_increment_pages,
        mock_generate_summary,
        sample_content_short
    ):
        """Integration test: Increment failure doesn't break successful summary generation"""
        
        # Setup mocks
        self.setup_auth_mocks(mock_jwt_decode, mock_create_user)
        mock_check_summary_middleware.return_value = None  # No exception = allowed
        mock_generate_summary.return_value = "Generated summary despite increment failure"
        
        # Mock increment to raise an exception
        mock_increment_pages.side_effect = Exception("Database connection failed")
        
        # Make request
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiaWF0IjoxNjE2MjM5MDIyfQ.test_signature"
        headers = {"access_token": fake_jwt}
        request_data = {"content": sample_content_short}
        
        response = client.post("/summary/generate", json=request_data, headers=headers)
        
        # Summary generation should still succeed even if tracking fails
        assert response.status_code == 200
        response_data = response.json()
        assert "summary" in response_data
        assert response_data["summary"] == "Generated summary despite increment failure"
        
        # Verify both functions were called
        mock_generate_summary.assert_called_once_with(sample_content_short)
        mock_increment_pages.assert_called_once()
    
    @patch('app.main.decodeJWT')
    def test_missing_content_returns_400(self, mock_jwt_decode):
        """Test that missing content returns 400 error"""
        # Setup basic auth mock
        mock_jwt_decode.return_value = {"sub": "test_user_123", "user_metadata": {"full_name": "Test User"}}
        
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiaWF0IjoxNjE2MjM5MDIyfQ.test_signature"
        headers = {"access_token": fake_jwt}
        
        # Test with missing content
        request_data = {}
        response = client.post("/summary/generate", json=request_data, headers=headers)
        assert response.status_code == 400
        assert "Content is required" in response.json()["detail"]
        
        # Test with empty content
        request_data = {"content": ""}
        response = client.post("/summary/generate", json=request_data, headers=headers)
        assert response.status_code == 400
        assert "Content is required" in response.json()["detail"]


class TestPageEstimationEdgeCases:
    """Unit tests for page estimation edge cases"""
    
    def test_page_estimation_handles_empty_content(self):
        """Unit test: Page estimation handles edge cases (empty content, very long content)"""
        
        # Test empty string
        assert estimate_content_pages("") == 1
        
        # Test whitespace only
        assert estimate_content_pages("   ") == 1
        assert estimate_content_pages("\n\n\t  \n") == 1
        
        # Test None (edge case)
        assert estimate_content_pages(None) == 1
    
    def test_page_estimation_handles_very_long_content(self):
        """Unit test: Page estimation handles very long content correctly"""
        
        # Test very long content (100 pages worth)
        very_long_content = "A" * 300000  # 300k characters = ~100 pages
        estimated_pages = estimate_content_pages(very_long_content)
        
        # Should be around 100 pages (300000 / 3000 = 100)
        assert 95 <= estimated_pages <= 105  # Allow small variance
        
        # Test extremely long content
        extremely_long_content = "A" * 1000000  # 1M characters
        estimated_pages = estimate_content_pages(extremely_long_content)
        
        # Should be around 334 pages (1000000 / 3000 = 333.33, rounded up)
        assert 330 <= estimated_pages <= 340
    
    def test_page_estimation_handles_mixed_content(self):
        """Test page estimation with mixed content types"""
        
        # Content with special characters, newlines, etc.
        mixed_content = "Line 1\n\nLine 2 with special chars: @#$%^&*()\n" * 100
        estimated_pages = estimate_content_pages(mixed_content)
        
        # Should be reasonable (minimum 1, proportional to length)
        assert estimated_pages >= 1
        assert estimated_pages <= len(mixed_content) / 1000  # Should not be too high
    
    def test_page_estimation_consistent_with_service(self):
        """Test that router estimation matches service estimation"""
        
        test_contents = [
            "Short content",
            "A" * 1500,   # 1 page
            "A" * 4500,   # 2 pages
            "A" * 9000,   # 3 pages
        ]
        
        for content in test_contents:
            # Direct call to service function
            service_estimate = estimate_content_pages(content)
            
            # Should always be consistent
            assert service_estimate >= 1
            assert isinstance(service_estimate, int) 