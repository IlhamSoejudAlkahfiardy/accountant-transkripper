"""
Fungsi untuk mengekstrak kata-kata dari halaman dokumen PDF dan mengelompokkannya per baris teks.
"""


def extract_pdf_lines(doc) -> list[tuple[float, list]]:
    """
    Mengekstrak kata-kata per halaman tanpa gangguan header berulang (y < 85)
    dan footer tanda tangan (y > 750), kemudian mengelompokkannya ke dalam baris-baris (lines)
    berdasarkan posisi koordinat y.
    
    Return: list of (y_value, line_words)
    """
    all_lines = []
    
    for page in doc:
        words = page.get_text("words")
        if not words:
            continue
            
        # Filter kata-kata header berulang (y < 85) dan footer tanda tangan (y > 750)
        content_words = [w for w in words if 85 <= w[1] <= 750]
        content_words.sort(key=lambda w: (round(w[1] / 3) * 3, w[0]))
        
        curr_y = None
        curr_line = []
        for w in content_words:
            y_group = round(w[1] / 3) * 3
            if curr_y is None or abs(y_group - curr_y) > 2.5:
                if curr_line:
                    all_lines.append((curr_y, curr_line))
                curr_line = [w]
                curr_y = y_group
            else:
                curr_line.append(w)
        if curr_line:
            all_lines.append((curr_y, curr_line))
            
    return all_lines
