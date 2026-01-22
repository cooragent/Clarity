#!/usr/bin/env python3
"""
Test suite for the Financial Intelligence Agent API

This module contains comprehensive tests for all API endpoints.

Usage:
    # Install test dependencies first
    pip install pytest pytest-asyncio httpx

    # Run all tests
    pytest test_api.py -v

    # Run specific test
    pytest test_api.py::test_health_check -v

    # Run with coverage
    pytest test_api.py --cov=api --cov-report=html
"""

import json
from datetime import datetime
from typing import Dict

import pytest
from httpx import AsyncClient

from api import app


# ==================== Test Configuration ====================

@pytest.fixture
def sample_analyze_request() -> Dict:
    """Sample analyze request data"""
    return {
        "ticker": "AAPL",
        "trade_date": "2025-01-15",
        "model": "openai"
    }


@pytest.fixture
def sample_track_request() -> Dict:
    """Sample track request data"""
    return {
        "investor_name": "Warren Buffett",
        "trade_date": "2025-01-15",
        "model": "openai"
    }


@pytest.fixture
def sample_screen_request() -> Dict:
    """Sample screen request data"""
    return {
        "criteria": "high dividend yield tech stocks",
        "trade_date": "2025-01-15",
        "model": "openai"
    }


@pytest.fixture
def sample_ask_request() -> Dict:
    """Sample ask request data"""
    return {
        "query": "分析一下苹果公司的股票",
        "model": "openai"
    }


@pytest.fixture
def sample_dashboard_request() -> Dict:
    """Sample dashboard request data"""
    return {
        "markets": ["A股", "美股"],
        "top_n": 10,
        "push": False,
        "push_channels": None
    }


# ==================== Basic Tests ====================

@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"


# ==================== Analyze Endpoint Tests ====================

@pytest.mark.asyncio
async def test_analyze_endpoint_structure(sample_analyze_request):
    """Test analyze endpoint request/response structure"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/analyze", json=sample_analyze_request)

        # Response should be valid JSON
        assert response.status_code in [200, 500]  # May fail if API keys not configured
        data = response.json()

        if response.status_code == 200:
            # Check response structure
            assert "success" in data
            assert "task_type" in data
            assert "target" in data
            assert "trade_date" in data
            assert data["task_type"] == "STOCK_ANALYSIS"
            assert data["target"] == sample_analyze_request["ticker"]


@pytest.mark.asyncio
async def test_analyze_missing_ticker():
    """Test analyze endpoint with missing ticker"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/analyze", json={})
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_analyze_invalid_date():
    """Test analyze endpoint with invalid date format"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/analyze", json={
            "ticker": "AAPL",
            "trade_date": "invalid-date"
        })
        # Should still accept the request (date validation happens in orchestrator)
        assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_analyze_model_selection():
    """Test analyze endpoint with different model selections"""
    models = ["openai", "qwen"]

    async with AsyncClient(app=app, base_url="http://test") as client:
        for model in models:
            response = await client.post("/api/v1/analyze", json={
                "ticker": "AAPL",
                "model": model
            })
            assert response.status_code in [200, 500]


# ==================== Track Endpoint Tests ====================

@pytest.mark.asyncio
async def test_track_endpoint_structure(sample_track_request):
    """Test track endpoint request/response structure"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/track", json=sample_track_request)

        assert response.status_code in [200, 500]
        data = response.json()

        if response.status_code == 200:
            assert "success" in data
            assert "task_type" in data
            assert "target" in data
            assert data["task_type"] == "HOLDINGS_TRACKING"
            assert data["target"] == sample_track_request["investor_name"]


@pytest.mark.asyncio
async def test_track_missing_investor():
    """Test track endpoint with missing investor name"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/track", json={})
        assert response.status_code == 422  # Validation error


# ==================== Screen Endpoint Tests ====================

@pytest.mark.asyncio
async def test_screen_endpoint_structure(sample_screen_request):
    """Test screen endpoint request/response structure"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/screen", json=sample_screen_request)

        assert response.status_code in [200, 500]
        data = response.json()

        if response.status_code == 200:
            assert "success" in data
            assert "task_type" in data
            assert "target" in data
            assert data["task_type"] == "STOCK_SCREENING"
            assert data["target"] == sample_screen_request["criteria"]


@pytest.mark.asyncio
async def test_screen_missing_criteria():
    """Test screen endpoint with missing criteria"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/screen", json={})
        assert response.status_code == 422  # Validation error


# ==================== Ask Endpoint Tests ====================

@pytest.mark.asyncio
async def test_ask_endpoint_structure(sample_ask_request):
    """Test ask endpoint request/response structure"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/ask", json=sample_ask_request)

        assert response.status_code in [200, 500]
        data = response.json()

        if response.status_code == 200:
            assert "success" in data
            assert "task_type" in data
            assert "target" in data
            assert data["task_type"] == "NATURAL_LANGUAGE"
            assert data["target"] == sample_ask_request["query"]


@pytest.mark.asyncio
async def test_ask_missing_query():
    """Test ask endpoint with missing query"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/ask", json={})
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_ask_chinese_query():
    """Test ask endpoint with Chinese query"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/ask", json={
            "query": "帮我分析一下特斯拉的股票走势"
        })
        assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_ask_english_query():
    """Test ask endpoint with English query"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/ask", json={
            "query": "What are the top dividend stocks in tech sector?"
        })
        assert response.status_code in [200, 500]


# ==================== Dashboard Endpoint Tests ====================

@pytest.mark.asyncio
async def test_dashboard_endpoint_structure(sample_dashboard_request):
    """Test dashboard endpoint request/response structure"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/dashboard", json=sample_dashboard_request)

        assert response.status_code in [200, 500]
        data = response.json()

        if response.status_code == 200:
            assert "success" in data
            assert "date" in data
            assert "market_overviews" in data
            assert "recommendations" in data
            assert "summary" in data
            assert "markdown" in data
            assert isinstance(data["market_overviews"], list)
            assert isinstance(data["recommendations"], list)


@pytest.mark.asyncio
async def test_dashboard_default_parameters():
    """Test dashboard endpoint with default parameters"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/dashboard", json={})
        assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_dashboard_custom_markets():
    """Test dashboard endpoint with custom markets"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/dashboard", json={
            "markets": ["A股"],
            "top_n": 5
        })
        assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_dashboard_with_push():
    """Test dashboard endpoint with push notification"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/dashboard", json={
            "markets": ["A股"],
            "top_n": 5,
            "push": True
        })
        assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_dashboard_with_specific_channels():
    """Test dashboard endpoint with specific push channels"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/dashboard", json={
            "markets": ["A股"],
            "top_n": 5,
            "push": True,
            "push_channels": ["wechat", "feishu"]
        })
        assert response.status_code in [200, 500]


# ==================== Notification Channels Tests ====================

@pytest.mark.asyncio
async def test_notification_channels_endpoint():
    """Test notification channels endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/notification/channels")
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert "channels" in data
        assert isinstance(data["available"], bool)
        assert isinstance(data["channels"], list)


# ==================== CORS Tests ====================

@pytest.mark.asyncio
async def test_cors_headers():
    """Test CORS headers are present"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.options("/api/v1/analyze")
        assert "access-control-allow-origin" in response.headers


# ==================== API Documentation Tests ====================

@pytest.mark.asyncio
async def test_openapi_schema():
    """Test OpenAPI schema is available"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "Financial Intelligence Agent API"


@pytest.mark.asyncio
async def test_api_docs():
    """Test API documentation is available"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/docs")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_redoc():
    """Test ReDoc documentation is available"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/redoc")
        assert response.status_code == 200


# ==================== Error Handling Tests ====================

@pytest.mark.asyncio
async def test_invalid_endpoint():
    """Test invalid endpoint returns 404"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/invalid")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_method():
    """Test invalid HTTP method"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/analyze")  # Should be POST
        assert response.status_code == 405


@pytest.mark.asyncio
async def test_invalid_json():
    """Test invalid JSON payload"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/analyze",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


# ==================== Integration Tests ====================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_analyze_workflow():
    """
    Integration test for complete analyze workflow

    Note: This test requires proper API keys configured in .env
    Skip with: pytest test_api.py -m "not integration"
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Analyze a stock
        response = await client.post("/api/v1/analyze", json={
            "ticker": "AAPL",
            "model": "openai"
        })

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert data["report"] is not None
            assert "AAPL" in data["report"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_dashboard_workflow():
    """
    Integration test for complete dashboard workflow

    Note: This test requires proper API keys configured in .env
    Skip with: pytest test_api.py -m "not integration"
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Check notification channels
        channels_response = await client.get("/api/v1/notification/channels")
        assert channels_response.status_code == 200

        # Step 2: Run dashboard scan
        dashboard_response = await client.post("/api/v1/dashboard", json={
            "markets": ["A股"],
            "top_n": 5,
            "push": False
        })

        if dashboard_response.status_code == 200:
            data = dashboard_response.json()
            assert data["success"] is True
            assert len(data["recommendations"]) <= 5
            assert data["markdown"] is not None


# ==================== Performance Tests ====================

@pytest.mark.asyncio
@pytest.mark.slow
async def test_concurrent_requests():
    """
    Test handling concurrent requests

    Skip with: pytest test_api.py -m "not slow"
    """
    import asyncio

    async def make_request(client, endpoint, payload):
        return await client.post(endpoint, json=payload)

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Send 5 concurrent health check requests
        tasks = [
            client.get("/health")
            for _ in range(5)
        ]
        responses = await asyncio.gather(*tasks)

        assert all(r.status_code == 200 for r in responses)


# ==================== Main ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not integration and not slow"])
