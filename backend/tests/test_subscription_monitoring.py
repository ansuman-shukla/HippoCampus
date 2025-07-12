import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import time

from app.services.subscription_monitoring_service import (
    SubscriptionMonitoringService,
    get_memory_usage_patterns,
    get_summary_generation_trends,
    get_upgrade_conversion_rates,
    get_subscription_health,
    get_comprehensive_monitoring_report,
    monitoring_service
)
from app.core.database import collection
from app.models.user_model import userModel


class TestSubscriptionMonitoringService:
    """Test subscription monitoring service functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment before each test"""
        # Clear ALL test data (more aggressive cleanup)
        collection.delete_many({"$or": [
            {"email": {"$regex": ".*test.*"}},
            {"id": {"$regex": ".*test.*"}},
            {"id": {"$regex": ".*user_.*"}},
            {"id": {"$regex": ".*perf_.*"}},
            {"id": {"$regex": ".*cache_.*"}},
            {"id": {"$regex": ".*ttl_.*"}},
            {"id": {"$regex": ".*health_.*"}},
            {"id": {"$regex": ".*endpoint_.*"}}
        ]})
        
        # Clear monitoring cache
        monitoring_service._metrics_cache.clear()
        monitoring_service._last_cache_update.clear()
        
        yield
        
        # Cleanup after test - more aggressive
        collection.delete_many({"$or": [
            {"email": {"$regex": ".*test.*"}},
            {"id": {"$regex": ".*test.*"}},
            {"id": {"$regex": ".*user_.*"}},
            {"id": {"$regex": ".*perf_.*"}},
            {"id": {"$regex": ".*cache_.*"}},
            {"id": {"$regex": ".*ttl_.*"}},
            {"id": {"$regex": ".*health_.*"}},
            {"id": {"$regex": ".*endpoint_.*"}}
        ]})
    
    def create_test_user(self, user_id: str, tier: str = "free", memories: int = 0, 
                        summary_pages: int = 0, status: str = "active") -> dict:
        """Helper to create test user with subscription data"""
        now = datetime.now(timezone.utc)
        user_data = {
            "id": user_id,
            "email": f"{user_id}@test.com",
            "subscription_tier": tier,
            "subscription_status": status,
            "subscription_start_date": now - timedelta(days=30),
            "subscription_end_date": now + timedelta(days=30) if tier == "pro" else None,
            "total_memories_saved": memories,
            "monthly_summary_pages_used": summary_pages,
            "monthly_summary_reset_date": now - timedelta(days=15)
        }
        
        collection.insert_one(user_data)
        return user_data
    
    def test_memory_usage_patterns_analysis(self):
        """Integration test: Memory usage patterns are collected accurately"""
        # Create test users with various memory usage patterns
        self.create_test_user("user_free_low", "free", memories=25, summary_pages=2)
        self.create_test_user("user_free_medium", "free", memories=65, summary_pages=3)
        self.create_test_user("user_free_high", "free", memories=95, summary_pages=4)
        self.create_test_user("user_free_limit", "free", memories=100, summary_pages=5)
        self.create_test_user("user_pro_active", "pro", memories=250, summary_pages=25, status="active")
        self.create_test_user("user_pro_cancelled", "pro", memories=180, summary_pages=15, status="cancelled")
        
        # Test memory usage patterns analysis
        patterns = get_memory_usage_patterns(30)
        
        # Verify overall structure
        assert "analysis_period_days" in patterns
        assert "timestamp" in patterns
        assert "tiers" in patterns
        assert "overall" in patterns
        assert "free_user_distribution" in patterns
        
        # Verify tier-specific data
        assert "free" in patterns["tiers"]
        assert "pro" in patterns["tiers"]
        
        free_tier = patterns["tiers"]["free"]
        assert free_tier["total_users"] == 4
        assert free_tier["total_memories"] == 285  # 25+65+95+100
        assert free_tier["users_at_limit"] == 1  # user_free_limit
        assert free_tier["limit"] == 100
        
        pro_tier = patterns["tiers"]["pro"]
        assert pro_tier["total_users"] == 2
        assert pro_tier["total_memories"] == 430  # 250+180
        assert pro_tier["limit"] == "unlimited"
        
        # Verify overall metrics
        assert patterns["overall"]["total_users"] == 6
        assert patterns["overall"]["total_memories"] == 715
        assert patterns["overall"]["limit_pressure"] > 0  # Should show pressure from limit users
        
        # Verify usage distribution buckets
        distribution = patterns["free_user_distribution"]
        assert isinstance(distribution, dict)
        assert len(distribution) > 0
        
        print(f"✅ Memory usage patterns test passed - analyzed {patterns['overall']['total_users']} users")
    
    def test_summary_generation_trends_analysis(self):
        """Integration test: Summary generation trends are collected accurately"""
        # Create test users with various summary usage patterns
        self.create_test_user("user_inactive", "free", memories=10, summary_pages=0)
        self.create_test_user("user_light", "free", memories=30, summary_pages=2)
        self.create_test_user("user_heavy", "free", memories=80, summary_pages=5)
        self.create_test_user("user_pro_light", "pro", memories=150, summary_pages=10, status="active")
        self.create_test_user("user_pro_heavy", "pro", memories=300, summary_pages=45, status="active")
        
        # Test summary trends analysis
        trends = get_summary_generation_trends(30)
        
        # Verify overall structure
        assert "analysis_period_days" in trends
        assert "timestamp" in trends
        assert "tiers" in trends
        assert "overall" in trends
        assert "free_user_page_distribution" in trends
        
        # Verify tier-specific data
        free_tier = trends["tiers"]["free"]
        assert free_tier["total_users"] == 3
        assert free_tier["active_users"] == 2  # light and heavy users
        assert free_tier["total_pages_generated"] == 7  # 2+5
        assert free_tier["users_at_limit"] == 1  # heavy user
        
        pro_tier = trends["tiers"]["pro"]
        assert pro_tier["total_users"] == 2
        assert pro_tier["active_users"] == 2
        assert pro_tier["total_pages_generated"] == 55  # 10+45
        
        # Verify overall metrics
        overall = trends["overall"]
        assert overall["total_users"] == 5
        assert overall["active_users"] == 4
        assert overall["total_pages_generated"] == 62
        assert overall["utilization_rate"] == 80.0  # 4/5 * 100
        
        # Verify usage distribution
        distribution = trends["free_user_page_distribution"]
        assert isinstance(distribution, dict)
        
        print(f"✅ Summary trends test passed - {overall['utilization_rate']}% utilization rate")
    
    def test_upgrade_conversion_rates_analysis(self):
        """Integration test: Conversion rates are collected accurately"""
        # Create test users representing conversion funnel
        recent_date = datetime.now(timezone.utc) - timedelta(days=15)
        
        # Free users at various stages
        self.create_test_user("user_new", "free", memories=5, summary_pages=1)
        self.create_test_user("user_near_memory", "free", memories=85, summary_pages=2)
        self.create_test_user("user_near_summary", "free", memories=40, summary_pages=4)
        self.create_test_user("user_at_memory_limit", "free", memories=100, summary_pages=3)
        self.create_test_user("user_at_summary_limit", "free", memories=50, summary_pages=5)
        
        # Pro users (including recent conversions)
        pro_user_data = self.create_test_user("user_pro_active", "pro", memories=200, summary_pages=20, status="active")
        collection.update_one(
            {"id": "user_pro_active"},
            {"$set": {"subscription_start_date": recent_date}}
        )
        
        self.create_test_user("user_pro_expired", "pro", memories=150, summary_pages=15, status="expired")
        
        # Test conversion analysis
        conversion_data = get_upgrade_conversion_rates(30)
        
        # Verify structure
        assert "analysis_period_days" in conversion_data
        assert "user_segments" in conversion_data
        assert "conversion_metrics" in conversion_data
        assert "conversion_triggers" in conversion_data
        assert "revenue_analytics" in conversion_data
        assert "conversion_funnel" in conversion_data
        
        # Verify user segments
        segments = conversion_data["user_segments"]
        assert segments["total_users"] == 7
        assert segments["free_users"] == 5
        assert segments["pro_users"] == 2
        assert segments["active_pro_users"] == 1
        assert segments["expired_pro_users"] == 1
        
        # Verify conversion triggers
        triggers = conversion_data["conversion_triggers"]
        assert triggers["near_memory_limit"]["count"] == 1  # user_near_memory
        assert triggers["at_memory_limit"]["count"] == 1   # user_at_memory_limit
        assert triggers["near_summary_limit"]["count"] == 1 # user_near_summary
        assert triggers["at_summary_limit"]["count"] == 1  # user_at_summary_limit
        
        # Verify conversion metrics
        metrics = conversion_data["conversion_metrics"]
        assert metrics["overall_conversion_rate"] == round((2/7) * 100, 2)  # 2 pro / 7 total
        assert metrics["recent_upgrades"] == 1  # user_pro_active
        
        # Verify revenue analytics
        revenue = conversion_data["revenue_analytics"]
        assert revenue["monthly_recurring_revenue"] == 8  # 1 active pro * $8
        assert revenue["annual_recurring_revenue"] == 96   # 1 active pro * $8 * 12
        
        print(f"✅ Conversion rates test passed - {metrics['overall_conversion_rate']}% conversion rate")
    
    def test_subscription_service_health_check(self):
        """Integration test: Health checks return correct status"""
        # Create some test data to ensure database is accessible
        self.create_test_user("health_test_user", "free", memories=50, summary_pages=2)
        
        # Test health check
        health_data = get_subscription_health()
        
        # Verify structure
        assert "timestamp" in health_data
        assert "overall_status" in health_data
        assert "services" in health_data
        assert "performance_metrics" in health_data
        assert "alerts" in health_data
        
        # Verify services
        services = health_data["services"]
        assert "database" in services
        assert "subscription_service" in services
        assert "monitoring_cache" in services
        
        # Database should be healthy
        db_service = services["database"]
        assert db_service["status"] == "healthy"
        assert "response_time_ms" in db_service
        assert db_service["subscription_data_accessible"] is True
        
        # Subscription service should be healthy
        sub_service = services["subscription_service"]
        assert sub_service["status"] == "healthy"
        assert sub_service["core_functions_accessible"] is True
        assert sub_service["tier_limits_configured"] is True
        
        # Performance metrics should be present
        perf = health_data["performance_metrics"]
        assert "subscription_query_time_ms" in perf
        assert "total_subscription_users" in perf
        assert "performance_status" in perf
        
        # Business metrics should be present
        business = health_data["business_metrics"]
        assert "total_users" in business
        assert "free_users" in business
        assert "pro_users" in business
        assert "conversion_rate" in business
        
        # Overall status should be healthy if no issues
        if len(health_data["alerts"]) == 0:
            assert health_data["overall_status"] == "healthy"
        
        print(f"✅ Health check test passed - status: {health_data['overall_status']}")
    
    def test_comprehensive_monitoring_report(self):
        """Monitoring test: Comprehensive dashboard displays correct data"""
        # Create comprehensive test dataset
        users_data = [
            ("user_free_1", "free", 20, 1),
            ("user_free_2", "free", 75, 3),
            ("user_free_3", "free", 100, 5),
            ("user_pro_1", "pro", 200, 25),
            ("user_pro_2", "pro", 350, 45)
        ]
        
        for user_id, tier, memories, pages in users_data:
            self.create_test_user(user_id, tier, memories, pages, 
                                status="active" if tier == "pro" else "active")
        
        # Test comprehensive report
        report = get_comprehensive_monitoring_report(30)
        
        # Verify top-level structure
        assert "report_timestamp" in report
        assert "analysis_period_days" in report
        assert "health_status" in report
        assert "memory_usage_patterns" in report
        assert "summary_generation_trends" in report
        assert "upgrade_conversion_rates" in report
        assert "report_summary" in report
        
        # Verify health status is included
        health = report["health_status"]
        assert "overall_status" in health
        assert "services" in health
        
        # Verify memory patterns are included
        memory = report["memory_usage_patterns"]
        assert "tiers" in memory
        assert "overall" in memory
        
        # Verify summary trends are included
        summary = report["summary_generation_trends"]
        assert "tiers" in summary
        assert "overall" in summary
        
        # Verify conversion data is included
        conversion = report["upgrade_conversion_rates"]
        assert "conversion_metrics" in conversion
        assert "revenue_analytics" in conversion
        
        # Verify executive summary
        summary_data = report["report_summary"]
        assert "system_health" in summary_data
        assert "total_users" in summary_data
        assert "conversion_rate" in summary_data
        assert "monthly_revenue" in summary_data
        
        # Verify data consistency
        assert summary_data["total_users"] == 5
        assert summary_data["monthly_revenue"] == 16  # 2 pro users * $8
        
        print(f"✅ Comprehensive report test passed - {summary_data['total_users']} users analyzed")
    
    def test_metrics_collection_performance(self):
        """Performance test: Metrics collection doesn't impact performance"""
        # Create a larger dataset for performance testing
        users_count = 50
        for i in range(users_count):
            tier = "pro" if i % 5 == 0 else "free"  # 20% pro, 80% free
            memories = min(i * 2, 100) if tier == "free" else i * 5
            pages = min(i // 10, 5) if tier == "free" else i // 5
            self.create_test_user(f"perf_user_{i}", tier, memories, pages)
        
        # Test performance of each monitoring function
        performance_results = {}
        
        # Test memory patterns performance
        start_time = time.time()
        memory_patterns = get_memory_usage_patterns(30)
        memory_time = (time.time() - start_time) * 1000
        performance_results["memory_patterns_ms"] = memory_time
        
        # Test summary trends performance
        start_time = time.time()
        summary_trends = get_summary_generation_trends(30)
        summary_time = (time.time() - start_time) * 1000
        performance_results["summary_trends_ms"] = summary_time
        
        # Test conversion rates performance
        start_time = time.time()
        conversion_rates = get_upgrade_conversion_rates(30)
        conversion_time = (time.time() - start_time) * 1000
        performance_results["conversion_rates_ms"] = conversion_time
        
        # Test health check performance
        start_time = time.time()
        health_check = get_subscription_health()
        health_time = (time.time() - start_time) * 1000
        performance_results["health_check_ms"] = health_time
        
        # Test comprehensive report performance
        start_time = time.time()
        comprehensive_report = get_comprehensive_monitoring_report(30)
        comprehensive_time = (time.time() - start_time) * 1000
        performance_results["comprehensive_report_ms"] = comprehensive_time
        
        # Performance assertions (reasonable thresholds)
        assert memory_time < 1000, f"Memory patterns too slow: {memory_time}ms"
        assert summary_time < 1000, f"Summary trends too slow: {summary_time}ms"
        assert conversion_time < 1000, f"Conversion rates too slow: {conversion_time}ms"
        assert health_time < 500, f"Health check too slow: {health_time}ms"
        assert comprehensive_time < 2000, f"Comprehensive report too slow: {comprehensive_time}ms"
        
        # Verify data quality wasn't compromised for performance
        assert memory_patterns["overall"]["total_users"] == users_count
        assert summary_trends["overall"]["total_users"] == users_count
        assert conversion_rates["user_segments"]["total_users"] == users_count
        assert health_check["business_metrics"]["total_users"] == users_count
        
        print(f"✅ Performance test passed:")
        for metric, time_ms in performance_results.items():
            print(f"   ├─ {metric}: {time_ms:.1f}ms")
        print(f"   └─ All metrics under performance thresholds")
    
    def test_monitoring_cache_functionality(self):
        """Integration test: Monitoring cache improves performance"""
        # Create test data
        self.create_test_user("cache_test_user", "free", 50, 3)
        
        # Clear cache first
        monitoring_service._metrics_cache.clear()
        monitoring_service._last_cache_update.clear()
        
        # First call should hit database
        start_time = time.time()
        first_call = get_memory_usage_patterns(30)
        first_call_time = (time.time() - start_time) * 1000
        
        # Second call should use cache
        start_time = time.time()
        second_call = get_memory_usage_patterns(30)
        second_call_time = (time.time() - start_time) * 1000
        
        # Verify cache improved performance
        assert second_call_time < first_call_time, "Cache should improve performance"
        assert second_call_time < 10, f"Cached call should be very fast: {second_call_time}ms"
        
        # Verify cached data is identical
        assert first_call == second_call, "Cached data should be identical"
        
        # Verify cache contains the data
        cache_key = "memory_patterns_30"
        assert cache_key in monitoring_service._metrics_cache
        assert cache_key in monitoring_service._last_cache_update
        
        print(f"✅ Cache test passed:")
        print(f"   ├─ First call (DB): {first_call_time:.1f}ms")
        print(f"   ├─ Second call (cache): {second_call_time:.1f}ms")
        print(f"   └─ Performance improvement: {((first_call_time - second_call_time) / first_call_time * 100):.1f}%")
    
    def test_monitoring_error_handling(self):
        """Integration test: Monitoring handles errors gracefully"""
        # Test with database connection issues
        with patch('app.services.subscription_monitoring_service.collection') as mock_collection:
            mock_collection.aggregate.side_effect = Exception("Database connection failed")
            
            # Should raise exception for data collection functions
            with pytest.raises(Exception):
                get_memory_usage_patterns(30)
        
        # Test health check with database errors
        with patch('app.services.subscription_monitoring_service.collection.find_one') as mock_find:
            mock_find.side_effect = Exception("Database error")
            
            health_data = get_subscription_health()
            
            # Should return degraded status with alerts
            assert health_data["overall_status"] in ["degraded", "unhealthy"]
            assert len(health_data["alerts"]) > 0
            # Check if any alert mentions database issues
            alert_messages = " ".join(health_data["alerts"])
            assert "database" in alert_messages.lower() or "failed" in alert_messages.lower()
        
        print("✅ Error handling test passed")
    
    def test_cache_ttl_expiration(self):
        """Integration test: Cache TTL works correctly"""
        # Create test data
        self.create_test_user("ttl_test_user", "free", 25, 2)
        
        # Clear cache
        monitoring_service._metrics_cache.clear()
        monitoring_service._last_cache_update.clear()
        
        # Set a very short TTL for testing
        original_ttl = monitoring_service._cache_ttl
        monitoring_service._cache_ttl = 1  # 1 second
        
        try:
            # First call
            first_result = get_memory_usage_patterns(30)
            
            # Verify cache is populated
            cache_key = "memory_patterns_30"
            assert cache_key in monitoring_service._metrics_cache
            
            # Wait for TTL to expire
            time.sleep(1.1)
            
            # Verify cache is considered invalid
            assert not monitoring_service._is_cache_valid(cache_key)
            
            # Second call should refresh cache
            second_result = get_memory_usage_patterns(30)
            
            # Results should be mostly identical (except timestamps)
            # Compare key data fields instead of full objects
            assert first_result["analysis_period_days"] == second_result["analysis_period_days"]
            assert first_result["tiers"] == second_result["tiers"]
            assert first_result["overall"] == second_result["overall"]
            assert first_result["free_user_distribution"] == second_result["free_user_distribution"]
            
        finally:
            # Restore original TTL
            monitoring_service._cache_ttl = original_ttl
        
        print("✅ Cache TTL test passed")


@pytest.mark.asyncio
class TestMonitoringRouter:
    """Test monitoring router endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        collection.delete_many({"$or": [
            {"email": {"$regex": ".*test.*"}},
            {"id": {"$regex": ".*test.*"}},
            {"id": {"$regex": ".*endpoint_.*"}}
        ]})
        monitoring_service._metrics_cache.clear()
        monitoring_service._last_cache_update.clear()
        yield
        collection.delete_many({"$or": [
            {"email": {"$regex": ".*test.*"}},
            {"id": {"$regex": ".*test.*"}},
            {"id": {"$regex": ".*endpoint_.*"}}
        ]})
    
    def create_test_admin_user(self, user_id: str = "admin_test") -> dict:
        """Helper to create admin test user"""
        admin_data = {
            "id": user_id,
            "email": "admin@test.com",
            "subscription_tier": "pro",
            "subscription_status": "active",
            "total_memories_saved": 100,
            "monthly_summary_pages_used": 10
        }
        collection.insert_one(admin_data)
        return admin_data
    
    async def test_health_endpoint_accessibility(self):
        """Integration test: Health endpoint is accessible without auth"""
        from app.routers.monitoring_router import subscription_service_health
        
        # Health endpoint should work without authentication
        response = await subscription_service_health()
        
        # Should return valid health data
        assert hasattr(response, 'status_code')
        
        print("✅ Health endpoint accessibility test passed")
    
    async def test_admin_authentication_required(self):
        """Integration test: Admin endpoints require authentication"""
        from app.routers.monitoring_router import require_admin
        from fastapi import Request, HTTPException
        
        # Mock request without user_id
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.user_id = None
        
        # Should raise 401 error
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(mock_request)
        assert exc_info.value.status_code == 401
        
        print("✅ Admin authentication test passed")
    
    async def test_monitoring_endpoints_functionality(self):
        """Integration test: All monitoring endpoints return correct data"""
        # This test would require full FastAPI test client setup
        # For now, we test the underlying functions which the endpoints call
        
        # Create test data
        test_user_data = {
            "id": "endpoint_test_user",
            "email": "endpoint@test.com",
            "subscription_tier": "free",
            "subscription_status": "active",
            "total_memories_saved": 75,
            "monthly_summary_pages_used": 3,
            "monthly_summary_reset_date": datetime.now(timezone.utc)
        }
        collection.insert_one(test_user_data)
        
        # Test all monitoring functions that endpoints use
        memory_patterns = get_memory_usage_patterns(7)
        summary_trends = get_summary_generation_trends(7)
        conversion_rates = get_upgrade_conversion_rates(7)
        health_status = get_subscription_health()
        comprehensive = get_comprehensive_monitoring_report(7)
        
        # Verify all functions return valid data
        assert isinstance(memory_patterns, dict)
        assert isinstance(summary_trends, dict)
        assert isinstance(conversion_rates, dict)
        assert isinstance(health_status, dict)
        assert isinstance(comprehensive, dict)
        
        # Verify key fields are present
        assert "tiers" in memory_patterns
        assert "overall" in summary_trends
        assert "conversion_metrics" in conversion_rates
        assert "overall_status" in health_status
        assert "report_summary" in comprehensive
        
        print("✅ Monitoring endpoints functionality test passed")


if __name__ == "__main__":
    # Run tests manually for development
    pytest.main([__file__, "-v"]) 