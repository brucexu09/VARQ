# VARQ — Project Page

Demo / project page for **VARQ: Training-Free KV-Cache Quantization for Visual Autoregressive Generation**.

Live site: https://boxunxu.top/VARQ/

## Structure

```
VARQ/
├── index.html          # Main page
├── manifest.json       # Auto-generated gallery index (models × methods × bits × samples)
├── static/
│   ├── style.css       # Styles
│   └── gallery.js      # Interactive comparison gallery (reads manifest.json)
├── samples/            # Media, laid out as Model/Method/qbits/<file>
│   ├── VAR_d20 … VAR_d30
│   ├── Infinity2B / Infinity8B
│   ├── InfinityStar480p / InfinityStar720p
│   └── self_forcing / longlive
└── README.md
```

## What it shows

An interactive **qualitative comparison** gallery. Pick a model and a KV-cache
bit-width; the page renders each sample as a side-by-side row comparing
**Baseline (FP)**, prior post-hoc quantizers (**KIVI**, **FlexGen/GPTQ**), and
**VARQ (Ours)**. Images render inline; videos autoplay with a playback-speed control.

## Regenerating the manifest

Media lives under `samples/<Model>/<Method>/<qbits>/`. `manifest.json` is produced
by the generator script (`gen_manifest.py`) which walks that tree, aligns samples
across methods, and attaches prompts / PSNR margins from the source `_metadata`.

## Local preview

```bash
python3 -m http.server 8000
# open http://localhost:8000
```
