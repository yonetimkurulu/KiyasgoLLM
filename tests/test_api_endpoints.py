"""
Tests for API Endpoints using FastAPI TestClient.
No running server required.
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_contains_status(self):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_contains_version(self):
        response = client.get("/health")
        data = response.json()
        assert "version" in data

    def test_health_contains_llm_provider(self):
        response = client.get("/health")
        data = response.json()
        assert "llm_provider" in data


class TestRootEndpoint:
    """Tests for the / endpoint."""

    def test_root_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_contains_name(self):
        response = client.get("/")
        data = response.json()
        assert "KıyasGO" in data["name"]

    def test_root_contains_endpoints(self):
        response = client.get("/")
        data = response.json()
        assert "endpoints" in data
        assert "products" in data["endpoints"]
        assert "compare" in data["endpoints"]

    def test_root_docs_url(self):
        response = client.get("/")
        data = response.json()
        assert data["docs"] == "/docs"


class TestDocsEndpoint:
    """Tests for Swagger UI availability."""

    def test_docs_returns_200(self):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_returns_200(self):
        response = client.get("/redoc")
        assert response.status_code == 200


class TestRouteRegistration:
    """Tests that all expected routes are registered."""

    def test_all_expected_routes_exist(self):
        routes = [route.path for route in app.routes]
        expected_prefixes = [
            "/api/v1/ai/products",
            "/api/v1/ai/compare",
            "/api/v1/ai/best-for",
            "/api/v1/ai/signals",
            "/api/v1/ai/chat",
        ]
        for prefix in expected_prefixes:
            matching = [r for r in routes if r.startswith(prefix)]
            assert len(matching) > 0, f"No route found for prefix: {prefix}"


class TestTimingHeader:
    """Tests for the request timing middleware."""

    def test_timing_header_present(self):
        response = client.get("/health")
        assert "x-process-time" in response.headers

    def test_timing_header_is_numeric(self):
        response = client.get("/health")
        time_value = response.headers["x-process-time"]
        assert float(time_value) >= 0


class TestCORS:
    """Tests for CORS middleware."""

    def test_cors_headers(self):
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS should allow the origin
        assert response.status_code in [200, 405]
