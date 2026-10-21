"""
Fungsi untuk mengekstrak kata-kata dari halaman dokumen PDF dan mengelompokkannya per baris teks (Engine V2).
Menggunakan clustering vertikal adaptif sehingga tidak memecah kata-kata pada baris yang sama.
"""


def extract_pdf_lines(doc) -> list[tuple[float, list]]:
    """
    Mengekstrak kata-kata per halaman tanpa gangguan header berulang (y < 85)
    dan footer tanda tangan (y > 750), kemudian mengelompokkannya ke dalam baris-baris (lines)
    berdasarkan kedekatan posisi vertikal adaptif (threshold 3.0 point).
    
    Return: list of (y_value, line_words)
    """
    all_lines = []
    
    for page in doc:
        words = page.get_text("words")
        if not words:
            continue
            
        # Filter kata-kata header berulang (y < 85) dan footer tanda tangan (y > 750)
        content_words = [w for w in words if 85 <= w[1] <= 750]
        # Urutkan berdasarkan y0 kemudian x0
        content_words.sort(key=lambda w: (w[1], w[0]))
        
        page_lines = []
        for w in content_words:
            matched = False
            for line in page_lines:
                avg_y = sum(lw[1] for lw in line) / len(line)
                # Jika selisih vertikal <= 3.0 point, kelompokkan ke baris yang sama
                if abs(w[1] - avg_y) <= 3.0:
                    line.append(w)
                    matched = True
                    break
            if not matched:
                page_lines.append([w])
                
        # Urutkan kata-kata pada setiap baris dari kiri ke kanan (x0)
        for line in page_lines:
            line.sort(key=lambda w: w[0])
            all_lines.append((line[0][1], line))
            
    return all_lines
