"""
Local runner for Oracle Order & Credit Status Transcriber Web UI.
Jalankan file ini untuk menjalankan web server lokal:
    python app.py
Lalu buka di browser:
    http://localhost:5000
"""
import os
import sys

# Ensure current dir is in sys.path
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from api.index import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n=======================================================")
    print(f"[*] Oracle Scanner Web App berjalan!")
    print(f"[>] Buka browser di: http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=True)

