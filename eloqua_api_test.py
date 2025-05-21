import os
import base64
import requests
import json
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()
ELOQUA_COMPANY = os.getenv("ELOQUA_COMPANY")
ELOQUA_USERNAME = os.getenv("ELOQUA_USERNAME")
ELOQUA_PASSWORD = os.getenv("ELOQUA_PASSWORD")

# 🧪 Function to test Eloqua authentication
def test_eloqua_auth():
    print("🔍 Testing Eloqua authentication...")

    # 👇 Use the correct format: CompanyName\Username:Password
    auth_string = f"{ELOQUA_COMPANY}\\{ELOQUA_USERNAME}:{ELOQUA_PASSWORD}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/json"
    }

    url = "https://secure.p04.eloqua.com/api/REST/2.0/assets/emails"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("✅ Eloqua authentication successful!")
    else:
        print(f"❌ Eloqua authentication failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_eloqua_auth()

