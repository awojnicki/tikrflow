# Tikrflow

Responsiv dashboard for svenska Large Cap-aktier med signalfilter for Ichimoku och enkel signal. Första publika deployen använder befintlig SQLite-data i `data/market.db`.

## Kör lokalt

```bash
python3 server.py
```

Öppna sedan `http://localhost:4173`.

## Data

Appen läser `data/market.db`. Databasen innehåller tabellerna `stocks`, `prices`, `indicators`, `ema_screen` och `metadata`. `prices` innehåller OHLCV- och RSI14-rader från `2025-01-01`, och `indicators` innehåller EMA, RSI, MACD och Ichimoku-beräkningar.

Vill du bygga om databasen lokalt:

```bash
python3 scripts/import_market_data.py
```

## Deploy till Render

För första deployen används den befintliga databasen i `data/market.db`. Kör alltså inte importen som build step.

1. Skapa ett GitHub-repo, till exempel `tikrflow`.
2. Lägg upp hela projektmappen i repot, inklusive `data/market.db`.
3. Logga in på Render och välj `New` -> `Web Service`.
4. Koppla GitHub-repot.
5. Render kan läsa `render.yaml` automatiskt. Annars ange:
   - Runtime: `Python`
   - Build command: lämna tomt
   - Start command: `python3 server.py`
6. Deploya.

Render sätter miljövariabeln `PORT` automatiskt. `server.py` lyssnar på den porten.

## Automatisk datauppdatering

GitHub Actions-workflowen `.github/workflows/update-market-data.yml` kör importen varje vardag kl. `17:00 UTC`, efter Stockholmsbörsens stängning. Workflowen bygger om `data/market.db`, committar ändringen till GitHub och Render deployar sedan den nya databasen automatiskt om auto-deploy är på.

Du kan också starta uppdateringen manuellt i GitHub:

1. Gå till fliken `Actions`.
2. Välj `Update market data`.
3. Klicka `Run workflow`.
