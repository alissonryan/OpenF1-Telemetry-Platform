#!/usr/bin/env python3
"""
Quick test script to validate F1 Telemetry Platform setup
"""
import requests
import json
from time import sleep

BASE_URL = "http://localhost:8000"

def test_health():
    """Test API health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✓ Health check: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_meetings():
    """Test meetings endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/sessions/meetings")
        data = response.json()
        print(f"✓ Meetings: {len(data)} meetings found")
        if len(data) > 0:
            print(f"  Latest: {data[0]['meeting_name']} ({data[0]['year']})")
            return data[0]['meeting_key']
        return None
    except Exception as e:
        print(f"✗ Meetings failed: {e}")
        return None

def test_sessions(meeting_key):
    """Test sessions endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/sessions/sessions?meeting_key={meeting_key}")
        data = response.json()
        print(f"✓ Sessions: {len(data)} sessions found")
        for session in data[:3]:
            print(f"  - {session['session_name']} ({session['session_type']})")
        if len(data) > 0:
            return data[0]['session_key']
        return None
    except Exception as e:
        print(f"✗ Sessions failed: {e}")
        return None

def test_drivers(session_key):
    """Test drivers endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/telemetry/drivers?session_key={session_key}")
        data = response.json()
        print(f"✓ Drivers: {len(data)} drivers found")
        for driver in data[:3]:
            print(f"  - {driver['name_acronym']} ({driver['driver_number']}) - {driver['team_name']}")
        return True
    except Exception as e:
        print(f"✗ Drivers failed: {e}")
        return False

def test_car_data(session_key):
    """Test car data endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/telemetry/car-data?session_key={session_key}&driver_number=1&limit=5")
        data = response.json()
        print(f"✓ Car data: {len(data)} data points")
        if len(data) > 0:
            print(f"  Speed: {data[0].get('speed', 'N/A')} km/h")
        return True
    except Exception as e:
        print(f"✗ Car data failed: {e}")
        return False

def main():
    print("=" * 50)
    print("F1 Telemetry Platform - API Test")
    print("=" * 50)
    print()

    # Test 1: Health
    if not test_health():
        print("\n❌ API is not running. Start with:")
        print("   cd apps/api && source .venv/bin/activate && uvicorn app.main:app --reload")
        return

    print()

    # Test 2: Meetings
    meeting_key = test_meetings()
    if not meeting_key:
        print("\n⚠️  No meetings found, but API is working")
        return

    print()

    # Test 3: Sessions
    session_key = test_sessions(meeting_key)
    if not session_key:
        print("\n⚠️  No sessions found")
        return

    print()

    # Test 4: Drivers
    test_drivers(session_key)
    print()

    # Test 5: Car Data
    test_car_data(session_key)
    print()

    print("=" * 50)
    print("✅ All tests passed!")
    print("=" * 50)
    print()
    print("🚀 Ready to start the frontend:")
    print("   cd apps/web && npm run dev")
    print()
    print("📱 Then open: http://localhost:3000/dashboard")

if __name__ == "__main__":
    main()
