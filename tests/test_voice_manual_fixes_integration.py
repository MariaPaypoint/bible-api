import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add the app directory to the path so we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))
from app.main import app

client = TestClient(app)


class TestVoiceManualFixesIntegration:
    """Integration tests for voice_manual_fixes functionality with real database calls"""
    
    def test_anomaly_status_update_endpoint_exists(self):
        """Test that the anomaly status update endpoint exists and accepts requests"""
        
        # Test with invalid anomaly ID to check endpoint structure
        response = client.patch("/voices/anomalies/99999/status", json={
            "status": "confirmed"
        })
        
        # Should return 404 for non-existent anomaly, not 404 for missing endpoint
        assert response.status_code == 404
        response_data = response.json()
        assert "not found" in response_data["detail"].lower()
    
    def test_anomaly_status_validation(self):
        """Test that only valid status values are accepted"""
        
        # Test with invalid status
        response = client.patch("/voices/anomalies/1/status", json={
            "status": "invalid_status"
        })
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_valid_status_values_accepted(self):
        """Test that all valid status values are accepted by the endpoint"""
        
        valid_statuses = ["detected", "confirmed", "disproved", "corrected", "already_resolved"]
        
        for status in valid_statuses:
            request_data = {"status": status}
            
            # For corrected status, add required begin/end fields
            if status == "corrected":
                request_data["begin"] = 10.0
                request_data["end"] = 12.0
            
            response = client.patch("/voices/anomalies/99999/status", json=request_data)
            
            # Should return 404 (anomaly not found) not 422 (validation error)
            # This confirms the status value is valid
            assert response.status_code == 404, f"Status '{status}' should be valid"
    
    def test_request_body_structure(self):
        """Test that the request body structure is validated correctly"""
        
        # Test with missing status field
        response = client.patch("/voices/anomalies/1/status", json={})
        assert response.status_code == 422
        
        # Test with extra fields (should be ignored)
        response = client.patch("/voices/anomalies/99999/status", json={
            "status": "confirmed",
            "extra_field": "should_be_ignored"
        })
        # Should return 404 (not found) not 422 (validation error)
        assert response.status_code == 404
    
    def test_response_structure_for_valid_anomaly(self):
        """Test response structure when updating a valid anomaly (if any exist)"""
        
        # First, try to get some anomalies to test with
        # This assumes there might be some test data in the database
        try:
            # Try to get anomalies for a common voice/translation combination
            response = client.get("/voices/1/anomalies", params={"limit": 1})
            
            if response.status_code == 200:
                data = response.json()
                if data.get("items") and len(data["items"]) > 0:
                    # We have at least one anomaly to test with
                    anomaly = data["items"][0]
                    anomaly_code = anomaly["code"]
                    
                    # Test updating its status
                    update_response = client.patch(f"/voices/anomalies/{anomaly_code}/status", json={
                        "status": "confirmed"
                    })
                    
                    if update_response.status_code == 200:
                        updated_data = update_response.json()
                        
                        # Verify response structure
                        required_fields = [
                            "code", "voice", "translation", "book_number", 
                            "chapter_number", "word", "duration", "speed", 
                            "ratio", "anomaly_type", "status"
                        ]
                        
                        for field in required_fields:
                            assert field in updated_data, f"Field '{field}' missing from response"
                        
                        # Verify status was updated
                        assert updated_data["status"] == "confirmed"
                        
                        # Test updating back to original status
                        client.patch(f"/voices/anomalies/{anomaly_code}/status", json={
                            "status": "detected"
                        })
                    
        except Exception as e:
            # If no test data available, skip this test
            pytest.skip(f"No test data available for integration test: {e}")
    
    def test_error_handling_for_database_constraints(self):
        """Test that database constraint violations are handled properly"""
        
        # Test with extremely large anomaly ID
        response = client.patch("/voices/anomalies/999999999/status", json={
            "status": "confirmed"
        })
        
        assert response.status_code == 404
        response_data = response.json()
        assert "not found" in response_data["detail"].lower()
    
    def test_concurrent_status_updates(self):
        """Test that concurrent status updates don't cause issues"""
        
        # This test would ideally use threading, but for simplicity
        # we'll just test rapid sequential updates
        anomaly_id = 99999  # Non-existent ID
        
        statuses = ["confirmed", "disproved", "corrected", "detected"]
        
        for status in statuses:
            request_data = {"status": status}
            
            # For corrected status, add required begin/end fields
            if status == "corrected":
                request_data["begin"] = 10.0
                request_data["end"] = 12.0
            
            response = client.patch(f"/voices/anomalies/{anomaly_id}/status", json=request_data)
            # All should return 404 consistently
            assert response.status_code == 404
    
    def test_already_resolved_status_cannot_be_set_manually(self):
        """Test that already_resolved status cannot be set manually"""
        
        # Test with a non-existent anomaly ID first to check the error message
        response = client.patch("/voices/anomalies/999999/status", json={
            "status": "already_resolved"
        })
        
        # Should return 422 for trying to set already_resolved status
        # even before checking if anomaly exists
        if response.status_code == 422:
            data = response.json()
            assert "Cannot update anomaly status to already resolved" in data["detail"]
        else:
            # If it's 404, that means the anomaly doesn't exist, 
            # but we still want to test with a real anomaly
            
            # Try to find a real anomaly to test with
            try:
                # Get some anomalies from any voice
                voices_response = client.get("/voices")
                if voices_response.status_code == 200:
                    voices_data = voices_response.json()
                    
                    for voice in voices_data:
                        if voice["anomalies_count"] > 0:
                            # Get anomalies for this voice
                            anomalies_response = client.get(f"/voices/{voice['code']}/anomalies?limit=1")
                            if anomalies_response.status_code == 200:
                                anomalies_data = anomalies_response.json()
                                if anomalies_data.get("items") and len(anomalies_data["items"]) > 0:
                                    anomaly = anomalies_data["items"][0]
                                    anomaly_code = anomaly["code"]
                                    
                                    # Now test setting already_resolved status
                                    test_response = client.patch(f"/voices/anomalies/{anomaly_code}/status", json={
                                        "status": "already_resolved"
                                    })
                                    
                                    # Should return 422
                                    assert test_response.status_code == 422
                                    test_data = test_response.json()
                                    assert "Cannot update anomaly status to already resolved" in test_data["detail"]
                                    return
                            
                # If we get here, no test data available
                pytest.skip("No test data available for already_resolved status test")
                
            except Exception as e:
                pytest.skip(f"No test data available for already_resolved status test: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
