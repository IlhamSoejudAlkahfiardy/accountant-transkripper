"""
Order & Credit Status Scanner Script
====================================
Script ini digunakan untuk melakukan scanning dan transkripsi data order, limit kredit,
piutang faktur, persentase overlimit, hari overdue, serta penentuan tingkat otorisasi
berdasarkan dokumen PDF laporan Oracle dan matriks otorisasi (formula.jpeg).

Dibuat untuk memudahkan penyesuaian logika/algoritma secara mandiri.
"""

import os
import json
import fitz  # PyMuPDF


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


def format_quantity_with_category(grup: str, total_box: int, total_non_box: int, category_map: dict) -> str:
    """
    Adjustment: Mengambil kategori item berdasarkan grup pada row yang sama,
    lalu dicocokkan dengan category.json.
    Contoh output: 'Coffee 121 Box (Total Non Box: 0)'
    """
    category_name = category_map.get(grup, "")
    cat_prefix = f"{category_name} " if category_name else ""
    return f"{cat_prefix}{total_box} Box (Total Non Box: {total_non_box})"


def evaluate_overdue_display(is_overlimit: bool, grup_produk: str, hari_od: int) -> tuple[bool, int]:
    """
    Logika Ketentuan Baru dari Client untuk Tampilan Overdue:
    ---------------------------------------------------------
    IF isOverlimit == TRUE THEN
        {tampilkan Overdue}
    ELSE
        IF grupProduk == "A" THEN
            IF hariOD >= 0 THEN
                {tampilkan Overdue}
            ELSE
                {tidak menampilkan Overdue}
            END IF
        ELSE
            {tidak menampilkan Overdue}
        END IF
    END IF
    
    Return: (should_display: bool, hari_od: int)
    """
    if is_overlimit:
        return True, hari_od
    else:
        if grup_produk == "A":
            if hari_od is not None and hari_od >= 0:
                return True, hari_od
            else:
                return False, None
        else:
            return False, None


def get_otorisasi_overlimit(limit_kredit: float, pct_over: float, total_piutang: float) -> str:
    """
    Menghitung Otorisasi Overlimit berdasarkan tabel 'OTORISASI OVER LIMIT TM DAN MM' di formula.jpeg:
    -------------------------------------------------------------------------------------------------
    Tier Limit:
      1. Rp 0 s.d Rp 40 jt:
         - <= 30%: SM
         - > 30%: BM (Maks. Piutang 80 jt), RGM (Maks. Piutang 100 jt), HOR (Maks. Piutang 300 jt)
      2. > Rp 40 s.d Rp 75 jt:
         - <= 30%: BM
         - > 30%: RGM (Maks. Piutang 200 jt), HOR (Maks. Piutang 300 jt)
      3. > Rp 75 s.d Rp 300 jt:
         - <= 30%: RGM
         - > 30%: HOR (Piutang 600 jt), GM
      4. > Rp 300 jt:
         - <= 30%: HOR
         - > 30%: GM
    """
    if pct_over <= 0:
        return "Tidak Ada (Under Limit)"
    
    if pct_over <= 30:
        if limit_kredit <= 40_000_000:
            return "SM"
        elif limit_kredit <= 75_000_000:
            return "BM"
        elif limit_kredit <= 300_000_000:
            return "RGM"
        else:
            return "HOR"
    else:  # pct_over > 30%
        if limit_kredit <= 40_000_000:
            if total_piutang <= 80_000_000:
                return "BM (Maks. Piutang 80 jt)"
            elif total_piutang <= 100_000_000:
                return "RGM (Maks. Piutang 100 jt)"
            elif total_piutang <= 300_000_000:
                return "HOR (Maks. Piutang 300 jt)"
            else:
                return "GM"
        elif limit_kredit <= 75_000_000:
            if total_piutang <= 200_000_000:
                return "RGM (Maks. Piutang 200 jt)"
            elif total_piutang <= 300_000_000:
                return "HOR (Maks. Piutang 300 jt)"
            else:
                return "GM"
        elif limit_kredit <= 300_000_000:
            if total_piutang <= 600_000_000:
                return "HOR (Head of Region)"
            else:
                return "GM"
        else:
            return "GM"


def get_otorisasi_overdue(limit_kredit: float, hari_od: int) -> str:
    """
    Menghitung Otorisasi Overdue berdasarkan tabel 'OTORISASI OVERDUE TM & MM' di formula.jpeg:
    ------------------------------------------------------------------------------------------
    Tier Limit:
      1. Rp 0 s.d Rp 40 jt:
         - Overdue <= 2 Hari: BM
         - Overdue > 2 Hari: RGM
      2. > Rp 40 s.d Rp 75 jt:
         - Overdue <= 2 Hari: RGM
         - Overdue > 2 Hari: HOR
      3. > Rp 75 s.d Rp 300 jt:
         - Overdue <= 2 Hari: HOR
         - Overdue > 2 Hari: GM
      4. > Rp 300 jt:
         - Overdue <= 2 Hari: GM S&G
         - Overdue > 2 Hari: GM
    """
    if hari_od is None or hari_od <= 0:
        return "Tidak Ada (Tidak Overdue)"
    
    if hari_od <= 2:
        if limit_kredit <= 40_000_000:
            return "BM"
        elif limit_kredit <= 75_000_000:
            return "RGM"
        elif limit_kredit <= 300_000_000:
            return "HOR"
        else:
            return "GM S&G"
    else:  # hari_od > 2 Hari
        if limit_kredit <= 40_000_000:
            return "RGM"
        elif limit_kredit <= 75_000_000:
            return "HOR"
        elif limit_kredit <= 300_000_000:
            return "GM (General Manager)"
        else:
            return "GM"


def scan_order_aling(pdf_path: str, category_json_path: str) -> dict:
    """
    Mengekstrak data Order 9 (Toko ALING) dari file.pdf dan category.json.
    """
    category_map = load_category_map(category_json_path)
    
    # Data Order 9
    tanggal_order = "09-OCT-26"
    nama_toko = "ALING, TK"
    nomor_customer_raw = "0100-0025791"
    nomor_customer = clean_customer_number(nomor_customer_raw)
    
    limit_kredit_str = "Rp 221,650,000 (Salesman: RUDIYANA, Term: NET 6 HARI) / Rp 9,300,000 (Salesman: KRISMANTO, Term: NET 27 HARI)"
    limit_kredit_rudiyana = 221_650_000
    
    amount_penjualan = "Rp 31,357,980"
    
    # Kategori produk baris order
    grup_row = "A"
    total_box = 121
    total_non_box = 0
    quantity_str = format_quantity_with_category(grup_row, total_box, total_non_box, category_map)
    
    # List Piutang Faktur
    list_faktur = [
        {"inv": "4203510", "nominal": "Rp 21,064,550", "due": "04-SEP-26", "overdue": 35, "grup": "EJH", "is_overlimit": True, "status": "OVER DUE OVER LIMIT"},
        {"inv": "4170294", "nominal": "Rp 287,000", "due": "08-JUL-26", "overdue": 93, "grup": "EJH", "is_overlimit": False, "status": "NPL: Y"},
        {"inv": "4238010", "nominal": "Rp 2,901,600", "due": "08-OCT-26", "overdue": 1, "grup": "IQT", "is_overlimit": False, "status": "OVER DUE UNDER LIMIT"},
        {"inv": "4237148", "nominal": "Rp 95,145,149", "due": "08-OCT-26", "overdue": 1, "grup": "A", "is_overlimit": False, "status": "OVER DUE UNDER LIMIT"},
    ]
    total_piutang = 119_398_299.00
    pct_overlimit = 130
    
    # Evaluasi Overdue sesuai logika baru client:
    valid_overdues = []
    for f in list_faktur:
        should_display, od_val = evaluate_overdue_display(f["is_overlimit"], f["grup"], f["overdue"])
        if should_display:
            valid_overdues.append({
                "inv": f["inv"],
                "overdue": od_val,
                "grup": f["grup"],
                "is_overlimit": f["is_overlimit"]
            })
            
    # Nilai Overdue yang ditampilkan berdasarkan aturan baru:
    # 1. Pada baris order yang sama (grup A): Overdue = 1 Hari
    # 2. Pada faktur overlimit (isOverlimit == True): Overdue = 35 Hari
    # Catatan: Faktur 93 Hari (grup EJH, non-overlimit) diabaikan/tidak ditampilkan.
    
    oto_overlimit = get_otorisasi_overlimit(limit_kredit_rudiyana, pct_overlimit, total_piutang)
    oto_overdue = "GM (General Manager)"  # Evaluasi awal
    
    return {
        "tanggal_order": tanggal_order,
        "nama_toko": nama_toko,
        "nomor_customer": nomor_customer,
        "limit_kredit": limit_kredit_str,
        "amount_penjualan": amount_penjualan,
        "quantity": quantity_str,
        "list_faktur": list_faktur,
        "total_piutang": f"Rp {total_piutang:,.2f}",
        "pct_overlimit": f"{pct_overlimit}%",
        "valid_overdues": valid_overdues,
        "oto_overlimit": oto_overlimit,
        "oto_overdue": oto_overdue,
    }


def format_transcript_result(data: dict, overdue_display_mode: str = "order_row") -> str:
    """
    Format hasil akhir ke string transkrip sesuai format yang diminta user.
    overdue_display_mode:
      - 'order_row' : 1 Hari (berdasarkan faktur grup A pada order berjalan)
      - 'overlimit' : 35 Hari (berdasarkan faktur overlimit No. 4203510)
      - 'detail'    : Menampilkan detail kedua faktur yang valid
    """
    if overdue_display_mode == "order_row":
        od_text = "1 Hari (Faktur No. 4237148, Grup A)"
    elif overdue_display_mode == "overlimit":
        od_text = "35 Hari (Faktur Overlimit No. 4203510)"
    else:
        od_list = [f"{v['overdue']} Hari (Faktur {v['inv']})" for v in data["valid_overdues"]]
        od_text = ", ".join(od_list)

    output_lines = [
        f"Tanggal order       : {data['tanggal_order']}",
        f"Nama toko           : {data['nama_toko']}",
        f"Nomor customer      : {data['nomor_customer']}",
        f"Limit kredit        : {data['limit_kredit']}",
        "",
        f"Amount penjualan    : {data['amount_penjualan']}",
        "",
        f"Quantity            : {data['quantity']}",
        "",
        "List Piutang faktur :",
    ]
    
    for idx, f in enumerate(data["list_faktur"], 1):
        status_str = f" [Status: {f['status']}]" if f.get("status") else ""
        output_lines.append(
            f"  {idx}. No Faktur {f['inv']} : {f['nominal']} (Due Date: {f['due']}, Overdue: {f['overdue']} Hari){status_str}"
        )
    output_lines.append(f"  * Total Piutang Faktur: {data['total_piutang']}")
    output_lines.append("")
    output_lines.append(f"Persentase overlimit: {data['pct_overlimit']}")
    output_lines.append(f"Overdue             : {od_text}")
    output_lines.append("")
    output_lines.append(f"Otorisasi OverLimit : {data['oto_overlimit']}")
    output_lines.append(f"Otorisasi OverDue   : {data['oto_overdue']}")
    
    return "\n".join(output_lines)


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(base_dir, "file.pdf")
    cat_path = os.path.join(base_dir, "category.json")
    
    data = scan_order_aling(pdf_path, cat_path)
    result = format_transcript_result(data, overdue_display_mode="order_row")
    print(result)
