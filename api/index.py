import os
import sys
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add root directory to sys.path so order_scanner can be imported in any context
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from order_scanner import scan_pdf

# Determine static folder path (public folder in root)
static_dir = os.path.join(root_dir, "public")
app = Flask(__name__, static_folder=static_dir, static_url_path="")
app.url_map.strict_slashes = False
CORS(app, resources={r"/*": {"origins": "*"}})



@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    return response


def get_category_path():
    # Look in current_dir first, then root_dir
    local_path = os.path.join(current_dir, "category.json")
    if os.path.exists(local_path):
        return local_path
    return os.path.join(root_dir, "category.json")


@app.route("/")
def serve_index():
    if os.path.exists(os.path.join(static_dir, "index.html")):
        return send_from_directory(static_dir, "index.html")
    return jsonify({"status": "ok", "message": "Credix Scanner API is online"}), 200


@app.route("/<path:path>")
def serve_static(path):
    if os.path.exists(os.path.join(static_dir, path)):
        return send_from_directory(static_dir, path)
    return jsonify({"error": "Not found"}), 404


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Credix Order & Credit Scanner API",
        "version": "1.0.0"
    }), 200


@app.route("/api/parse", methods=["POST", "OPTIONS", "GET"])
@app.route("/parse", methods=["POST", "OPTIONS", "GET"])
def parse_pdf():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    if request.method == "GET":
        return jsonify({"status": "ready", "message": "Gunakan POST multipart/form-data untuk parse PDF"}), 200

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


@app.route("/api/sample", methods=["GET"])
def sample_parse():
    """Endpoint pembantu untuk menguji sistem dengan file contoh."""
    sample_paths = [
        os.path.join(root_dir, "file", "file_3.pdf"),
        os.path.join(root_dir, "file", "file_2.pdf"),
        os.path.join(root_dir, "file", "file.pdf")
    ]
    target_sample = None
    for p in sample_paths:
        if os.path.exists(p):
            target_sample = p
            break

    if not target_sample:
        return jsonify({"error": "File contoh tidak ditemukan di server."}), 404

    try:
        with open(target_sample, "rb") as f:
            pdf_bytes = f.read()
        cat_path = get_category_path()
        orders = scan_pdf(pdf_bytes, cat_path)
        return jsonify({
            "success": True,
            "filename": os.path.basename(target_sample),
            "file_size": len(pdf_bytes),
            "total_orders": len(orders),
            "orders": orders,
            "is_sample": True
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Export app for Vercel Serverless Function
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Server running on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)

