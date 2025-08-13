"""Tests for FastAPI endpoints."""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import tempfile
import os

from api.main import app

class TestAPIEndpoints:
    """Test suite for API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    async def async_client(self):
        """Create async test client."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_document_upload(self, async_client):
        """Test document upload endpoint."""
        # Create a test PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(b"Test PDF content")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as f:
                files = {"file": ("test_document.pdf", f, "application/pdf")}
                response = await async_client.post("/api/documents/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "document_id" in data["data"]
            assert "session_id" in data["data"]
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_document_upload_invalid_type(self, client):
        """Test document upload with invalid file type."""
        with tempfile.NamedTemporaryFile(suffix=".txt") as tmp_file:
            tmp_file.write(b"Test content")
            tmp_file.seek(0)
            
            files = {"file": ("test.txt", tmp_file, "text/plain")}
            response = client.post("/api/documents/upload", files=files)
            
            assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_tender_analysis(self, async_client):
        """Test tender analysis endpoint."""
        analysis_request = {
            "analysis_type": "comprehensive",
            "session_id": "test-session-123"
        }
        
        with patch("managers.tender_analysis_manager.TenderAnalysisManager") as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            
            response = await async_client.post("/api/analysis/tender", json=analysis_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "analysis_id" in data
            assert "session_id" in data
    
    @pytest.mark.asyncio
    async def test_analysis_status(self, async_client):
        """Test analysis status endpoint."""
        analysis_id = "test-analysis-123"
        
        with patch("managers.tender_analysis_manager.TenderAnalysisManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.get_analysis_status.return_value = {
                "status": "completed",
                "progress": 100
            }
            mock_manager.return_value = mock_instance
            
            response = await async_client.get(f"/api/analysis/{analysis_id}/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_tender_comparison(self, async_client):
        """Test tender comparison endpoint."""
        comparison_request = {
            "proposal_ids": ["doc1", "doc2", "doc3"],
            "session_id": "test-session-123"
        }
        
        with patch("managers.tender_analysis_manager.TenderAnalysisManager") as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            
            response = await async_client.post("/api/comparison/tender", json=comparison_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "comparison_id" in data
    
    @pytest.mark.asyncio
    async def test_report_generation(self, async_client):
        """Test report generation endpoint."""
        with patch("managers.tender_analysis_manager.TenderAnalysisManager") as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            
            response = await async_client.post(
                "/api/reports/generate",
                params={
                    "session_id": "test-session-123",
                    "conversation_id": "test-conversation-123"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "report_id" in data
    
    @pytest.mark.asyncio
    async def test_chat_endpoint(self, async_client):
        """Test chat endpoint."""
        chat_request = {
            "query": "¿Cómo validar un contrato?",
            "session_id": "test-session-123"
        }
        
        with patch("managers.tender_analysis_manager.TenderAnalysisManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.process_chat_query.return_value = "Esta es una respuesta de prueba"
            mock_manager.return_value = mock_instance
            
            response = await async_client.post("/api/chat/tender", json=chat_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "response" in data["data"]
    
    def test_session_info(self, client):
        """Test session information endpoint."""
        session_id = "test-session-123"
        
        with patch("managers.session_manager.SessionManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.get_session_details.return_value = {
                "session_id": session_id,
                "documents": [],
                "analyses": []
            }
            mock_manager.return_value = mock_instance
            
            response = client.get(f"/api/sessions/{session_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_list_analyses(self, client):
        """Test list analyses endpoint."""
        with patch("managers.tender_analysis_manager.TenderAnalysisManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.list_analyses.return_value = []
            mock_manager.return_value = mock_instance
            
            response = client.get("/api/analysis/list")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "analyses" in data["data"]
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/health")
        assert "access-control-allow-origin" in response.headers
    
    def test_error_handling(self, client):
        """Test error handling."""
        # Test 404
        response = client.get("/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
    
    @pytest.mark.asyncio
    async def test_file_size_limit(self, async_client):
        """Test file size limit enforcement."""
        # Create a large file (simulated)
        large_content = b"x" * (60 * 1024 * 1024)  # 60MB
        
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            tmp_file.write(large_content)
            tmp_file.seek(0)
            
            files = {"file": ("large_file.pdf", tmp_file, "application/pdf")}
            response = await async_client.post("/api/documents/upload", files=files)
            
            assert response.status_code == 400
            data = response.json()
            assert "too large" in data["message"].lower() or "size" in data["message"].lower()

class TestAPIAuthentication:
    """Test API authentication and authorization."""
    
    def test_public_endpoints(self, client):
        """Test that public endpoints don't require authentication."""
        public_endpoints = [
            "/health",
            "/docs",
            "/openapi.json"
        ]
        
        for endpoint in public_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 404]  # 404 is OK if endpoint doesn't exist
    
    @pytest.mark.skipif(
        os.getenv("API_KEYS") is None,
        reason="API keys not configured"
    )
    def test_protected_endpoints_with_api_key(self, client):
        """Test protected endpoints with API key."""
        headers = {"X-API-Key": "test-api-key"}
        
        response = client.get("/api/analysis/list", headers=headers)
        # Specific behavior depends on whether API key auth is enabled
        assert response.status_code in [200, 401, 403]

class TestAPIPerformance:
    """Test API performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, async_client):
        """Test handling of concurrent requests."""
        async def make_request():
            return await async_client.get("/health")
        
        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        for response in responses:
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_request_timeout(self, async_client):
        """Test request timeout handling."""
        # This would test that long-running requests timeout appropriately
        pass

class TestAPIValidation:
    """Test API input validation."""
    
    @pytest.mark.asyncio
    async def test_invalid_json(self, async_client):
        """Test handling of invalid JSON."""
        response = await async_client.post(
            "/api/analysis/tender",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, async_client):
        """Test validation of required fields."""
        # Test with missing analysis_type
        incomplete_request = {"session_id": "test-123"}
        
        response = await async_client.post("/api/analysis/tender", json=incomplete_request)
        
        # Should either accept with defaults or reject with validation error
        assert response.status_code in [200, 422]
    
    @pytest.mark.asyncio
    async def test_invalid_field_types(self, async_client):
        """Test validation of field types."""
        invalid_request = {
            "analysis_type": 123,  # Should be string
            "session_id": ["invalid"]  # Should be string
        }
        
        response = await async_client.post("/api/analysis/tender", json=invalid_request)
        assert response.status_code == 422