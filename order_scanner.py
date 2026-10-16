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


def calculate_nominal_overlimit(amount_order: float, piutang_menggantung: float, limit_kredit: float) -> tuple[float, float, str]:
    """
    Menghitung nominal overlimit (Rp) dan persentase overlimit (%)
    berdasarkan rumus resmi di formula.jpeg:
    -------------------------------------------------------------
    Nominal Overlimit = (Jumlah Orderan + Piutang Menggantung) - Limit Kredit
    Persentase Overlimit = (Nominal Overlimit / Limit Kredit) * 100%
    
    Format: 'Rp {nominal:,} ({pct}%)'
    Contoh:
      - Toko CIPTA TK: Rp 35,847,292 (36%)
      - TOKO HIDUP BARU: Rp 650,978 (325%)
      - Jika tidak overlimit: Rp 0 (0%)
    """
    if limit_kredit <= 0:
        return 0.0, 0.0, "Rp 0 (0%)"
    
    total_exposure = amount_order + piutang_menggantung
    nominal_overlimit = total_exposure - limit_kredit
    
    if nominal_overlimit > 0:
        pct = (nominal_overlimit / limit_kredit) * 100
        formatted_str = f"Rp {nominal_overlimit:,.0f} ({round(pct)}%)"
        return nominal_overlimit, pct, formatted_str
    else:
        return 0.0, 0.0, "Rp 0 (0%)"


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


def scan_pdf(pdf_path: str, category_json_path: str) -> list[dict]:
    """
    Parser dan scanner PDF yang sepenuhnya dinamis untuk laporan Oracle Reports (FRM-LOG-027).
    Mampu membaca dan memproses dokumen PDF apapun dengan tata letak laporan yang sama,
    termasuk order yang terpecah melintasi beberapa halaman (cross-page).
    """
    import re
    category_map = load_category_map(category_json_path)
    doc = fitz.open(pdf_path)
    
    all_order_blocks = []
    current_order = None
    
    # 1. Ekstraksi kata-kata per halaman tanpa gangguan header & footer statis
    for page in doc:
        words = page.get_text("words")
        if not words:
            continue
            
        # Filter kata-kata header berulang (y < 85) dan footer tanda tangan (y > 750)
        content_words = [w for w in words if 85 <= w[1] <= 750]
        content_words.sort(key=lambda w: (round(w[1] / 3) * 3, w[0]))
        
        lines = []
        curr_y = None
        curr_line = []
        for w in content_words:
            y_group = round(w[1] / 3) * 3
            if curr_y is None or abs(y_group - curr_y) > 2.5:
                if curr_line:
                    lines.append((curr_y, curr_line))
                curr_line = [w]
                curr_y = y_group
            else:
                curr_line.append(w)
        if curr_line:
            lines.append((curr_y, curr_line))
            
        # Deteksi awal order baru (Nomor urut + Nama Toko + Tanggal order pada baris yang sama)
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
        
    # 2. Parsing rincian masing-masing order secara dinamis
    parsed_orders = []
    for block in all_order_blocks:
        hw = block["header_words"]
        order_num = int(hw[0][4])
        shop_words = [w[4] for w in hw if 40 <= w[0] < 180]
        nama_toko = " ".join(shop_words).strip()
        
        tgl_words = [w[4] for w in hw if 450 <= w[0] <= 510 and re.match(r"^\d{2}-[A-Z]{3}-\d{2}$", w[4])]
        tanggal_order = tgl_words[0] if tgl_words else ""
        
        amt_words = [w[4] for w in hw if 660 <= w[0] <= 740 and ("," in w[4] or w[4].isdigit())]
        amt_str = f"Rp {amt_words[0]}" if amt_words else ""
        amt_num = float(amt_words[0].replace(",", "")) if amt_words else 0.0
        
        # Cek jika amount berada di baris awal body (terkadang sedikit bergeser koordinat y)
        if amt_num == 0.0:
            for _, lw in block["body_lines"][:3]:
                bw = [w[4] for w in lw if 660 <= w[0] <= 740 and ("," in w[4] or w[4].isdigit())]
                if bw:
                    amt_str = f"Rp {bw[0]}"
                    amt_num = float(bw[0].replace(",", ""))
                    break
                    
        # Cari nomor customer
        nomor_cust_raw = ""
        for _, lw in block["body_lines"]:
            for w in lw:
                if (w[4].startswith("0100-") or w[4].startswith("0103-")) and 35 <= w[0] <= 115:
                    nomor_cust_raw = w[4]
                    break
            if nomor_cust_raw:
                break
                
        # Total Box dan Total Non Box
        total_box = 0
        total_non_box = 0
        for _, lw in block["body_lines"]:
            ltxt = " ".join([w[4] for w in lw])
            if "TOTAL BOX" in ltxt:
                vals = [w[4] for w in lw if 1140 <= w[0] <= 1225 and w[4].isdigit()]
                if vals:
                    total_box = int(vals[0])
            elif "TOTAL NON BOX" in ltxt:
                vals = [w[4] for w in lw if 1140 <= w[0] <= 1225 and w[4].isdigit()]
                if vals:
                    total_non_box = int(vals[0])
                    
        sales_entries = []
        faktur_entries = []
        grup_order = "A"
        total_piutang_str = "Rp 0.00"
        total_piutang_val = 0.0
        
        in_sales_section = False
        primary_sales_row = None
        overlimit_line = None
        
        for l_idx, (_, lw) in enumerate(block["body_lines"]):
            ltxt = " ".join([w[4] for w in lw])
            if "SALESPERSON" in ltxt:
                in_sales_section = True
                continue
                
            if "TOTAL" in ltxt and in_sales_section:
                # Cari total piutang faktur di baris ini dan baris sekitarnya (toleransi koordinat y)
                candidate_words = list(lw)
                if l_idx > 0:
                    candidate_words.extend(block["body_lines"][l_idx - 1][1])
                if l_idx + 1 < len(block["body_lines"]):
                    candidate_words.extend(block["body_lines"][l_idx + 1][1])
                for w in candidate_words:
                    val_txt = w[4].replace(",", "")
                    if 420 <= w[0] <= 530 and ("," in w[4] or "." in w[4]):
                        try:
                            f_val = float(val_txt)
                            total_piutang_str = f"Rp {w[4]}"
                            total_piutang_val = f_val
                            break
                        except:
                            pass
                            
            if in_sales_section:
                s_words = [w[4] for w in lw if 15 <= w[0] < 155]
                term_words = [w[4] for w in lw if 155 <= w[0] < 235]
                lim_words = [w[4] for w in lw if 235 <= w[0] < 320]
                
                inv_words = [w[4] for w in lw if 320 <= w[0] < 380 and w[4].isdigit()]
                nom_words = [w[4] for w in lw if 420 <= w[0] < 475 and ("," in w[4] or w[4].isdigit())]
                due_words = [w[4] for w in lw if 490 <= w[0] < 540 and "-" in w[4]]
                od_words = [w[4] for w in lw if 560 <= w[0] < 595 and (w[4].isdigit() or (w[4].startswith("-") and w[4][1:].isdigit()))]
                grp_words = [w[4] for w in lw if 600 <= w[0] < 635 and w[4].isalpha()]
                
                ord_amt_words = [w[4] for w in lw if 1100 <= w[0] < 1165 and ("," in w[4] or w[4].isdigit())]
                stat_words = [w[4] for w in lw if 1160 <= w[0] < 1290]
                pct_words = [w[4] for w in lw if 1290 <= w[0] < 1350 and w[4].isdigit()]
                
                # Baris Salesman & Limit Kredit
                if s_words and term_words and lim_words:
                    s_name = " ".join(s_words)
                    s_term = " ".join(term_words)
                    s_lim_str = lim_words[0]
                    s_lim_clean = s_lim_str.replace(",", "")
                    s_lim_num = float(s_lim_clean) if s_lim_clean.isdigit() else 0.0
                    
                    if not (s_name.startswith("0100-") and s_lim_num == 0):
                        row_entry = {
                            "salesman": s_name,
                            "term": s_term,
                            "limit_str": s_lim_str,
                            "limit_num": s_lim_num,
                            "has_order": bool(ord_amt_words)
                        }
                        sales_entries.append(row_entry)
                        if ord_amt_words:
                            primary_sales_row = row_entry
                            
                if ord_amt_words:
                    row_order_val = float(ord_amt_words[0].replace(",", ""))
                    if amt_num == 0.0:
                        amt_num = row_order_val
                        amt_str = f"Rp {ord_amt_words[0]}"
                if ord_amt_words and grp_words:
                    grup_order = grp_words[0]
                    
                # Cek baris overlimit
                stat_text = " ".join(stat_words)
                is_line_ol = "OVER LIMIT" in stat_text or (pct_words and int(pct_words[0]) > 0)
                
                if is_line_ol and not overlimit_line:
                    p_num = float(nom_words[0].replace(",", "")) if nom_words else 0.0
                    s_clean = lim_words[0].replace(",", "") if lim_words else ""
                    if s_clean.isdigit() and float(s_clean) > 0:
                        s_num = float(s_clean)
                    elif primary_sales_row:
                        s_num = primary_sales_row["limit_num"]
                    elif sales_entries:
                        s_num = sales_entries[0]["limit_num"]
                    else:
                        s_num = 0.0
                        
                    pct_n = int(pct_words[0]) if pct_words else 0
                    row_ord_amt = float(ord_amt_words[0].replace(",", "")) if ord_amt_words else (amt_num if bool(ord_amt_words) else 0.0)
                    
                    overlimit_line = {
                        "limit": s_num,
                        "order_amt": row_ord_amt,
                        "piutang_row": p_num,
                        "pct": pct_n
                    }
                    
                # Baris Faktur Piutang
                if inv_words and nom_words and due_words:
                    inv_no = inv_words[0]
                    inv_nom = nom_words[0]
                    inv_due = due_words[0]
                    inv_od = int(od_words[0]) if od_words else 0
                    inv_grp = grp_words[0] if grp_words else ""
                    inv_stat = " ".join(stat_words)
                    faktur_entries.append({
                        "inv": inv_no,
                        "nominal": f"Rp {inv_nom}",
                        "due": inv_due,
                        "overdue": inv_od,
                        "grup": inv_grp,
                        "is_overlimit": "OVER LIMIT" in inv_stat,
                        "status": inv_stat
                    })
                    
        if not primary_sales_row and sales_entries:
            primary_sales_row = sales_entries[0]
            
        primary_limit = primary_sales_row["limit_num"] if primary_sales_row else 0.0
        
        # Susun tampilan Limit kredit
        if sales_entries:
            other_entries = [s for s in sales_entries if s != primary_sales_row]
            sorted_entries = [primary_sales_row] + other_entries
            limit_str_parts = []
            seen = set()
            for s in sorted_entries:
                key = (s["limit_num"], s["salesman"], s["term"])
                if key not in seen and s["limit_num"] > 0:
                    seen.add(key)
                    limit_str_parts.append(f"Rp {s['limit_num']:,.0f} (Salesman: {s['salesman']}, Term: {s['term']})")
            limit_kredit_display = " / ".join(limit_str_parts) if limit_str_parts else f"Rp {primary_limit:,.0f}"
        else:
            limit_kredit_display = "Rp 0"
            
        # Hitung Nominal & Persentase Overlimit menggunakan rumus resmi formula.jpeg:
        # Nominal Overlimit = (Jumlah Orderan + Piutang Menggantung) - Limit Kredit
        if overlimit_line:
            nom_over, pct_over, str_over = calculate_nominal_overlimit(
                amount_order=overlimit_line["order_amt"],
                piutang_menggantung=overlimit_line["piutang_row"],
                limit_kredit=overlimit_line["limit"]
            )
            # Jika persentase di PDF memiliki pembulatan khusus, sinkronkan
            if overlimit_line["pct"] > 0 and nom_over > 0:
                str_over = f"Rp {nom_over:,.0f} ({overlimit_line['pct']}%)"
                pct_over = float(overlimit_line["pct"])
        else:
            nom_over, pct_over, str_over = 0.0, 0.0, "Rp 0 (0%)"
            
        # Evaluasi Overdue sesuai aturan baru client:
        # IF isOverlimit == TRUE THEN {tampilkan} ELSE IF grup == "A" AND hariOD >= 0 THEN {tampilkan}
        valid_overdues = []
        for f in faktur_entries:
            should_disp, od_val = evaluate_overdue_display(f["is_overlimit"], f["grup"], f["overdue"])
            if should_disp:
                valid_overdues.append({
                    "inv": f["inv"],
                    "overdue": od_val,
                    "grup": f["grup"],
                    "is_overlimit": f["is_overlimit"]
                })
                
        if not valid_overdues:
            if any(f["overdue"] < 0 for f in faktur_entries):
                min_od = min(f["overdue"] for f in faktur_entries)
                overdue_display = f"- (Belum Jatuh Tempo: {min_od} Hari)"
            elif faktur_entries and not any(f["grup"] == "A" for f in faktur_entries):
                overdue_display = "- (Faktur bukan grup A & Under Limit)"
            else:
                overdue_display = "-"
            primary_od_days = None
        else:
            top_od = valid_overdues[0]
            for v in valid_overdues:
                if v["grup"] == "A":
                    top_od = v
                    break
            overdue_display = f"{top_od['overdue']} Hari (Faktur No. {top_od['inv']})"
            primary_od_days = top_od["overdue"]
            
        # Otorisasi Overlimit & Overdue
        oto_ol = get_otorisasi_overlimit(primary_limit, pct_over, total_piutang_val)
        oto_od = get_otorisasi_overdue(primary_limit, primary_od_days)
        
        # Quantity dengan kategori
        qty_display = format_quantity_with_category(grup_order, total_box, total_non_box, category_map)
        
        parsed_orders.append({
            "order_num": order_num,
            "tanggal_order": tanggal_order,
            "nama_toko": nama_toko,
            "nomor_customer": clean_customer_number(nomor_cust_raw),
            "limit_kredit": limit_kredit_display,
            "amount_penjualan": amt_str if amt_str else "Rp 0",
            "quantity": qty_display,
            "list_faktur": faktur_entries,
            "total_piutang": total_piutang_str,
            "nominal_overlimit": nom_over,
            "pct_overlimit_val": pct_over,
            "pct_overlimit": str_over,
            "overdue_str": overdue_display,
            "oto_overlimit": oto_ol,
            "oto_overdue": oto_od
        })
        
    return parsed_orders


def format_transcript_result(data: dict) -> str:
    """
    Format hasil akhir ke string transkrip sesuai format standar yang diminta user.
    """
    od_text = data.get("overdue_str", "-")
    
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
    
    if data.get("list_faktur"):
        for idx, f in enumerate(data["list_faktur"], 1):
            status_str = f" [Status: {f['status']}]" if f.get("status") else ""
            output_lines.append(
                f"  {idx}. No Faktur {f['inv']} : {f['nominal']} (Due Date: {f['due']}, Overdue: {f['overdue']} Hari){status_str}"
            )
    else:
        output_lines.append("  (Tidak ada faktur piutang menggantung)")
        
    output_lines.append(f"  * Total Piutang Faktur: {data['total_piutang']}")
    output_lines.append("")
    output_lines.append(f"Persentase overlimit: {data['pct_overlimit']}")
    output_lines.append(f"Overdue             : {od_text}")
    output_lines.append("")
    output_lines.append(f"Otorisasi OverLimit : {data['oto_overlimit']}")
    output_lines.append(f"Otorisasi OverDue   : {data['oto_overdue']}")
    
    return "\n".join(output_lines)


if __name__ == "__main__":
    import sys
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cat_path = os.path.join(base_dir, "category.json")
    
    # Menerima path file apapun dari argumen CLI (misal: python order_scanner.py path/ke/file.pdf)
    if len(sys.argv) > 1:
        target_pdf = sys.argv[1]
    else:
        # Default jika dijalankan tanpa argumen: gunakan file/file_2.pdf jika ada, atau file/file.pdf
        f2 = os.path.join(base_dir, "file", "file_2.pdf")
        target_pdf = f2 if os.path.exists(f2) else os.path.join(base_dir, "file", "file.pdf")
        
    print(f"Scanning PDF secara dinamis: {target_pdf}")
    scanned_orders = scan_pdf(target_pdf, cat_path)
    print(f"Ditemukan {len(scanned_orders)} order:")
    print("=" * 60)
    
    for idx, order in enumerate(scanned_orders, 1):
        print(f"=== ORDER #{idx}: {order['nama_toko']} ===")
        print(format_transcript_result(order))
        print("-" * 60)
