"""
Fungsi untuk mem-parsing satu blok pesanan toko (order block) menjadi dictionary data terstruktur.
"""

import re
from .clean_customer_number import clean_customer_number
from .format_quantity_with_category import format_quantity_with_category
from .calculate_nominal_overlimit import calculate_nominal_overlimit
from .evaluate_overdue_display import evaluate_overdue_display
from .get_otorisasi_overlimit import get_otorisasi_overlimit
from .get_otorisasi_overdue import get_otorisasi_overdue
from .format_transcript_result import format_transcript_result


def parse_order_block(block: dict, category_map: dict) -> dict:
    """
    Mem-parsing satu blok data pesanan toko yang sudah diekstraksi dari PDF,
    melakukan kalkulasi limit, piutang faktur, overlimit, overdue, serta otorisasi.
    
    Return: dict order_item lengkap dengan formatted_transcript
    """
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
                        row_ord_val = float(ord_amt_words[0].replace(",", ""))
                        if primary_sales_row is None or abs(row_ord_val - amt_num) < 1.0:
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
    
    # Susun tampilan Limit kredit (hanya baris yang sebaris dengan nilai kolom ORDER)
    if primary_sales_row:
        limit_kredit_display = f"Rp {primary_sales_row['limit_num']:,.0f}"
    elif sales_entries:
        limit_kredit_display = f"Rp {sales_entries[0]['limit_num']:,.0f}"
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
    
    order_item = {
        "order_num": order_num,
        "tanggal_order": tanggal_order,
        "nama_toko": nama_toko,
        "nama_toko_str": f"{nama_toko} STR {oto_ol or oto_od}".strip(),
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
    }
    order_item["formatted_transcript"] = format_transcript_result(order_item)
    return order_item
