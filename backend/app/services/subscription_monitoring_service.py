from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import logging
import math

from app.core.database import collection
from app.services.subscription_service import TIER_LIMITS, get_user_subscription
from app.services.subscription_logging_service import subscription_logger
import json
import time

logger = logging.getLogger(__name__)

class SubscriptionMonitoringService:
    """
    Service for monitoring subscription-related metrics and health status.
    
    This service tracks:
    - Memory usage patterns across user segments
    - Summary generation trends and peak times
    - Upgrade conversion rates and user behavior
    - Subscription service health checks and performance metrics
    """
    
    def __init__(self):
        self.logger = logger
        self._metrics_cache = {}
        self._cache_ttl = 300  # 5 minutes cache TTL for performance
        self._last_cache_update = {}
        
    def _is_cache_valid(self, metric_key: str) -> bool:
        """Check if cached metric is still valid"""
        last_update = self._last_cache_update.get(metric_key, 0)
        return (time.time() - last_update) < self._cache_ttl
    
    def _cache_metric(self, metric_key: str, data: Any) -> None:
        """Cache metric data with timestamp"""
        self._metrics_cache[metric_key] = data
        self._last_cache_update[metric_key] = time.time()
    
    def track_memory_usage_patterns(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Track memory usage patterns across different user segments.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            dict: Memory usage patterns and analytics
        """
        cache_key = f"memory_patterns_{days_back}"
        if self._is_cache_valid(cache_key):
            return self._metrics_cache[cache_key]
            
        self.logger.info(f"📊 MONITORING: Analyzing memory usage patterns for last {days_back} days")
        
        try:
            # Get cutoff date
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            # Aggregate memory usage by tier
            pipeline = [
                {
                    "$group": {
                        "_id": "$subscription_tier",
                        "total_users": {"$sum": 1},
                        "total_memories": {"$sum": "$total_memories_saved"},
                        "avg_memories_per_user": {"$avg": "$total_memories_saved"},
                        "max_memories": {"$max": "$total_memories_saved"},
                        "min_memories": {"$min": "$total_memories_saved"},
                        "users_at_limit": {
                            "$sum": {
                                "$cond": [
                                    {
                                        "$and": [
                                            {"$eq": ["$subscription_tier", "free"]},
                                            {"$gte": ["$total_memories_saved", 100]}
                                        ]
                                    },
                                    1,
                                    0
                                ]
                            }
                        }
                    }
                }
            ]
            
            memory_stats = list(collection.aggregate(pipeline))
            
            # Calculate usage patterns
            patterns = {
                "analysis_period_days": days_back,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tiers": {},
                "overall": {
                    "total_users": 0,
                    "total_memories": 0,
                    "avg_memories_per_user": 0,
                    "limit_pressure": 0  # Percentage of free users at or near limit
                }
            }
            
            for tier_data in memory_stats:
                tier = tier_data["_id"] or "free"
                tier_info = {
                    "total_users": tier_data["total_users"],
                    "total_memories": tier_data["total_memories"],
                    "avg_memories_per_user": round(tier_data["avg_memories_per_user"], 2),
                    "max_memories": tier_data["max_memories"],
                    "min_memories": tier_data["min_memories"],
                    "users_at_limit": tier_data["users_at_limit"]
                }
                
                # Calculate tier-specific metrics
                if tier == "free":
                    limit_pressure = (tier_data["users_at_limit"] / tier_data["total_users"]) * 100 if tier_data["total_users"] > 0 else 0
                    tier_info["limit_pressure_percentage"] = round(limit_pressure, 2)
                    tier_info["limit"] = TIER_LIMITS["free"]["memories"]
                    tier_info["usage_percentage"] = round((tier_data["avg_memories_per_user"] / TIER_LIMITS["free"]["memories"]) * 100, 2)
                    patterns["overall"]["limit_pressure"] = limit_pressure
                else:
                    tier_info["limit"] = "unlimited"
                    tier_info["usage_percentage"] = "N/A"
                
                patterns["tiers"][tier] = tier_info
                
                # Update overall stats
                patterns["overall"]["total_users"] += tier_data["total_users"]
                patterns["overall"]["total_memories"] += tier_data["total_memories"]
            
            # Calculate overall average
            if patterns["overall"]["total_users"] > 0:
                patterns["overall"]["avg_memories_per_user"] = round(
                    patterns["overall"]["total_memories"] / patterns["overall"]["total_users"], 2
                )
            
            # Add usage distribution analysis
            distribution_pipeline = [
                {
                    "$match": {"subscription_tier": "free"}
                },
                {
                    "$bucket": {
                        "groupBy": "$total_memories_saved",
                        "boundaries": [0, 20, 40, 60, 80, 100, float("inf")],
                        "default": "100+",
                        "output": {
                            "count": {"$sum": 1},
                            "avg_memories": {"$avg": "$total_memories_saved"}
                        }
                    }
                }
            ]
            
            distribution_data = list(collection.aggregate(distribution_pipeline))
            usage_buckets = {}
            
            bucket_labels = ["0-19", "20-39", "40-59", "60-79", "80-99", "100+"]
            for i, bucket in enumerate(distribution_data):
                label = bucket_labels[i] if i < len(bucket_labels) else str(bucket["_id"])
                usage_buckets[label] = {
                    "user_count": bucket["count"],
                    "avg_memories": round(bucket["avg_memories"], 2)
                }
            
            patterns["free_user_distribution"] = usage_buckets
            
            self.logger.info(f"✅ Memory usage patterns analyzed successfully")
            self.logger.info(f"   ├─ Free users: {patterns['tiers'].get('free', {}).get('total_users', 0)}")
            self.logger.info(f"   ├─ Pro users: {patterns['tiers'].get('pro', {}).get('total_users', 0)}")
            self.logger.info(f"   └─ Limit pressure: {patterns['overall']['limit_pressure']:.1f}%")
            
            self._cache_metric(cache_key, patterns)
            return patterns
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing memory usage patterns: {str(e)}")
            raise
    
    def monitor_summary_generation_trends(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Monitor summary generation trends and peak usage times.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            dict: Summary generation trends and analytics
        """
        cache_key = f"summary_trends_{days_back}"
        if self._is_cache_valid(cache_key):
            return self._metrics_cache[cache_key]
            
        self.logger.info(f"📈 MONITORING: Analyzing summary generation trends for last {days_back} days")
        
        try:
            # Get summary usage by tier
            pipeline = [
                {
                    "$group": {
                        "_id": "$subscription_tier",
                        "total_users": {"$sum": 1},
                        "total_summary_pages": {"$sum": "$monthly_summary_pages_used"},
                        "avg_pages_per_user": {"$avg": "$monthly_summary_pages_used"},
                        "max_pages": {"$max": "$monthly_summary_pages_used"},
                        "users_at_limit": {
                            "$sum": {
                                "$cond": [
                                    {
                                        "$and": [
                                            {"$eq": ["$subscription_tier", "free"]},
                                            {"$gte": ["$monthly_summary_pages_used", 5]}
                                        ]
                                    },
                                    1,
                                    0
                                ]
                            }
                        },
                        "active_users": {
                            "$sum": {
                                "$cond": [
                                    {"$gt": ["$monthly_summary_pages_used", 0]},
                                    1,
                                    0
                                ]
                            }
                        }
                    }
                }
            ]
            
            summary_stats = list(collection.aggregate(pipeline))
            
            trends = {
                "analysis_period_days": days_back,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tiers": {},
                "overall": {
                    "total_users": 0,
                    "active_users": 0,
                    "total_pages_generated": 0,
                    "avg_pages_per_user": 0,
                    "utilization_rate": 0
                }
            }
            
            total_active_users = 0
            total_pages = 0
            total_users = 0
            
            for tier_data in summary_stats:
                tier = tier_data["_id"] or "free"
                active_users = tier_data["active_users"]
                total_users_tier = tier_data["total_users"]
                
                tier_info = {
                    "total_users": total_users_tier,
                    "active_users": active_users,
                    "utilization_rate": round((active_users / total_users_tier) * 100, 2) if total_users_tier > 0 else 0,
                    "total_pages_generated": tier_data["total_summary_pages"],
                    "avg_pages_per_user": round(tier_data["avg_pages_per_user"], 2),
                    "avg_pages_per_active_user": round(tier_data["total_summary_pages"] / active_users, 2) if active_users > 0 else 0,
                    "max_pages": tier_data["max_pages"],
                    "users_at_limit": tier_data["users_at_limit"]
                }
                
                # Calculate tier-specific metrics
                if tier == "free":
                    limit = TIER_LIMITS["free"]["monthly_summary_pages"]
                    tier_info["limit"] = limit
                    tier_info["avg_usage_percentage"] = round((tier_data["avg_pages_per_user"] / limit) * 100, 2)
                    tier_info["limit_pressure_percentage"] = round((tier_data["users_at_limit"] / total_users_tier) * 100, 2) if total_users_tier > 0 else 0
                else:
                    tier_info["limit"] = TIER_LIMITS["pro"]["monthly_summary_pages"]
                    tier_info["avg_usage_percentage"] = round((tier_data["avg_pages_per_user"] / TIER_LIMITS["pro"]["monthly_summary_pages"]) * 100, 2)
                
                trends["tiers"][tier] = tier_info
                
                # Update overall stats
                total_active_users += active_users
                total_pages += tier_data["total_summary_pages"]
                total_users += total_users_tier
            
            # Calculate overall metrics
            trends["overall"]["total_users"] = total_users
            trends["overall"]["active_users"] = total_active_users
            trends["overall"]["total_pages_generated"] = total_pages
            trends["overall"]["utilization_rate"] = round((total_active_users / total_users) * 100, 2) if total_users > 0 else 0
            trends["overall"]["avg_pages_per_user"] = round(total_pages / total_users, 2) if total_users > 0 else 0
            trends["overall"]["avg_pages_per_active_user"] = round(total_pages / total_active_users, 2) if total_active_users > 0 else 0
            
            # Add usage distribution for free users
            distribution_pipeline = [
                {
                    "$match": {"subscription_tier": "free"}
                },
                {
                    "$bucket": {
                        "groupBy": "$monthly_summary_pages_used",
                        "boundaries": [0, 1, 2, 3, 4, 5, float("inf")],
                        "default": "5+",
                        "output": {
                            "count": {"$sum": 1},
                            "avg_pages": {"$avg": "$monthly_summary_pages_used"}
                        }
                    }
                }
            ]
            
            distribution_data = list(collection.aggregate(distribution_pipeline))
            page_buckets = {}
            
            bucket_labels = ["0", "1", "2", "3", "4", "5+"]
            for i, bucket in enumerate(distribution_data):
                label = bucket_labels[i] if i < len(bucket_labels) else str(bucket["_id"])
                page_buckets[label] = {
                    "user_count": bucket["count"],
                    "avg_pages": round(bucket["avg_pages"], 2)
                }
            
            trends["free_user_page_distribution"] = page_buckets
            
            self.logger.info(f"✅ Summary generation trends analyzed successfully")
            self.logger.info(f"   ├─ Total users: {total_users}")
            self.logger.info(f"   ├─ Active users: {total_active_users}")
            self.logger.info(f"   ├─ Utilization rate: {trends['overall']['utilization_rate']:.1f}%")
            self.logger.info(f"   └─ Avg pages/user: {trends['overall']['avg_pages_per_user']}")
            
            self._cache_metric(cache_key, trends)
            return trends
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing summary generation trends: {str(e)}")
            raise
    
    def track_upgrade_conversion_rates(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Track upgrade conversion rates and user progression patterns.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            dict: Conversion rates and upgrade analytics
        """
        cache_key = f"conversion_rates_{days_back}"
        if self._is_cache_valid(cache_key):
            return self._metrics_cache[cache_key]
            
        self.logger.info(f"💰 MONITORING: Analyzing upgrade conversion rates for last {days_back} days")
        
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            # Get basic user counts
            total_users = collection.count_documents({})
            free_users = collection.count_documents({"subscription_tier": "free"})
            pro_users = collection.count_documents({"subscription_tier": "pro"})
            active_pro = collection.count_documents({"subscription_tier": "pro", "subscription_status": "active"})
            
            # Analyze conversion triggers (users near limits)
            near_memory_limit = collection.count_documents({
                "subscription_tier": "free",
                "total_memories_saved": {"$gte": 80}  # 80+ out of 100
            })
            
            at_memory_limit = collection.count_documents({
                "subscription_tier": "free", 
                "total_memories_saved": {"$gte": 100}
            })
            
            near_summary_limit = collection.count_documents({
                "subscription_tier": "free",
                "monthly_summary_pages_used": {"$gte": 4}  # 4+ out of 5
            })
            
            at_summary_limit = collection.count_documents({
                "subscription_tier": "free",
                "monthly_summary_pages_used": {"$gte": 5}
            })
            
            # Calculate churn analysis
            expired_pro = collection.count_documents({
                "subscription_tier": "pro",
                "subscription_status": {"$in": ["expired", "cancelled"]}
            })
            
            # Recent upgrade analysis (users who upgraded recently)
            recent_upgrades = collection.count_documents({
                "subscription_tier": "pro",
                "subscription_start_date": {"$gte": cutoff_date}
            })
            
            conversion_data = {
                "analysis_period_days": days_back,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_segments": {
                    "total_users": total_users,
                    "free_users": free_users,
                    "pro_users": pro_users,
                    "active_pro_users": active_pro,
                    "expired_pro_users": expired_pro
                },
                "conversion_metrics": {
                    "overall_conversion_rate": round((pro_users / total_users) * 100, 2) if total_users > 0 else 0,
                    "pro_retention_rate": round((active_pro / pro_users) * 100, 2) if pro_users > 0 else 0,
                    "recent_upgrades": recent_upgrades,
                    "monthly_upgrade_rate": round((recent_upgrades / free_users) * 100, 2) if free_users > 0 else 0
                },
                "conversion_triggers": {
                    "near_memory_limit": {
                        "count": near_memory_limit,
                        "percentage_of_free": round((near_memory_limit / free_users) * 100, 2) if free_users > 0 else 0,
                        "threshold": "80-99 memories saved"
                    },
                    "at_memory_limit": {
                        "count": at_memory_limit,
                        "percentage_of_free": round((at_memory_limit / free_users) * 100, 2) if free_users > 0 else 0,
                        "threshold": "100+ memories saved"
                    },
                    "near_summary_limit": {
                        "count": near_summary_limit,
                        "percentage_of_free": round((near_summary_limit / free_users) * 100, 2) if free_users > 0 else 0,
                        "threshold": "4+ summary pages used"
                    },
                    "at_summary_limit": {
                        "count": at_summary_limit,
                        "percentage_of_free": round((at_summary_limit / free_users) * 100, 2) if free_users > 0 else 0,
                        "threshold": "5+ summary pages used"
                    }
                },
                "revenue_analytics": {
                    "monthly_recurring_revenue": active_pro * 8,  # $8/month per Pro user
                    "annual_recurring_revenue": active_pro * 8 * 12,
                    "potential_revenue_from_triggers": (near_memory_limit + near_summary_limit) * 8,
                    "churn_impact": expired_pro * 8
                }
            }
            
            # Calculate conversion funnel stages
            conversion_data["conversion_funnel"] = {
                "stage_1_users": free_users,  # All free users
                "stage_2_near_limit": near_memory_limit + near_summary_limit,  # Users approaching limits
                "stage_3_at_limit": at_memory_limit + at_summary_limit,  # Users hitting limits
                "stage_4_converted": recent_upgrades,  # Recent conversions
                "funnel_rates": {
                    "approach_to_limit": round(((near_memory_limit + near_summary_limit) / free_users) * 100, 2) if free_users > 0 else 0,
                    "hit_limit": round(((at_memory_limit + at_summary_limit) / free_users) * 100, 2) if free_users > 0 else 0,
                    "limit_to_conversion": round((recent_upgrades / max(at_memory_limit + at_summary_limit, 1)) * 100, 2)
                }
            }
            
            self.logger.info(f"✅ Conversion rates analyzed successfully")
            self.logger.info(f"   ├─ Overall conversion: {conversion_data['conversion_metrics']['overall_conversion_rate']:.1f}%")
            self.logger.info(f"   ├─ Recent upgrades: {recent_upgrades}")
            self.logger.info(f"   ├─ Users near limits: {near_memory_limit + near_summary_limit}")
            self.logger.info(f"   └─ MRR: ${conversion_data['revenue_analytics']['monthly_recurring_revenue']}")
            
            self._cache_metric(cache_key, conversion_data)
            return conversion_data
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing conversion rates: {str(e)}")
            raise
    
    def get_subscription_service_health(self) -> Dict[str, Any]:
        """
        Get comprehensive health status for subscription services.
        
        Returns:
            dict: Health status of all subscription-related services
        """
        self.logger.info(f"🔍 MONITORING: Checking subscription service health")
        
        try:
            health_status = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "overall_status": "healthy",
                "services": {},
                "performance_metrics": {},
                "alerts": []
            }
            
            # 1. Database health for subscription operations
            try:
                # Test subscription data access
                test_query = collection.find_one({"subscription_tier": {"$exists": True}})
                db_response_time = time.time()
                collection.count_documents({"subscription_tier": "free"})
                db_response_time = (time.time() - db_response_time) * 1000  # Convert to ms
                
                health_status["services"]["database"] = {
                    "status": "healthy",
                    "response_time_ms": round(db_response_time, 2),
                    "subscription_data_accessible": bool(test_query)
                }
                
            except Exception as e:
                health_status["services"]["database"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall_status"] = "degraded"
                health_status["alerts"].append(f"Database subscription access failed: {str(e)}")
            
            # 2. Subscription service functions health
            try:
                # Test core subscription functions
                test_user_data = get_user_subscription("health_check_test")  # Will return None for non-existent user
                
                health_status["services"]["subscription_service"] = {
                    "status": "healthy",
                    "core_functions_accessible": True,
                    "tier_limits_configured": bool(TIER_LIMITS)
                }
                
            except Exception as e:
                health_status["services"]["subscription_service"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall_status"] = "degraded"
                health_status["alerts"].append(f"Subscription service functions failed: {str(e)}")
            
            # 3. Monitoring cache health
            try:
                cache_size = len(self._metrics_cache)
                cache_age = time.time() - min(self._last_cache_update.values()) if self._last_cache_update else 0
                
                health_status["services"]["monitoring_cache"] = {
                    "status": "healthy",
                    "cached_metrics": cache_size,
                    "oldest_cache_age_seconds": round(cache_age, 2),
                    "cache_ttl_seconds": self._cache_ttl
                }
                
            except Exception as e:
                health_status["services"]["monitoring_cache"] = {
                    "status": "degraded",
                    "error": str(e)
                }
                health_status["alerts"].append(f"Monitoring cache issue: {str(e)}")
            
            # 4. Performance metrics
            try:
                # Quick performance test
                start_time = time.time()
                user_count = collection.count_documents({"subscription_tier": {"$exists": True}})
                query_time = (time.time() - start_time) * 1000
                
                health_status["performance_metrics"] = {
                    "subscription_query_time_ms": round(query_time, 2),
                    "total_subscription_users": user_count,
                    "performance_status": "good" if query_time < 100 else "slow" if query_time < 1000 else "poor"
                }
                
                if query_time > 500:
                    health_status["alerts"].append(f"Slow subscription query performance: {query_time:.1f}ms")
                    if health_status["overall_status"] == "healthy":
                        health_status["overall_status"] = "degraded"
                
            except Exception as e:
                health_status["performance_metrics"] = {
                    "error": str(e)
                }
                health_status["alerts"].append(f"Performance metrics collection failed: {str(e)}")
            
            # 5. Business metrics health
            try:
                free_users = collection.count_documents({"subscription_tier": "free"})
                pro_users = collection.count_documents({"subscription_tier": "pro"})
                
                health_status["business_metrics"] = {
                    "total_users": free_users + pro_users,
                    "free_users": free_users,
                    "pro_users": pro_users,
                    "conversion_rate": round((pro_users / (free_users + pro_users)) * 100, 2) if (free_users + pro_users) > 0 else 0
                }
                
                # Business health checks
                if free_users + pro_users == 0:
                    health_status["alerts"].append("No users found in subscription system")
                    health_status["overall_status"] = "unhealthy"
                
            except Exception as e:
                health_status["business_metrics"] = {
                    "error": str(e)
                }
                health_status["alerts"].append(f"Business metrics collection failed: {str(e)}")
            
            self.logger.info(f"✅ Subscription service health check completed")
            self.logger.info(f"   ├─ Overall status: {health_status['overall_status']}")
            self.logger.info(f"   ├─ Services checked: {len(health_status['services'])}")
            self.logger.info(f"   └─ Alerts: {len(health_status['alerts'])}")
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"❌ Error checking subscription service health: {str(e)}")
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "overall_status": "error",
                "error": str(e),
                "services": {},
                "alerts": [f"Health check system failed: {str(e)}"]
            }
    
    def get_comprehensive_metrics(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Get all monitoring metrics in a single comprehensive report.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            dict: Comprehensive monitoring report
        """
        self.logger.info(f"📊 MONITORING: Generating comprehensive metrics report")
        
        try:
            comprehensive_report = {
                "report_timestamp": datetime.now(timezone.utc).isoformat(),
                "analysis_period_days": days_back,
                "health_status": self.get_subscription_service_health(),
                "memory_usage_patterns": self.track_memory_usage_patterns(days_back),
                "summary_generation_trends": self.monitor_summary_generation_trends(days_back),
                "upgrade_conversion_rates": self.track_upgrade_conversion_rates(days_back),
                "report_summary": {}
            }
            
            # Generate executive summary
            try:
                health = comprehensive_report["health_status"]
                memory = comprehensive_report["memory_usage_patterns"]
                summary = comprehensive_report["summary_generation_trends"]
                conversion = comprehensive_report["upgrade_conversion_rates"]
                
                summary_data = {
                    "system_health": health["overall_status"],
                    "total_users": memory["overall"]["total_users"],
                    "conversion_rate": conversion["conversion_metrics"]["overall_conversion_rate"],
                    "memory_limit_pressure": memory["overall"]["limit_pressure"],
                    "summary_utilization": summary["overall"]["utilization_rate"],
                    "monthly_revenue": conversion["revenue_analytics"]["monthly_recurring_revenue"],
                    "users_near_upgrade": (
                        conversion["conversion_triggers"]["near_memory_limit"]["count"] +
                        conversion["conversion_triggers"]["near_summary_limit"]["count"]
                    ),
                    "alerts_count": len(health["alerts"])
                }
                
                comprehensive_report["report_summary"] = summary_data
                
            except Exception as e:
                self.logger.warning(f"⚠️ Error generating report summary: {str(e)}")
                comprehensive_report["report_summary"] = {"error": str(e)}
            
            self.logger.info(f"✅ Comprehensive metrics report generated successfully")
            return comprehensive_report
            
        except Exception as e:
            self.logger.error(f"❌ Error generating comprehensive metrics report: {str(e)}")
            raise

# Global monitoring service instance
monitoring_service = SubscriptionMonitoringService()

# Convenience functions for external access
def get_memory_usage_patterns(days_back: int = 30) -> Dict[str, Any]:
    """Get memory usage patterns"""
    return monitoring_service.track_memory_usage_patterns(days_back)

def get_summary_generation_trends(days_back: int = 30) -> Dict[str, Any]:
    """Get summary generation trends"""
    return monitoring_service.monitor_summary_generation_trends(days_back)

def get_upgrade_conversion_rates(days_back: int = 30) -> Dict[str, Any]:
    """Get upgrade conversion rates"""
    return monitoring_service.track_upgrade_conversion_rates(days_back)

def get_subscription_health() -> Dict[str, Any]:
    """Get subscription service health"""
    return monitoring_service.get_subscription_service_health()

def get_comprehensive_monitoring_report(days_back: int = 30) -> Dict[str, Any]:
    """Get comprehensive monitoring report"""
    return monitoring_service.get_comprehensive_metrics(days_back) 