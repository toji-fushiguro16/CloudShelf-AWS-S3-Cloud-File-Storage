"""CloudShelf: S3 backed file manager with a local demo mode."""
from __future__ import annotations
import io, os
from pathlib import Path
from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "local-demo-secret-change-before-deploy")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
BUCKET = os.getenv("S3_BUCKET", "").strip()
REGION = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")

def s3_client():
    if not BUCKET: return None
    import boto3
    return boto3.client("s3", region_name=REGION)

def get_files():
    client = s3_client()
    if client:
        items = client.list_objects_v2(Bucket=BUCKET).get("Contents", [])
        return [{"name": x["Key"], "size": x["Size"], "updated": x["LastModified"].strftime("%Y-%m-%d %H:%M UTC")} for x in items], "Amazon S3"
    files = []
    for path in sorted(DATA_DIR.iterdir(), key=lambda p: p.name.lower()):
        if path.is_file(): files.append({"name": path.name, "size": path.stat().st_size, "updated": "Local demo storage"})
    return files, "Local demo storage"

@app.get("/health")
def health(): return {"status": "ok", "storage": "s3" if BUCKET else "local"}

@app.get("/")
def index():
    files, storage = get_files()
    return render_template("index.html", files=files, storage=storage, bucket=BUCKET)

@app.post("/upload")
def upload():
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        flash("Choose a file before uploading.", "error"); return redirect(url_for("index"))
    name = secure_filename(uploaded.filename)
    if not name:
        flash("That filename is not supported.", "error"); return redirect(url_for("index"))
    client = s3_client()
    if client: client.upload_fileobj(uploaded, BUCKET, name)
    else: uploaded.save(DATA_DIR / name)
    flash(f"{name} uploaded successfully.", "success")
    return redirect(url_for("index"))

@app.get("/download/<path:name>")
def download(name):
    client = s3_client()
    if client:
        data = client.get_object(Bucket=BUCKET, Key=name)["Body"].read()
        return send_file(io.BytesIO(data), as_attachment=True, download_name=Path(name).name)
    path = DATA_DIR / secure_filename(name)
    return send_file(path, as_attachment=True) if path.is_file() else ("File not found", 404)

@app.post("/delete/<path:name>")
def delete(name):
    client = s3_client()
    if client: client.delete_object(Bucket=BUCKET, Key=name)
    else:
        path = DATA_DIR / secure_filename(name)
        if path.exists(): path.unlink()
    flash(f"{Path(name).name} deleted.", "success")
    return redirect(url_for("index"))

if __name__ == "__main__": app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
