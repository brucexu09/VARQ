#!/usr/bin/env python3
"""Rewrite the paired showcase cards (scale = InfinityStar 720p, frame = Self-Forcing, long = LongLive) from clip specs.

usage: update_showcase.py --bits 4-bit --q q4 [--kv] \
         --frame IDX:Title [IDX:Title ...] --long IDX:Title [...] --scale IDX:Title [...]
Files are samples/<model>/<Method>/<q>/prompt{IDX:03d}.mp4; prompts come from the per-model prompt lists.
Regenerates posters (first frame, 640x369 webp), showcase-data.json and the cards in index.html.
"""
import argparse, json, re, os, cv2
ap = argparse.ArgumentParser()
ap.add_argument("--bits", default="4-bit"); ap.add_argument("--q", default="q4"); ap.add_argument("--kv", action="store_true")
ap.add_argument("--frame", nargs="+"); ap.add_argument("--long", nargs="+"); ap.add_argument("--scale", nargs="+")
ap.add_argument("--sf-prompts", default="/data1/boxunxu/varq_demo/v2/prompts/sf.txt")
ap.add_argument("--ll-prompts", default="/data1/boxunxu/varq_demo/v2/prompts/ll.txt")
ap.add_argument("--star-prompts", default="/data1/boxunxu/varq_demo/istar/prompts.txt")
a = ap.parse_args()
def lines(p): return [l.rstrip("\n") for l in open(p, encoding="utf-8") if l.strip()]
CARDS = {"frame": ("self_forcing", "Self-Forcing", "Next-frame", a.frame, lines(a.sf_prompts)),
         "long": ("longlive", "LongLive", "Next-frame", a.long, lines(a.ll_prompts)),
         "scale": ("InfinityStar720p", "InfinityStar · 720p", "Next-scale", a.scale, lines(a.star_prompts))}
KV = json.load(open("kv-memory.json")) if a.kv else {}
def poster(src, dst):
    cap = cv2.VideoCapture(src); ok, im = cap.read(); assert ok, src
    cv2.imwrite(dst, cv2.resize(im, (640, 369), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_WEBP_QUALITY, 82])
data = json.load(open("showcase-data.json")); html = open("index.html").read()
def patch_card(html, key, model_label, entries, bits, kvm):
    m = re.search(rf'<article class="feature-card[^"]*" data-feature="{key}">.*?</article>', html, re.S)
    if not m: return html
    block = m.group(0); e0 = entries[0]
    block = re.sub(r'data-src="samples/[^"]*/Baseline/[^"]*"', f'data-src="{e0["sources"]["Baseline"]}"', block)
    block = re.sub(r'data-src="samples/[^"]*/VARQ/[^"]*"', f'data-src="{e0["sources"]["VARQ"]}"', block)
    block = re.sub(r'poster="assets/posters/[^"]*Baseline[^"]*"', f'poster="{e0["posters"]["Baseline"]}"', block)
    block = re.sub(r'poster="assets/posters/[^"]*VARQ[^"]*"', f'poster="{e0["posters"]["VARQ"]}"', block)
    block = re.sub(r'(<noscript><a href=")[^"]*(")', rf'\g<1>{e0["sources"]["VARQ"]}\g<2>', block)
    block = re.sub(r'(aria-label="[^"]*?: )[^"]*"', lambda mm: mm.group(1) + e0["prompt"].replace('"', "'") + '"', block)
    block = re.sub(r'\b[2-8]-bit\b', bits, block)
    block = re.sub(r'<p class="feature-prompt">.*?</p>', f'<p class="feature-prompt">{e0["prompt"]}</p>', block, flags=re.S)
    opts = "".join(f'\n                  <option value="{n}">{e["title"]}</option>' for n, e in enumerate(entries))
    block = re.sub(r'(<select disabled="">).*?(\n\s*</select>)', lambda mm: mm.group(1) + opts + mm.group(2), block, flags=re.S)
    block = re.sub(r'<span class="feature-index">\d+ / \d+</span>', f'<span class="feature-index">01 / {len(entries):02d}</span>', block)
    if kvm and "Baseline" in kvm and "VARQ" in kvm:
        b, v = kvm["Baseline"], kvm["VARQ"]
        block = re.sub(r'<figcaption>BF16 reference[^<]*</figcaption>', f'<figcaption>BF16 reference · KV cache {b:.1f} GB</figcaption>', block)
        block = re.sub(r'<figcaption>VAR-Q · [^<]*</figcaption>', f'<figcaption>VAR-Q · {bits} · KV cache {v:.1f} GB (−{round((1 - v / b) * 100)}%)</figcaption>', block)
    return html[:m.start()] + block + html[m.end():]
for key, (mid, label, paradigm, specs, prompts) in CARDS.items():
    if not specs: continue
    entries = []
    for n, item in enumerate(specs):
        idx, title = item.split(":", 1); i = int(idx)
        sources = {m: f"samples/{mid}/{m}/{a.q}/prompt{i:03d}.mp4" for m in ("Baseline", "VARQ")}
        posters = {m: f"assets/posters/{key}-{n}-{m}.webp" for m in ("Baseline", "VARQ")}
        for m in ("Baseline", "VARQ"):
            assert os.path.exists(sources[m]), sources[m]; poster(sources[m], posters[m])
        entries.append({"title": title, "prompt": prompts[i], "sources": sources, "posters": posters})
    data[key] = {"model": label, "paradigm": paradigm, "bits": a.bits, "clips": entries}
    for k in [k for k in data if k.startswith(f"{key}-sample-")]: del data[k]
    kvm = KV.get(mid, {}).get("bits", {}).get(a.q, {}) if a.kv else {}
    html = patch_card(html, key, label, entries, a.bits, kvm)
    print(key, len(entries), [e["title"] for e in entries])
json.dump(data, open("showcase-data.json", "w"), indent=2, ensure_ascii=False); open("showcase-data.json", "a").write("\n")
open("index.html", "w").write(html)
