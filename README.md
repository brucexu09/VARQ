# VAR-Q · NeurIPS 2026

Project page for **VAR-Q: Tuning-free KV Cache Quantization for Visual Autoregressive Image and Video Generation**.

Live site: https://boxunxu.top/VARQ/

## Structure

- `index.html`, `style.css`, `app.js`: research page, interactive paper figures, attribution, grouping diagram, benchmark selector, and citation.
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

Update model metrics in `app.js` with the corresponding paper table and configuration. The attribution figures and claims come from Section 3.3, Figures 5–7. Keep the NeurIPS citation, author list, and personal website bibliography consistent. This repository independently publishes `/VARQ/`; personal homepage content is maintained in `brucexu09.github.io`.
