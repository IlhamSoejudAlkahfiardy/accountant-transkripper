"""
Fungsi untuk mengevaluasi apakah hari overdue perlu ditampilkan sesuai aturan bisnis.
"""


def evaluate_overdue_display(is_overlimit: bool, grup_produk: str, hari_od: int) -> tuple[bool, int]:
    """
    Logika Ketentuan Baru dari Client untuk Tampilan Overdue:
    ---------------------------------------------------------
    IF hariOD < 1 THEN
        {tidak menampilkan Overdue}

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
            # {tidak menampilkan Overdue}
            {menampilkan Overdue}
        END IF
    END IF
    
    Return: (should_display: bool, hari_od: int)
    """
    if hari_od is None or hari_od < 1:
            return False, None
    
    if is_overlimit:
        return True, hari_od
    else:
        if grup_produk == "A":
            if hari_od is not None and hari_od >= 0:
                return True, hari_od
            else:
                return False, None
        else:
            # {tidak menampilkan Overdue}
            return True, hari_od
