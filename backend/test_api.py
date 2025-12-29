import requests
import json

BASE_URL = "http://localhost:8000"

def test_root():
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Root endpoint: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"Root endpoint failed: {e}")
        return False

def test_login():
    try:
        # Test client login
        data = {"username": "testuser", "password": "test123"}
        response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
        print(f"Client login: {response.status_code}")
        if response.status_code == 200:
            print("✅ Client login successful!")
            token = response.json().get("access_token")
            return token
        else:
            print(f"❌ Client login failed: {response.text}")
            return None
    except Exception as e:
        print(f"Client login error: {e}")
        return None

def test_driver_login():
    try:
        # Test driver login
        data = {"email": "driver@example.com", "password": "driver123"}
        response = requests.post(f"{BASE_URL}/api/driver/login", json=data)
        print(f"Driver login: {response.status_code}")
        if response.status_code == 200:
            print("✅ Driver login successful!")
            return True
        else:
            print(f"❌ Driver login failed: {response.text}")
            return False
    except Exception as e:
        print(f"Driver login error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Multi-Agent Delivery System API...")
    print("=" * 50)

    # Test root endpoint
    if not test_root():
        print("❌ Backend not running or root endpoint failed")
        exit(1)

    # Test authentication
    token = test_login()
    driver_success = test_driver_login()

    print("=" * 50)
    if token and driver_success:
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️ Some tests failed. Check authentication setup.")
