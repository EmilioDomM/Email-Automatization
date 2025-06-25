import re
import random
from config import FALLBACK_IMAGES

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

