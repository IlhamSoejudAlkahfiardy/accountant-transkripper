"""
Fungsi untuk menghitung nominal dan persentase overlimit berdasarkan rumus resmi di formula.jpeg (Engine V2).
"""


def calculate_nominal_overlimit(amount_order: float, piutang_menggantung: float, limit_kredit: float) -> tuple[float, float, str]:
    """
    Menghitung nominal overlimit (Rp) dan persentase overlimit (%)
    berdasarkan rumus resmi di formula.jpeg:
    -------------------------------------------------------------
    Nominal Overlimit = (Jumlah Orderan + Piutang Menggantung) - Limit Kredit
    Persentase Overlimit = (Nominal Overlimit / Limit Kredit) * 100%
    
    Format: 'Rp {nominal:,} ({pct}%)'
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
