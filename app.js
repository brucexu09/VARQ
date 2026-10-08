"use strict";

const compareNames = { varq: "VAR-Q", kivi: "KIVI", flexgen: "FlexGen" };
const compareImage = document.querySelector(".compare-image");
document.querySelector("#comparison-range").addEventListener("input", (event) => {
  compareImage.style.setProperty("--split", `${event.target.value}%`);
});
document.querySelectorAll("[data-compare]").forEach((button) => {
  button.addEventListener("click", () => {
    const key = button.dataset.compare;
    document.querySelectorAll("[data-compare]").forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
    const img = document.querySelector("#compare-target");
    img.src = `assets/cats-${key}.webp`;
    img.alt = `${compareNames[key]} at INT2`;
    document.querySelector("#compare-name").textContent = `${compareNames[key]} · INT2`;
  });
});

const videos = {
  selfforcing: {
    file: "selfforcing-int4",
    caption: "Self-Forcing · Next-frame generation · INT4 KV cache · Figure 39.",
    width: 2000,
    height: 1195,
    alt: "Four sampled frames for BF16, FlexGen, KIVI and VAR-Q: skyscrapers transform into a robot.",
  },
  infinitystar: {
    file: "infinitystar-int3",
    caption: "InfinityStar-8B · Next-scale generation · 720p · INT3 KV cache · Figure 32.",
    width: 2000,
    height: 1172,
    alt: "InfinityStar 720p INT3 comparison of sampled video frames for BF16, FlexGen, KIVI and VAR-Q.",
  },
  longlive: {
    file: "longlive-int4",
    caption: "LongLive-1.3B · Next-frame generation · INT4 KV cache · Figure 45.",
    width: 2000,
    height: 862,
    alt: "LongLive INT4 comparison of sampled video frames for BF16, FlexGen, KIVI and VAR-Q.",
  },
};
document.querySelector("#video-model").addEventListener("change", (event) => {
  const data = videos[event.target.value];
  const img = document.querySelector("#video-figure");
  img.src = `assets/${data.file}.webp`;
  img.alt = data.alt;
  img.width = data.width;
  img.height = data.height;
  const link = document.querySelector("#video-link");
  link.href = img.src;
  link.dataset.caption = data.caption;
  document.querySelector("#video-caption").textContent = data.caption;
});

const matrix = document.querySelector("#cache-matrix");
const magnitudes = [0.08, 0.12, 0.18, 0.78, 0.16, 0.12, 0.1, 0.18, 0.3, 0.87, 0.17, 0.13, 0.23, 0.12, 0.7, 0.14];
for (let row = 0; row < 12; row += 1) {
  for (let col = 0; col < 16; col += 1) {
    const cell = document.createElement("span");
    cell.className = "matrix-cell";
    const blockFactor = [0.55, 1, 0.72][Math.floor(row / 4)];
    const magnitude = Math.min(1, magnitudes[col] * blockFactor + ((row * 7 + col * 3) % 5) * 0.013);
    cell.style.backgroundColor = `hsl(249 ${28 + magnitude * 13}% ${96 - magnitude * 74}%)`;
    matrix.append(cell);
  }
}
const descriptions = {
  tensor: "One scale factor covers the entire tensor. Large-magnitude cells set the range for all channels and blocks.",
  channel: "Each channel has its own scale factor, but magnitudes can still shift between generation blocks within that channel.",
  joint: "VAR-Q separates feature channels and generation blocks, so each group follows both axes of the cache.",
};
function setGrouping(type) {
  matrix.querySelectorAll(".matrix-boundary").forEach((item) => item.remove());
  const columns = type === "tensor" ? 1 : 16;
  const blocks = type === "joint" ? 3 : 1;
  for (let col = 0; col < columns; col += 1) {
    for (let block = 0; block < blocks; block += 1) {
      const boundary = document.createElement("span");
      boundary.className = "matrix-boundary";
      Object.assign(boundary.style, {
        left: `${(col * 100) / columns}%`,
        top: `${(block * 100) / blocks}%`,
        width: `${100 / columns}%`,
        height: `${100 / blocks}%`,
      });
      matrix.append(boundary);
    }
  }
  matrix.setAttribute("aria-label", `Schematic KV cache. ${descriptions[type]}`);
  document.querySelector("#group-description").textContent = descriptions[type];
}
setGrouping("joint");
document.querySelectorAll("[data-group]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-group]").forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
    setGrouping(button.dataset.group);
  });
});

const dialog = document.querySelector("#figure-dialog");
document.querySelectorAll("[data-zoom]").forEach((link) => {
  link.addEventListener("click", (event) => {
    if (typeof dialog.showModal !== "function") return;
    event.preventDefault();
    const img = document.querySelector("#dialog-image");
    img.src = link.href;
    img.alt = link.dataset.caption;
    document.querySelector("#dialog-caption").textContent = link.dataset.caption;
    dialog.showModal();
  });
});
document.querySelector("#close-dialog").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (event) => {
  if (event.target === dialog) {
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  }
});
document.querySelectorAll("[data-copy]").forEach((button) => {
  const label = button.textContent;
  button.addEventListener("click", async () => {
    const code = document.getElementById(button.dataset.copy);
    try {
      await navigator.clipboard.writeText(code.textContent);
      button.textContent = "Copied!";
      document.querySelector("#copy-status").textContent = `${label} succeeded.`;
      window.setTimeout(() => {
        button.textContent = label;
      }, 2000);
    } catch {
      const range = document.createRange();
      range.selectNodeContents(code);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      document.querySelector("#copy-status").textContent = "Text selected. Use your keyboard or context menu to copy.";
    }
  });
});

// Deep links to supplementary tables also open their disclosure panel.
function revealLinkedTable() {
  const id = window.location.hash.slice(1);
  const target = id ? document.getElementById(id) : null;
  if (target?.tagName === "DETAILS") target.open = true;
}
window.addEventListener("hashchange", revealLinkedTable);
revealLinkedTable();
