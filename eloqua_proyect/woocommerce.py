import requests
from config import WOO_URL, WOO_KEY, WOO_SECRET

def fetch_products_stream():
    page = 1
    while True:
        response = requests.get(
            WOO_URL,
            params={
                "per_page": 100,
                "page": page,
                "_fields": "id,sku,name,slug,meta_data,attributes,images,price,permalink,on_sale"
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