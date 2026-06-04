const params = new URLSearchParams(window.location.search);
const symbol = params.get("symbol");
const chartState = {
  period: "3m",
  history: [],
  currency: "SEK",
  indicators: new Set(),
};

const numberFormatter = new Intl.NumberFormat("sv-SE", {
  maximumFractionDigits: 2,
});

const priceFormatter = new Intl.NumberFormat("sv-SE", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const nodes = {
  name: document.querySelector("#stockName"),
  meta: document.querySelector("#stockMeta"),
  description: document.querySelector("#stockDescription"),
  chart: document.querySelector("#candleChart"),
  chartRange: document.querySelector("#chartRange"),
  chartTitle: document.querySelector(".chart-head h2"),
  chartPeriods: [...document.querySelectorAll(".chart-period")],
  indicatorOptions: [...document.querySelectorAll(".indicator-option")],
  overview: document.querySelector("#overviewMetrics"),
  fundamentals: document.querySelector("#fundamentalMetrics"),
  technical: document.querySelector("#technicalMetrics"),
};

async function loadStock() {
  if (!symbol) {
    throw new Error("Ingen aktie vald.");
  }
  const response = await fetch(`/api/stock?symbol=${encodeURIComponent(symbol)}&cache=${Date.now()}`);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Bolaget kunde inte hämtas.");
  }
  renderStock(payload);
}

function renderStock(payload) {
  const { stock, latest, profile, history } = payload;
  const changePercent = latest.open ? ((latest.close - latest.open) / latest.open) * 100 : null;

  nodes.name.textContent = stock.name;
  nodes.meta.textContent = [stock.displaySymbol, segmentName(stock.segment), stock.market, stock.currency]
    .filter(Boolean)
    .join(" · ");
  nodes.description.textContent =
    profile.description ||
    "Kort verksamhetsbeskrivning saknas i den kompletterande datakällan just nu. Tekniska mätvärden visas från Tikrflows databas.";
  chartState.history = history || [];
  chartState.currency = stock.currency;
  renderCandles();

  renderOverview([
    ["Senaste datum", latest.date],
    ["Öppning", price(latest.open, stock.currency)],
    ["Stängning", price(latest.close, stock.currency)],
    ["Dagens utveckling", percent(changePercent)],
    ["Volym", compact(latest.volume)],
    ["Sektor", profile.sector || "-"],
    ["Bransch", profile.industry || "-"],
    ["Ledning", officersText(profile.officers || [])],
  ]);

  renderMetrics(nodes.fundamentals, fundamentalMetrics(profile.fundamentals || []));

  renderMetrics(nodes.technical, [
    ["EMA20", price(latest.ema20, stock.currency)],
    ["EMA50", price(latest.ema50, stock.currency)],
    ["EMA200", price(latest.ema200, stock.currency)],
    ["RSI14", decimal(latest.rsi14)],
    ["Enkel signal", latest.simpleSignal || "-"],
    ["Ichimoku", latest.ichimokuSignal || "-"],
    ["Tenkan-sen", price(latest.tenkanSen, stock.currency)],
    ["Kijun-sen", price(latest.kijunSen, stock.currency)],
  ]);

}

function renderOverview(metrics) {
  nodes.overview.innerHTML = metrics
    .map(
      ([label, value]) => `<span>${escapeHtml(label)}: <strong>${escapeHtml(value || "-")}</strong></span>`,
    )
    .join("");
}

function fundamentalMetrics(metrics) {
  const values = new Map(metrics.map((item) => [item.label, item.value]));
  return [
    "Börsvärde",
    "P/E-tal",
    "Framåtblickande P/E",
    "P/B-tal",
    "Direktavkastning",
    "Beta",
    "Vinstmarginal",
    "ROE",
    "Skuldsättning",
    "Omsättningstillväxt",
  ].map((label) => [label, values.get(label) || "-"]);
}

function renderCandles() {
  const chartRows = rowsForPeriod(chartState.history, chartState.period).filter(
    (row) => row.high !== null && row.low !== null,
  );
  if (!chartRows.length) {
    nodes.chart.innerHTML = '<p class="muted-text">Kursdata saknas för grafen.</p>';
    nodes.chartRange.textContent = "";
    return;
  }

  const width = 760;
  const height = 300;
  const padding = { top: 16, right: 22, bottom: 58, left: 96 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const scaleValues = chartRows.flatMap((row) => [
    row.high,
    row.low,
    ...(chartState.indicators.has("ema20") ? [row.ema20] : []),
    ...(chartState.indicators.has("ema50") ? [row.ema50] : []),
    ...(chartState.indicators.has("ema200") ? [row.ema200] : []),
    ...(chartState.indicators.has("ichimoku")
      ? [row.tenkanSen, row.kijunSen, row.senkouSpanA, row.senkouSpanB]
      : []),
  ]);
  const numericScaleValues = scaleValues.map(Number).filter((value) => Number.isFinite(value));
  const high = Math.max(...numericScaleValues);
  const low = Math.min(...numericScaleValues);
  const range = high - low || 1;
  const slot = chartWidth / chartRows.length;
  const candleWidth = Math.max(1.7, Math.min(9, slot * 0.54));
  const y = (value) => padding.top + ((high - Number(value)) / range) * chartHeight;
  const x = (index) => padding.left + slot * index + slot / 2;
  const gridValues = [low, low + range * 0.25, low + range * 0.5, low + range * 0.75, high];
  const monthTicks = chartTicks(chartRows);

  nodes.chartTitle.textContent = chartPeriodLabel(chartState.period);
  nodes.chartRange.textContent = formatDateRange(chartRows[0].date, chartRows[chartRows.length - 1].date);

  const grid = gridValues
    .map((value) => {
      const yy = y(value);
      return `
        <line class="chart-grid" x1="${padding.left}" x2="${width - padding.right}" y1="${yy}" y2="${yy}" />
        <text class="chart-label y-label" x="${padding.left - 10}" y="${yy + 4}">${escapeHtml(
          price(value, chartState.currency),
        )}</text>
      `;
    })
    .join("");

  const xTicks = monthTicks
    .map((tick) => {
      const xx = x(tick.index);
      return `
        <line class="chart-tick" x1="${xx}" x2="${xx}" y1="${height - padding.bottom}" y2="${height - padding.bottom + 5}" />
        <text class="chart-date" x="${xx}" y="${height - 18}">${escapeHtml(tick.label)}</text>
      `;
    })
    .join("");

  const candles = chartRows
    .map((row, index) => {
      const candleX = x(index);
      const openY = y(row.open);
      const closeY = y(row.close);
      const highY = y(row.high);
      const lowY = y(row.low);
      const bodyY = Math.min(openY, closeY);
      const bodyHeight = Math.max(2, Math.abs(closeY - openY));
      const direction = Number(row.close) >= Number(row.open) ? "up" : "down";
      return `
        <g class="candle ${direction}">
          <title>${escapeHtml(
            `${row.date}: O ${price(row.open, chartState.currency)}, H ${price(row.high, chartState.currency)}, L ${price(
              row.low,
              chartState.currency,
            )}, C ${price(row.close, chartState.currency)}`,
          )}</title>
          <line x1="${candleX}" x2="${candleX}" y1="${highY}" y2="${lowY}" />
          <rect x="${candleX - candleWidth / 2}" y="${bodyY}" width="${candleWidth}" height="${bodyHeight}" rx="1.5" />
        </g>
      `;
    })
    .join("");
  const overlays = renderIndicatorOverlays(chartRows, x, y);

  nodes.chart.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Candlestick-graf senaste tre månaderna">
      ${grid}
      <line class="chart-axis" x1="${padding.left}" x2="${padding.left}" y1="${padding.top}" y2="${height - padding.bottom}" />
      <line class="chart-axis" x1="${padding.left}" x2="${width - padding.right}" y1="${height - padding.bottom}" y2="${height - padding.bottom}" />
      ${xTicks}
      ${overlays.cloud}
      ${candles}
      ${overlays.lines}
    </svg>
  `;
  updateChartPeriods();
  updateIndicatorOptions();
}

function renderIndicatorOverlays(rows, x, y) {
  const lines = [
    chartState.indicators.has("ema20") ? indicatorPath(rows, x, y, "ema20", "ema20", "EMA20") : "",
    chartState.indicators.has("ema50") ? indicatorPath(rows, x, y, "ema50", "ema50", "EMA50") : "",
    chartState.indicators.has("ema200") ? indicatorPath(rows, x, y, "ema200", "ema200", "EMA200") : "",
    chartState.indicators.has("ichimoku")
      ? [
          indicatorPath(rows, x, y, "tenkanSen", "tenkan", "Tenkan-sen"),
          indicatorPath(rows, x, y, "kijunSen", "kijun", "Kijun-sen"),
          indicatorPath(rows, x, y, "senkouSpanA", "senkou-a", "Senkou Span A"),
          indicatorPath(rows, x, y, "senkouSpanB", "senkou-b", "Senkou Span B"),
        ].join("")
      : "",
  ].join("");
  const cloud = chartState.indicators.has("ichimoku") ? ichimokuCloud(rows, x, y) : "";
  return { cloud, lines };
}

function indicatorPath(rows, x, y, key, className, label) {
  const points = rows
    .map((row, index) => ({ value: Number(row[key]), x: x(index) }))
    .filter((point) => Number.isFinite(point.value));
  if (points.length < 2) return "";
  const d = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${y(point.value)}`).join(" ");
  return `<path class="indicator-line ${className}" d="${d}"><title>${escapeHtml(label)}</title></path>`;
}

function ichimokuCloud(rows, x, y) {
  const points = rows
    .map((row, index) => ({
      x: x(index),
      a: Number(row.senkouSpanA),
      b: Number(row.senkouSpanB),
    }))
    .filter((point) => Number.isFinite(point.a) && Number.isFinite(point.b));
  if (points.length < 2) return "";
  const upper = points.map((point) => `${point.x} ${y(Math.max(point.a, point.b))}`).join(" L ");
  const lower = points
    .slice()
    .reverse()
    .map((point) => `${point.x} ${y(Math.min(point.a, point.b))}`)
    .join(" L ");
  return `<path class="ichimoku-cloud" d="M ${upper} L ${lower} Z"><title>Ichimoku moln</title></path>`;
}

function rowsForPeriod(history, period) {
  if (period === "1w") return history.slice(-5);
  if (period === "1m") return history.slice(-22);
  if (period === "3m") return history.slice(-66);
  return history.slice(-252);
}

function chartTicks(rows) {
  if (chartState.period === "1w") {
    return rows.map((row, index) => ({ date: row.date, index, label: formatShortDate(row.date) }));
  }
  if (chartState.period === "1m") {
    return evenlySpacedTicks(rows, 5).map((tick) => ({ ...tick, label: formatShortDate(tick.date) }));
  }

  const monthStarts = rows.reduce((ticks, row, index) => {
    const month = row.date.slice(0, 7);
    if (!ticks.length || ticks[ticks.length - 1].month !== month) {
      ticks.push({ month, date: row.date, index });
    }
    return ticks;
  }, []);
  if (chartState.period === "3m") {
    return includeLastTick(monthStarts, rows).map((tick) => ({ ...tick, label: formatMonth(tick.date) }));
  }

  const maxTicks = 7;
  const step = Math.max(1, Math.ceil(monthStarts.length / maxTicks));
  return includeLastTick(
    monthStarts.filter((_, index) => index % step === 0),
    rows,
  ).map((tick) => ({ ...tick, label: formatMonth(tick.date) }));
}

function evenlySpacedTicks(rows, count) {
  const lastIndex = rows.length - 1;
  if (lastIndex < 0) return [];
  const indexes = new Set();
  for (let index = 0; index < count; index += 1) {
    indexes.add(Math.round((lastIndex * index) / (count - 1)));
  }
  return [...indexes].sort((a, b) => a - b).map((index) => ({ date: rows[index].date, index }));
}

function includeLastTick(ticks, rows) {
  const lastIndex = rows.length - 1;
  const lastDate = rows[lastIndex]?.date;
  const lastMonth = lastDate?.slice(0, 7);
  if (
    !lastDate ||
    ticks.some((tick) => tick.index === lastIndex) ||
    ticks.some((tick) => tick.date.slice(0, 7) === lastMonth)
  ) {
    return ticks;
  }
  return [...ticks, { date: lastDate, index: lastIndex }];
}

function chartPeriodLabel(period) {
  if (period === "1w") return "Senaste veckan";
  if (period === "1m") return "Senaste månaden";
  if (period === "3m") return "Senaste tre månaderna";
  return "Senaste året";
}

function updateChartPeriods() {
  nodes.chartPeriods.forEach((button) => {
    const isActive = button.dataset.chartPeriod === chartState.period;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });
}

function updateIndicatorOptions() {
  nodes.indicatorOptions.forEach((button) => {
    const isActive = chartState.indicators.has(button.dataset.indicator);
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });
}

function renderMetrics(target, metrics) {
  target.innerHTML = metrics
    .map(
      ([label, value]) => `
        <div>
          <dt>${escapeHtml(label)}</dt>
          <dd>${escapeHtml(value ?? "-")}</dd>
        </div>
      `,
    )
    .join("");
}

function officersText(officers) {
  if (!officers.length) return "-";
  const people = officers
    .slice(0, 4)
    .map((officer) => `${officer.name}${officer.title ? `, ${officer.title}` : ""}`)
    .join("; ");
  return people;
}

function segmentName(segment) {
  if (segment === "L") return "Large Cap";
  if (segment === "M") return "Mid Cap";
  if (segment === "S") return "Small Cap";
  return segment;
}

function formatShortDate(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("sv-SE", {
    day: "numeric",
    month: "short",
  }).format(new Date(`${value}T12:00:00`));
}

function formatDateRange(start, end) {
  if (!start || !end) return "";
  const includeYear = start.slice(0, 4) !== end.slice(0, 4);
  const options = {
    day: "numeric",
    month: "short",
    ...(includeYear ? { year: "numeric" } : {}),
  };
  const formatter = new Intl.DateTimeFormat("sv-SE", options);
  return `${formatter.format(new Date(`${start}T12:00:00`))}–${formatter.format(new Date(`${end}T12:00:00`))}`;
}

function formatMonth(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("sv-SE", {
    month: "short",
  }).format(new Date(`${value}T12:00:00`));
}

function price(value, currency) {
  if (value === null || value === undefined) return "-";
  return `${priceFormatter.format(value)} ${currency || ""}`.trim();
}

function percent(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return `${numberFormatter.format(value)}%`;
}

function decimal(value) {
  if (value === null || value === undefined) return "-";
  return numberFormatter.format(value);
}

function compact(value) {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat("sv-SE", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

nodes.chartPeriods.forEach((button) => {
  button.addEventListener("click", () => {
    chartState.period = button.dataset.chartPeriod || "3m";
    renderCandles();
  });
});

nodes.indicatorOptions.forEach((button) => {
  button.addEventListener("click", () => {
    const indicator = button.dataset.indicator;
    if (!indicator) return;
    if (chartState.indicators.has(indicator)) {
      chartState.indicators.delete(indicator);
    } else {
      chartState.indicators.add(indicator);
    }
    renderCandles();
  });
});

loadStock().catch((error) => {
  nodes.name.textContent = "Bolaget kunde inte visas";
  nodes.meta.textContent = "Tikrflow";
  nodes.description.textContent = error.message;
  nodes.overview.innerHTML = "";
  nodes.fundamentals.innerHTML = "";
  nodes.technical.innerHTML = "";
  nodes.officers.innerHTML = "";
});
