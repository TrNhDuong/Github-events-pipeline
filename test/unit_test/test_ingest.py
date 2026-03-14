import pytest
from unittest.mock import patch, Mock
import gzip
import json

from src.ingestion.ingest import ingest_hour

@patch('src.ingestion.ingest.requests.get')
def test_ingest_hour_success(mock_get):
    # Mocking standard successful response
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    
    fake_data = [
        {"id": "1", "type": "PushEvent"}, 
        {"id": "2", "type": "PullRequestEvent"}
    ]
    # Simulate a file with newline-separated JSON objects
    jsonl_data = "\n".join([json.dumps(r) for r in fake_data]).encode('utf-8')
    gzipped_data = gzip.compress(jsonl_data)
    
    mock_response.content = gzipped_data
    mock_get.return_value = mock_response
    
    records = ingest_hour("2025-01-01", 1)
    
    assert len(records) == 2
    assert records[0]["id"] == "1"
    assert records[1]["type"] == "PullRequestEvent"
    
    # Assert get was called with exactly these arguments
    mock_get.assert_called_once_with(
        "https://data.gharchive.org/2025-01-01-1.json.gz", 
        timeout=120
    )

@patch('src.ingestion.ingest.requests.get')
def test_ingest_hour_failure(mock_get):
    from requests.exceptions import RequestException
    
    mock_get.side_effect = RequestException("Connection error")
    
    with pytest.raises(ValueError, match="Error fetching data for 2025-01-01-1: Connection error"):
        ingest_hour("2025-01-01", 1)
