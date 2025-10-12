import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestCreateAnomalyIntegration:
    """Integration tests for POST /voices/anomalies endpoint"""
    
    def test_create_anomaly_endpoint_exists(self):
        """Test that the endpoint exists and accepts POST requests"""
        # Test with invalid data to check endpoint exists
        response = client.post("/api/voices/anomalies", json={})
        # Should return 422 (validation error) not 404 (not found)
        assert response.status_code == 422
    
    def test_create_anomaly_validation_errors(self):
        """Test validation errors for required fields"""
        # Missing required fields
        response = client.post("/api/voices/anomalies", json={})
        assert response.status_code == 422
        
        # Invalid ratio (negative)
        response = client.post("/api/voices/anomalies", json={
            "voice": 1,
            "translation": 1,
            "book_number": 1,
            "chapter_number": 1,
            "verse_number": 1,
            "ratio": -1.0
        })
        assert response.status_code == 422
        assert "Ratio must be positive" in response.text
        
        # Invalid anomaly_type
        response = client.post("/api/voices/anomalies", json={
            "voice": 1,
            "translation": 1,
            "book_number": 1,
            "chapter_number": 1,
            "verse_number": 1,
            "ratio": 1.5,
            "anomaly_type": "invalid_type"
        })
        assert response.status_code == 422
        assert "Anomaly type must be one of" in response.text
    
    def test_create_anomaly_valid_types(self):
        """Test that all valid anomaly types are accepted"""
        valid_types = ['fast', 'slow', 'long', 'short', 'manual']
        
        for anomaly_type in valid_types:
            response = client.post("/api/voices/anomalies", json={
                "voice": 999999,  # Non-existent voice to get 404
                "translation": 1,
                "book_number": 1,
                "chapter_number": 1,
                "verse_number": 1,
                "ratio": 1.5,
                "anomaly_type": anomaly_type
            })
            # Should get 404 (voice not found) not 422 (validation error)
            # This confirms the anomaly_type is valid
            assert response.status_code == 404
    
    def test_create_anomaly_default_values(self):
        """Test default values in request"""
        response = client.post("/api/voices/anomalies", json={
            "voice": 999999,  # Non-existent voice to get 404
            "translation": 1,
            "book_number": 1,
            "chapter_number": 1,
            "verse_number": 1,
            "ratio": 1.5
            # anomaly_type should default to 'manual'
            # status should default to 'detected'
        })
        # Should get 404 (voice not found) not 422 (validation error)
        assert response.status_code == 404
    
    def test_create_anomaly_with_optional_fields(self):
        """Test creation with all optional fields"""
        response = client.post("/api/voices/anomalies", json={
            "voice": 999999,  # Non-existent voice to get 404
            "translation": 1,
            "book_number": 1,
            "chapter_number": 1,
            "verse_number": 1,
            "word": "test_word",
            "position_in_verse": 5,
            "position_from_end": 3,
            "duration": 1.5,
            "speed": 2.0,
            "ratio": 1.8,
            "anomaly_type": "manual",
            "status": "detected"
        })
        # Should get 404 (voice not found) not 422 (validation error)
        assert response.status_code == 404
    
    def test_create_anomaly_response_structure(self):
        """Test that error responses have correct structure"""
        # Test voice not found
        response = client.post("/api/voices/anomalies", json={
            "voice": 999999,
            "translation": 1,
            "book_number": 1,
            "chapter_number": 1,
            "verse_number": 1,
            "ratio": 1.5
        })
        assert response.status_code == 404
        assert "Voice 999999 not found" in response.json()["detail"]
    
    def test_manual_anomaly_type_specifically(self):
        """Test that 'manual' anomaly type is specifically supported"""
        response = client.post("/api/voices/anomalies", json={
            "voice": 999999,  # Non-existent voice
            "translation": 1,
            "book_number": 1,
            "chapter_number": 1,
            "verse_number": 1,
            "ratio": 1.5,
            "anomaly_type": "manual"
        })
        # Should get 404 (voice not found) not 422 (validation error)
        # This confirms 'manual' is a valid type
        assert response.status_code == 404
        assert "Voice 999999 not found" in response.json()["detail"]
    
    def test_create_anomaly_openapi_schema(self):
        """Test that the endpoint is properly documented in OpenAPI schema"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})
        
        # Check that POST /api/voices/anomalies exists
        assert "/api/voices/anomalies" in paths
        assert "post" in paths["/api/voices/anomalies"]
        
        # Check operation details
        post_operation = paths["/api/voices/anomalies"]["post"]
        assert post_operation["operationId"] == "create_voice_anomaly"
        assert "Voices" in post_operation["tags"]
        
        # Check request body schema
        request_body = post_operation.get("requestBody", {})
        assert "content" in request_body
        assert "application/json" in request_body["content"]
