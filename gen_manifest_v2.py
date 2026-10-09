#!/usr/bin/env python3
"""Merge new demo samples (generated with the public VAR-Q repo) into manifest.json.

Source layout (per model):  <src>/<Method>/<qbits>/{idx|prompt}NN.{jpg|mp4}  +  <src>/metrics_<qbits>.json
Site layout:                samples/<Model>/<Method>/<qbits>/<file>
Existing manifest entries for other (model, qbits) pairs are preserved verbatim.
"""
import json, os, re, shutil, sys

REPO = os.path.dirname(os.path.abspath(__file__))
SAMP = os.path.join(REPO, "samples")
SRC = "/data1/boxunxu/varq_demo"

METHOD_ORDER = ["Baseline", "FlexGen", "KIVI", "VARQ"]
METHOD_LABEL = {"Baseline": "Baseline (BF16)", "FlexGen": "FlexGen", "KIVI": "KIVI", "VARQ": "VARQ (Ours)"}
MODEL_META = {  # id -> (label, type, task)
    "self_forcing": ("Self-Forcing", "video", "Streaming autoregressive video (Wan 1.3B, 5 s, 832×480)"),
    "longlive": ("LongLive", "video", "Long-horizon autoregressive video (30 s, 832×480)"),
    "Infinity8B": ("Infinity-8B", "image", "Text-to-Image generation (1024×1024)"),
}
MODEL_ORDER = ["self_forcing", "longlive", "Infinity8B", "InfinityStar480p", "InfinityStar720p",
               "Infinity2B", "VAR_d30", "VAR_d24", "VAR_d20"]

# (model, qbits) -> source root, method dir names, file stem, extension, optional index selection
NEW = {
    ("self_forcing", "q4"): dict(src=f"{SRC}/self_forcing", dirs={"Baseline": "Baseline", "VARQ": "VARQr8", "KIVI": "KIVI", "FlexGen": "FlexGen"}, stem="prompt", ext="mp4", caption=False),
    ("longlive", "q4"): dict(src=f"{SRC}/longlive", dirs={"Baseline": "Baseline", "VARQ": "VARQr8", "KIVI": "KIVI", "FlexGen": "FLexGen"}, stem="prompt", ext="mp4", caption=False),
    ("Infinity8B", "q2"): dict(src=f"{SRC}/infinity8b", dirs={"Baseline": "Baseline", "VARQ": "VARQ", "KIVI": "KIVI", "FlexGen": "FlexGen"}, stem="idx", ext="jpg"),
    ("Infinity8B", "q3"): dict(src=f"{SRC}/infinity8b", dirs={"Baseline": "Baseline", "VARQ": "VARQ", "KIVI": "KIVI", "FlexGen": "FlexGen"}, stem="idx", ext="jpg"),
}
SELECT_FILE = os.path.join(REPO, "selection.json")  # {"self_forcing/q4": [3, 7, ...], ...}; absent -> all


def qlabel(q):
    m = re.match(r"q(\d+)", q); return f"{m.group(1)}-bit" if m else q


def caption(psnr):
    if "VARQ" not in psnr: return None
    parts = [f"VARQ <b>{psnr['VARQ']:.1f} dB</b>"]
    others = [(m, psnr[m]) for m in ("KIVI", "FlexGen") if m in psnr]
    parts += [f"{m} {v:.1f}" for m, v in others]
    s = " &nbsp;·&nbsp; ".join(parts)
    if others:
        margin = psnr["VARQ"] - max(v for _, v in others)
        s += f" &nbsp;<span class='pos'>({margin:+.1f} dB PSNR)</span>"
    return s


def build_samples(mid, q, spec, select):
    mpath = os.path.join(spec["src"], f"metrics_{q}.json")
    if not os.path.exists(mpath):
        return []
    metrics = json.load(open(mpath))
    idxs = [f"{i:02d}" for i in select] if select else sorted(metrics)
    samples = []
    for key in idxs:
        m = metrics[key]; media = {}
        for meth, d in spec["dirs"].items():
            fn = f"{spec['stem']}{key}.{spec['ext']}"
            srcf = os.path.join(spec["src"], d, q, fn)
            if not os.path.exists(srcf):
                continue
            dst_dir = os.path.join(SAMP, mid, meth, q); os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, fn)
            if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(srcf):
                shutil.copy2(srcf, dst)
            media[meth] = f"samples/{mid}/{meth}/{q}/{fn}"
        if "Baseline" in media and "VARQ" in media:
            cap = caption(m.get("psnr", {})) if spec.get("caption", True) else None
            samples.append({"prompt": m.get("prompt"), "caption": cap, "media": media})
    return samples


def main():
    manifest = json.load(open(os.path.join(REPO, "manifest.json")))
    by_id = {m["id"]: m for m in manifest["models"]}
    select = json.load(open(SELECT_FILE)) if os.path.exists(SELECT_FILE) else {}
    for (mid, q), spec in NEW.items():
        samples = build_samples(mid, q, spec, select.get(f"{mid}/{q}"))
        if not samples:
            print(f"[skip] {mid}/{q}: no complete samples"); continue
        # drop stale copies of this (model, qbits) on disk that are not in the new set
        keep = {os.path.basename(p) for s in samples for p in s["media"].values()}
        for meth in spec["dirs"]:
            d = os.path.join(SAMP, mid, meth, q)
            if os.path.isdir(d):
                for fn in os.listdir(d):
                    if fn not in keep: os.remove(os.path.join(d, fn))
        label, mtype, task = MODEL_META[mid]
        entry = by_id.get(mid) or {"id": mid, "samples": {}}
        entry.update({"label": label, "type": mtype, "task": task})
        entry["samples"][q] = samples
        entry["bits"] = sorted(entry["samples"], key=lambda x: int(re.match(r"q(\d+)", x).group(1)))
        entry["bitLabels"] = {b: qlabel(b) for b in entry["bits"]}
        entry["methodsByBit"] = {b: [m for m in METHOD_ORDER if any(m in s["media"] for s in entry["samples"][b])] for b in entry["bits"]}
        entry["methods"] = [m for m in METHOD_ORDER if any(m in ms for ms in entry["methodsByBit"].values())]
        entry["methodLabels"] = {m: METHOD_LABEL[m] for m in entry["methods"]}
        by_id[mid] = entry
        print(f"[ok] {mid}/{q}: {len(samples)} samples, methods={entry['methodsByBit'][q]}")
    ordered = [by_id[i] for i in MODEL_ORDER if i in by_id] + [m for i, m in by_id.items() if i not in MODEL_ORDER]
    manifest["models"] = ordered
    json.dump(manifest, open(os.path.join(REPO, "manifest.json"), "w"), indent=1, ensure_ascii=False)
    for me in manifest["models"]:
        counts = ", ".join("%s:%d" % (q, len(me["samples"][q])) for q in me["bits"])
        print("%-20s %-5s bits=%s n={%s}" % (me["label"], me["type"], me["bits"], counts))

if __name__ == "__main__":
    main()
