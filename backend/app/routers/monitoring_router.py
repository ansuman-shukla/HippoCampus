from fastapi import APIRouter, HTTPException, Request, Query, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from app.services.subscription_monitoring_service import (
    get_memory_usage_patterns,
    get_summary_generation_trends,
    get_upgrade_conversion_rates,
    get_subscription_health,
    get_comprehensive_monitoring_report
)
from app.services.admin_service import is_admin_user
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/monitoring", 
    tags=["monitoring"],
    responses={
        500: {"description": "Internal server error"}
    }
)

async def require_admin(request: Request) -> dict:
    """
    Dependency to require admin authentication for monitoring endpoints.
    
    Ensures that only authenticated users with admin privileges can access
    monitoring data and metrics.
    
    Args:
        request: FastAPI request object with user authentication state
        
    Returns:
        dict: Admin user information if authorized
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin
    """
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        logger.warning(f"🚫 MONITORING ACCESS: No user_id in request state")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    admin_user = is_admin_user(user_id)
    if not admin_user:
        logger.warning(f"🚫 MONITORING ACCESS: Non-admin user {user_id} attempted to access monitoring")
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logger.info(f"✅ MONITORING ACCESS: Admin user {admin_user.get('email')} accessing monitoring")
    return admin_user

@router.get(
    "/health",
    summary="Subscription Service Health Check",
    description="""
    Get comprehensive health status for subscription services and infrastructure.
    
    This endpoint provides detailed health information including:
    - Database connectivity and performance metrics
    - Subscription service function availability
    - Background job scheduler status
    - Cache performance and hit rates
    - Business metric alerts and warnings
    
    **Health Categories**:
    - **Database**: Connection status, query performance, error rates
    - **Services**: Subscription logic, monitoring cache, background jobs
    - **Performance**: Response times, cache hit rates, query latency
    - **Business**: User metrics, conversion alerts, usage patterns
    
    **Status Levels**:
    - `healthy`: All systems operational
    - `degraded`: Some issues but service available
    - `unhealthy`: Critical issues affecting service
    
    **Public Endpoint**: No authentication required for health checks.
    """,
    responses={
        200: {
            "description": "System is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2024-01-15T10:30:00Z",
                        "overall_status": "healthy",
                        "services": {
                            "database": {
                                "status": "healthy",
                                "connection_test": "passed",
                                "query_time_ms": 15
                            },
                            "subscription_service": {
                                "status": "healthy",
                                "last_check": "2024-01-15T10:29:50Z"
                            },
                            "monitoring_cache": {
                                "status": "healthy",
                                "hit_rate": 95.5,
                                "entries": 42
                            }
                        },
                        "performance_metrics": {
                            "subscription_query_time_ms": 12,
                            "cache_hit_rate": 95.5,
                            "active_users_last_hour": 25
                        },
                        "alerts": []
                    }
                }
            }
        },
        206: {"description": "System is degraded but functional"},
        503: {"description": "System is unhealthy or experiencing critical issues"}
    }
)
async def subscription_service_health():
    """
    Get comprehensive health status for subscription services.
    
    Returns detailed health information about database connectivity, service availability,
    performance metrics, and business alerts.
    """
    logger.info(f"🔍 MONITORING: Health check requested")
    
    try:
        health_data = get_subscription_health()
        
        # Determine HTTP status code based on health
        status_code = 200
        if health_data.get("overall_status") == "unhealthy":
            status_code = 503
        elif health_data.get("overall_status") == "degraded":
            status_code = 206  # Partial Content
        
        logger.info(f"✅ MONITORING: Health check completed - {health_data.get('overall_status')}")
        return JSONResponse(status_code=status_code, content=health_data)
        
    except Exception as e:
        logger.error(f"❌ MONITORING: Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "overall_status": "error",
                "error": str(e),
                "services": {},
                "alerts": [f"Health check system failed: {str(e)}"]
            }
        )

@router.get(
    "/metrics/memory-usage",
    summary="Memory Usage Patterns",
    description="""
    Get detailed memory usage patterns and analytics across user segments.
    
    This endpoint analyzes memory (bookmark) usage patterns including:
    - Usage distribution by subscription tier (Free vs Pro)
    - Users approaching their memory limits
    - Memory usage distribution in buckets (0-25%, 25-50%, etc.)
    - Limit pressure metrics and upgrade triggers
    - Historical usage trends over the specified time period
    
    **Analytics Categories**:
    - **Tier Analysis**: Memory usage patterns by Free vs Pro users
    - **Limit Pressure**: Users at or near their memory limits
    - **Distribution**: Usage spread across different usage levels
    - **Trends**: Memory usage changes over time
    - **Upgrade Signals**: Users showing upgrade potential
    
    **Business Use Cases**:
    - Capacity planning and limit optimization
    - Identifying upgrade conversion opportunities
    - Understanding user engagement with memory features
    - Monitoring system load and usage patterns
    
    **Admin Authentication Required**: User must have admin privileges.
    """,
    responses={
        200: {
            "description": "Successfully retrieved memory usage patterns",
            "content": {
                "application/json": {
                    "example": {
                        "period_analyzed": "30 days",
                        "memory_usage_by_tier": {
                            "free": {
                                "total_users": 1000,
                                "average_memories": 35,
                                "users_near_limit": 45,
                                "limit_pressure_percentage": 4.5
                            },
                            "pro": {
                                "total_users": 150,
                                "average_memories": 250,
                                "unlimited_usage": True
                            }
                        },
                        "usage_distribution": {
                            "0-25%": 650,
                            "25-50%": 220,
                            "50-75%": 85,
                            "75-90%": 30,
                            "90-100%": 15
                        },
                        "upgrade_signals": {
                            "users_at_limit": 15,
                            "users_near_limit": 45,
                            "conversion_potential": "medium"
                        }
                    }
                }
            }
        }
    }
)
async def memory_usage_patterns(
    request: Request,
    days_back: int = Query(30, ge=1, le=365, description="Number of days to analyze (1-365)"),
    admin_user: dict = Depends(require_admin)
):
    """
    Get memory usage patterns across user segments.
    
    Analyzes memory usage patterns with tier-based insights, limit pressure analysis,
    and upgrade conversion signals.
    """
    logger.info(f"📊 MONITORING: Memory usage patterns requested")
    logger.info(f"   ├─ Admin: {admin_user.get('email')}")
    logger.info(f"   └─ Days back: {days_back}")
    
    try:
        patterns = get_memory_usage_patterns(days_back)
        
        logger.info(f"✅ MONITORING: Memory usage patterns retrieved successfully")
        return patterns
        
    except Exception as e:
        logger.error(f"❌ MONITORING: Failed to get memory usage patterns: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve memory usage patterns")

@router.get(
    "/metrics/summary-trends",
    summary="Summary Generation Trends",
    description="""
    Get detailed summary generation trends and utilization analytics.
    
    This endpoint analyzes summary generation patterns including:
    - Summary usage by subscription tier and limits
    - Active vs inactive users in summary generation
    - Peak usage patterns and timing analysis
    - Monthly utilization rates and capacity planning
    - Feature adoption and engagement metrics
    
    **Analytics Categories**:
    - **Tier Utilization**: Summary usage patterns by Free (5/month) vs Pro (100/month) users
    - **User Engagement**: Active summary users vs total registered users
    - **Peak Patterns**: When and how users generate summaries
    - **Capacity Planning**: Monthly limit utilization and overflow patterns
    - **Feature Health**: Summary generation success rates and performance
    
    **Business Use Cases**:
    - Feature adoption and engagement analysis
    - Capacity planning for AI summary generation
    - Understanding usage patterns for limit optimization
    - Identifying power users and upgrade candidates
    - Monitoring AI service performance and costs
    
    **Admin Authentication Required**: User must have admin privileges.
    """,
    responses={
        200: {
            "description": "Successfully retrieved summary generation trends",
            "content": {
                "application/json": {
                    "example": {
                        "period_analyzed": "30 days",
                        "summary_usage_by_tier": {
                            "free": {
                                "total_users": 1000,
                                "active_users": 350,
                                "average_pages_per_user": 3.2,
                                "users_at_limit": 25,
                                "utilization_rate": 64.0
                            },
                            "pro": {
                                "total_users": 150,
                                "active_users": 85,
                                "average_pages_per_user": 28.5,
                                "utilization_rate": 28.5
                            }
                        },
                        "engagement_metrics": {
                            "total_active_users": 435,
                            "activation_rate": 37.8,
                            "repeat_usage_rate": 68.5
                        },
                        "peak_usage_patterns": {
                            "peak_hour": "14:00-15:00 UTC",
                            "peak_day": "Tuesday",
                            "average_pages_per_session": 2.3
                        }
                    }
                }
            }
        }
    }
)
async def summary_generation_trends(
    request: Request,
    days_back: int = Query(30, ge=1, le=365, description="Number of days to analyze (1-365)"),
    admin_user: dict = Depends(require_admin)
):
    """
    Get summary generation trends and utilization rates.
    
    Analyzes summary generation patterns with engagement metrics, utilization rates,
    and feature adoption insights.
    """
    logger.info(f"📈 MONITORING: Summary generation trends requested")
    logger.info(f"   ├─ Admin: {admin_user.get('email')}")
    logger.info(f"   └─ Days back: {days_back}")
    
    try:
        trends = get_summary_generation_trends(days_back)
        
        logger.info(f"✅ MONITORING: Summary generation trends retrieved successfully")
        return trends
        
    except Exception as e:
        logger.error(f"❌ MONITORING: Failed to get summary generation trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve summary generation trends")

@router.get(
    "/metrics/conversion-rates",
    summary="Upgrade Conversion Analytics",
    description="""
    Get comprehensive upgrade conversion rates and user progression analytics.
    
    This endpoint analyzes conversion patterns and revenue opportunities including:
    - Overall Free-to-Pro conversion rates and trends
    - Users near upgrade triggers (memory limits, summary limits)
    - Revenue impact analysis and potential revenue calculations
    - Conversion funnel metrics and drop-off analysis
    - Upgrade timing patterns and seasonal trends
    
    **Analytics Categories**:
    - **Conversion Metrics**: Overall rates, trends, and benchmark comparisons
    - **Trigger Analysis**: Users approaching limits that trigger upgrades
    - **Revenue Analytics**: Current revenue, potential revenue, ARPU calculations
    - **Funnel Analysis**: User journey from Free trial to Pro conversion
    - **Cohort Analysis**: Conversion rates by user cohorts and time periods
    
    **Business Use Cases**:
    - Marketing campaign effectiveness measurement
    - Pricing strategy optimization and limit tuning
    - Revenue forecasting and growth planning
    - User experience optimization for conversion
    - Customer success and retention strategy
    
    **Admin Authentication Required**: User must have admin privileges.
    """,
    responses={
        200: {
            "description": "Successfully retrieved conversion rate analytics",
            "content": {
                "application/json": {
                    "example": {
                        "period_analyzed": "30 days",
                        "conversion_metrics": {
                            "overall_conversion_rate": 12.5,
                            "conversions_this_period": 18,
                            "conversion_trend": "increasing",
                            "benchmark_comparison": "above_average"
                        },
                        "upgrade_triggers": {
                            "users_at_memory_limit": 15,
                            "users_at_summary_limit": 25,
                            "total_near_upgrade": 40,
                            "trigger_conversion_rate": 37.5
                        },
                        "revenue_analytics": {
                            "current_monthly_revenue": 1200.0,
                            "potential_revenue_from_triggers": 320.0,
                            "arpu": 8.0,
                            "ltv_estimate": 96.0
                        },
                        "funnel_metrics": {
                            "free_signups": 145,
                            "feature_activation": 87,
                            "limit_reached": 40,
                            "upgrade_completed": 18
                        }
                    }
                }
            }
        }
    }
)
async def upgrade_conversion_rates(
    request: Request,
    days_back: int = Query(30, ge=1, le=365, description="Number of days to analyze (1-365)"),
    admin_user: dict = Depends(require_admin)
):
    """
    Get upgrade conversion rates and user progression analytics.
    
    Analyzes conversion patterns with trigger analysis, revenue impact assessment,
    and funnel optimization insights.
    """
    logger.info(f"💰 MONITORING: Upgrade conversion rates requested")
    logger.info(f"   ├─ Admin: {admin_user.get('email')}")
    logger.info(f"   └─ Days back: {days_back}")
    
    try:
        conversion_data = get_upgrade_conversion_rates(days_back)
        
        logger.info(f"✅ MONITORING: Upgrade conversion rates retrieved successfully")
        return conversion_data
        
    except Exception as e:
        logger.error(f"❌ MONITORING: Failed to get upgrade conversion rates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve upgrade conversion rates")

@router.get(
    "/metrics/comprehensive",
    summary="Comprehensive Monitoring Report",
    description="""
    Get a comprehensive monitoring report combining all metrics and health data.
    
    This endpoint provides a complete monitoring dashboard including:
    - System health status across all services
    - Memory usage patterns and analysis
    - Summary generation trends and utilization
    - Conversion rate analytics and revenue metrics
    - Executive summary with key insights and recommendations
    - Alert aggregation and prioritization
    
    **Report Sections**:
    - **Health Status**: Overall system health and service availability
    - **Usage Analytics**: Memory and summary usage patterns
    - **Business Metrics**: Conversion rates, revenue, user engagement
    - **Performance Data**: Response times, cache performance, throughput
    - **Executive Summary**: Key insights, trends, and recommendations
    - **Alerts & Actions**: Current alerts with recommended actions
    
    **Business Use Cases**:
    - Executive dashboards and board reporting
    - System operations and reliability monitoring
    - Product strategy and feature planning
    - Customer success and growth analytics
    - Performance optimization and capacity planning
    
    **Admin Authentication Required**: User must have admin privileges.
    """,
    responses={
        200: {
            "description": "Successfully generated comprehensive monitoring report",
            "content": {
                "application/json": {
                    "example": {
                        "report_metadata": {
                            "generated_at": "2024-01-15T10:30:00Z",
                            "period_analyzed": "30 days",
                            "report_version": "1.0"
                        },
                        "health_status": {
                            "overall_status": "healthy",
                            "services_count": 4,
                            "alerts_count": 0
                        },
                        "usage_analytics": {
                            "total_users": 1150,
                            "memory_utilization": 68.5,
                            "summary_utilization": 45.2
                        },
                        "business_metrics": {
                            "conversion_rate": 12.5,
                            "monthly_revenue": 1200.0,
                            "user_growth": 8.3
                        },
                        "executive_summary": {
                            "key_insights": [
                                "Conversion rate increased 15% this month",
                                "Memory usage trending upward - consider capacity",
                                "Summary feature showing strong adoption"
                            ],
                            "recommendations": [
                                "Monitor memory limits for optimization opportunities",
                                "Consider promotional campaign for limit-approaching users"
                            ]
                        }
                    }
                }
            }
        }
    }
)
async def comprehensive_monitoring_report(
    request: Request,
    days_back: int = Query(30, ge=1, le=365, description="Number of days to analyze (1-365)"),
    admin_user: dict = Depends(require_admin)
):
    """
    Get comprehensive monitoring report with all metrics.
    
    Provides a complete monitoring dashboard with health status, usage analytics,
    business metrics, and executive insights.
    """
    logger.info(f"📊 MONITORING: Comprehensive report requested")
    logger.info(f"   ├─ Admin: {admin_user.get('email')}")
    logger.info(f"   └─ Days back: {days_back}")
    
    try:
        report = get_comprehensive_monitoring_report(days_back)
        
        logger.info(f"✅ MONITORING: Comprehensive report generated successfully")
        logger.info(f"   ├─ Health status: {report.get('health_status', {}).get('overall_status', 'unknown')}")
        logger.info(f"   ├─ Total users: {report.get('report_summary', {}).get('total_users', 'unknown')}")
        logger.info(f"   └─ Alerts: {report.get('report_summary', {}).get('alerts_count', 'unknown')}")
        
        return report
        
    except Exception as e:
        logger.error(f"❌ MONITORING: Failed to generate comprehensive report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate comprehensive monitoring report")

@router.get(
    "/dashboard",
    summary="Monitoring Dashboard Data",
    description="""
    Get optimized data for monitoring dashboard display.
    
    This endpoint provides key metrics formatted for dashboard consumption:
    - System health summary with traffic light indicators
    - Key performance indicators (KPIs) and metrics
    - Alert summary with priority levels
    - Quick stats for at-a-glance monitoring
    - Real-time status indicators
    
    **Dashboard Sections**:
    - **Health Summary**: Overall system status and service health
    - **User Metrics**: Total users, conversion rates, growth indicators
    - **Revenue Metrics**: Monthly revenue, potential revenue, trends
    - **Usage Metrics**: Memory pressure, summary utilization, capacity
    - **Performance Metrics**: Response times, cache performance
    - **Alert Summary**: Active alerts with severity levels
    
    **Optimizations**:
    - Fast response times (< 200ms) with cached data
    - Simplified data structure for frontend consumption
    - Real-time indicators for live monitoring
    - Mobile-friendly format for responsive dashboards
    
    **Admin Authentication Required**: User must have admin privileges.
    """,
    responses={
        200: {
            "description": "Successfully retrieved dashboard data",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2024-01-15T10:30:00Z",
                        "health": {
                            "status": "healthy",
                            "alerts_count": 0,
                            "services_healthy": 4
                        },
                        "users": {
                            "total": 1150,
                            "conversion_rate": 12.5,
                            "near_upgrade": 40
                        },
                        "revenue": {
                            "monthly": 1200.0,
                            "potential": 320.0
                        },
                        "usage": {
                            "memory_pressure": 4.5,
                            "summary_utilization": 45.2
                        },
                        "performance": {
                            "avg_query_time": 12,
                            "cache_status": "healthy"
                        }
                    }
                }
            }
        }
    }
)
async def monitoring_dashboard_data(
    request: Request,
    admin_user: dict = Depends(require_admin)
):
    """
    Get summarized data for monitoring dashboard display.
    
    Provides key metrics optimized for dashboard display with fast response times
    and simplified data structure.
    """
    logger.info(f"📱 MONITORING: Dashboard data requested")
    logger.info(f"   └─ Admin: {admin_user.get('email')}")
    
    try:
        # Get comprehensive report with 7 days for dashboard (recent data)
        report = get_comprehensive_monitoring_report(7)
        
        # Extract dashboard-friendly data
        dashboard_data = {
            "timestamp": datetime.now(timezone.utc),
            "health": {
                "status": report.get("health_status", {}).get("overall_status", "unknown"),
                "alerts_count": len(report.get("health_status", {}).get("alerts", [])),
                "services_healthy": sum(1 for service in report.get("health_status", {}).get("services", {}).values() 
                                      if service.get("status") == "healthy")
            },
            "users": {
                "total": report.get("report_summary", {}).get("total_users", 0),
                "conversion_rate": report.get("report_summary", {}).get("conversion_rate", 0),
                "near_upgrade": report.get("report_summary", {}).get("users_near_upgrade", 0)
            },
            "revenue": {
                "monthly": report.get("report_summary", {}).get("monthly_revenue", 0),
                "potential": report.get("upgrade_conversion_rates", {}).get("revenue_analytics", {}).get("potential_revenue_from_triggers", 0)
            },
            "usage": {
                "memory_pressure": report.get("report_summary", {}).get("memory_limit_pressure", 0),
                "summary_utilization": report.get("report_summary", {}).get("summary_utilization", 0)
            },
            "performance": {
                "avg_query_time": report.get("health_status", {}).get("performance_metrics", {}).get("subscription_query_time_ms", 0),
                "cache_status": report.get("health_status", {}).get("services", {}).get("monitoring_cache", {}).get("status", "unknown")
            }
        }
        
        logger.info(f"✅ MONITORING: Dashboard data prepared successfully")
        logger.info(f"   ├─ Health: {dashboard_data['health']['status']}")
        logger.info(f"   ├─ Users: {dashboard_data['users']['total']}")
        logger.info(f"   └─ Alerts: {dashboard_data['health']['alerts_count']}")
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"❌ MONITORING: Failed to prepare dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to prepare dashboard data")

@router.get(
    "/alerts",
    summary="Active System Alerts",
    description="""
    Get current active alerts and system warnings with priority analysis.
    
    This endpoint provides detailed alert information including:
    - Active alerts with severity levels and categories
    - System warnings and performance issues
    - Business metric alerts (conversion drops, usage spikes)
    - Recommended actions and troubleshooting steps
    - Alert history and trend analysis
    
    **Alert Categories**:
    - **Database**: Connection issues, query performance, storage alerts
    - **Performance**: Slow response times, cache misses, timeout errors
    - **Business**: Conversion drops, usage anomalies, revenue impacts
    - **System**: Service failures, background job issues, capacity alerts
    
    **Severity Levels**:
    - **High**: Critical issues requiring immediate attention
    - **Medium**: Important issues that should be addressed soon
    - **Low**: Informational alerts for monitoring trends
    
    **Admin Authentication Required**: User must have admin privileges.
    """,
    responses={
        200: {
            "description": "Successfully retrieved active alerts",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2024-01-15T10:30:00Z",
                        "total_alerts": 2,
                        "system_status": "degraded",
                        "alerts": [
                            {
                                "message": "Database query performance degraded",
                                "severity": "medium",
                                "category": "performance"
                            },
                            {
                                "message": "15 users approaching memory limit",
                                "severity": "low",
                                "category": "business"
                            }
                        ],
                        "recommendations": [
                            "Consider optimizing database queries or adding indexes",
                            "Review user engagement and subscription conversion strategies"
                        ]
                    }
                }
            }
        }
    }
)
async def active_alerts(
    request: Request,
    admin_user: dict = Depends(require_admin)
):
    """
    Get current active alerts and warnings.
    
    Returns detailed alert information with severity levels, categories,
    and recommended actions for resolution.
    """
    logger.info(f"🚨 MONITORING: Active alerts requested")
    logger.info(f"   └─ Admin: {admin_user.get('email')}")
    
    try:
        health_data = get_subscription_health()
        alerts = health_data.get("alerts", [])
        
        alert_summary = {
            "timestamp": datetime.now(timezone.utc),
            "total_alerts": len(alerts),
            "system_status": health_data.get("overall_status", "unknown"),
            "alerts": [
                {
                    "message": alert,
                    "severity": "high" if "failed" in alert.lower() or "error" in alert.lower() else "medium",
                    "category": "database" if "database" in alert.lower() else 
                               "performance" if "slow" in alert.lower() or "performance" in alert.lower() else
                               "business" if "users" in alert.lower() else "system"
                }
                for alert in alerts
            ],
            "recommendations": []
        }
        
        # Add recommendations based on alerts
        if any("slow" in alert.lower() for alert in alerts):
            alert_summary["recommendations"].append("Consider optimizing database queries or adding indexes")
        
        if any("users" in alert.lower() for alert in alerts):
            alert_summary["recommendations"].append("Review user engagement and subscription conversion strategies")
        
        if any("failed" in alert.lower() for alert in alerts):
            alert_summary["recommendations"].append("Immediate attention required for system reliability")
        
        logger.info(f"✅ MONITORING: Active alerts retrieved - {len(alerts)} alerts found")
        return alert_summary
        
    except Exception as e:
        logger.error(f"❌ MONITORING: Failed to get active alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve active alerts")

@router.post(
    "/cache/clear",
    summary="Clear Monitoring Cache",
    description="""
    Clear monitoring metrics cache to force fresh data collection.
    
    This endpoint allows admins to:
    - Clear cached monitoring data to force refresh
    - Reset metrics collection for troubleshooting
    - Ensure fresh data after system changes
    - Improve accuracy of real-time monitoring
    
    **Use Cases**:
    - Troubleshooting stale or incorrect metrics
    - Forcing data refresh after system updates
    - Testing monitoring system functionality
    - Performance troubleshooting and optimization
    
    **Impact**:
    - Next monitoring requests will rebuild cache
    - Temporary performance impact until cache rebuilds
    - Ensures fresh and accurate metrics collection
    - All cached metrics data will be regenerated
    
    **Admin Authentication Required**: User must have admin privileges.
    """,
    responses={
        200: {
            "description": "Successfully cleared monitoring cache",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2024-01-15T10:30:00Z",
                        "status": "success",
                        "message": "Monitoring cache cleared successfully",
                        "cache_entries_cleared": 42,
                        "admin_user": "admin@hippocampus.ai"
                    }
                }
            }
        }
    }
)
async def clear_monitoring_cache(
    request: Request,
    admin_user: dict = Depends(require_admin)
):
    """
    Clear monitoring metrics cache to force fresh data collection.
    
    Clears all cached monitoring data and forces regeneration on next request.
    Useful for troubleshooting and ensuring fresh metrics.
    """
    logger.info(f"🧹 MONITORING: Cache clear requested")
    logger.info(f"   └─ Admin: {admin_user.get('email')}")
    
    try:
        # Access the global monitoring service instance to clear cache
        from app.services.subscription_monitoring_service import monitoring_service
        
        cache_size_before = len(monitoring_service._metrics_cache)
        monitoring_service._metrics_cache.clear()
        monitoring_service._last_cache_update.clear()
        
        result = {
            "timestamp": datetime.now(timezone.utc),
            "status": "success",
            "message": "Monitoring cache cleared successfully",
            "cache_entries_cleared": cache_size_before,
            "admin_user": admin_user.get("email")
        }
        
        logger.info(f"✅ MONITORING: Cache cleared successfully - {cache_size_before} entries removed")
        return result
        
    except Exception as e:
        logger.error(f"❌ MONITORING: Failed to clear cache: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear monitoring cache") 