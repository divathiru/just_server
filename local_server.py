#!/usr/bin/env python3
"""
Watershed Telemetry — local server + dashboard host.
No pip install needed — uses only the Python standard library.

Run:
    python3 local_server.py

Then:
    - Dashboard:       http://localhost:5000/
    - ESP32 posts to:  http://<this-laptop's-LAN-IP>:5000/telemetry
      (find your LAN IP with `ipconfig` on Windows, `ifconfig`/`hostname -I` on Mac/Linux)

Keep this file in the SAME FOLDER as watershed_telemetry_dashboard.html.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 5000
HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watershed_telemetry_dashboard.html")

readings = []  # in-memory history, most recent last
MAX_HISTORY = 50


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            try:
                with open(HTML_FILE, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self._cors()
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self.send_response(404)
                self._cors()
                self.end_headers()
                self.wfile.write(b"watershed_telemetry_dashboard.html not found next to this script.")
            return

        if self.path == "/telemetry/latest":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            latest = readings[-1] if readings else {}
            self.wfile.write(json.dumps(latest).encode())
            return

        if self.path == "/telemetry":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps(readings).encode())
            return

        self.send_response(404)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path == "/telemetry":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_response(400)
                self._cors()
                self.end_headers()
                self.wfile.write(b'{"error":"bad json"}')
                return
            readings.append(data)
            if len(readings) > MAX_HISTORY:
                readings.pop(0)
            print(f"received: {data}")
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
            return

        self.send_response(404)
        self._cors()
        self.end_headers()

    def log_message(self, format, *args):
        pass  # keep the terminal clean — only "received: ..." lines print


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Watershed local server running on port {PORT}")
    print(f"Dashboard:      http://localhost:{PORT}/")
    print(f"ESP32 endpoint: http://<this-laptop's-LAN-IP>:{PORT}/telemetry")
    server.serve_forever()