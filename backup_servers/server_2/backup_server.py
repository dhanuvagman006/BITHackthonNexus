from flask import Flask, send_file, jsonify
import hashlib, os

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
ZIP_FILE = os.path.join(BASE, "backend_backup.zip")
HASH_FILE = os.path.join(BASE, "stored_hash.txt")

@app.route("/check-integrity")
def check():
    try:
        with open(HASH_FILE, "r") as f:
            stored_hash = f.read().strip()
        return jsonify({"status": "clean", "hash": stored_hash})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/get-backup")
def get():
    return send_file(ZIP_FILE)

if __name__ == "__main__":
    import sys
    port = 8002
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    app.run(host="0.0.0.0", port=port)
