"""
Fungsi untuk memformat tampilan kuantiti order dilengkapi nama kategori produk (Engine V2).
"""


def format_quantity_with_category(grup: str, total_box: int, total_non_box: int, category_map: dict) -> str:
    """
    Adjustment: Mengambil kategori item berdasarkan grup pada row yang sama,
    lalu dicocokkan dengan category.json.
    Contoh output: 'Coffee 121 Box (Total Non Box: 0)'
    """
    category_name = category_map.get(grup, "")
    cat_prefix = f"{category_name} " if category_name else ""
    return f"{cat_prefix}{total_box} Box (Total Non Box: {total_non_box})"
