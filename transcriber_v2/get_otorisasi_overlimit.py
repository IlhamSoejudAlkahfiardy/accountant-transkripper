"""
Fungsi untuk menentukan tingkat otorisasi overlimit berdasarkan matriks persetujuan formula.jpeg (Engine V2).
"""


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
        return ""
    
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
                return "BM"
            elif total_piutang <= 100_000_000:
                return "RGM"
            elif total_piutang <= 300_000_000:
                return "HOR"
            else:
                return "GM"
        elif limit_kredit <= 75_000_000:
            if total_piutang <= 200_000_000:
                return "RGM"
            elif total_piutang <= 300_000_000:
                return "HOR"
            else:
                return "GM"
        elif limit_kredit <= 300_000_000:
            if total_piutang <= 600_000_000:
                return "HOR"
            else:
                return "GM"
        else:
            return "GM"
