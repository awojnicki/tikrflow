#!/usr/bin/env python3
import datetime as dt
import json
import math
import os
import sqlite3
import time
import urllib.parse
import urllib.request


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
PUBLIC_DIR = os.path.join(ROOT, "public")
DB_PATH = os.path.join(DATA_DIR, "market.db")

STORE_START = dt.date(2025, 1, 1)
EMA_WARMUP_START = dt.date(2025, 1, 1)

STOCKS = [
    ("ABB", "ABB.ST", "ABB Ltd"),
    ("Alfa Laval", "ALFA.ST", "Alfa Laval AB"),
    ("Alleima", "ALLEI.ST", "Alleima AB"),
    ("Assa Abloy B", "ASSA-B.ST", "Assa Abloy AB ser. B"),
    ("AstraZeneca", "AZN.ST", "AstraZeneca PLC"),
    ("Atlas Copco A", "ATCO-A.ST", "Atlas Copco AB ser. A"),
    ("Atlas Copco B", "ATCO-B.ST", "Atlas Copco AB ser. B"),
    ("Autoliv SDB", "ALIV-SDB.ST", "Autoliv Inc. SDB"),
    ("Avanza Bank", "AZA.ST", "Avanza Bank Holding AB"),
    ("Axfood", "AXFO.ST", "Axfood AB"),
    ("Beijer Ref B", "BEIJ-B.ST", "Beijer Ref AB ser. B"),
    ("Billerud", "BILL.ST", "Billerud AB"),
    ("Boliden", "BOL.ST", "Boliden AB"),
    ("Bure Equity", "BURE.ST", "Bure Equity AB"),
    ("Camurus", "CAMX.ST", "Camurus AB"),
    ("Castellum", "CAST.ST", "Castellum AB"),
    ("Elekta B", "EKTA-B.ST", "Elekta AB ser. B"),
    ("Electrolux B", "ELUX-B.ST", "Electrolux AB ser. B"),
    ("Epiroc A", "EPI-A.ST", "Epiroc AB ser. A"),
    ("Epiroc B", "EPI-B.ST", "Epiroc AB ser. B"),
    ("Ericsson B", "ERIC-B.ST", "Telefonaktiebolaget LM Ericsson ser. B"),
    ("Essity B", "ESSITY-B.ST", "Essity AB ser. B"),
    ("Evolution", "EVO.ST", "Evolution AB"),
    ("EQT", "EQT.ST", "EQT AB"),
    ("Fabege", "FABG.ST", "Fabege AB"),
    ("Getinge B", "GETI-B.ST", "Getinge AB ser. B"),
    ("H&M B", "HM-B.ST", "Hennes & Mauritz AB ser. B"),
    ("Hexagon B", "HEXA-B.ST", "Hexagon AB ser. B"),
    ("Hexpol B", "HPOL-B.ST", "Hexpol AB ser. B"),
    ("Holmen B", "HOLM-B.ST", "Holmen AB ser. B"),
    ("Hufvudstaden A", "HUFV-A.ST", "Hufvudstaden AB ser. A"),
    ("Husqvarna A", "HUSQ-A.ST", "Husqvarna AB ser. A"),
    ("Husqvarna B", "HUSQ-B.ST", "Husqvarna AB ser. B"),
    ("Industrivarden A", "INDU-A.ST", "Industrivarden AB ser. A"),
    ("Industrivarden C", "INDU-C.ST", "Industrivarden AB ser. C"),
    ("Indutrade", "INDT.ST", "Indutrade AB"),
    ("Investor A", "INVE-A.ST", "Investor AB ser. A"),
    ("Investor B", "INVE-B.ST", "Investor AB ser. B"),
    ("Kinnevik B", "KINV-B.ST", "Kinnevik AB ser. B"),
    ("Lagercrantz B", "LAGR-B.ST", "Lagercrantz Group AB ser. B"),
    ("Latour B", "LATO-B.ST", "Investment AB Latour ser. B"),
    ("Lifco B", "LIFCO-B.ST", "Lifco AB ser. B"),
    ("Loomis", "LOOMIS.ST", "Loomis AB"),
    ("Lundbergforetagen B", "LUND-B.ST", "L E Lundbergforetagen AB ser. B"),
    ("Medicover B", "MCOV-B.ST", "Medicover AB ser. B"),
    ("Millicom SDB", "TIGO-SDB.ST", "Millicom International Cellular SDB"),
    ("Munters", "MTRS.ST", "Munters Group AB"),
    ("Mycronic", "MYCR.ST", "Mycronic AB"),
    ("NCC B", "NCC-B.ST", "NCC AB ser. B"),
    ("Nibe B", "NIBE-B.ST", "Nibe Industrier AB ser. B"),
    ("Nolato B", "NOLA-B.ST", "Nolato AB ser. B"),
    ("Nordea Bank", "NDA-SE.ST", "Nordea Bank Abp"),
    ("Pandox B", "PNDX-B.ST", "Pandox AB ser. B"),
    ("Saab B", "SAAB-B.ST", "Saab AB ser. B"),
    ("Sagax B", "SAGA-B.ST", "AB Sagax ser. B"),
    ("Sandvik", "SAND.ST", "Sandvik AB"),
    ("SCA B", "SCA-B.ST", "Svenska Cellulosa AB SCA ser. B"),
    ("SEB A", "SEB-A.ST", "Skandinaviska Enskilda Banken AB ser. A"),
    ("Securitas B", "SECU-B.ST", "Securitas AB ser. B"),
    ("Sectra B", "SECT-B.ST", "Sectra AB ser. B"),
    ("Sinch", "SINCH.ST", "Sinch AB"),
    ("Skanska B", "SKA-B.ST", "Skanska AB ser. B"),
    ("SKF B", "SKF-B.ST", "AB SKF ser. B"),
    ("SSAB A", "SSAB-A.ST", "SSAB AB ser. A"),
    ("SSAB B", "SSAB-B.ST", "SSAB AB ser. B"),
    ("Svenska Handelsbanken A", "SHB-A.ST", "Svenska Handelsbanken AB ser. A"),
    ("Sobi", "SOBI.ST", "Swedish Orphan Biovitrum AB"),
    ("Swedbank A", "SWED-A.ST", "Swedbank AB ser. A"),
    ("Sweco B", "SWEC-B.ST", "Sweco AB ser. B"),
    ("Tele2 B", "TEL2-B.ST", "Tele2 AB ser. B"),
    ("Telia Company", "TELIA.ST", "Telia Company AB"),
    ("Thule", "THULE.ST", "Thule Group AB"),
    ("Trelleborg B", "TREL-B.ST", "Trelleborg AB ser. B"),
    ("Vitrolife", "VITR.ST", "Vitrolife AB"),
    ("Volvo A", "VOLV-A.ST", "AB Volvo ser. A"),
    ("Volvo B", "VOLV-B.ST", "AB Volvo ser. B"),
    ("Volvo Car B", "VOLCAR-B.ST", "Volvo Car AB ser. B"),
    ("Wallenstam B", "WALL-B.ST", "Wallenstam AB ser. B"),
    ("Wihlborgs", "WIHL.ST", "Wihlborgs Fastigheter AB"),
]


def yahoo_chart(symbol, start_date, end_date):
    period1 = int(dt.datetime.combine(start_date, dt.time(), tzinfo=dt.timezone.utc).timestamp())
    period2 = int(dt.datetime.combine(end_date + dt.timedelta(days=1), dt.time(), tzinfo=dt.timezone.utc).timestamp())
    params = urllib.parse.urlencode(
        {
            "period1": period1,
            "period2": period2,
            "interval": "1d",
            "events": "history",
            "includeAdjustedClose": "true",
        }
    )
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        payload = json.loads(response.read().decode("utf-8"))
    result = payload.get("chart", {}).get("result")
    if not result:
        raise ValueError(payload.get("chart", {}).get("error") or "No chart result")
    return result[0]


def rows_from_chart(chart):
    timestamps = chart.get("timestamp") or []
    quote = chart.get("indicators", {}).get("quote", [{}])[0]
    rows = []
    for index, timestamp in enumerate(timestamps):
        close = value_at(quote.get("close"), index)
        open_ = value_at(quote.get("open"), index)
        high = value_at(quote.get("high"), index)
        low = value_at(quote.get("low"), index)
        volume = value_at(quote.get("volume"), index)
        if close is None or open_ is None or high is None or low is None:
            continue
        day = dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).date()
        rows.append(
            {
                "date": day.isoformat(),
                "open": float(open_),
                "high": float(high),
                "low": float(low),
                "close": float(close),
                "volume": int(volume or 0),
            }
        )
    return rows


def value_at(values, index):
    if values is None or index >= len(values):
        return None
    value = values[index]
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def ema(values, period):
    output = [None] * len(values)
    if len(values) < period:
        return output
    current = sum(values[:period]) / period
    output[period - 1] = current
    alpha = 2 / (period + 1)
    for index in range(period, len(values)):
        current = (values[index] * alpha) + (current * (1 - alpha))
        output[index] = current
    return output


def rsi_components(values, period=14):
    output = [None] * len(values)
    changes = [None] * len(values)
    ups = [None] * len(values)
    downs = [None] * len(values)
    avg_ups = [None] * len(values)
    avg_downs = [None] * len(values)
    rs_values = [None] * len(values)
    if len(values) <= period:
        return {
            "change": changes,
            "up": ups,
            "down": downs,
            "avg_up": avg_ups,
            "avg_down": avg_downs,
            "rs": rs_values,
            "rsi": output,
        }

    gains = []
    losses = []
    for index in range(1, len(values)):
        change = values[index] - values[index - 1]
        changes[index] = change
        ups[index] = max(change, 0)
        downs[index] = max(-change, 0)

    for index in range(1, period + 1):
        gains.append(ups[index])
        losses.append(downs[index])

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    avg_ups[period] = avg_gain
    avg_downs[period] = avg_loss
    rs_values[period] = None if avg_loss == 0 else avg_gain / avg_loss
    output[period] = rsi_value(avg_gain, avg_loss)

    for index in range(period + 1, len(values)):
        gain = ups[index]
        loss = downs[index]
        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period
        avg_ups[index] = avg_gain
        avg_downs[index] = avg_loss
        rs_values[index] = None if avg_loss == 0 else avg_gain / avg_loss
        output[index] = rsi_value(avg_gain, avg_loss)
    return {
        "change": changes,
        "up": ups,
        "down": downs,
        "avg_up": avg_ups,
        "avg_down": avg_downs,
        "rs": rs_values,
        "rsi": output,
    }


def rsi_value(avg_gain, avg_loss):
    if avg_loss == 0:
        return 100.0
    relative_strength = avg_gain / avg_loss
    return 100 - (100 / (1 + relative_strength))


def rolling_midpoint(highs, lows, period):
    output = [None] * len(highs)
    for index in range(period - 1, len(highs)):
        output[index] = (max(highs[index - period + 1 : index + 1]) + min(lows[index - period + 1 : index + 1])) / 2
    return output


def shifted_forward(values, periods):
    output = [None] * len(values)
    for index in range(periods, len(values)):
        output[index] = values[index - periods]
    return output


def shifted_backward(values, periods):
    output = [None] * len(values)
    for index in range(0, len(values) - periods):
        output[index] = values[index + periods]
    return output


def macd_signal(macd_values, period=9):
    output = [None] * len(macd_values)
    valid_indexes = [index for index, value in enumerate(macd_values) if value is not None]
    if len(valid_indexes) < period:
        return output
    seed_indexes = valid_indexes[:period]
    seed_index = seed_indexes[-1]
    current = sum(macd_values[index] for index in seed_indexes) / period
    output[seed_index] = current
    alpha = 2 / (period + 1)
    for index in range(seed_index + 1, len(macd_values)):
        if macd_values[index] is None:
            continue
        current = (macd_values[index] * alpha) + (current * (1 - alpha))
        output[index] = current
    return output


def signal_text(close, ema20, ema50, ema200, rsi14, macd, signal):
    if None in (ema20, ema50, ema200, rsi14, macd, signal):
        return None
    if close > ema20 > ema50 > ema200 and rsi14 < 70 and macd > signal:
        return "KÖP"
    if close < ema20 < ema50 < ema200 and rsi14 > 30 and macd < signal:
        return "SÄLJ"
    return "NEUTRAL"


def macd_signal_text(macd, signal, previous_macd, previous_signal):
    if None in (macd, signal, previous_macd, previous_signal):
        return None
    if macd > signal and previous_macd <= previous_signal:
        return "MACD KÖP"
    if macd < signal and previous_macd >= previous_signal:
        return "MACD SÄLJ"
    return "-"


def ichimoku_signal(close, tenkan, kijun, senkou_a, senkou_b):
    if None in (close, tenkan, kijun, senkou_a, senkou_b):
        return None
    if close > max(senkou_a, senkou_b) and tenkan > kijun:
        return "ICHIMOKU KÖP"
    if close < min(senkou_a, senkou_b) and tenkan < kijun:
        return "ICHIMOKU SÄLJ"
    return "NEUTRAL"


def init_db(conn):
    conn.executescript(
        """
        DROP TABLE IF EXISTS prices;
        DROP TABLE IF EXISTS stocks;
        DROP TABLE IF EXISTS ema_screen;
        DROP TABLE IF EXISTS indicators;
        DROP TABLE IF EXISTS metadata;

        CREATE TABLE stocks (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          symbol TEXT NOT NULL UNIQUE,
          display_symbol TEXT NOT NULL,
          name TEXT NOT NULL,
          market TEXT NOT NULL,
          segment TEXT NOT NULL,
          currency TEXT NOT NULL DEFAULT 'SEK'
        );

        CREATE TABLE prices (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          stock_id INTEGER NOT NULL,
          trade_date TEXT NOT NULL,
          open REAL NOT NULL,
          high REAL NOT NULL,
          low REAL NOT NULL,
          close REAL NOT NULL,
          volume INTEGER NOT NULL,
          rsi14 REAL,
          FOREIGN KEY(stock_id) REFERENCES stocks(id),
          UNIQUE(stock_id, trade_date)
        );

        CREATE INDEX idx_prices_stock_date ON prices(stock_id, trade_date);

        CREATE TABLE ema_screen (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          stock_id INTEGER NOT NULL,
          screen_date TEXT NOT NULL,
          open REAL NOT NULL,
          high REAL NOT NULL,
          low REAL NOT NULL,
          close REAL NOT NULL,
          volume INTEGER NOT NULL,
          ema20 REAL NOT NULL,
          ema50 REAL NOT NULL,
          ema200 REAL NOT NULL,
          rsi14 REAL,
          change_percent REAL,
          FOREIGN KEY(stock_id) REFERENCES stocks(id),
          UNIQUE(stock_id, screen_date)
        );

        CREATE TABLE indicators (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          stock_id INTEGER NOT NULL,
          trade_date TEXT NOT NULL,
          ema20 REAL,
          ema50 REAL,
          ema200 REAL,
          rsi_change REAL,
          rsi_up REAL,
          rsi_down REAL,
          rsi_avg_up14 REAL,
          rsi_avg_down14 REAL,
          rs REAL,
          rsi14 REAL,
          simple_signal TEXT,
          macd REAL,
          ema12 REAL,
          ema26 REAL,
          macd_signal REAL,
          macd_histogram REAL,
          macd_signal_text TEXT,
          tenkan_sen REAL,
          kijun_sen REAL,
          senkou_span_a REAL,
          senkou_span_b REAL,
          chikou_span REAL,
          ichimoku_signal TEXT,
          FOREIGN KEY(stock_id) REFERENCES stocks(id),
          UNIQUE(stock_id, trade_date)
        );

        CREATE INDEX idx_indicators_stock_date ON indicators(stock_id, trade_date);

        CREATE TABLE metadata (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        );
        """
    )


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PUBLIC_DIR, exist_ok=True)

    today = dt.date.today()
    latest_completed = today - dt.timedelta(days=1)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    screened = []
    imported_symbols = []
    skipped = []

    for display_symbol, yahoo_symbol, name in STOCKS:
        try:
            chart = yahoo_chart(yahoo_symbol, EMA_WARMUP_START, latest_completed)
            history = rows_from_chart(chart)
            stored_history = [row for row in history if dt.date.fromisoformat(row["date"]) >= STORE_START]
            if not stored_history:
                skipped.append({"symbol": yahoo_symbol, "reason": "No rows since 2025-01-01"})
                continue

            currency = chart.get("meta", {}).get("currency") or "SEK"
            cur = conn.execute(
                """
                INSERT INTO stocks (symbol, display_symbol, name, market, segment, currency)
                VALUES (?, ?, ?, 'Nasdaq Stockholm', 'Large Cap', ?)
                """,
                (yahoo_symbol, display_symbol, name, currency),
            )
            stock_id = cur.lastrowid
            closes = [row["close"] for row in history]
            highs = [row["high"] for row in history]
            lows = [row["low"] for row in history]
            ema20 = ema(closes, 20)
            ema50 = ema(closes, 50)
            ema200 = ema(closes, 200)
            ema12 = ema(closes, 12)
            ema26 = ema(closes, 26)
            macd_values = [
                None if ema12[index] is None or ema26[index] is None else ema12[index] - ema26[index]
                for index in range(len(history))
            ]
            macd_signal_values = macd_signal(macd_values, 9)
            macd_histogram = [
                None
                if macd_values[index] is None or macd_signal_values[index] is None
                else macd_values[index] - macd_signal_values[index]
                for index in range(len(history))
            ]
            rsi_parts = rsi_components(closes, 14)
            rsi14 = rsi_parts["rsi"]
            tenkan_sen = rolling_midpoint(highs, lows, 9)
            kijun_sen = rolling_midpoint(highs, lows, 26)
            senkou_span_a_base = [
                None if tenkan_sen[index] is None or kijun_sen[index] is None else (tenkan_sen[index] + kijun_sen[index]) / 2
                for index in range(len(history))
            ]
            senkou_span_a = shifted_forward(senkou_span_a_base, 26)
            senkou_span_b = shifted_forward(rolling_midpoint(highs, lows, 52), 26)
            chikou_span = shifted_backward(closes, 26)
            rsi_by_date = {row["date"]: rsi14[index] for index, row in enumerate(history)}
            indicator_rows = []
            for index, row in enumerate(history):
                if dt.date.fromisoformat(row["date"]) < STORE_START:
                    continue
                previous_index = index - 1
                macd_text = macd_signal_text(
                    macd_values[index],
                    macd_signal_values[index],
                    macd_values[previous_index] if previous_index >= 0 else None,
                    macd_signal_values[previous_index] if previous_index >= 0 else None,
                )
                indicator_rows.append(
                    (
                        stock_id,
                        row["date"],
                        ema20[index],
                        ema50[index],
                        ema200[index],
                        rsi_parts["change"][index],
                        rsi_parts["up"][index],
                        rsi_parts["down"][index],
                        rsi_parts["avg_up"][index],
                        rsi_parts["avg_down"][index],
                        rsi_parts["rs"][index],
                        rsi14[index],
                        signal_text(
                            row["close"],
                            ema20[index],
                            ema50[index],
                            ema200[index],
                            rsi14[index],
                            macd_values[index],
                            macd_signal_values[index],
                        ),
                        macd_values[index],
                        ema12[index],
                        ema26[index],
                        macd_signal_values[index],
                        macd_histogram[index],
                        macd_text,
                        tenkan_sen[index],
                        kijun_sen[index],
                        senkou_span_a[index],
                        senkou_span_b[index],
                        chikou_span[index],
                        ichimoku_signal(
                            row["close"],
                            tenkan_sen[index],
                            kijun_sen[index],
                            senkou_span_a[index],
                            senkou_span_b[index],
                        ),
                    )
                )
            conn.executemany(
                """
                INSERT INTO indicators (
                  stock_id, trade_date, ema20, ema50, ema200, rsi_change, rsi_up, rsi_down,
                  rsi_avg_up14, rsi_avg_down14, rs, rsi14, simple_signal, macd, ema12, ema26,
                  macd_signal, macd_histogram, macd_signal_text, tenkan_sen, kijun_sen,
                  senkou_span_a, senkou_span_b, chikou_span, ichimoku_signal
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                indicator_rows,
            )
            conn.executemany(
                """
                INSERT INTO prices (stock_id, trade_date, open, high, low, close, volume, rsi14)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        stock_id,
                        row["date"],
                        row["open"],
                        row["high"],
                        row["low"],
                        row["close"],
                        row["volume"],
                        rsi_by_date.get(row["date"]),
                    )
                    for row in stored_history
                ],
            )

            latest_index = len(history) - 1
            latest = history[latest_index]
            imported_symbols.append(yahoo_symbol)

            if (
                ema20[latest_index] is not None
                and ema50[latest_index] is not None
                and ema200[latest_index] is not None
                and latest["close"] > ema20[latest_index] > ema50[latest_index] > ema200[latest_index]
            ):
                previous_close = None
                if latest_index > 0:
                    previous_close = history[latest_index - 1]["close"]
                screened.append(
                    {
                        "stockId": stock_id,
                        "symbol": yahoo_symbol,
                        "displaySymbol": display_symbol,
                        "name": name,
                        "date": latest["date"],
                        "open": latest["open"],
                        "high": latest["high"],
                        "low": latest["low"],
                        "close": latest["close"],
                        "volume": latest["volume"],
                        "ema20": ema20[latest_index],
                        "ema50": ema50[latest_index],
                        "ema200": ema200[latest_index],
                        "rsi14": rsi14[latest_index],
                        "changePercent": None
                        if previous_close in (None, 0)
                        else ((latest["close"] - previous_close) / previous_close) * 100,
                    }
                )
            time.sleep(0.08)
        except Exception as exc:
            skipped.append({"symbol": yahoo_symbol, "reason": str(exc)})

    conn.commit()

    screened.sort(key=lambda row: (row["ema20"] - row["ema50"]) / row["close"], reverse=True)
    metadata = {
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "screenDate": latest_completed.isoformat(),
        "storeStartDate": STORE_START.isoformat(),
        "emaWarmupStartDate": EMA_WARMUP_START.isoformat(),
        "source": "Yahoo Finance chart endpoint",
        "database": os.path.relpath(DB_PATH, ROOT),
        "importedCount": len(imported_symbols),
        "screenedCount": len(screened),
        "skipped": skipped,
    }
    conn.executemany(
        """
        INSERT INTO ema_screen (
          stock_id, screen_date, open, high, low, close, volume, ema20, ema50, ema200, rsi14, change_percent
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["stockId"],
                row["date"],
                row["open"],
                row["high"],
                row["low"],
                row["close"],
                row["volume"],
                row["ema20"],
                row["ema50"],
                row["ema200"],
                row["rsi14"],
                row["changePercent"],
            )
            for row in screened
        ],
    )
    conn.execute(
        "INSERT INTO metadata (key, value) VALUES ('import', ?)",
        (json.dumps(metadata, ensure_ascii=False),),
    )
    conn.commit()

    for row in screened:
        row.pop("stockId", None)

    print(f"Imported {len(imported_symbols)} instruments into {DB_PATH}")
    print(f"Screen matched {len(screened)} instruments for {latest_completed.isoformat()}")
    if skipped:
        print(f"Skipped {len(skipped)} instruments")


if __name__ == "__main__":
    main()
