"""
Fungsi untuk mengelompokkan baris-baris teks PDF ke dalam blok-blok pesanan toko (order blocks).
"""

import re


def group_order_blocks(lines: list[tuple[float, list]]) -> list[dict]:
    """
    Mengelompokkan baris-baris teks menjadi blok order berdasarkan deteksi
    header awal order (Nomor urut + Nama Toko + Tanggal order pada baris yang sama).
    Mendukung order yang terpotong antar beberapa halaman (cross-page).
    
    Return: list of dict {"header_words": list, "body_lines": list}
    """
    all_order_blocks = []
    current_order = None
    
    for y_val, l_words in lines:
        first_w = l_words[0]
        is_new_order = False
        if 15 <= first_w[0] <= 35 and first_w[4].isdigit() and len(l_words) > 1:
            second_w = l_words[1]
            if 40 <= second_w[0] <= 110:
                has_date = any(re.match(r"^\d{2}-[A-Z]{3}-\d{2}$", w[4]) for w in l_words if 450 <= w[0] <= 510)
                if has_date:
                    is_new_order = True
                    
        if is_new_order:
            if current_order:
                all_order_blocks.append(current_order)
            current_order = {"header_words": l_words, "body_lines": []}
        else:
            if current_order:
                current_order["body_lines"].append((y_val, l_words))
                
    if current_order:
        all_order_blocks.append(current_order)
        
    return all_order_blocks
