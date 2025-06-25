# 📧 Automatización de Correos Dinámicos para Productos CHRISTUS MUGUERZA

Este proyecto automatiza la generación y envío de correos electrónicos dinámicos usando productos de WooCommerce, Notion como fuente de datos, y Eloqua como plataforma de distribución.

---

## 🔧 ¿Qué hace este sistema?

1. **Conecta con Notion** para obtener los productos asignados por hospital.
2. **Filtra productos activos** desde WooCommerce (`status == "publish"`).
3. **Cruza información de Notion y WooCommerce**, asegurando que los productos coincidan con su unidad/hospital.
4. **Genera una plantilla HTML personalizada** para cada hospital con máximo 6 productos (con diseño responsivo 3x en escritorio y 2x en móviles).
5. **Publica el correo directamente en Eloqua**, en la carpeta correspondiente.
6. **Asigna automáticamente links con parámetros UTM** para seguimiento analítico.

---

## 🧠 Estructura de Archivos

| Archivo        | Propósito |
|----------------|----------|
| `emails.py`    | Script principal que hace toda la lógica de autenticación, extracción, filtrado y envío. |
| `email.html`   | Plantilla base del correo. Se inyectan los productos y un banner aleatorio. |
| `.env`         | Contiene todas las claves y configuraciones necesarias (seguridad). |

---

## 📦 Requisitos

- Python 3.9+
- Cuenta en Notion con acceso al API
- WooCommerce con API habilitada
- Plataforma Eloqua (API activada)

Instala dependencias con:

```bash
pip install python-dotenv requests
```

---

## 🔐 .env (Ejemplo)

Este archivo debe estar en la raíz del proyecto y **no debe compartirse públicamente**.

```env
NOTION_API_TOKEN=secret_xxxx
DATABASE_ID_FORMS=xxxxxxxxxxxxxxxxxxx

WOO_URL=https://dominio.com/wp-json/wc/v3/products
WOO_KEY=ck_xxxxx
WOO_SECRET=cs_xxxxx

ELOQUA_COMPANY=empresa
ELOQUA_USERNAME=usuario
ELOQUA_PASSWORD=clave
ELOQUA_EMAIL_FOLDER_ID=1234
```

---

## 🚀 Cómo usar

Una vez configurado `.env`, ejecuta:

```bash
python emails.py
```

El script hará lo siguiente automáticamente:

- Autenticarse con Eloqua
- Consultar entradas recientes de Notion (del mes actual)
- Obtener productos activos desde WooCommerce
- Filtrar productos válidos por hospital
- Generar un correo por hospital con hasta 6 productos
- Enviar a Eloqua como nuevo email en la carpeta indicada

---

## 💡 Detalles técnicos

- Se usa `@media` CSS para asegurar que el diseño en móviles sea **2x2x2** productos.
- Si un producto no tiene imagen, se asigna un **fallback aleatorio** (hombre, mujer o general).
- Se selecciona también un **banner GIF aleatorio** para mayor dinamismo visual.
- Los enlaces de producto incluyen `utm_campaign=correos_dinamicos_<siglas>` para segmentar por hospital.

---

## 📁 Plantilla HTML

El archivo `email.html` contiene un marcador especial que **no debes eliminar**:

```html
<!-- PRODUCT_GRID_HERE -->
```

Aquí se insertan los productos dinámicamente al generar el correo.

---

## ✅ Ejemplo de resultado final

Correo para **H. Sur**:

- Nombre del email: `Productos - H. Sur - June 2025`
- 6 productos como máximo
- GIF superior rotativo
- Diseño adaptativo
- Enlaces personalizados

---
