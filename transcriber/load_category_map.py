"""
Fungsi untuk memuat pemetaan kode grup produk ke nama kategori dari file JSON.
"""

import os
import json


def load_category_map(category_json_path: str) -> dict:
    """
    Memuat pemetaan grup produk ke kategori dari category.json.
    Contoh: {"A": "Coffee", "EJH": "Home Care", "IQT": "Tea Bontah tarik", ...}
    """
    if not os.path.exists(category_json_path):
        return {}
    with open(category_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["grup"]: item.get("category", "") for item in data}
