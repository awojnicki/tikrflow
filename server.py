#!/usr/bin/env python3
import json
import mimetypes
import os
import sqlite3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(ROOT, "public")
DB_PATH = os.path.join(ROOT, "data", "market.db")
PORT = int(os.environ.get("PORT", "4173"))
HOST = os.environ.get("HOST", "0.0.0.0")


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/screen":
            self.send_json(load_screen())
            return
        return super().do_GET()

    def translate_path(self, path):
        parsed = urlparse(path)
        relative = parsed.path.lstrip("/") or "index.html"
        return os.path.normpath(os.path.join(PUBLIC_DIR, relative))

    def send_json(self, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def guess_type(self, path):
        if path.endswith(".js"):
            return "text/javascript; charset=utf-8"
        return mimetypes.guess_type(path)[0] or "application/octet-stream"


def load_screen():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    metadata_row = conn.execute("SELECT value FROM metadata WHERE key = 'import'").fetchone()
    metadata = json.loads(metadata_row["value"]) if metadata_row else {}
    rows = conn.execute(
        """
        SELECT
          s.symbol,
          s.display_symbol AS displaySymbol,
          s.name,
          p.trade_date AS date,
          p.open,
          p.close,
          p.volume,
          i.rsi14,
          i.simple_signal AS simpleSignal,
          i.macd_signal_text AS macdSignal,
          i.ichimoku_signal AS ichimokuSignal,
          CASE
            WHEN p.close > i.ema20 AND i.ema20 > i.ema50 AND i.ema50 > i.ema200 THEN 1
            ELSE 0
          END AS trendMatch,
          CASE WHEN i.rsi14 < 70 THEN 1 ELSE 0 END AS rsiMatch,
          CASE WHEN i.simple_signal = 'KÖP' THEN 1 ELSE 0 END AS simpleSignalMatch,
          CASE WHEN i.ichimoku_signal = 'ICHIMOKU KÖP' THEN 1 ELSE 0 END AS ichimokuMatch
        FROM stocks s
        JOIN prices p ON p.stock_id = s.id
        LEFT JOIN indicators i ON i.stock_id = s.id AND i.trade_date = p.trade_date
        WHERE p.trade_date = (
          SELECT MAX(inner_prices.trade_date)
          FROM prices inner_prices
          WHERE inner_prices.stock_id = s.id
        )
        ORDER BY s.display_symbol
        """
    ).fetchall()
    return {"metadata": metadata, "stocks": [dict(row) for row in rows]}


if __name__ == "__main__":
    os.chdir(PUBLIC_DIR)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Tikrflow running at http://{HOST}:{PORT}")
    server.serve_forever()
