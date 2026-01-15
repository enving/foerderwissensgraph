import requests
import time
import subprocess
import sys
from pathlib import Path


def smoke_test():
    print("🚬 Starting Smoke Test...")

    # Check if API is reachable
    api_url = "http://localhost:5001/api/search"
    try:
        print(f"Checking API at {api_url}...")
        response = requests.get(api_url, params={"q": "test", "limit": 1}, timeout=5)
        if response.status_code == 200:
            print("✅ API is UP and responding (200 OK)")
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API is DOWN (Connection Error)")
        return False

    # Check if Frontend is reachable
    frontend_url = "http://localhost:8000/docs/dashboard.html"
    try:
        print(f"Checking Frontend at {frontend_url}...")
        response = requests.get(frontend_url, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is UP and serving (200 OK)")
            if "Bund-ZuwendungsGraph" in response.text:
                print("✅ Frontend content verified (Title present)")
            else:
                print("⚠️ Frontend content suspicious (Title missing)")
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Frontend is DOWN (Connection Error)")
        return False

    return True


if __name__ == "__main__":
    success = smoke_test()
    if not success:
        sys.exit(1)
