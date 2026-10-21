"""
Transcriber Engine Factory & Dynamic Switcher
==============================================
Modul ini bertindak sebagai switch dinamis antara:
- v1: Pendekatan pertama (folder `transcriber`, menggunakan koordinat kaku)
- v2: Pendekatan terbaru (folder `transcriber_v2`, menggunakan baris adaptif & pola teks)

Konfigurasi ditentukan melalui file `.env` dengan variabel `TRANSCRIBER_ENGINE=v1` atau `TRANSCRIBER_ENGINE=v2`.
"""

import os
import sys

# Pastikan direktori root berada dalam sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def load_env_variables(env_path: str = None) -> dict:
    """
    Parser sederhana untuk membaca file .env tanpa ketergantungan library luar.
    """
    if env_path is None:
        env_path = os.path.join(BASE_DIR, ".env")
        
    env_vars = {}
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        env_vars[k] = v
                        # Set juga ke os.environ jika belum ada
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass
    return env_vars


# Muat variabel .env saat modul diimpor
load_env_variables()


def get_active_engine_name() -> str:
    """
    Mengembalikan nama engine yang aktif ('v1' atau 'v2'). Default adalah 'v2'.
    """
    val = os.environ.get("TRANSCRIBER_ENGINE", "").strip().lower()
    if val in ("v1", "legacy", "1"):
        return "v1"
    return "v2"


ACTIVE_ENGINE = get_active_engine_name()

if ACTIVE_ENGINE == "v1":
    import transcriber as _engine
else:
    import transcriber_v2 as _engine

# Ekspos seluruh fungsi sesuai engine yang terpilih
scan_pdf = _engine.scan_pdf
load_category_map = _engine.load_category_map
clean_customer_number = _engine.clean_customer_number
format_quantity_with_category = _engine.format_quantity_with_category
calculate_nominal_overlimit = _engine.calculate_nominal_overlimit
evaluate_overdue_display = _engine.evaluate_overdue_display
get_otorisasi_overlimit = _engine.get_otorisasi_overlimit
get_otorisasi_overdue = _engine.get_otorisasi_overdue
format_transcript_result = _engine.format_transcript_result
extract_pdf_lines = _engine.extract_pdf_lines
group_order_blocks = _engine.group_order_blocks
parse_order_block = _engine.parse_order_block

__all__ = [
    "get_active_engine_name",
    "scan_pdf",
    "load_category_map",
    "clean_customer_number",
    "format_quantity_with_category",
    "calculate_nominal_overlimit",
    "evaluate_overdue_display",
    "get_otorisasi_overlimit",
    "get_otorisasi_overdue",
    "format_transcript_result",
    "extract_pdf_lines",
    "group_order_blocks",
    "parse_order_block",
]
