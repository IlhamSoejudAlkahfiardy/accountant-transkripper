"""
Fungsi untuk menentukan tingkat otorisasi overdue berdasarkan hari keterlambatan dan limit kredit (Engine V2).
"""


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
        return ""
    
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
            return "GM"
        else:
            return "GM"
