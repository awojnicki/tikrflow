#!/usr/bin/env python3
import json
import mimetypes
import os
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


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
        if parsed.path == "/api/stock":
            params = parse_qs(parsed.query)
            symbol = params.get("symbol", [""])[0]
            detail = load_stock_detail(symbol)
            self.send_json(detail if detail else {"error": "Bolaget hittades inte"}, 404 if detail is None else 200)
            return
        return super().do_GET()

    def translate_path(self, path):
        parsed = urlparse(path)
        relative = parsed.path.lstrip("/") or "index.html"
        return os.path.normpath(os.path.join(PUBLIC_DIR, relative))

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
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
          CASE s.segment
            WHEN 'Large Cap' THEN 'L'
            WHEN 'Mid Cap' THEN 'M'
            WHEN 'Small Cap' THEN 'S'
            ELSE SUBSTR(s.segment, 1, 1)
          END AS segment,
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


def load_stock_detail(symbol):
    if not symbol:
        return None

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    stock = conn.execute(
        """
        SELECT
          id,
          symbol,
          display_symbol AS displaySymbol,
          name,
          market,
          segment,
          currency
        FROM stocks
        WHERE symbol = ? OR display_symbol = ?
        """,
        (symbol, symbol),
    ).fetchone()
    if stock is None:
        return None

    latest = conn.execute(
        """
        SELECT
          p.trade_date AS date,
          p.open,
          p.high,
          p.low,
          p.close,
          p.volume,
          i.ema20,
          i.ema50,
          i.ema200,
          i.rsi14,
          i.simple_signal AS simpleSignal,
          i.macd,
          i.macd_signal AS macdSignalValue,
          i.macd_histogram AS macdHistogram,
          i.macd_signal_text AS macdSignal,
          i.tenkan_sen AS tenkanSen,
          i.kijun_sen AS kijunSen,
          i.senkou_span_a AS senkouSpanA,
          i.senkou_span_b AS senkouSpanB,
          i.chikou_span AS chikouSpan,
          i.ichimoku_signal AS ichimokuSignal
        FROM prices p
        LEFT JOIN indicators i ON i.stock_id = p.stock_id AND i.trade_date = p.trade_date
        WHERE p.stock_id = ?
        ORDER BY p.trade_date DESC
        LIMIT 1
        """,
        (stock["id"],),
    ).fetchone()

    history = conn.execute(
        """
        SELECT
          p.trade_date AS date,
          p.open,
          p.high,
          p.low,
          p.close,
          p.volume,
          i.ema20,
          i.ema50,
          i.ema200,
          i.tenkan_sen AS tenkanSen,
          i.kijun_sen AS kijunSen,
          i.senkou_span_a AS senkouSpanA,
          i.senkou_span_b AS senkouSpanB
        FROM prices p
        LEFT JOIN indicators i ON i.stock_id = p.stock_id AND i.trade_date = p.trade_date
        WHERE p.stock_id = ?
        ORDER BY p.trade_date ASC
        """,
        (stock["id"],),
    ).fetchall()

    profile = fetch_yahoo_profile(stock["symbol"])
    return {
        "stock": dict(stock),
        "latest": dict(latest) if latest else {},
        "history": [dict(row) for row in history],
        "profile": profile,
    }


def fetch_yahoo_profile(symbol):
    modules = ",".join(
        [
            "assetProfile",
            "summaryProfile",
            "summaryDetail",
            "defaultKeyStatistics",
            "financialData",
            "price",
        ]
    )
    encoded_symbol = urllib.parse.quote(symbol)
    url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{encoded_symbol}?modules={modules}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return {"available": False}

    result = payload.get("quoteSummary", {}).get("result") or []
    if not result:
        return {"available": False}

    data = result[0]
    asset_profile = data.get("assetProfile") or data.get("summaryProfile") or {}
    financial_data = data.get("financialData") or {}
    key_stats = data.get("defaultKeyStatistics") or {}
    summary = data.get("summaryDetail") or {}
    price = data.get("price") or {}

    fundamentals = [
        metric("Börsvärde", price.get("marketCap") or summary.get("marketCap"), "currency"),
        metric("P/E-tal", summary.get("trailingPE"), "number"),
        metric("Framåtblickande P/E", summary.get("forwardPE"), "number"),
        metric("P/B-tal", key_stats.get("priceToBook"), "number"),
        metric("Direktavkastning", summary.get("dividendYield"), "percent"),
        metric("Beta", summary.get("beta"), "number"),
        metric("Vinstmarginal", financial_data.get("profitMargins"), "percent"),
        metric("ROE", financial_data.get("returnOnEquity"), "percent"),
        metric("Skuldsättning", financial_data.get("debtToEquity"), "number"),
        metric("Omsättningstillväxt", financial_data.get("revenueGrowth"), "percent"),
    ]

    officers = [
        {
            "name": officer.get("name"),
            "title": officer.get("title"),
        }
        for officer in asset_profile.get("companyOfficers", [])[:6]
        if officer.get("name")
    ]

    return {
        "available": True,
        "description": asset_profile.get("longBusinessSummary") or "",
        "sector": asset_profile.get("sector") or "",
        "industry": asset_profile.get("industry") or "",
        "website": asset_profile.get("website") or "",
        "city": asset_profile.get("city") or "",
        "country": asset_profile.get("country") or "",
        "officers": officers,
        "fundamentals": [item for item in fundamentals if item["value"] != "-"],
    }


def metric(label, value, value_type):
    return {"label": label, "value": format_yahoo_value(value, value_type)}


def format_yahoo_value(value, value_type):
    if not value:
        return "-"
    raw = value.get("raw") if isinstance(value, dict) else value
    formatted = value.get("fmt") if isinstance(value, dict) else None
    if formatted:
        return formatted
    if raw is None:
        return "-"
    if value_type == "percent":
        return f"{raw * 100:.1f}%"
    if value_type == "currency":
        return f"{raw:,.0f}".replace(",", " ")
    if isinstance(raw, float):
        return f"{raw:.2f}"
    return str(raw)


if __name__ == "__main__":
    os.chdir(PUBLIC_DIR)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Tikrflow running at http://{HOST}:{PORT}")
    server.serve_forever()
