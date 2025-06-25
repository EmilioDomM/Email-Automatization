import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
WOO_URL = os.getenv("WOO_URL")
WOO_KEY = os.getenv("WOO_KEY")
WOO_SECRET = os.getenv("WOO_SECRET")

def contar_productos_published():
    page = 1
    total_published = 0
    total_total = 0

    print("🔎 Buscando productos con status 'publish'...")

    while True:
        response = requests.get(
            WOO_URL,
            params={
                "per_page": 100,
                "page": page,
                "_fields": "id,name,status"
            },
            auth=(WOO_KEY, WOO_SECRET)
        )

        if response.status_code != 200:
            print(f"❌ Error al consultar productos (código {response.status_code})")
            print(response.text)
            break

        products = response.json()
        if not products:
            break

        for product in products:
            total_total += 1
            if product.get("status") == "publish":
                total_published += 1

        page += 1

    print(f"✅ Total de productos encontrados: {total_total}")
    print(f"📦 Publicados (status='publish'): {total_published}")

if __name__ == "__main__":
    contar_productos_published()
