#!/usr/bin/env python3
"""Point the paired showcase cards (frame = Self-Forcing, long = LongLive) at curated clips.

usage: update_showcase.py <bits-label e.g. 6-bit> <qbits e.g. q6> \
         --frame IDX:Title IDX:Title IDX:Title --long IDX:Title IDX:Title IDX:Title
Regenerates posters (first frame, 640x369 webp), showcase-data.json and the six cards in index.html.
"""
import argparse, json, re, os, cv2
ap = argparse.ArgumentParser(); ap.add_argument("bits"); ap.add_argument("q")
ap.add_argument("--frame", nargs=3, required=True); ap.add_argument("--long", nargs=3, required=True)
ap.add_argument("--kv", action="store_true", help="annotate figcaptions with KV memory from kv-memory.json")
ap.add_argument("--pad", type=int, default=2); ap.add_argument("--long-pad", type=int, default=None)
ap.add_argument("--ll-prompts", default="/data1/boxunxu/varq_demo/v2/prompts/ll.txt")
a = ap.parse_args()
SF = [l.rstrip("\n") for l in open('/data1/boxunxu/varq_demo/v2/prompts/sf.txt') if l.strip()]
LL = [l.rstrip("\n") for l in open(a.ll_prompts) if l.strip()]
def parse(items): return [(int(s.split(":", 1)[0]), s.split(":", 1)[1]) for s in items]
CLIPS = {"frame": ("self_forcing", "Self-Forcing", parse(a.frame), SF), "long": ("longlive", "LongLive", parse(a.long), LL)}
data = json.load(open('showcase-data.json'))
def poster(src, dst):
    cap = cv2.VideoCapture(src); ok, im = cap.read(); assert ok, src
    cv2.imwrite(dst, cv2.resize(im, (640, 369), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_WEBP_QUALITY, 82])
for key, (mid, label, clips, prompts) in CLIPS.items():
    entries = []
    for n, (i, title) in enumerate(clips):
        pad = a.long_pad if (key == "long" and a.long_pad is not None) else a.pad
        sources = {m: f"samples/{mid}/{m}/{a.q}/prompt{i:0{pad}d}.mp4" for m in ("Baseline", "VARQ")}
        posters = {m: f"assets/posters/{key}-{n}-{m}.webp" for m in ("Baseline", "VARQ")}
        for m in ("Baseline", "VARQ"):
            assert os.path.exists(sources[m]), sources[m]; poster(sources[m], posters[m])
        entries.append({"title": title, "prompt": prompts[i], "sources": sources, "posters": posters})
    data[key] = {"model": label, "paradigm": "Next-frame", "bits": a.bits, "clips": entries}
    for n in (2, 3):
        data[f"{key}-sample-{n}"] = {"model": label, "paradigm": "Next-frame", "bits": a.bits, "clips": [entries[n - 1]]}
json.dump(data, open('showcase-data.json', 'w'), indent=2, ensure_ascii=False); open('showcase-data.json', 'a').write("\n")
html = open('index.html').read()
def patch_card(html, key, entry_list, hero):
    m = re.search(rf'<article class="feature-card[^"]*" data-feature="{key}">.*?</article>', html, re.S)
    if not m:
        return html  # card no longer exists on the page (sample cards were replaced by the dense grids)
    block = m.group(0); e0 = entry_list[0]
    block = re.sub(r'data-src="samples/[^"]*/Baseline/[^"]*"', f'data-src="{e0["sources"]["Baseline"]}"', block)
    block = re.sub(r'data-src="samples/[^"]*/VARQ/[^"]*"', f'data-src="{e0["sources"]["VARQ"]}"', block)
    block = re.sub(r'(<noscript><a href=")[^"]*(")', rf'\g<1>{e0["sources"]["VARQ"]}\g<2>', block)
    block = re.sub(r'(aria-label="[^"]*?: )[^"]*"', lambda mm: mm.group(1) + e0["prompt"] + '"', block)
    block = re.sub(r'\b[2-8]-bit\b', a.bits, block)
    if a.kv:
        kvm = json.load(open('kv-memory.json'))[CLIPS[key.split("-")[0]][0]]["bits"].get(a.q, {})
        if "Baseline" in kvm and "VARQ" in kvm:
            b, v = kvm["Baseline"], kvm["VARQ"]
            block = re.sub(r'<figcaption>BF16 reference[^<]*</figcaption>', f'<figcaption>BF16 reference · KV cache {b:.1f} GB</figcaption>', block)
            block = re.sub(r'<figcaption>VAR-Q · [^<]*</figcaption>', f'<figcaption>VAR-Q · {a.bits} · KV cache {v:.1f} GB (−{round((1 - v / b) * 100)}%)</figcaption>', block)
    block = re.sub(r'<p class="feature-prompt">.*?</p>', f'<p class="feature-prompt">{e0["prompt"]}</p>', block, flags=re.S)
    opts = "".join(f'\n                  <option value="{n}">{e["title"]}</option>' for n, e in enumerate(entry_list))
    block = re.sub(r'(<select disabled="">).*?(\n\s*</select>)', lambda mm: mm.group(1) + opts + mm.group(2), block, flags=re.S)
    if not hero:
        block = re.sub(r'(<div class="feature-top">\s*<div>\s*<span[^>]*>[^<]*</span>\s*<h3>)[^<]*(</h3>)', rf'\g<1>{e0["title"]}\g<2>', block)
    return html[:m.start()] + block + html[m.end():]
for key in CLIPS:
    html = patch_card(html, key, data[key]["clips"], hero=True)
    for n in (2, 3):
        html = patch_card(html, f"{key}-sample-{n}", data[f"{key}-sample-{n}"]["clips"], hero=False)
open('index.html', 'w').write(html); print("showcase updated:", {k: [c["title"] for c in data[k]["clips"]] for k in ("frame", "long")})
