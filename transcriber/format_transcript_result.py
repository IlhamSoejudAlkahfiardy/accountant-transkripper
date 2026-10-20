"""
Fungsi untuk menyusun teks transkrip siap salin sesuai format standar Credix.
"""


def format_transcript_result(data: dict) -> str:
    """
    Format hasil akhir ke string transkrip sesuai format standar yang diminta user.
    """
    od_text = data.get("overdue_str", "-")
    
    output_lines = [
        f"Tanggal order       : {data['tanggal_order']}",
        f"Nama toko           : {data['nama_toko']} STR {data['oto_overlimit'] or data['oto_overdue']}",
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
