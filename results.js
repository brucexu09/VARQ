"use strict";
(() => {
  const model = document.querySelector("#result-model");
  const precision = document.querySelector("#result-precision");
  const metric = document.querySelector("#result-metric");
  const status = document.querySelector("#result-status");
  let datasets = [];
  const current = () => datasets.find((d) => d.id === model.value);
  function options(select, entries, value) {
    select.replaceChildren(
      ...entries.map(([v, text]) => {
        const option = document.createElement("option");
        option.value = v;
        option.textContent = text;
        return option;
      }),
    );
    select.value = value;
    select.disabled = false;
  }
  function tableCell(tr, text, type = "td") {
    const cell = document.createElement(type);
    cell.textContent = text;
    if (type === "th") cell.scope = tr.parentElement?.tagName === "THEAD" ? "col" : "row";
    tr.append(cell);
  }
  function render() {
    const d = current();
    const mi = Number(metric.value);
    const base = d.rows[0];
    const rows = d.rows.filter((r) => r.precision === "BF16" || precision.value === "all" || r.precision === precision.value);
    document.querySelector("#result-setting").textContent = `${d.setting} · Table ${d.table}`;
    const source = document.querySelector("#result-source");
    source.href = `/assets/pdf/VAR-Q.pdf#page=${d.page}`;
    source.textContent = `Table ${d.table} ↗`;
    document.querySelector("#result-metric-label").textContent = d.metrics[mi];
    const bars = document.querySelector("#result-bars");
    bars.replaceChildren();
    rows.forEach((r) => {
      const row = document.createElement("div");
      row.className = `result-bar-row${r.method === "VAR-Q" ? " result-ours" : ""}`;
      const memory = document.createElement("div");
      memory.className = "result-memory";
      const label = document.createElement("span");
      label.className = "result-bar-label";
      label.textContent = r.method === "BF16" ? "BF16 reference" : `${r.method} · ${r.precision}`;
      const track = document.createElement("span");
      track.className = "result-track";
      const bar = document.createElement("span");
      bar.style.width = `${(Number(r.kv) / Number(base.kv)) * 100}%`;
      track.append(bar);
      const value = document.createElement("span");
      value.className = "result-kv";
      value.textContent = r.kv;
      memory.append(label, track, value);
      const quality = document.createElement("strong");
      quality.textContent = r.values[mi];
      const delta = document.createElement("span");
      delta.className = "result-delta";
      const change = Number(r.values[mi]) - Number(base.values[mi]);
      delta.textContent = r === base || !Number.isFinite(change) ? "—" : `${change > 0 ? "+" : ""}${change.toFixed(2)}`;
      row.append(memory, quality, delta);
      bars.append(row);
    });
    const table = document.querySelector("#result-table");
    table.replaceChildren();
    const caption = document.createElement("caption");
    caption.textContent = `${d.label} · Table ${d.table} · ${precision.value === "all" ? "all reported precisions" : precision.value + " and BF16"}`;
    table.append(caption);
    const head = document.createElement("thead");
    const hr = document.createElement("tr");
    head.append(hr);
    ["Method", "Precision", ...d.metrics, "KV (GB) ↓", "KV saving vs. BF16"].forEach((v) => tableCell(hr, v, "th"));
    table.append(head);
    const body = document.createElement("tbody");
    rows.forEach((r) => {
      const tr = document.createElement("tr");
      if (r.method === "VAR-Q") tr.className = "highlight";
      tableCell(tr, r.method, "th");
      [r.precision, ...r.values, r.kv, r === base ? "—" : `${r.saving}%`].forEach((v) => tableCell(tr, v));
      body.append(tr);
    });
    table.append(body);
    status.textContent = `${rows.length} rows shown. All metric, memory, and savings values reproduce the paper tables. Use All reported precisions to reveal every row.`;
  }
  function setModel() {
    const d = current();
    const bits = [...new Set(d.rows.slice(1).map((r) => r.precision))];
    options(precision, [["all", "All reported precisions"], ...bits.map((b) => [b, b])], d.defaultPrecision);
    options(
      metric,
      d.metrics.map((m, i) => [String(i), m]),
      String(d.defaultMetric),
    );
    render();
  }
  model.addEventListener("change", setModel);
  precision.addEventListener("change", render);
  metric.addEventListener("change", render);
  document.querySelector("#result-csv").addEventListener("click", () => {
    const d = current();
    const rows = [["Method", "Precision", ...d.metrics, "KV (GB)"], ...d.rows.map((r) => [r.method, r.precision, ...r.values, r.kv])];
    const csv = rows.map((row) => row.map((v) => `"${v.replaceAll('"', '""')}"`).join(",")).join("\r\n");
    const url = URL.createObjectURL(new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `VAR-Q-table-${d.table}-${d.id}.csv`;
    document.body.append(a);
    a.click();
    a.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  fetch("results-data.json")
    .then((r) => {
      if (!r.ok) throw new Error("Results unavailable");
      return r.json();
    })
    .then((data) => {
      datasets = data.datasets;
      options(
        model,
        datasets.map((d) => [d.id, d.label]),
        "star720",
      );
      document.querySelector("#result-csv").disabled = false;
      setModel();
    })
    .catch(() => {
      status.textContent = "The results could not load. Download the data above or open the linked paper tables.";
    });
})();
