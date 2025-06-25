from notion import get_database_entries, get_product_titles_and_units
from woocommerce import fetch_products_stream
from eloqua import test_eloqua_auth, send_email_to_eloqua, get_or_create_monthly_folder
from email_template import load_email_template, generate_email_html
from utils import clean_product_name
from config import ELOQUA_FOLDER_ID
import json

# Other imports and mappings here

if __name__ == "__main__":
    if not test_eloqua_auth():
        exit()

    get_or_create_monthly_folder()  # Ensure folder exists first

    hospital_product_map = build_hospital_product_map()  # from notion.py
    matched_data_matrix = match_and_store_products(hospital_product_map)  # matching logic remains

    for unidad_id, products in matched_data_matrix.items():
        if products:
            hospital_name = unidad_to_hospital.get(unidad_id, f"Unidad {unidad_id}")
            for product in products:
                product["name"] = clean_product_name(product["name"], hospital_name)
            send_email_to_eloqua(hospital_name, unidad_id, products)
