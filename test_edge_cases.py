#!/usr/bin/env python3
"""
Edge Case Testing Script for Phase 5: Error Handling and Edge Cases

Tests various edge cases to validate comprehensive error handling:
- Large payloads
- Malformed JSON
- Invalid data structures  
- Missing required fields
- Nested objects and arrays
- Various timestamp formats
"""

import json
import requests
import time
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"

def test_api_endpoint(description: str, payload: Dict[str, Any], expected_status: int = None):
    """Test an API endpoint with given payload and validate response."""
    print(f"\n🧪 Testing: {description}")
    print(f"Payload size: {len(json.dumps(payload))} bytes")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/alerts",
            json=payload,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: Alert ID {data.get('alert_id')}")
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"❌ Error: {error_data}")
            
        if expected_status and response.status_code != expected_status:
            print(f"⚠️  Expected status {expected_status}, got {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error - make sure backend is running")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")

def run_edge_case_tests():
    """Run comprehensive edge case tests."""
    
    print("🚀 PHASE 5 EDGE CASE TESTING")
    print("=" * 50)
    
    # Test 1: Valid flexible alert
    test_api_endpoint(
        "Valid flexible alert with nested data",
        {
            "alert_type": "kubernetes",
            "runbook": "https://github.com/org/runbooks/kubernetes.md",
            "data": {
                "severity": "high",
                "cluster": "prod-us-west-2",
                "namespace": "default",
                "pod_info": {
                    "name": "web-server-abc123",
                    "replicas": 3,
                    "resources": {
                        "cpu": "500m",
                        "memory": "1Gi"
                    }
                },
                "metrics": [100, 250, 300, 150],
                "labels": {
                    "app": "web-server",
                    "version": "v2.1.0",
                    "environment": "production"
                }
            }
        },
        200
    )
    
    # Test 2: Missing required fields
    test_api_endpoint(
        "Missing alert_type (should fail)",
        {
            "runbook": "https://github.com/org/runbooks/test.md",
            "data": {"message": "test"}
        },
        422
    )
    
    # Test 3: Empty alert_type
    test_api_endpoint(
        "Empty alert_type (should fail)", 
        {
            "alert_type": "",
            "runbook": "https://github.com/org/runbooks/test.md"
        },
        400
    )
    
    # Test 4: Invalid runbook URL
    test_api_endpoint(
        "Invalid runbook URL (should fail)",
        {
            "alert_type": "test",
            "runbook": "not-a-valid-url"
        },
        400
    )
    
    # Test 5: Large nested payload
    large_data = {
        "alert_type": "performance",
        "runbook": "https://github.com/org/runbooks/performance.md", 
        "data": {
            "metrics": {f"metric_{i}": list(range(100)) for i in range(50)},
            "logs": ["Log entry " * 100] * 100,
            "config": {
                "nested_level_1": {
                    "nested_level_2": {
                        "nested_level_3": {
                            "deep_data": "x" * 10000
                        }
                    }
                }
            }
        }
    }
    
    test_api_endpoint(
        "Large nested payload (testing size limits)",
        large_data,
        200  # Should work if under 10MB limit
    )
    
    # Test 6: Edge case values
    test_api_endpoint(
        "Edge case data types",
        {
            "alert_type": "edge_cases",
            "runbook": "https://github.com/org/runbooks/edge.md",
            "data": {
                "null_value": None,
                "boolean_true": True,
                "boolean_false": False,
                "zero": 0,
                "negative": -42,
                "float_value": 3.141592653589793,
                "empty_string": "",
                "empty_array": [],
                "empty_object": {},
                "unicode": "🚀 Test with émojis and spëcial chars",
                "very_long_string": "x" * 5000,
                "scientific_notation": 1.23e-4
            }
        },
        200
    )
    
    # Test 7: Timestamp variations
    test_api_endpoint(
        "Various timestamp formats",
        {
            "alert_type": "timestamp_test",
            "runbook": "https://github.com/org/runbooks/time.md",
            "timestamp": int(time.time()),  # Unix timestamp
            "data": {
                "event_time": "2024-01-15T10:30:00Z",
                "alert_created": int(time.time() * 1000000),  # Microseconds
                "durations": [1.5, 2.7, 3.9]
            }
        },
        200
    )
    
    print("\n" + "=" * 50)
    print("🏁 Edge case testing completed!")
    print("\nTo run this test:")
    print("1. Start the backend: cd backend && python -m tarsy.main")
    print("2. Run this script: python test_edge_cases.py")

if __name__ == "__main__":
    run_edge_case_tests()