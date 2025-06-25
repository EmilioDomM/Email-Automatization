import os
from dotenv import load_dotenv

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

NOTION_HEADERS = {
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

FALLBACK_IMAGES = [
    "https://uxkomf.stripocdn.email/content/guids/CABINET_0347bc35b3efc51497569a7bf5ba974f7d4cd4706262b1fc7ba4d253bd492e16/images/checkupejecutivo_mayor_40.png",
    "https://uxkomf.stripocdn.email/content/guids/CABINET_0347bc35b3efc51497569a7bf5ba974f7d4cd4706262b1fc7ba4d253bd492e16/images/checkupejecutivo_menor_40.png",
]
