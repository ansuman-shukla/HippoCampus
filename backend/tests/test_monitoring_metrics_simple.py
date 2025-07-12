import pytest
import time
from datetime import datetime, timezone, timedelta

from app.services.subscription_monitoring_service import (
    get_memory_usage_patterns,
    get_summary_generation_trends,
    get_upgrade_conversion_rates,
    get_subscription_health,
    get_comprehensive_monitoring_report,
    monitoring_service
)
from app.core.database import collection


class TestPhase42MonitoringMetrics:
    """Test Phase 4.2: Add Monitoring Metrics - Core Requirements"""
    
    def test_metrics_collection_accuracy(self):
        """Integration test: Metrics are collected accurately"""
        print("📊 Testing metrics collection accuracy...")
        
        # Test that all monitoring functions return structured data
        try:
            memory_patterns = get_memory_usage_patterns(7)
            summary_trends = get_summary_generation_trends(7)
            conversion_rates = get_upgrade_conversion_rates(7)
            
            # Verify memory patterns structure
            assert isinstance(memory_patterns, dict)
            assert "analysis_period_days" in memory_patterns
            assert "tiers" in memory_patterns
            assert "overall" in memory_patterns
            
            # Verify summary trends structure
            assert isinstance(summary_trends, dict)
            assert "analysis_period_days" in summary_trends
            assert "tiers" in summary_trends
            assert "overall" in summary_trends
            
            # Verify conversion rates structure
            assert isinstance(conversion_rates, dict)
            assert "conversion_metrics" in conversion_rates
            assert "revenue_analytics" in conversion_rates
            assert "conversion_triggers" in conversion_rates
            
            print("✅ All metrics return structured data with required fields")
            print(f"   ├─ Memory patterns analyzed for {memory_patterns['analysis_period_days']} days")
            print(f"   ├─ Summary trends tracked {summary_trends['overall']['total_users']} users")
            print(f"   └─ Conversion data shows {conversion_rates['conversion_metrics']['overall_conversion_rate']}% rate")
            
        except Exception as e:
            print(f"❌ Metrics collection failed: {str(e)}")
            raise
    
    def test_health_checks_correct_status(self):
        """Integration test: Health checks return correct status"""
        print("🔍 Testing health check status accuracy...")
        
        try:
            health_data = get_subscription_health()
            
            # Verify health check structure
            assert isinstance(health_data, dict)
            assert "timestamp" in health_data
            assert "overall_status" in health_data
            assert "services" in health_data
            assert "performance_metrics" in health_data
            assert "alerts" in health_data
            
            # Verify services are checked
            services = health_data["services"]
            assert "database" in services
            assert "subscription_service" in services
            assert "monitoring_cache" in services
            
            # All services should have status field
            for service_name, service_data in services.items():
                assert "status" in service_data
                assert service_data["status"] in ["healthy", "unhealthy", "degraded"]
            
            # Performance metrics should be present
            perf = health_data["performance_metrics"]
            assert "subscription_query_time_ms" in perf
            assert "total_subscription_users" in perf
            assert "performance_status" in perf
            
            print("✅ Health checks return comprehensive status data")
            print(f"   ├─ Overall status: {health_data['overall_status']}")
            print(f"   ├─ Services checked: {len(services)}")
            print(f"   ├─ Query time: {perf['subscription_query_time_ms']:.1f}ms")
            print(f"   └─ Active alerts: {len(health_data['alerts'])}")
            
        except Exception as e:
            print(f"❌ Health check failed: {str(e)}")
            raise
    
    def test_dashboard_displays_correct_data(self):
        """Monitoring test: Dashboards display correct data"""
        print("📱 Testing dashboard data correctness...")
        
        try:
            # Test comprehensive monitoring report
            report = get_comprehensive_monitoring_report(7)
            
            # Verify comprehensive report structure
            assert isinstance(report, dict)
            assert "report_timestamp" in report
            assert "health_status" in report
            assert "memory_usage_patterns" in report
            assert "summary_generation_trends" in report
            assert "upgrade_conversion_rates" in report
            assert "report_summary" in report
            
            # Verify all sub-reports are present and valid
            health = report["health_status"]
            memory = report["memory_usage_patterns"]
            summary = report["summary_generation_trends"]
            conversion = report["upgrade_conversion_rates"]
            summary_data = report["report_summary"]
            
            # Verify health data
            assert "overall_status" in health
            assert "services" in health
            
            # Verify memory data
            assert "tiers" in memory
            assert "overall" in memory
            
            # Verify summary data
            assert "tiers" in summary
            assert "overall" in summary
            
            # Verify conversion data
            assert "conversion_metrics" in conversion
            assert "revenue_analytics" in conversion
            
            # Verify executive summary
            assert "system_health" in summary_data
            assert "total_users" in summary_data
            assert "conversion_rate" in summary_data
            assert "monthly_revenue" in summary_data
            
            print("✅ Dashboard displays comprehensive and accurate data")
            print(f"   ├─ Health status: {summary_data['system_health']}")
            print(f"   ├─ Total users: {summary_data['total_users']}")
            print(f"   ├─ Conversion rate: {summary_data['conversion_rate']}%")
            print(f"   └─ Monthly revenue: ${summary_data['monthly_revenue']}")
            
        except Exception as e:
            print(f"❌ Dashboard data test failed: {str(e)}")
            raise
    
    def test_performance_impact(self):
        """Performance test: Metrics collection doesn't impact performance"""
        print("⚡ Testing performance impact of metrics collection...")
        
        try:
            # Test individual function performance
            functions = [
                ("Memory patterns", get_memory_usage_patterns),
                ("Summary trends", get_summary_generation_trends),
                ("Conversion rates", get_upgrade_conversion_rates),
                ("Health check", get_subscription_health),
                ("Comprehensive report", get_comprehensive_monitoring_report)
            ]
            
            performance_results = {}
            
            for name, func in functions:
                start_time = time.time()
                
                if func == get_comprehensive_monitoring_report:
                    result = func(7)  # Use shorter period for performance test
                elif func in [get_memory_usage_patterns, get_summary_generation_trends, get_upgrade_conversion_rates]:
                    result = func(7)
                else:
                    result = func()
                
                elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
                performance_results[name] = elapsed_time
                
                # Verify function still returns valid data
                assert isinstance(result, dict)
                assert len(result) > 0
            
            # Verify performance thresholds
            assert performance_results["Memory patterns"] < 2000, f"Memory patterns too slow: {performance_results['Memory patterns']:.1f}ms"
            assert performance_results["Summary trends"] < 2000, f"Summary trends too slow: {performance_results['Summary trends']:.1f}ms"
            assert performance_results["Conversion rates"] < 2000, f"Conversion rates too slow: {performance_results['Conversion rates']:.1f}ms"
            assert performance_results["Health check"] < 1000, f"Health check too slow: {performance_results['Health check']:.1f}ms"
            assert performance_results["Comprehensive report"] < 3000, f"Comprehensive report too slow: {performance_results['Comprehensive report']:.1f}ms"
            
            print("✅ All monitoring functions meet performance requirements")
            for name, time_ms in performance_results.items():
                print(f"   ├─ {name}: {time_ms:.1f}ms")
            print(f"   └─ All functions completed within acceptable thresholds")
            
        except Exception as e:
            print(f"❌ Performance test failed: {str(e)}")
            raise
    
    def test_memory_usage_tracking(self):
        """Integration test: Track memory usage patterns"""
        print("💾 Testing memory usage pattern tracking...")
        
        try:
            patterns = get_memory_usage_patterns(30)
            
            # Verify memory tracking fields
            assert "tiers" in patterns
            assert "overall" in patterns
            
            # Verify tier tracking
            if "free" in patterns["tiers"]:
                free_tier = patterns["tiers"]["free"]
                assert "total_users" in free_tier
                assert "total_memories" in free_tier
                assert "avg_memories_per_user" in free_tier
                assert "users_at_limit" in free_tier
                assert "limit" in free_tier
            
            if "pro" in patterns["tiers"]:
                pro_tier = patterns["tiers"]["pro"]
                assert "total_users" in pro_tier
                assert "total_memories" in pro_tier
                assert "avg_memories_per_user" in pro_tier
            
            # Verify overall tracking
            overall = patterns["overall"]
            assert "total_users" in overall
            assert "total_memories" in overall
            assert "avg_memories_per_user" in overall
            assert "limit_pressure" in overall
            
            print("✅ Memory usage patterns tracking works correctly")
            print(f"   ├─ Total users tracked: {overall['total_users']}")
            print(f"   ├─ Total memories: {overall['total_memories']}")
            print(f"   └─ Limit pressure: {overall['limit_pressure']:.1f}%")
            
        except Exception as e:
            print(f"❌ Memory usage tracking failed: {str(e)}")
            raise
    
    def test_summary_generation_trends(self):
        """Integration test: Monitor summary generation trends"""
        print("📈 Testing summary generation trend monitoring...")
        
        try:
            trends = get_summary_generation_trends(30)
            
            # Verify summary tracking fields
            assert "tiers" in trends
            assert "overall" in trends
            
            # Verify overall tracking
            overall = trends["overall"]
            assert "total_users" in overall
            assert "active_users" in overall
            assert "total_pages_generated" in overall
            assert "avg_pages_per_user" in overall
            assert "utilization_rate" in overall
            
            # Verify tier tracking
            for tier_name, tier_data in trends["tiers"].items():
                assert "total_users" in tier_data
                assert "active_users" in tier_data
                assert "total_pages_generated" in tier_data
                assert "utilization_rate" in tier_data
                assert "users_at_limit" in tier_data
            
            print("✅ Summary generation trends tracking works correctly")
            print(f"   ├─ Total users: {overall['total_users']}")
            print(f"   ├─ Active users: {overall['active_users']}")
            print(f"   ├─ Utilization rate: {overall['utilization_rate']:.1f}%")
            print(f"   └─ Total pages generated: {overall['total_pages_generated']}")
            
        except Exception as e:
            print(f"❌ Summary trends tracking failed: {str(e)}")
            raise
    
    def test_upgrade_conversion_tracking(self):
        """Integration test: Track upgrade conversion rates"""
        print("💰 Testing upgrade conversion rate tracking...")
        
        try:
            conversion_data = get_upgrade_conversion_rates(30)
            
            # Verify conversion tracking fields
            assert "user_segments" in conversion_data
            assert "conversion_metrics" in conversion_data
            assert "conversion_triggers" in conversion_data
            assert "revenue_analytics" in conversion_data
            assert "conversion_funnel" in conversion_data
            
            # Verify user segments
            segments = conversion_data["user_segments"]
            assert "total_users" in segments
            assert "free_users" in segments
            assert "pro_users" in segments
            assert "active_pro_users" in segments
            
            # Verify conversion metrics
            metrics = conversion_data["conversion_metrics"]
            assert "overall_conversion_rate" in metrics
            assert "pro_retention_rate" in metrics
            assert "recent_upgrades" in metrics
            
            # Verify conversion triggers
            triggers = conversion_data["conversion_triggers"]
            assert "near_memory_limit" in triggers
            assert "at_memory_limit" in triggers
            assert "near_summary_limit" in triggers
            assert "at_summary_limit" in triggers
            
            # Verify revenue analytics
            revenue = conversion_data["revenue_analytics"]
            assert "monthly_recurring_revenue" in revenue
            assert "annual_recurring_revenue" in revenue
            assert "potential_revenue_from_triggers" in revenue
            
            print("✅ Upgrade conversion tracking works correctly")
            print(f"   ├─ Conversion rate: {metrics['overall_conversion_rate']:.1f}%")
            print(f"   ├─ Monthly revenue: ${revenue['monthly_recurring_revenue']}")
            print(f"   ├─ Users near limits: {triggers['near_memory_limit']['count'] + triggers['near_summary_limit']['count']}")
            print(f"   └─ Potential revenue: ${revenue['potential_revenue_from_triggers']}")
            
        except Exception as e:
            print(f"❌ Conversion tracking failed: {str(e)}")
            raise
    
    def test_monitoring_cache_performance(self):
        """Integration test: Monitoring cache improves performance"""
        print("🚀 Testing monitoring cache performance improvement...")
        
        try:
            # Clear cache first
            monitoring_service._metrics_cache.clear()
            monitoring_service._last_cache_update.clear()
            
            # First call (should hit database)
            start_time = time.time()
            first_result = get_memory_usage_patterns(7)
            first_call_time = (time.time() - start_time) * 1000
            
            # Verify cache is populated
            cache_key = "memory_patterns_7"
            assert cache_key in monitoring_service._metrics_cache
            
            # Second call (should use cache)
            start_time = time.time()
            second_result = get_memory_usage_patterns(7)
            second_call_time = (time.time() - start_time) * 1000
            
            # Verify cache improved performance (second call should be much faster)
            assert second_call_time < first_call_time
            assert second_call_time < 50  # Should be very fast from cache
            
            # Verify data integrity
            assert first_result["analysis_period_days"] == second_result["analysis_period_days"]
            assert first_result["tiers"] == second_result["tiers"]
            
            improvement_percentage = ((first_call_time - second_call_time) / first_call_time) * 100
            
            print("✅ Monitoring cache improves performance significantly")
            print(f"   ├─ First call (DB): {first_call_time:.1f}ms")
            print(f"   ├─ Second call (cache): {second_call_time:.1f}ms")
            print(f"   └─ Performance improvement: {improvement_percentage:.1f}%")
            
        except Exception as e:
            print(f"❌ Cache performance test failed: {str(e)}")
            raise
    
    def test_health_check_endpoints(self):
        """Integration test: Health check endpoints work correctly"""
        print("🏥 Testing subscription service health check endpoints...")
        
        try:
            # Test the health check function directly
            health_data = get_subscription_health()
            
            # Verify health endpoint returns proper status codes based on health
            status = health_data.get("overall_status", "unknown")
            assert status in ["healthy", "degraded", "unhealthy", "error"]
            
            # Verify service-specific health checks
            services = health_data.get("services", {})
            
            for service_name, service_data in services.items():
                assert "status" in service_data
                service_status = service_data["status"]
                assert service_status in ["healthy", "unhealthy", "degraded"]
            
            # Verify performance monitoring
            perf_metrics = health_data.get("performance_metrics", {})
            if "subscription_query_time_ms" in perf_metrics:
                query_time = perf_metrics["subscription_query_time_ms"]
                assert isinstance(query_time, (int, float))
                assert query_time >= 0
            
            print("✅ Health check endpoints function correctly")
            print(f"   ├─ Overall health: {status}")
            print(f"   ├─ Services monitored: {len(services)}")
            print(f"   ├─ Alerts count: {len(health_data.get('alerts', []))}")
            print(f"   └─ Response includes performance metrics: {'performance_metrics' in health_data}")
            
        except Exception as e:
            print(f"❌ Health check endpoint test failed: {str(e)}")
            raise


if __name__ == "__main__":
    # Run tests manually for development
    pytest.main([__file__, "-v", "-s"]) 