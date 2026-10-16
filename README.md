# VAR-Q · NeurIPS 2026 (to appear)

Project page for **VAR-Q: Tuning-free KV Cache Quantization for Visual Autoregressive Image and Video Generation**.

Live site: https://boxunxu.top/VARQ/

## Structure

- `index.html`, `style.css`, `research.css`, `editorial.css`, `app.js`: research page (editorial typography layer in `editorial.css`, loaded last), paper figures, interactive grouping diagram, attribution analysis, and citation. Sections: hero → paired comparisons → overview → method → key results (with the complete Tables 2–4) → mechanistic analysis → examples → code & citation.
- `showcase.js`, `showcase-data.json`: curated BF16 / VAR-Q video pairs (10 InfinityStar 720p, 10 Self-Forcing, 6 LongLive, all 4-bit) plus the hero pair; `update_showcase.py` picks clips and posters, `build_showcase.py` renders one synchronized, auto-playing card per clip (optional `label` / `note` per group).
- `dense.js`, `manifest.json`, `selection.json`, `gen_manifest_v2.py`: Infinity-8B 2-bit grid (BF16 / FlexGen / KIVI / VAR-Q per prompt) in the Examples section.
- `results-data.json`, `kv-memory.json`: all 64 rows from Tables 2–4 and the paper's KV-memory numbers (`results.js` is not loaded by the page).
- `assets/`: figures extracted from the paper, posters, and the site favicon.
- `samples/`: curated images and MP4 videos.

## Preview

```sh
python3 -m http.server 8000
```

Open http://localhost:8000. The project uses plain static HTML, CSS, and JavaScript. No build step is required. Root-relative paper and homepage links resolve against boxunxu.top when published.

## Content maintenance

Update model metrics and printed KV savings in `results-data.json` with the corresponding paper table and configuration. Tables 1 and 5–6 are reproduced in their sections of `index.html`; Tables 2–4 sit at the end of Key results; Table 8 links to the full evaluation prompt list. The 64 main result rows were checked as complete numerical sequences against the paper. The attribution figures and claims come from Section 3.3, Figures 5–7. Samples on the page: Infinity-8B at a 2-bit KV cache (BF16 / FlexGen / KIVI / VAR-Q per prompt); Self-Forcing, LongLive and InfinityStar at 4-bit as BF16 / VAR-Q pairs, all generated with the public VAR-Q runtime from the same seed (raw outputs, prompts, configs and PSNR metrics live in `/data1/boxunxu/varq_demo` on euclid; `gen_manifest_v2.py` + `selection.json` publish the curated subset). Posters are first frames from the original files; playback does not crop, retime, or re-encode the source videos. Author links in the hero point to each author's homepage or Scholar profile; keep them, the NeurIPS citation, and the personal website bibliography consistent. This repository independently publishes `/VARQ/`; personal homepage content is maintained in `brucexu09.github.io`.
