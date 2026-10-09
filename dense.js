"use strict";
// Dense qualitative grids driven by manifest.json: one row per prompt, every method side by side.
(() => {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const dialog = document.querySelector("#figure-dialog");
  const labelFor = (model, bit, method) => {
    const bits = model.bitLabels[bit];
    const base = method === "VARQ" ? `VAR-Q · ${bits}` : method === "Baseline" ? "BF16" : `${model.methodLabels[method]} · ${bits}`;
    const kv = model.kvMemory && model.kvMemory[bit] && model.kvMemory[bit][method];
    if (!kv) return base;
    const ref = model.kvMemory[bit].Baseline;
    return method === "Baseline" || !ref ? `${base} · ${kv.toFixed(1)} GB` : `${base} · ${kv.toFixed(1)} GB (−${Math.round((1 - kv / ref) * 100)}%)`;
  };
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const video = entry.target;
        if (entry.isIntersecting) {
          if (!video.src) {
            video.src = video.dataset.src;
            video.load();
          }
          if (!reducedMotion.matches) video.play().catch(() => {});
        } else if (!video.paused) video.pause();
      });
    },
    { threshold: 0.2 },
  );
  function openZoom(src, caption) {
    if (!dialog || typeof dialog.showModal !== "function") return window.open(src, "_blank");
    const img = document.querySelector("#dialog-image");
    img.src = src;
    img.alt = caption;
    document.querySelector("#dialog-caption").textContent = caption;
    dialog.showModal();
  }
  function cell(model, bit, method, sample) {
    const src = sample.media[method];
    const fig = document.createElement("figure");
    fig.className = `dense-cell${method === "VARQ" ? " dense-ours" : ""}`;
    const cap = document.createElement("figcaption");
    cap.textContent = labelFor(model, bit, method);
    const caption = `${cap.textContent}: ${sample.prompt || model.task}`;
    if (src && src.startsWith("samples/") && !src.includes("..")) {
      if (model.type === "video") {
        const v = document.createElement("video");
        v.muted = true;
        v.loop = true;
        v.playsInline = true;
        v.preload = "none";
        v.dataset.src = src;
        v.setAttribute("aria-label", caption);
        v.addEventListener("click", () => (v.paused ? v.play().catch(() => {}) : v.pause()));
        fig.append(v);
        observer.observe(v);
      } else {
        const a = document.createElement("a");
        a.href = src;
        a.className = "dense-zoom";
        a.addEventListener("click", (e) => {
          e.preventDefault();
          openZoom(src, caption);
        });
        const img = document.createElement("img");
        img.loading = "lazy";
        img.decoding = "async";
        img.src = src;
        img.alt = caption;
        a.append(img);
        fig.append(a);
      }
    } else {
      const p = document.createElement("p");
      p.className = "missing-media";
      p.textContent = "n/a";
      fig.append(p);
    }
    fig.append(cap);
    return fig;
  }
  function row(model, bit, methods, sample, index) {
    const r = document.createElement("div");
    r.className = "dense-row";
    const p = document.createElement("p");
    p.className = "dense-prompt";
    const text = sample.prompt || `${model.task} — sample ${index + 1}`;
    p.textContent = `${String(index + 1).padStart(2, "0")} · ${text}`;
    p.title = text;
    r.append(p);
    const cells = document.createElement("div");
    cells.className = "dense-cells";
    cells.style.setProperty("--cols", String(methods.length));
    methods.forEach((m) => cells.append(cell(model, bit, m, sample)));
    r.append(cells);
    return r;
  }
  fetch("manifest.json")
    .then((r) => r.json())
    .then((data) => {
      document.querySelectorAll(".dense-block").forEach((block) => {
        const model = data.models.find((m) => m.id === block.dataset.model);
        const bit = block.dataset.bit;
        const samples = (model && model.samples[bit]) || [];
        const methods = (model && ((model.methodsByBit && model.methodsByBit[bit]) || model.methods)) || [];
        const rows = block.querySelector(".dense-rows");
        const more = block.querySelector(".dense-more");
        const count = block.querySelector(".dense-count");
        let shown = 0;
        const step = Number(block.dataset.step || 12);
        if (count) count.textContent = `${samples.length} prompts × ${methods.length} methods`;
        function render(n) {
          samples.slice(shown, shown + n).forEach((s, i) => rows.append(row(model, bit, methods, s, shown + i)));
          shown = Math.min(samples.length, shown + n);
          if (more) {
            more.hidden = shown >= samples.length;
            more.textContent = `Show ${Math.min(step, samples.length - shown)} more (${shown}/${samples.length})`;
          }
        }
        if (!samples.length) {
          block.hidden = true;
          return;
        }
        render(Number(block.dataset.initial || step));
        if (more) more.addEventListener("click", () => render(step));
      });
    })
    .catch(() => {
      document.querySelectorAll(".dense-block").forEach((b) => (b.hidden = true));
    });
})();
