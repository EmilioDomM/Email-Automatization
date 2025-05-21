import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
 
# Credenciales de WooCommerce
woo_url = os.getenv("WOO_URL")
woo_key = os.getenv("WOO_KEY")
woo_secret = os.getenv("WOO_SECRET")
 
# Credenciales de notion
notion_token = os.getenv("NOTION_API_TOKEN")
notion_database_id = os.getenv("DATABASE_ID_MAINDATABASE")

# es para autentificar
headers = {
    "Authorization": f"Bearer {notion_token}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}
# Cambia el número de la unidad por el nombre en la página
unidad_to_hospital = {
    "565": "H. Alta Especialidad",
    "566": "H. Conchita",
    "567": "H. Sur",
    "568": "H. Vidriera",
    "569": "H. Reynosa",
    "570": "H. del Parque",
    "571": "H. Saltillo",
    "572": "H. Betania",
    "573": "H. UPAEP",
    "574": "H. San Nicolás",
    "575": "H. Faro del Mayab",
    "576": "H. Cumbres",
    "577": "H. Altagracia",
    "578": "C. San Pedro",
    "579": "C. Juventud",
    "580": "C. Irapuato",
}

#Trae los productos del WooCommerce
def fetch_products_stream():
    page = 1
    while True:
        response = requests.get(
            woo_url,
            params = {
                "per_page": 100,
                "page": page,
                "_fields": "id,sku,name,slug,meta_data,attributes" #Trae solamente estos datos de todos los datos que había por producto
            },
            auth=(woo_key, woo_secret)
        )
        #Si tarda mucho da error
        if response.status_code != 200:
            print(f"Error fetching page {page}: {response.status_code}")
            break

        products = response.json()
        if not products:
            break

        for product in products:
            yield product

        page += 1


def send_to_notion(product):

    hospital_name = "Unknown Hospital"
    unidad_id = None

    #Es lo de los nombres de la unidad
    for meta in product.get("meta_data", []):
        if meta.get("key") == "unidad":
            raw_value = meta.get("value")
            if isinstance(raw_value, list) and raw_value:
                unidad_id = str(raw_value[0])
            elif raw_value is not None:
                unidad_id = str(raw_value)

    if unidad_id and unidad_id in unidad_to_hospital:
        hospital_name = unidad_to_hospital[unidad_id]

    options = ""
    for attr in product.get("attributes", []):
        if attr.get("name") == "Estudio":
            options = ", ".join(attr.get("options", []))
            break

    # Son los headers de los datos que recibimos
    product_data = {
        "Product ID": product['id'],
        "SKU": product.get('sku', ''),
        "Name": product['name'],
        "Slug": product['slug'],
        "Unidad (ID)": unidad_id if unidad_id else 'N/A',
        "Unidad": hospital_name,
        "Options": options
    }

    try:
        unidad_value = int(product_data["Unidad (ID)"]) if product_data["Unidad (ID)"].isdigit() else None
    except:
        unidad_value = None

    #Son lo que van a recibir las tablas de Notion
    notion_data = {
        "parent": {"database_id": notion_database_id},
        "properties": {
            "Product ID": {"number": product_data["Product ID"]},
            "SKU": {"rich_text": [{"text": {"content": product_data["SKU"]}}]},
            "Name": {"title": [{"text": {"content": product_data["Name"]}}]},
            "Slug": {"rich_text": [{"text": {"content": product_data["Slug"]}}]},
            "Unidad (ID)": {"number": unidad_value},
            "Unidad": {"select": {"name": product_data["Unidad"]}},
            "Options": {"rich_text": [{"text": {"content": product_data["Options"]}}]}
        }
    }

    response = requests.post("https://api.notion.com/v1/pages", json=notion_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to insert product ID {product_data['Product ID']}: {response.text}")
    else:
        print(f"✅ Sent product ID {product_data['Product ID']} to Notion")

# Thread-safe wrapper
semaphore = threading.Semaphore(3)

#el tiempo que va a tardar cada fetch
def safe_send_to_notion(product):
    with semaphore:
        send_to_notion(product)
        time.sleep(0.3)

#Con esto haces varios procesos al mismo tiempo, hace que el código sea más rápido
def stream_all_products():
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for product in fetch_products_stream():
            futures.append(executor.submit(safe_send_to_notion, product))
        for future in as_completed(futures):
            future.result()

#con esto se corre
stream_all_products()
print("🎉 Finished sending all products.")
