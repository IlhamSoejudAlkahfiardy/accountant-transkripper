import os
import sys
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from order_scanner import scan_pdf

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app, resources={r"/*": {"origins": "*"}})


@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    return response


def get_category_path():
    p = os.path.join(current_dir, "category.json")
    if os.path.exists(p):
        return p
    return os.path.join(root_dir, "category.json")


@app.route("/", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/parse", methods=["GET", "POST", "OPTIONS"])
@app.route("/parse", methods=["GET", "POST", "OPTIONS"])
def handle_parse():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    if request.method == "GET":
        return jsonify({
            "status": "ready",
            "endpoint": "/api/parse",
            "message": "Gunakan POST multipart/form-data dengan field 'file' (.pdf) untuk memproses laporan."
        }), 200

    if "file" not in request.files:
        return jsonify({"error": "Tidak ada file yang diunggah. Silakan pilih file PDF."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "File tidak boleh kosong."}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Format file tidak didukung. Harap unggah file PDF (.pdf)."}), 400

    try:
        pdf_bytes = file.read()
        if len(pdf_bytes) == 0:
            return jsonify({"error": "File PDF kosong (ukuran 0 byte)."}), 400

        cat_path = get_category_path()
        orders = scan_pdf(pdf_bytes, cat_path)

        return jsonify({
            "success": True,
            "filename": file.filename,
            "file_size": len(pdf_bytes),
            "total_orders": len(orders),
            "orders": orders
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Gagal membaca atau mem-parsing PDF: {str(e)}"
        }), 500


# Export for Vercel Serverless Function
if __name__ == "__main__":
    app.run(port=5001, debug=True)
