#!/usr/bin/env python3
"""Render every showcase clip as its own BF16 / VAR-Q pair card (no dropdown).

Reads the master entries scale / frame / long in showcase-data.json (written by update_showcase.py, which also makes the
posters), writes one per-card entry per clip (scale-00, frame-03, ...) and rewrites the hero grid and the LongLive block
in index.html between the markers <!-- showcase:groups --> / <!-- showcase:long -->.
"""
import json, re, html as H
data = json.load(open("showcase-data.json")); page = open("index.html").read()
GROUPS = {"scale": ("Next-scale", "scale"), "frame": ("Next-frame", "frame"), "long": ("Next-frame", "long")}

KV = json.load(open("kv-memory.json"))
KV_MODEL = {"scale": "InfinityStar720p", "frame": "self_forcing", "long": "longlive"}

def kv_for(key, bits):
    q = "q" + bits.split("-")[0]
    entry = KV.get(KV_MODEL[key], {}).get("bits", {}).get(q, {})
    if "Baseline" in entry and "VARQ" in entry:
        b, v = entry["Baseline"], entry["VARQ"]
        return b, v, round((1 - v / b) * 100)
    return None

def card(key, n, cfg, clip):
    k = f"{key}-{n:02d}"; model = cfg["model"]; bits = cfg["bits"]; prompt = H.escape(clip["prompt"], quote=True)
    kv = kv_for(key, bits); prec = "INT" + bits.split("-")[0]
    cap_b = f"<b>BF16</b><br>{kv[0]:.1f} GB" if kv else "<b>BF16</b>"
    cap_v = f"<b>VAR-Q {prec}</b><br>{kv[1]:.1f} GB · −{kv[2]}%" if kv else f"<b>VAR-Q {prec}</b>"
    return f'''          <article class="feature-card direct-demo" data-feature="{k}">
            <h3 class="feature-title" title="{prompt}">{H.escape(clip["title"])}</h3>
            <div class="feature-pair">
              <figure class="feature-video">
                <figcaption>{cap_b}</figcaption>
                <video aria-describedby="showcase-note" aria-label="{H.escape(model)} BF16: {prompt}" data-src="{clip["sources"]["Baseline"]}" loop="" muted="" playsinline="" poster="{clip["posters"]["Baseline"]}" preload="none"></video>
              </figure>
              <figure class="feature-video feature-ours">
                <figcaption>{cap_v}</figcaption>
                <video aria-describedby="showcase-note" aria-label="{H.escape(model)} VAR-Q {prec}: {prompt}" data-src="{clip["sources"]["VARQ"]}" loop="" muted="" playsinline="" poster="{clip["posters"]["VARQ"]}" preload="none"></video>
              </figure>
            </div>
            <p class="feature-status sr-only" role="status"></p>
            <noscript><a href="{clip["sources"]["VARQ"]}">Watch the VAR-Q video</a></noscript>
          </article>
'''

def group(key, cfg):
    kv = kv_for(key, cfg["bits"])
    kvline = f" · KV cache {kv[0]:.1f} → {kv[1]:.1f} GB (−{kv[2]}%)" if kv else ""
    cards = "".join(card(key, n, cfg, c) for n, c in enumerate(cfg["clips"]))
    tag, cls = GROUPS[key]
    note = f'          <p class="showcase-group-note">{H.escape(cfg["note"])}</p>\n' if cfg.get("note") else ""
    head = f'''        <div class="showcase-group">
          <div class="showcase-group-head">
            <span class="paradigm-tag {cls}">{tag}</span>
            <h3>{H.escape(cfg.get("label", cfg["model"] + " · " + cfg["bits"] + " KV cache"))}</h3>
            <span class="showcase-group-count">{len(cfg["clips"])} prompts · same seed{kvline}</span>
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
open("index.html", "w").write(page)
json.dump(data, open("showcase-data.json", "w"), indent=2, ensure_ascii=False); open("showcase-data.json", "a").write("\n")
print({k: len(v["clips"]) for k, v in data.items() if k in GROUPS}, "cards:", page.count('class="feature-card direct-demo"'))
