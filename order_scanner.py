"""
Order & Credit Status Scanner Script (Facade & CLI Runner)
==========================================================
File ini menyediakan facade kompatibilitas mundur dan runner CLI untuk modul `transcriber`.
Seluruh implementasi algoritma dan logika transkrip berada di dalam paket `transcriber/`.
"""

import os
import sys

# Ensure root directory is in sys.path
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from transcriber_factory import (
    get_active_engine_name,
    load_category_map,
    clean_customer_number,
    format_quantity_with_category,
    calculate_nominal_overlimit,
    evaluate_overdue_display,
    get_otorisasi_overlimit,
    get_otorisasi_overdue,
    format_transcript_result,
    extract_pdf_lines,
    group_order_blocks,
    parse_order_block,
    scan_pdf,
)

__all__ = [
    "load_category_map",
    "clean_customer_number",
    "format_quantity_with_category",
    "calculate_nominal_overlimit",
    "evaluate_overdue_display",
    "get_otorisasi_overlimit",
    "get_otorisasi_overdue",
    "format_transcript_result",
    "extract_pdf_lines",
    "group_order_blocks",
    "parse_order_block",
    "scan_pdf",
]


if __name__ == "__main__":
    cat_path = os.path.join(base_dir, "category.json")
    
    # Menerima path file apapun dari argumen CLI (misal: python order_scanner.py path/ke/file.pdf)
    if len(sys.argv) > 1:
        target_pdf = sys.argv[1]
    else:
        # Default jika dijalankan tanpa argumen: gunakan file/file_2.pdf jika ada, atau file/file.pdf
        f2 = os.path.join(base_dir, "file", "file_2.pdf")
        target_pdf = f2 if os.path.exists(f2) else os.path.join(base_dir, "file", "file.pdf")
        
    engine_name = get_active_engine_name()
    print(f"Scanning PDF secara dinamis (Engine: {engine_name.upper()}): {target_pdf}")
    scanned_orders = scan_pdf(target_pdf, cat_path)
    print(f"Ditemukan {len(scanned_orders)} order:")
    print("=" * 60)
    
    for idx, order in enumerate(scanned_orders, 1):
        print(f"=== ORDER #{idx}: {order['nama_toko']} ===")
        print(format_transcript_result(order))
        print("-" * 60)
