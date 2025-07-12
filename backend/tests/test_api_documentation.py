"""
Tests for API documentation functionality and completeness.

This module tests:
- All endpoints are properly documented
- Documentation examples work correctly
- API documentation matches actual implementation
- FastAPI OpenAPI schema generation
"""

import pytest
import requests
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from app.main import app

client = TestClient(app)

class TestAPIDocumentationStructure:
    """Test that FastAPI documentation is properly configured and accessible."""
    
    def test_swagger_ui_accessible(self):
        """Test that Swagger UI documentation is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()
        assert "HippoCampus API" in response.text
    
    def test_redoc_accessible(self):
        """Test that ReDoc documentation is accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower()
        assert "HippoCampus API" in response.text
    
    def test_openapi_json_schema(self):
        """Test that OpenAPI JSON schema is accessible and valid."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        
        # Verify basic OpenAPI structure
        assert "openapi" in openapi_spec
        assert "info" in openapi_spec
        assert "paths" in openapi_spec
        assert "components" in openapi_spec
        
        # Verify API metadata
        info = openapi_spec["info"]
        assert info["title"] == "HippoCampus API"
        assert info["version"] == "1.0.0"
        assert "description" in info
        assert "contact" in info
        assert "license" in info
        
        # Verify servers configuration
        assert "servers" in openapi_spec
        servers = openapi_spec["servers"]
        assert len(servers) >= 2  # Production and development servers
        
        server_urls = [server["url"] for server in servers]
        assert "https://hippocampus-backend.onrender.com" in server_urls
        assert "http://localhost:8000" in server_urls

class TestEndpointsDocumentation:
    """Test that all key endpoints are properly documented."""
    
    def test_subscription_endpoints_documented(self):
        """Test that all subscription endpoints are documented in OpenAPI spec."""
        response = client.get("/openapi.json")
        openapi_spec = response.json()
        paths = openapi_spec["paths"]
        
        # Check key subscription endpoints are documented
        expected_endpoints = [
            "/subscription/status",
            "/subscription/upgrade", 
            "/subscription/usage",
            "/subscription/downgrade"
        ]
        
        for endpoint in expected_endpoints:
            assert endpoint in paths, f"Endpoint {endpoint} not found in OpenAPI spec"
            endpoint_spec = paths[endpoint]
            for method in endpoint_spec:
                method_spec = endpoint_spec[method]
                assert "summary" in method_spec, f"{endpoint} {method} missing summary"
                assert "description" in method_spec, f"{endpoint} {method} missing description"
                assert "responses" in method_spec, f"{endpoint} {method} missing responses"
    
    def test_admin_endpoints_documented(self):
        """Test that admin endpoints are properly documented."""
        response = client.get("/openapi.json")
        openapi_spec = response.json()
        paths = openapi_spec["paths"]
        
        # Check key admin endpoints are documented
        admin_endpoints = ["/admin/users", "/admin/analytics"]
        
        for endpoint in admin_endpoints:
            assert endpoint in paths, f"Admin endpoint {endpoint} not found in OpenAPI spec"
            endpoint_spec = paths[endpoint]
            for method in endpoint_spec:
                method_spec = endpoint_spec[method]
                assert "summary" in method_spec
                assert "description" in method_spec
                assert "responses" in method_spec
    
    def test_monitoring_endpoints_documented(self):
        """Test that monitoring endpoints are properly documented."""
        response = client.get("/openapi.json")
        openapi_spec = response.json()
        paths = openapi_spec["paths"]
        
        # Check key monitoring endpoints are documented
        monitoring_endpoints = ["/monitoring/health", "/monitoring/dashboard"]
        
        for endpoint in monitoring_endpoints:
            assert endpoint in paths, f"Monitoring endpoint {endpoint} not found in OpenAPI spec"
            endpoint_spec = paths[endpoint]
            for method in endpoint_spec:
                method_spec = endpoint_spec[method]
                assert "summary" in method_spec
                assert "description" in method_spec
                assert "responses" in method_spec

class TestDocumentationExamples:
    """Test that documentation examples are valid and work correctly."""
    
    def test_schema_components_defined(self):
        """Test that all schema components are properly defined."""
        response = client.get("/openapi.json")
        openapi_spec = response.json()
        
        # Verify components section exists and has schemas
        assert "components" in openapi_spec
        components = openapi_spec["components"]
        assert "schemas" in components
        
        schemas = components["schemas"]
        
        # Check for key schema definitions
        expected_schemas = [
            "SubscriptionStatus",
            "SubscriptionUpgrade", 
            "UsageResponse"
        ]
        
        for schema_name in expected_schemas:
            assert schema_name in schemas, f"Schema {schema_name} not found in components"
            
            # Verify schema has properties
            schema = schemas[schema_name]
            assert "properties" in schema or "type" in schema, \
                f"Schema {schema_name} missing properties or type definition"
    
    def test_health_endpoint_public_access(self):
        """Test that health endpoint is accessible without authentication."""
        response = client.get("/monitoring/health")
        assert response.status_code == 200
        
        # Should return health status
        health_data = response.json()
        assert "timestamp" in health_data
        assert "overall_status" in health_data or "status" in health_data

class TestAPIErrorHandling:
    """Test that API error handling matches documentation."""
    
    def test_authentication_error_format(self):
        """Test that authentication errors follow documented format."""
        # Test 401 error structure
        response = client.get("/subscription/status")  # No auth
        assert response.status_code == 401
        
        error_data = response.json()
        # Check for any reasonable error response format
        assert ("error" in error_data or "detail" in error_data), \
            "401 error should have error or detail field"
        
        # Should have some form of error identification
        has_error_info = any(key in error_data for key in ["error", "detail", "message"])
        assert has_error_info, "Error response should contain error information"

class TestDocumentationCompleteness:
    """Test that documentation is complete and covers key functionality."""
    
    def test_key_endpoints_are_documented(self):
        """Test that all critical API endpoints are documented."""
        response = client.get("/openapi.json")
        openapi_spec = response.json()
        documented_paths = set(openapi_spec["paths"].keys())
        
        # Key endpoints that must be documented
        critical_endpoints = [
            "/subscription/status",
            "/subscription/usage", 
            "/admin/users",
            "/admin/analytics",
            "/monitoring/health"
        ]
        
        missing_critical = [ep for ep in critical_endpoints if ep not in documented_paths]
        assert len(missing_critical) == 0, f"Critical endpoints missing documentation: {missing_critical}"
    
    def test_documentation_metadata_complete(self):
        """Test that API documentation has complete metadata."""
        response = client.get("/openapi.json")
        openapi_spec = response.json()
        
        # Check essential metadata
        info = openapi_spec["info"]
        assert info["title"] == "HippoCampus API"
        assert "version" in info
        assert "description" in info
        assert len(info["description"]) > 50, "Description should be comprehensive"
        
        # Check contact and license info
        assert "contact" in info
        assert "license" in info

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 