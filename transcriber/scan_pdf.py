"""
Fungsi utama untuk mem-parsing dokumen PDF Credix (FRM-LOG-027) secara dinamis.
"""

import pymupdf
from .load_category_map import load_category_map
from .extract_pdf_lines import extract_pdf_lines
from .group_order_blocks import group_order_blocks
from .parse_order_block import parse_order_block


def scan_pdf(pdf_path, category_json_path: str) -> list[dict]:
    """
    Parser dan scanner PDF yang sepenuhnya dinamis untuk laporan Credix Reports (FRM-LOG-027).
    Mampu membaca dan memproses dokumen PDF apapun dengan tata letak laporan yang sama,
    termasuk order yang terpecah melintasi beberapa halaman (cross-page).
    
    Argumen:
      - pdf_path: path file string atau bytes/bytearray data PDF
      - category_json_path: path ke file category.json
      
    Return: list of parsed order dicts
    """
    category_map = load_category_map(category_json_path)
    if isinstance(pdf_path, (bytes, bytearray)):
        doc = pymupdf.open(stream=pdf_path, filetype="pdf")
    else:
        doc = pymupdf.open(pdf_path)

    lines = extract_pdf_lines(doc)
    all_order_blocks = group_order_blocks(lines)

    parsed_orders = []
    for block in all_order_blocks:
        order_item = parse_order_block(block, category_map)
        parsed_orders.append(order_item)

    return parsed_orders
