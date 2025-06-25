import os, requests, threading, base64, re, json, random
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

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
    "H. Alta Especialidad": {"unidad_id": "565", "url_id": "53120233092"},
    "H. Conchita": {"unidad_id": "566", "url_id": "53120233093"},
    "H. Sur": {"unidad_id": "567", "url_id": "53120233094"},
    "H. Vidriera": {"unidad_id": "568", "url_id": "53120233095"},
    "H. Reynosa": {"unidad_id": "569", "url_id": "53120233096"},
    "H. del Parque": {"unidad_id": "570", "url_id": "53120233097"},
    "H. Saltillo": {"unidad_id": "571", "url_id": "53120233098"},
    "H. Betania": {"unidad_id": "572", "url_id": "53120233099"},
    "H. UPAEP": {"unidad_id": "573", "url_id": "53120233100"},
    "H. San Nicolás": {"unidad_id": "574", "url_id": "53120233101"},
    "H. Faro del Mayab": {"unidad_id": "575", "url_id": "53120233102"},
    "H. Cumbres": {"unidad_id": "576", "url_id": "53120233103"},
    "H. Altagracia": {"unidad_id": "577", "url_id": "53120233104"},
    "C. San Pedro": {"unidad_id": "578", "url_id": "53120233105"},
    "C. Juventud": {"unidad_id": "579", "url_id": "53120233106"},
    "C. Irapuato": {"unidad_id": "580", "url_id": "53120233107"},
}

unidad_to_hospital = {v["unidad_id"]: k for k, v in hospital_to_unidad.items()}

hospital_to_siglas = {
    "H. Alta Especialidad": "cmae",
    "H. Conchita": "cmc",
    "H. Sur": "cmsur",
    "H. Vidriera": "cmv",
    "H. Reynosa": "cmr",
    "H. del Parque": "cmdp",
    "H. Saltillo": "cms",
    "H. Betania": "cmb",
    "H. UPAEP": "cmupaep",
    "H. San Nicolás": "cmsn",
    "H. Faro del Mayab": "cmfm",
    "H. Cumbres": "cmcu",
    "H. Altagracia": "cmag",
    "C. San Pedro": "cmsp",
    "C. Juventud": "cmj",
    "C. Irapuato": "cmi",
}


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
                "_fields": "id,sku,name,slug,meta_data,attributes,images,price,permalink,on_sale,status"
            },
            auth=(WOO_KEY, WOO_SECRET)
        )
        if response.status_code != 200:
            break
        products = response.json()
        if not products:
            break
        for product in products:
            if product.get("status") == "publish":
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
                hospital_data = hospital_to_unidad.get(unidad_servicio)
                if hospital_data:
                    unidad_id = hospital_data["unidad_id"]
                    hospital_product_map.setdefault(unidad_id, []).append(title)

    print("✅ Hospital-Product Map built:")
    print(json.dumps(hospital_product_map, indent=2, ensure_ascii=False))
    return hospital_product_map


def clean_product_name(name, hospital_name=None):
    cleaned = re.sub(r"\s*\(.*?\)\s*", " ", name)
    cleaned = re.sub(r"CHRISTUS MUGUERZA", "", cleaned, flags=re.IGNORECASE)

    if hospital_name:
        possible_aliases = [
            hospital_name,
            hospital_name.replace("H. ", "Hospital "),
            hospital_name.replace("C. ", "Clínica ")
        ]
        for alias in possible_aliases:
            cleaned = re.sub(re.escape(alias), "", cleaned, flags=re.IGNORECASE)

    return re.sub(r"\s{2,}", " ", cleaned).strip()

BANNER_GIFS = [
    "http://img04.en25.com/EloquaImages/clients/Christus/%7B6d051d00-67ac-40cc-8952-2b0639faa692%7D_gif_muguerza_1.gif",
    "http://img04.en25.com/EloquaImages/clients/Christus/%7B1c4ce003-491f-4fcc-89de-1f98295b015e%7D_gif_muguerza_2.gif",
    "http://img04.en25.com/EloquaImages/clients/Christus/%7Bea96ab7a-559c-479c-9f4d-805cf90a2359%7D_gif_muguerza_3.gif",
    "http://img04.en25.com/EloquaImages/clients/Christus/%7Bdd05ab25-a1a5-4d09-9e80-2c1dc14ec0dd%7D_gif_muguerza_4.gif"
]

def get_fallback_image(product_name):
    hombre_images = [
        "https://uxkomf.stripocdn.email/content/guids/CABINET_0347bc35b3efc51497569a7bf5ba974f7d4cd4706262b1fc7ba4d253bd492e16/images/checkupejecutivo_mayor_40.png",
        "https://uxkomf.stripocdn.email/content/guids/CABINET_0347bc35b3efc51497569a7bf5ba974f7d4cd4706262b1fc7ba4d253bd492e16/images/checkupejecutivo_menor_40.png",
        "http://img04.en25.com/EloquaImages/clients/Christus/%7B522e17d6-fe96-470f-b54c-aee4ee2b441a%7D_hombre_imagen2.png",
        "http://img04.en25.com/EloquaImages/clients/Christus/%7B6004ff72-8112-4004-aaff-b9829091951f%7D_hombre_imagen1.png"
    ]

    mujer_images = [
        "http://img04.en25.com/EloquaImages/clients/Christus/%7Bc376debc-4c79-4c13-88d6-b0ac4ad8f64d%7D_mujer_imagen3.png",
        "http://img04.en25.com/EloquaImages/clients/Christus/%7B94918eca-20cb-4c7c-baba-36fb6e141710%7D_mujer_imagen2.png",
        "http://img04.en25.com/EloquaImages/clients/Christus/%7Bb27377da-3fa0-4d8b-bece-152a949ba108%7D_mujer_imagen4.png",
        "http://img04.en25.com/EloquaImages/clients/Christus/%7B11a8f1cd-468f-42b9-8071-dd8b12fe0c0c%7D_mujer_imagen1.png"
    ]

    general_images = [
        "http://img04.en25.com/EloquaImages/clients/Christus/%7Bd916f173-8bce-40b9-922b-b7e34e87387f%7D_general_imagen1.png",
        "http://img04.en25.com/EloquaImages/clients/Christus/%7B138547e7-ce71-4d6e-ac99-83bf8d457003%7D_general_imagen2.png",
        "http://img04.en25.com/EloquaImages/clients/Christus/%7B903a1676-5ee0-4dc0-b19f-3e1194f92d1a%7D_general_imagen3.png"
    ]

    all_images = hombre_images + mujer_images + general_images
    name_lower = product_name.lower()

    if "hombre" in name_lower:
        return random.choice(hombre_images)
    elif "mujer" in name_lower:
        return random.choice(mujer_images)
    else:
        return random.choice(all_images)


def send_to_matrix(product, hospital_product_map, filtered_results):
    unidad_id = None
    price = product.get('price', '')
    product_name = product.get("name")
    slug = product.get("slug")

    for meta in product.get("meta_data", []):
        if meta.get("key") == "unidad":
            raw_value = meta.get("value")
            if isinstance(raw_value, list) and raw_value:
                unidad_id = str(raw_value[0])
            elif raw_value is not None:
                unidad_id = str(raw_value)

    image_src = get_fallback_image(product_name)

    if unidad_id and unidad_id in hospital_product_map:
        accepted_titles = set(hospital_product_map[unidad_id])
        if product_name in accepted_titles:
            hospital_name = unidad_to_hospital.get(unidad_id)
            if hospital_name:
                siglas = hospital_to_siglas[hospital_name].lower()
                url_id = hospital_to_unidad[hospital_name]["url_id"]
                constructed_url = (
                    f"https://christusmuguerza.com.mx/producto/{slug}/"
                    f"?select_unidad={url_id}"
                    f"&utm_source=eloqua"
                    f"&utm_medium=email"
                    f"&utm_campaign=correos_dinamicos_{siglas}"
                )
            else:
                constructed_url = f"https://christusmuguerza.com.mx/producto/{slug}/"

            filtered_results.setdefault(unidad_id, []).append({
                'name': product_name,
                'price': price,
                'image': image_src,
                'url': constructed_url,
                'on_sale': product.get('on_sale', False)
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
    html = """
    <!--[if mso]>
    <style type="text/css">
        .fallback-table {width: 100% !important;}
    </style>
    <![endif]-->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" align="center" style="border-collapse: collapse; margin: 0 auto;">
    """

    total = len(products)
    per_row = 3

    for i in range(0, total, per_row):
        chunk = products[i:i + per_row]
        num_items = len(chunk)

        # Calculate spacing for center alignment
        spacer_td = ''
        if num_items == 1:
            spacer_td = '<td width="33%"></td>'
        elif num_items == 2:
            spacer_td = '<td width="16.5%"></td>'

        html += "<tr>"

        if spacer_td:
            html += spacer_td

        for product in chunk:
            # Botón dinámico dependiendo de si está en oferta
            on_sale = product.get("on_sale", False)
            button_text = "En Oferta" if on_sale else "Ver producto"
            button_color = "#FFA500" if on_sale else "#6D247A"
            button_border = "#FFA500" if on_sale else "#6D247A"

            html += f"""
            <td align="center" valign="top" style="padding: 10px; vertical-align: top;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse: collapse; background-color: white; height: 400px; table-layout: fixed;">
                    <tr>
                        <td align="center" style="height: 180px;">
                            <img src="{product['image']}" alt="{product['name']}" width="180px" style="display: block; max-width: 100%; height: auto;" />
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="font-family: Arial, sans-serif; font-size: 20px; line-height: 24px; height: 80px; display: table-cell; vertical-align: middle;">
                            <div style="display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; max-height: 72px; line-height: 24px; margin: 0 auto;">
                                {product['name']}
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="font-family: Arial, sans-serif; font-size: 28px; font-weight: bold; color: #6D247A; height: 50px; display: table-cell; vertical-align: bottom;">
                            ${product['price']}
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="padding: 10px 0; display: table-cell; vertical-align: top;">
                            <a href="{product['url']}" style="
                                display: inline-block;
                                padding: 10px 26px;
                                text-decoration: none;
                                font-size: 18px;
                                border: 2px solid {button_border};
                                border-radius: 24px;
                                color: white;
                                background-color: {button_color};
                                font-family: Arial, sans-serif;
                            ">{button_text}</a>
                        </td>
                    </tr>
                </table>
            </td>
            """

        if spacer_td:
            html += spacer_td

        html += "</tr>"

    html += "</table>"
    return html

def inject_random_banner(html_template):
    # Reemplaza la URL original de la imagen por un GIF aleatorio
    original_banner_url = "http://img04.en25.com/EloquaImages/clients/Christus/%7B3952c7f5-400c-4741-957c-2f4b15ee8d01%7D_image_5ss.png"
    random_gif = random.choice(BANNER_GIFS)
    return html_template.replace(original_banner_url, random_gif)


def send_email_to_eloqua(hospital_name, unidad_id, products):
    now = datetime.now()
    month_year = now.strftime("%B %Y")  # e.g. "June 2025"
    email_name = f"Productos - {hospital_name} - {month_year}"
    product_html = generate_email_html(products[:6])
    template = load_email_template()
    template = inject_random_banner(template)
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
            
            for product in products:
                product["name"] = clean_product_name(product["name"], hospital_name)

            send_email_to_eloqua(hospital_name, unidad_id, products)