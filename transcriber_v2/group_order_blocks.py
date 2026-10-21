"""
Fungsi untuk mengelompokkan baris-baris teks PDF ke dalam blok-blok pesanan toko (Engine V2).
Mendeteksi header awal order berdasarkan pola nomor urut dan tanggal order.
"""

import re


def group_order_blocks(lines: list[tuple[float, list]]) -> list[dict]:
    """
    Mengelompokkan baris-baris teks menjadi blok order berdasarkan deteksi
    header awal order (Nomor urut di kolom kiri + format tanggal pesanan pada baris yang sama).
    Mendukung order yang terpotong antar beberapa halaman (cross-page).
    
    Return: list of dict {"header_words": list, "body_lines": list}
    """
    all_order_blocks = []
    current_order = None
    
    for y_val, l_words in lines:
        if not l_words:
            continue
            
        first_w = l_words[0]
        is_new_order = False
        
        # Deteksi awal order baru:
        # 1. Kata pertama berada di margin kiri kolom No (x0 antara 15 s.d 35) dan berupa angka digit
        if 15 <= first_w[0] <= 35 and first_w[4].isdigit() and len(l_words) > 2:
            # 2. Baris memuat pola tanggal pesanan resmi Credix (contoh: 16-OCT-26 atau 12-OCT-26)
            has_date = any(re.match(r"^\d{2}-[A-Z]{3}-\d{2}$", w[4]) for w in l_words)
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
