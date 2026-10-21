"""
Fungsi untuk mengevaluasi apakah hari overdue perlu ditampilkan sesuai aturan bisnis (Engine V2).
"""


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
