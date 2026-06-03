const state = {
  stocks: [],
  metadata: {},
  showIchimokuOnly: false,
  showSimpleSignalOnly: false,
  sortKey: "displaySymbol",
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
  nodes.databaseNote.textContent = `Data från ${state.metadata.storeStartDate || "-"}, uppdaterad ${
    state.metadata.screenDate || "-"
  }`;

  nodes.body.innerHTML = filtered.map(rowTemplate).join("");
  nodes.empty.hidden = filtered.length > 0;
  updateSortHeaders();
}

function compareStocks(a, b) {
  const direction = state.sortDirection === "asc" ? 1 : -1;
  if (state.sortKey === "displaySymbol") {
    return a.displaySymbol.localeCompare(b.displaySymbol, "sv-SE") * direction;
  }
  return (Number(a[state.sortKey]) - Number(b[state.sortKey])) * direction;
}

function rowTemplate(stock) {
  return `
    <tr>
      <td>
        <span class="stock-cell">
          <strong>${escapeHtml(stock.displaySymbol)}</strong>
        </span>
      </td>
      <td>${price(stock.open)}</td>
      <td>${price(stock.close)}</td>
      <td>${volumeFormatter.format(stock.volume)}</td>
    </tr>
  `;
}

function price(value) {
  return formatter.format(value);
}

function formatDate(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("sv-SE", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(`${value}T12:00:00`));
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

loadData().catch((error) => {
  nodes.summaryText.textContent = error.message;
  nodes.databaseNote.textContent = "";
  nodes.empty.hidden = false;
  nodes.empty.textContent = "Kör importen för att skapa databasen och dashboardens data.";
});
