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
            return self._send_json(
                _list_files(
                    "character-reference", {".png", ".jpg", ".jpeg", ".webp"}
                )
            )
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

        if path == "/api/jobs":
            jobs = _read_jobs()
            prompt_name = str(body.get("prompt") or "")
            job = {
                "id": str(len(jobs) + 1),
                "product": str(body.get("product") or "").strip(),
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
