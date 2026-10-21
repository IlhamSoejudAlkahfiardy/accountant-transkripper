"""
Fungsi untuk membersihkan prefix nomor customer (misal menghilangkan '0100-') (Engine V2).
"""


def clean_customer_number(raw_cust_no: str) -> str:
    """
    Adjustment: Menghilangkan 4 digit awal (misal '0100-')
    dan hanya menampilkan sisa nomor customer (misal '0025791').
    """
    raw_cust_no = raw_cust_no.strip()
    if "-" in raw_cust_no:
        parts = raw_cust_no.split("-", 1)
        return parts[1].strip()
    elif len(raw_cust_no) > 4:
        return raw_cust_no[4:].lstrip("-").strip()
    return raw_cust_no
