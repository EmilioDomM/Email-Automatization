import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

WOO_URL = os.getenv("WOO_URL")
WOO_KEY = os.getenv("WOO_KEY")
WOO_SECRET = os.getenv("WOO_SECRET")

def fetch_products_with_images():
    page = 1
    total_fetched = 0

    while total_fetched < 100:
        response = requests.get(
            WOO_URL,
            params={
                "per_page": 100,
                "page": page,
                "_fields": "id,name,images"
            },
            auth=(WOO_KEY, WOO_SECRET)
        )

        if response.status_code != 200:
            print(f"❌ Failed to fetch products: {response.status_code}")
            print(response.text)
            break

        products = response.json()
        if not products:
            break

        for product in products:
            name = product.get("name", "Unnamed Product")
            images = product.get("images", [])
            first_image = images[0]["src"] if images else "❌ No image found"

            print(f"✅ {name} → {first_image}")
            total_fetched += 1
            if total_fetched >= 100:
                break

        page += 1

if __name__ == "__main__":
    fetch_products_with_images()
