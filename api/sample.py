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
@app.route("/api/sample", methods=["GET", "POST", "OPTIONS"])
@app.route("/sample", methods=["GET", "POST", "OPTIONS"])
def handle_sample():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

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
        return jsonify({"error": "File contoh tidak tersedia di server. Silakan upload file PDF Anda sendiri."}), 404

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


if __name__ == "__main__":
    app.run(port=5002, debug=True)
