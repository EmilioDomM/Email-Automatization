import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import threading
import base64
import json

# Load environment variables
load_dotenv()
NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID_FORMS")
WOO_URL = os.getenv("WOO_URL")
WOO_KEY = os.getenv("WOO_KEY")
WOO_SECRET = os.getenv("WOO_SECRET")

ELOQUA_COMPANY = os.getenv("ELOQUA_COMPANY")
ELOQUA_USERNAME = os.getenv("ELOQUA_USERNAME")
ELOQUA_PASSWORD = os.getenv("ELOQUA_PASSWORD")
ELOQUA_FOLDER_ID = os.getenv("ELOQUA_EMAIL_FOLDER_ID")

headers = {
    "Authorization": f"Bearer {NOTION_API_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

hospital_to_unidad = {
    "H. Alta Especialidad": "565",
    "H. Conchita": "566",
    "H. Sur": "567",
    "H. Vidriera": "568",
    "H. Reynosa": "569",
    "H. del Parque": "570",
    "H. Saltillo": "571",
    "H. Betania": "572",
    "H. UPAEP": "573",
    "H. San Nicolás": "574",
    "H. Faro del Mayab": "575",
    "H. Cumbres": "576",
    "H. Altagracia": "577",
    "C. San Pedro": "578",
    "C. Juventud": "579",
    "C. Irapuato": "580",
}

unidad_to_hospital = {v: k for k, v in hospital_to_unidad.items()}

def get_eloqua_auth_header():
    auth_string = f"{ELOQUA_COMPANY}\\{ELOQUA_USERNAME}:{ELOQUA_PASSWORD}"
    b64_auth = base64.b64encode(auth_string.encode()).decode()
    return {"Authorization": f"Basic {b64_auth}", "Content-Type": "application/json"}

def test_eloqua_auth():
    print("Testing Eloqua authentication...")
    url = "https://secure.p04.eloqua.com/API/REST/2.0/assets/emails"
    response = requests.get(url, headers=get_eloqua_auth_header())
    if response.status_code == 200:
        print("✅ Eloqua authentication successful.")
        return True
    else:
        print(f"❌ Eloqua authentication failed: {response.status_code}")
        print(response.text)
        return False

def get_database_entries():
    print("Fetching Notion database entries...")
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    entries = []
    next_cursor = None

    while True:
        payload = {"page_size": 100}
        if next_cursor:
            payload["start_cursor"] = next_cursor

        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        if response.status_code != 200:
            print("Error fetching database entries:", data)
            break

        entries.extend(data["results"])
        if not data.get("has_more"):
            break
        next_cursor = data.get("next_cursor")

    print(f"✅ Retrieved {len(entries)} entries from Notion")
    return entries

def get_product_titles_and_units(product_relations):
    titles = []
    unidades = []
    for item in product_relations:
        page_id = item.get("id")
        if not page_id:
            continue

        url = f"https://api.notion.com/v1/pages/{page_id}"
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            continue

        props = res.json().get("properties", {})
        title = next((t["plain_text"] for p in props.values() if p["type"] == "title" for t in p.get("title", [])), None)
        unidad = props.get("Unidad", {}).get("select", {}).get("name")
        if title and unidad:
            titles.append(title)
            unidades.append(unidad)

    return titles, unidades

def fetch_products_stream():
    page = 1
    while True:
        response = requests.get(
            WOO_URL,
            params={
                "per_page": 100,
                "page": page,
                "_fields": "id,sku,name,slug,meta_data,attributes,images,price,permalink"
            },
            auth=(WOO_KEY, WOO_SECRET)
        )
        if response.status_code != 200:
            break
        products = response.json()
        if not products:
            break
        for product in products:
            yield product
        page += 1

def build_hospital_product_map():
    entries = get_database_entries()
    now = datetime.now()
    hospital_product_map = {}

    for entry in entries:
        created = entry.get("created_time")
        if not created:
            continue

        created_date = datetime.fromisoformat(created)
        if created_date.month != now.month or created_date.year != now.year:
            continue

        props = entry.get("properties", {})
        unidad_servicio = props.get("Unidad de servicio", {}).get("select", {}).get("name")
        productos = props.get("Productos", {}).get("relation", [])
        if not unidad_servicio or not productos:
            continue

        titles, unidades = get_product_titles_and_units(productos)
        for title, unidad_producto in zip(titles, unidades):
            if unidad_producto == unidad_servicio:
                hospital_id = hospital_to_unidad.get(unidad_servicio)
                if hospital_id:
                    hospital_product_map.setdefault(hospital_id, []).append(title)

    print("✅ Hospital-Product Map built:")
    print(json.dumps(hospital_product_map, indent=2, ensure_ascii=False))
    return hospital_product_map

def send_to_matrix(product, hospital_product_map, filtered_results):
    unidad_id = None
    image_src = None
    price = product.get('price', '')
    product_name = product.get("name")
    permalink = product.get("permalink")

    for meta in product.get("meta_data", []):
        if meta.get("key") == "unidad":
            raw_value = meta.get("value")
            if isinstance(raw_value, list) and raw_value:
                unidad_id = str(raw_value[0])
            elif raw_value is not None:
                unidad_id = str(raw_value)

    for image in product.get("images", []):
        image_src = image.get("src")
        if image_src:
            break

    if unidad_id and unidad_id in hospital_product_map:
        accepted_titles = set(hospital_product_map[unidad_id])
        if product_name in accepted_titles:
            filtered_results.setdefault(unidad_id, []).append({
                'name': product_name,
                'price': price,
                'image': image_src,
                'url': permalink
            })

def match_and_store_products(hospital_product_map):
    print("🔎 Matching WooCommerce products with Notion data...")
    filtered_results = {}
    threads = []
    for product in fetch_products_stream():
        thread = threading.Thread(target=send_to_matrix, args=(product, hospital_product_map, filtered_results))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    print("✅ Matched Matrix:")
    print(json.dumps(filtered_results, indent=2, ensure_ascii=False))
    return filtered_results

def load_email_template():
    with open("email.html", "r", encoding="utf-8") as f:
        return f.read()

def generate_email_html(products):
    html = '<table style="width:100%; border-collapse:collapse;">'
    for i in range(0, len(products), 3):
        html += "<tr>"
        for product in products[i:i+3]:
            html += f"""
            <td style="border:1px solid #ccc; text-align:center; padding:10px;">
                <img src="{product['image']}" alt="{product['name']}" style="max-width:100px;"><br>
                <strong>{product['name']}</strong><br>
                ${product['price']}<br>
                <a href="{product['url']}" style="
                    display: inline-block;
                    margin-top: 8px;
                    padding: 6px 12px;
                    background-color: #6D247A;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    font-size: 14px;
                ">Ver producto</a>
            </td>"""
        html += "</tr>"
    html += "</table>"
    return html

def send_email_to_eloqua(hospital_name, unidad_id, products):
    email_name = f"Productos - {hospital_name}"
    product_html = generate_email_html(products[:6])
    template = load_email_template()
    full_html = template.replace("<!-- PRODUCT_GRID_HERE -->", product_html)

    payload = {
        "name": email_name,
        "subject": email_name,
        "emailGroupId": 1,
        "folderId": int(ELOQUA_FOLDER_ID),
        "htmlContent": {
            "type": "RawHtmlContent",
            "html": full_html
        },
        "encodingId": 1,
        "isTracked": True,
        "isContentProtected": False
    }

    print(f"📤 Sending email to Eloqua for {hospital_name}...")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    url = "https://secure.p04.eloqua.com/API/REST/2.0/assets/email"
    response = requests.post(url, headers=get_eloqua_auth_header(), json=payload)

    if response.status_code == 201:
        print(f"✅ Email created for {hospital_name} with {len(products[:6])} products.")
    else:
        print(f"❌ Failed to create email for {hospital_name}: {response.status_code}")
        print("Response:", response.text)

if __name__ == "__main__":
    if not test_eloqua_auth():
        exit()

    print("Fetching products and matching with Notion data...")
    hospital_product_map = build_hospital_product_map()
    matched_data_matrix = match_and_store_products(hospital_product_map)

    print("\nSending emails to Eloqua...")
    for unidad_id, products in matched_data_matrix.items():
        if products:
            hospital_name = unidad_to_hospital.get(unidad_id, f"Unidad {unidad_id}")
            send_email_to_eloqua(hospital_name, unidad_id, products)
