# VAR-Q · NeurIPS 2026 (to appear)

Project page for **VAR-Q: Tuning-free KV Cache Quantization for Visual Autoregressive Image and Video Generation**.

Live site: https://boxunxu.top/VARQ/

## Structure

- `index.html`, `style.css`, `research.css`, `editorial.css`, `app.js`: research page (editorial typography layer in `editorial.css`, loaded last), responsive diagrams, paper figures, attribution, and citation.
- `showcase.js`, `showcase-data.json`: curated BF16 / VAR-Q video pairs (10 InfinityStar 720p, 10 Self-Forcing, 6 LongLive, all 4-bit); `update_showcase.py` picks clips and posters, `build_showcase.py` renders one synchronized card per clip.
- `dense.js`: Infinity-8B 2-bit grid (BF16 / FlexGen / KIVI / VAR-Q per prompt) driven by `manifest.json`.
- `results.js`, `results-data.json`: all 64 rows from Tables 2–4 (nine checkpoints across five model families), with precision / metric filters and CSV export.
- `gallery.js`: model / precision / sample gallery with shared video playback, seeking, restart, and speed controls.
- `assets/`: figures extracted from the paper and the site favicon.
- `manifest.json`: original project sample index.
- `samples/`: original images and MP4 videos; existing media is preserved.
- `gen_manifest.py`: regenerate the sample index from the existing sample layout.
- `static/`: retained legacy gallery assets.

## Preview

```sh
python3 -m http.server 8000
```

Open http://localhost:8000. The project uses plain static HTML, CSS, and JavaScript. No build step is required. Root-relative paper and homepage links resolve against boxunxu.top when published.

## Content maintenance

Update model metrics and printed KV savings in `results-data.json` with the corresponding paper table and configuration. Tables 1 and 5–7 are reproduced in their relevant sections of `index.html`; Table 8 links to the full evaluation prompt list. The 64 main result rows were checked as complete numerical sequences against the supplied paper. The attribution figures and claims come from Section 3.3, Figures 5–7. Samples on the page: Infinity-8B at a 2-bit KV cache (BF16 / FlexGen / KIVI / VAR-Q per prompt); Self-Forcing, LongLive and InfinityStar at 4-bit as BF16 / VAR-Q pairs, all generated with the public VAR-Q runtime from the same seed (raw outputs, prompts, configs and PSNR metrics live in `/data1/boxunxu/varq_demo` on euclid; `gen_manifest_v2.py` + `selection.json` publish the curated subset).json` (`selection.json` picks the published prompts; `methodsByBit` lets a model show different method columns per precision). Infinity-8B INT3/INT4/INT6 image sets come from the same pipeline; INT2 is kept offline because it visibly changes image content. Posters are first frames from the original files; playback does not crop, retime, or re-encode the source videos. Keep the NeurIPS citation, author list, and personal website bibliography consistent. This repository independently publishes `/VARQ/`; personal homepage content is maintained in `brucexu09.github.io`.
