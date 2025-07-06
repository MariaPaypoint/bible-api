import pytest
import requests
import json
from fastapi.testclient import TestClient
import sys
import os

# Add the app directory to the path so we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.main import app

client = TestClient(app)

def test_excerpt_jhn_3_16_17():
    """Test requesting John 3:16-17 with translation=16"""
    
    # Make request to the API
    response = client.get("/excerpt_with_alignment", params={
        "translation": 16,
        "excerpt": "jhn 3:16-17"
    })
    
    # Check status code
    assert response.status_code == 200
    
    # Parse response
    data = response.json()
    
    # Basic structure checks
    assert "parts" in data
    assert len(data["parts"]) == 1
    
    # Check the book info
    book_info = data["parts"][0]["book"]
    assert book_info["alias"] == "jhn"
    
    # Check chapter number
    assert data["parts"][0]["chapter_number"] == 3
    
    # Check verses
    verses = data["parts"][0]["verses"]
    assert len(verses) == 2  # We requested 2 verses (16-17)
    
    # Check verse numbers
    verse_numbers = [verse["number"] for verse in verses]
    assert 16 in verse_numbers
    assert 17 in verse_numbers
    
    # Check verse content (just make sure it's not empty)
    for verse in verses:
        assert verse["html"]  # HTML content should not be empty
        assert verse["text"]  # Plain text should not be empty
    
    print("Test passed successfully!")

if __name__ == "__main__":
    test_excerpt_jhn_3_16_17()
