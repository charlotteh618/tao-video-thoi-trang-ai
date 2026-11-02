#!/usr/bin/env python3
"""Web Studio don gian cho Aff Video Tool.

Chi chay tren may cua ban (127.0.0.1), khong co dang nhap, khong gui
cookie hay key ra ngoai. Giao dien giup quan ly: tong quan, san pham,
nhan vat, tao video (tao job + prompt de dung trong chat voi Muse),
va ket qua (video trong output/).

Chay: python3 web/server.py
     python3 web/server.py --port 8080
Mo: http://127.0.0.1:8080
"""

import argparse
import json
import os
import sys
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "static"
JOBS_FILE = ROOT / "jobs" / "jobs.json"


def _list_files(folder, suffixes):
    folder = ROOT / folder
    if not folder.exists():
        return []
    out = []
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.suffix.lower() in suffixes:
            out.append({"name": path.name, "size": path.stat().st_size})
    return out


def _read_jobs():
    if not JOBS_FILE.exists():
        return []
    try:
        data = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (ValueError, OSError):
        return []


def _write_jobs(jobs):
    JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    JOBS_FILE.write_text(
        json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8"
    )


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
IMAGE_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


def _safe_name(name):
    """Chi giu ten file anh hop le, chan duong dan ra ngoai thu muc."""
    base = Path(str(name or "")).name.strip()
    safe = "".join(c for c in base if c.isalnum() or c in ("-", "_", "."))
    if not safe or safe.startswith("."):
        return ""
    if Path(safe).suffix.lower() not in IMAGE_SUFFIXES:
        return ""
    return safe


def _read_prompt(name):
    # Chi doc file trong prompts/, khong cho duong dan ra ngoai.
    safe = Path(name).name
    path = ROOT / "prompts" / safe
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, content_type):
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            return self._send_file(STATIC / "index.html", "text/html; charset=utf-8")
        if path == "/app.js":
            return self._send_file(STATIC / "app.js", "text/javascript; charset=utf-8")
        if path == "/style.css":
            return self._send_file(STATIC / "style.css", "text/css; charset=utf-8")

        if path == "/api/overview":
            jobs = _read_jobs()
            return self._send_json(
                {
                    "prompts": len(_list_files("prompts", {".md"})),
                    "jobs": len(jobs),
                    "jobs_done": sum(1 for j in jobs if j.get("status") == "done"),
                    "outputs": len(_list_files("output", {".mp4"})),
                    "products": len(_list_files("input", IMAGE_SUFFIXES)),
                    "characters": len(
                        _list_files(
                            "character-reference",
                            {".png", ".jpg", ".jpeg", ".webp"},
                        )
                    ),
                }
            )
        if path == "/api/prompts":
            items = []
            for item in _list_files("prompts", {".md"}):
                text = _read_prompt(item["name"])
                first = next(
                    (line.lstrip("# ").strip() for line in text.splitlines() if line.strip()),
                    item["name"],
                )
                items.append({"name": item["name"], "title": first, "text": text})
            return self._send_json(items)
        if path == "/api/jobs":
            return self._send_json(_read_jobs())
        if path == "/api/outputs":
            return self._send_json(_list_files("output", {".mp4"}))
        if path == "/api/character":
            return self._send_json(_list_files("character-reference", IMAGE_SUFFIXES))
        if path == "/api/products":
            return self._send_json(_list_files("input", IMAGE_SUFFIXES))
        if path.startswith("/input/"):
            name = _safe_name(unquote(path[len("/input/"):]))
            target = ROOT / "input" / name if name else None
            if target and target.exists():
                return self._send_file(target, IMAGE_TYPES[target.suffix.lower()])
            return self._send_json({"error": "not found"}, status=404)
        if path.startswith("/character/"):
            name = _safe_name(unquote(path[len("/character/"):]))
            target = ROOT / "character-reference" / name if name else None
            if target and target.exists():
                return self._send_file(target, IMAGE_TYPES[target.suffix.lower()])
            return self._send_json({"error": "not found"}, status=404)
        if path.startswith("/output/"):
            name = Path(unquote(path[len("/output/"):])).name
            target = ROOT / "output" / name
            if target.exists() and target.suffix.lower() == ".mp4":
                return self._send_file(target, "video/mp4")
            return self._send_json({"error": "not found"}, status=404)

        return self._send_json({"error": "not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except ValueError:
            body = {}

        if path == "/api/uploads":
            import base64

            kind = str(body.get("kind") or "")
            folder = {"product": "input", "character": "character-reference"}.get(kind)
            name = _safe_name(body.get("name"))
            raw_data = str(body.get("data") or "")
            if "," in raw_data:
                raw_data = raw_data.split(",", 1)[1]
            if not folder or not name:
                return self._send_json(
                    {"error": "Thieu loai anh hoac ten file khong hop le (png/jpg/webp)"},
                    status=400,
                )
            try:
                content = base64.b64decode(raw_data, validate=True)
            except (ValueError, Exception):
                return self._send_json({"error": "Anh khong dung dinh dang"}, status=400)
            if not content or len(content) > 12 * 1024 * 1024:
                return self._send_json(
                    {"error": "Anh qua lon (toi da 12 MB)"}, status=400
                )
            target_dir = ROOT / folder
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / name
            stem, suffix = target.stem, target.suffix
            n = 2
            while target.exists():
                target = target_dir / f"{stem}-{n}{suffix}"
                n += 1
            target.write_bytes(content)
            return self._send_json(
                {"name": target.name, "size": len(content)}, status=201
            )

        if path == "/api/jobs":
            jobs = _read_jobs()
            prompt_name = str(body.get("prompt") or "")
            job = {
                "id": str(len(jobs) + 1),
                "product": str(body.get("product") or "").strip(),
                "product_image": _safe_name(body.get("product_image")),
                "character_image": _safe_name(body.get("character_image")),
                "details": str(body.get("details") or "").strip(),
                "prompt": prompt_name,
                "prompt_text": _read_prompt(prompt_name),
                "notes": str(body.get("notes") or "").strip(),
                "status": "cho_tao",
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
            if not job["product"] or not job["prompt"]:
                return self._send_json(
                    {"error": "Thieu ten san pham hoac prompt"}, status=400
                )
            jobs.append(job)
            _write_jobs(jobs)
            return self._send_json(job, status=201)

        if path.startswith("/api/jobs/") and path.endswith("/done"):
            job_id = path.split("/")[3]
            jobs = _read_jobs()
            for job in jobs:
                if job["id"] == job_id:
                    job["status"] = "done"
                    _write_jobs(jobs)
                    return self._send_json(job)
            return self._send_json({"error": "not found"}, status=404)

        return self._send_json({"error": "not found"}, status=404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) == 3 and parts[0] == "api" and parts[1] in ("products", "characters"):
            folder = "input" if parts[1] == "products" else "character-reference"
            name = _safe_name(unquote(parts[2]))
            target = ROOT / folder / name if name else None
            if target and target.exists():
                target.unlink()
                return self._send_json({"deleted": name})
        return self._send_json({"error": "not found"}, status=404)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Aff Video Tool dang chay: http://{args.host}:{args.port}")
    print("Nhan Ctrl+C de dung. Server chi nghe tren may cua ban.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
