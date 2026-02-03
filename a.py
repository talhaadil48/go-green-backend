import requests

BASE_URL = "http://localhost:8000"

# --- 1. Test /claims without token ---
r = requests.get(f"{BASE_URL}/api/claims")
print("Without token:", r.status_code, r.text)  # Should be 401 Unauthorized

# --- 2. Login to get access_token ---
login_data = {"username": "zenab", "password": "12345678"}
r = requests.post(f"{BASE_URL}/auth/login", params=login_data)  # use params if your route expects query params
if r.status_code != 200:
    print("Login failed:", r.status_code, r.text)
    exit()

tokens = r.json()
access_token = tokens.get("access_token")
print("Access token:", access_token)

# --- 3. Access /claims with token ---
headers = {"Authorization": f"Bearer {access_token}"}
r = requests.get(f"{BASE_URL}/api/claims", headers=headers)
print("With token:", r.status_code, r.json())
