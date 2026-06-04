const state = {
  stocks: [],
  metadata: {},
  segmentFilter: "all",
  showIchimokuOnly: false,
  showSimpleSignalOnly: false,
  sortKey: "name",
  sortDirection: "asc",
};

const formatter = new Intl.NumberFormat("sv-SE", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const volumeFormatter = new Intl.NumberFormat("sv-SE", {
  notation: "compact",
  maximumFractionDigits: 1,
});

const nodes = {
  body: document.querySelector("#stocksBody"),
  empty: document.querySelector("#emptyState"),
  ichimokuFilter: document.querySelector("#ichimokuFilter"),
  simpleSignalFilter: document.querySelector("#simpleSignalFilter"),
  summaryText: document.querySelector("#summaryText"),
  databaseNote: document.querySelector("#databaseNote"),
  segmentOptions: [...document.querySelectorAll(".segment-option")],
  sortHeaders: [...document.querySelectorAll(".sort-header")],
};

async function loadData() {
  const response = await fetch(`/api/screen?cache=${Date.now()}`);
  if (!response.ok) {
    throw new Error("Kunde inte läsa marknadsdata");
  }
  const payload = await response.json();
  state.stocks = payload.stocks || [];
  state.metadata = payload.metadata || {};
  render();
}

function render() {
  const filtered = state.stocks
    .filter((stock) => state.segmentFilter === "all" || stock.segment === state.segmentFilter)
    .filter((stock) => !state.showIchimokuOnly || Number(stock.ichimokuMatch) === 1)
    .filter((stock) => !state.showSimpleSignalOnly || Number(stock.simpleSignalMatch) === 1)
    .sort(compareStocks);

  const ichimokuCount = state.stocks.filter((stock) => Number(stock.ichimokuMatch) === 1).length;
  const simpleSignalCount = state.stocks.filter((stock) => Number(stock.simpleSignalMatch) === 1).length;
  nodes.summaryText.textContent = [
    `Visar ${filtered.length} av ${state.metadata.importedCount ?? state.stocks.length} aktier`,
    `Ichimoku ${ichimokuCount}`,
    `Enkel signal ${simpleSignalCount}`,
  ].join(" · ");
  nodes.databaseNote.textContent = `Uppdaterad ${formatDateTime(state.metadata.generatedAt)}`;

  nodes.body.innerHTML = filtered.map(rowTemplate).join("");
  nodes.empty.hidden = filtered.length > 0;
  updateSegmentFilter();
  updateSortHeaders();
}

function compareStocks(a, b) {
  const direction = state.sortDirection === "asc" ? 1 : -1;
  if (state.sortKey === "displaySymbol" || state.sortKey === "name" || state.sortKey === "segment") {
    return (
      String(a[state.sortKey] || "").localeCompare(String(b[state.sortKey] || ""), "sv-SE") * direction
    );
  }
  if (state.sortKey === "dayChange") {
    return (dayChange(a) - dayChange(b)) * direction;
  }
  return (Number(a[state.sortKey]) - Number(b[state.sortKey])) * direction;
}

function rowTemplate(stock) {
  const day = dayDirection(stock);
  return `
    <tr>
      <td>
        <a class="stock-cell stock-link" href="./stock.html?symbol=${encodeURIComponent(stock.symbol)}">
          <strong>${escapeHtml(stock.name || stock.displaySymbol)}</strong>
        </a>
      </td>
      <td><span class="segment-pill">${escapeHtml(stock.segment || "-")}</span></td>
      <td><span class="day-indicator ${day.className}" title="${day.label}" aria-label="${day.label}"></span></td>
      <td>${price(stock.open)}</td>
      <td>${price(stock.close)}</td>
      <td>${volumeFormatter.format(stock.volume)}</td>
    </tr>
  `;
}

function price(value) {
  return formatter.format(value);
}

function dayChange(stock) {
  const open = Number(stock.open);
  const close = Number(stock.close);
  if (close > open) return 1;
  if (close < open) return -1;
  return 0;
}

function dayDirection(stock) {
  const change = dayChange(stock);
  if (change > 0) return { className: "up", label: "Upp för dagen" };
  if (change < 0) return { className: "down", label: "Ner för dagen" };
  return { className: "flat", label: "Oförändrad för dagen" };
}

function formatDate(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("sv-SE", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(`${value}T12:00:00`));
}

function formatDateTime(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("sv-SE", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

nodes.ichimokuFilter.addEventListener("change", (event) => {
  state.showIchimokuOnly = event.target.checked;
  render();
});

nodes.simpleSignalFilter.addEventListener("change", (event) => {
  state.showSimpleSignalOnly = event.target.checked;
  render();
});

nodes.segmentOptions.forEach((button) => {
  button.addEventListener("click", () => {
    state.segmentFilter = button.dataset.segmentFilter || "all";
    render();
  });
});

nodes.sortHeaders.forEach((button) => {
  button.addEventListener("click", () => {
    const key = button.dataset.sortKey;
    if (state.sortKey === key) {
      state.sortDirection = state.sortDirection === "asc" ? "desc" : "asc";
    } else {
      state.sortKey = key;
      state.sortDirection = "asc";
    }
    render();
  });
});

function updateSortHeaders() {
  nodes.sortHeaders.forEach((button) => {
    const isActive = button.dataset.sortKey === state.sortKey;
    const direction = isActive ? state.sortDirection : "none";
    const header = button.closest("th");
    button.classList.toggle("active", isActive);
    button.classList.toggle("asc", isActive && state.sortDirection === "asc");
    button.classList.toggle("desc", isActive && state.sortDirection === "desc");
    header?.setAttribute(
      "aria-sort",
      direction === "asc" ? "ascending" : direction === "desc" ? "descending" : "none",
    );
  });
}

function updateSegmentFilter() {
  nodes.segmentOptions.forEach((button) => {
    const isActive = button.dataset.segmentFilter === state.segmentFilter;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });
}

loadData().catch((error) => {
  nodes.summaryText.textContent = error.message;
  nodes.databaseNote.textContent = "";
  nodes.empty.hidden = false;
  nodes.empty.textContent = "Kör importen för att skapa databasen och dashboardens data.";
});
