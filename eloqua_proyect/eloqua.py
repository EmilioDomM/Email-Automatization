import base64
import requests
from datetime import datetime
from config import ELOQUA_COMPANY, ELOQUA_USERNAME, ELOQUA_PASSWORD, ELOQUA_FOLDER_ID


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

def send_email_to_eloqua(hospital_name, unidad_id, products):
    email_name = f"Productos - {hospital_name}"
    product_html = generate_email_html(products[:6])
    template = load_email_template()
    full_html = template.replace("<!-- PRODUCT_GRID_HERE -->", product_html)

    # Use the monthly folder
    folder_id = get_or_create_monthly_folder(ELOQUA_FOLDER_ID)
    if folder_id is None:
        print("❌ Cannot proceed without valid folder.")
        return

    payload = {
        "name": email_name,
        "subject": email_name,
        "emailGroupId": 1,
        "folderId": int(folder_id),
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

def get_or_create_monthly_folder(parent_folder_id):
    """
    Checks if a folder named 'Month-Year' exists under the parent_folder_id.
    If it doesn't, creates it. Returns the folder ID.
    """
    now = datetime.now()
    month_year = now.strftime("%B-%Y")  # e.g., "June-2025"

    # Fetch existing folders under the parent
    url = f"https://secure.p04.eloqua.com/API/REST/1.0/assets/email/folders?depth=complete"
    response = requests.get(url, headers=get_eloqua_auth_header())
    if response.status_code != 200:
        print("❌ Failed to retrieve folders:", response.status_code, response.text)
        return None

    folders = response.json().get('elements', [])
    for folder in folders:
        if folder.get("name") == month_year and folder.get("parentId") == int(parent_folder_id):
            print(f"✅ Found existing folder: {month_year} (ID: {folder.get('id')})")
            return folder.get("id")

    # Folder not found, create it
    payload = {
        "name": month_year,
        "parentId": int(parent_folder_id)
    }
    create_url = "https://secure.p04.eloqua.com/API/REST/1.0/assets/email/folder"
    create_response = requests.post(create_url, headers=get_eloqua_auth_header(), json=payload)

    if create_response.status_code == 201:
        new_folder_id = create_response.json().get("id")
        print(f"📁 Created new folder: {month_year} (ID: {new_folder_id})")
        return new_folder_id
    else:
        print("❌ Failed to create folder:", create_response.status_code, create_response.text)
        return None
