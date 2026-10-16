#!/usr/bin/env python3
"""Render every showcase clip as its own BF16 / VAR-Q pair card (no dropdown).

Reads the master entries scale / frame / long in showcase-data.json (written by update_showcase.py, which also makes the
posters), writes one per-card entry per clip (scale-00, frame-03, ...) and rewrites the hero grid and the LongLive block
in index.html between the markers <!-- showcase:groups --> / <!-- showcase:long -->.
"""
import json, re, html as H
data = json.load(open("showcase-data.json")); page = open("index.html").read()
GROUPS = {"scale": ("Next-scale", "scale"), "frame": ("Next-frame", "frame"), "long": ("Next-frame", "long")}

def card(key, n, cfg, clip):
    k = f"{key}-{n:02d}"; model = cfg["model"]; bits = cfg["bits"]; prompt = H.escape(clip["prompt"], quote=True)
    cap_b, cap_v = cfg.get("captions", {}).get("Baseline", "BF16 reference"), cfg.get("captions", {}).get("VARQ", f"VAR-Q · {bits}")
    tag, cls = GROUPS[key]
    return f'''          <article class="feature-card direct-demo" data-feature="{k}">
            <div class="feature-top">
              <div>
                <span class="paradigm-tag {cls}">{tag}</span>
                <h3>{H.escape(clip["title"])}</h3>
              </div>
              <span class="feature-index">{H.escape(model)}</span>
            </div>
            <div class="feature-pair">
              <figure class="feature-video">
                <figcaption>{cap_b}</figcaption>
                <video aria-describedby="showcase-note" aria-label="{H.escape(model)} BF16: {prompt}" data-src="{clip["sources"]["Baseline"]}" loop="" muted="" playsinline="" poster="{clip["posters"]["Baseline"]}" preload="none"></video>
              </figure>
              <figure class="feature-video feature-ours">
                <figcaption>{cap_v}</figcaption>
                <video aria-describedby="showcase-note" aria-label="{H.escape(model)} VAR-Q {bits}: {prompt}" data-src="{clip["sources"]["VARQ"]}" loop="" muted="" playsinline="" poster="{clip["posters"]["VARQ"]}" preload="none"></video>
              </figure>
            </div>
            <div class="feature-controls">
              <button aria-label="Play {H.escape(model)} comparison" class="feature-play" disabled="" type="button">Play pair</button
              ><label class="feature-select" hidden=""><span class="sr-only">{H.escape(model)} sample</span><select disabled=""><option value="0">{H.escape(clip["title"])}</option></select></label
              ><output class="feature-time">0.0 s</output>
            </div>
            <label class="sr-only" for="seek-{k}">{H.escape(model)} shared timeline</label
            ><input class="feature-seek" disabled="" id="seek-{k}" max="1" min="0" step=".05" type="range" value="0" />
            <p class="feature-prompt">{prompt}</p>
            <p class="feature-status sr-only" role="status"></p>
            <noscript><a href="{clip["sources"]["VARQ"]}">Watch the VAR-Q video</a></noscript>
          </article>
'''

def group(key, cfg):
    # captions with KV memory come from the master card figcaptions already rendered in index.html by update_showcase.py
    m = re.search(rf'data-feature="{key}">.*?<figcaption>([^<]*)</figcaption>.*?<figcaption>([^<]*)</figcaption>', page, re.S)
    cfg["captions"] = {"Baseline": m.group(1), "VARQ": m.group(2)} if m else {}
    cards = "".join(card(key, n, cfg, c) for n, c in enumerate(cfg["clips"]))
    tag, cls = GROUPS[key]
    note = f'          <p class="showcase-group-note">{H.escape(cfg["note"])}</p>\n' if cfg.get("note") else ""
    head = f'''        <div class="showcase-group">
          <div class="showcase-group-head">
            <span class="paradigm-tag {cls}">{tag}</span>
            <h3>{H.escape(cfg.get("label", cfg["model"] + " · " + cfg["bits"] + " KV cache"))}</h3>
            <span class="showcase-group-count">{len(cfg["clips"])} prompts · BF16 vs VAR-Q, same seed</span>
          </div>
{note}          <div class="more-video-grid">
{cards}          </div>
        </div>
'''
    return head

for key in ("scale", "frame", "long"):
    for k in [k for k in data if re.fullmatch(rf"{key}-\d+", k) or k.startswith(f"{key}-sample-")]: del data[k]
    for n, c in enumerate(data[key]["clips"]):
        data[f"{key}-{n:02d}"] = {"model": data[key]["model"], "paradigm": data[key]["paradigm"], "bits": data[key]["bits"], "clips": [c]}

hero = "        <!-- showcase:groups -->\n" + group("scale", data["scale"]) + group("frame", data["frame"]) + "        <!-- /showcase:groups -->\n"
if "<!-- showcase:groups -->" in page:
    page = re.sub(r"        <!-- showcase:groups -->.*?        <!-- /showcase:groups -->\n", lambda _: hero, page, flags=re.S)
else:
    s = page.index('        <div class="showcase-grid">'); e = page.index('        <div class="showcase-foot">')
    page = page[:s] + hero + page[e:]
longblock = "        <!-- showcase:long -->\n" + group("long", data["long"]) + "        <!-- /showcase:long -->\n"
if "<!-- showcase:long -->" in page:
    page = re.sub(r"        <!-- showcase:long -->.*?        <!-- /showcase:long -->\n", lambda _: longblock, page, flags=re.S)
else:
    s = page.index('        <div class="long-showcase">'); e = page.index('        <div class="dense-section"')
    intro = re.search(r'          <div class="long-intro">.*?\n          </div>\n', page[s:e], re.S).group(0)
    page = page[:s] + '        <div class="long-showcase stacked">\n' + intro + '        </div>\n' + longblock + page[e:]
for k in ("scale", "frame", "long"):
    data[k].pop("captions", None)
open("index.html", "w").write(page)
json.dump(data, open("showcase-data.json", "w"), indent=2, ensure_ascii=False); open("showcase-data.json", "a").write("\n")
print({k: len(v["clips"]) for k, v in data.items() if k in GROUPS}, "cards:", page.count('class="feature-card direct-demo"'))
