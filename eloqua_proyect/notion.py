import requests
import json
from datetime import datetime
from config import DATABASE_ID, NOTION_API_TOKEN

headers = {
    "Authorization": f"Bearer {NOTION_API_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

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
