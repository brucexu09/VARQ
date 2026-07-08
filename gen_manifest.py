#!/usr/bin/env python3
import os, re, json, glob

DEMO = "/data/jiaji_lu/NIPS/samples/demo"
REPO = "/home/boxunxu/research/VARQ"
SAMP = os.path.join(REPO, "samples")

# Display config per model
MODELS = [
    ("VAR_d30", "VAR-d30", "image", "Class-conditional ImageNet 256×256"),
    ("VAR_d24", "VAR-d24", "image", "Class-conditional ImageNet 256×256"),
    ("VAR_d20", "VAR-d20", "image", "Class-conditional ImageNet 256×256"),
    ("Infinity2B", "Infinity-2B", "image", "Text-to-Image generation"),
    ("Infinity8B", "Infinity-8B", "image", "Text-to-Image generation"),
    ("InfinityStar480p", "InfinityStar-480p", "video", "Text-to-Video generation (480p)"),
    ("InfinityStar720p", "InfinityStar-720p", "video", "Text-to-Video generation (720p)"),
    ("self_forcing", "Self-Forcing", "video", "Streaming autoregressive video"),
    ("longlive", "LongLive", "video", "Long-horizon video generation"),
]
METHOD_ORDER = ["Baseline", "FlexGen", "KIVI", "VARQ"]
METHOD_LABEL = {"Baseline": "Baseline (BF16)", "FlexGen": "FlexGen", "KIVI": "KIVI", "VARQ": "VARQ (Ours)"}

def qlabel(q):
    m = re.match(r"q(\d+)", q)
    return f"{m.group(1)}-bit" if m else q

def idx_key(fn):
    m = re.search(r"idx(\d+)", fn)
    return m.group(1) if m else None

def video_key(fn):
    # strip leading groupNN_ ; align across methods by remainder
    return re.sub(r"^group\d+_", "", fn)

def read_prompts_infinity(model):
    """group number -> prompt text"""
    md = os.path.join(DEMO, model, "_metadata")
    out = {}  # qbits -> {group -> prompt}
    for q in os.listdir(md):
        qd = os.path.join(md, q)
        if not os.path.isdir(qd):
            continue
        gp = {}
        for f in glob.glob(os.path.join(qd, "group*_prompt.txt")):
            g = re.search(r"group(\d+)_prompt", f).group(1)
            gp[g] = open(f).read().strip()
        out[q] = gp
    return out

def read_prompts_video(model):
    """qbits -> {idx(str,no pad) -> prompt}"""
    md = os.path.join(DEMO, model, "_metadata")
    out = {}
    if not os.path.isdir(md):
        return out
    for q in os.listdir(md):
        qd = os.path.join(md, q)
        if not os.path.isdir(qd):
            continue
        pm = {}
        for f in glob.glob(os.path.join(qd, "group*_prompt.txt")):
            for line in open(f):
                m = re.match(r"\[\d+\]\s*idx=(\d+):\s*(.+)", line.strip())
                if m:
                    pm[str(int(m.group(1)))] = m.group(2).strip()
        out[q] = pm
    return out

def read_scores(model):
    """qbits -> {rawidx(str,int) -> (varq_psnr, margin)}"""
    md = os.path.join(DEMO, model, "_metadata")
    out = {}
    if not os.path.isdir(md):
        return out
    for q in os.listdir(md):
        qd = os.path.join(md, q)
        if not os.path.isdir(qd):
            continue
        sc = {}
        for f in glob.glob(os.path.join(qd, "group*_scores.txt")):
            for line in open(f):
                m = re.match(r"idx=(\d+)\s+iters=(\d+)\s+img=(\d+)\s+varq_psnr=([\d.]+)\s+margin=([\-\d.]+)", line.strip())
                if m:
                    sc[f"iters{m.group(2)}_img{m.group(3)}"] = (float(m.group(4)), float(m.group(5)))
        out[q] = sc
    return out

manifest = {"models": []}

for mid, label, mtype, task in MODELS:
    mroot = os.path.join(SAMP, mid)
    if not os.path.isdir(mroot):
        continue
    methods_present = [m for m in METHOD_ORDER if os.path.isdir(os.path.join(mroot, m))]
    # determine bits present (union across methods)
    bits = set()
    for m in methods_present:
        for q in os.listdir(os.path.join(mroot, m)):
            if os.path.isdir(os.path.join(mroot, m, q)):
                bits.add(q)
    bits = sorted(bits, key=lambda x: int(re.match(r"q(\d+)", x).group(1)))

    inf_prompts = read_prompts_infinity(mid) if mid.startswith("Infinity") and "Star" not in mid else {}
    vid_prompts = read_prompts_video(mid) if mtype == "video" else {}
    scores = read_scores(mid)

    model_entry = {
        "id": mid, "label": label, "type": mtype, "task": task,
        "methods": methods_present,
        "methodLabels": {m: METHOD_LABEL[m] for m in methods_present},
        "bits": bits, "bitLabels": {q: qlabel(q) for q in bits},
        "samples": {},
    }

    for q in bits:
        # collect files per method for this bit
        per_method = {}
        for m in methods_present:
            d = os.path.join(mroot, m, q)
            if os.path.isdir(d):
                per_method[m] = sorted(os.listdir(d))
        # build grouping key -> {method: relpath}
        groups = {}   # key -> {method: relpath, "sortidx": ...}
        for m, files in per_method.items():
            for fn in files:
                if mtype == "video":
                    key = video_key(fn)
                else:
                    key = idx_key(fn) or fn
                rel = f"samples/{mid}/{m}/{q}/{fn}"
                g = groups.setdefault(key, {"media": {}, "fn": {}})
                g["media"][m] = rel
                g["fn"][m] = fn
        # order keys: prefer VARQ file order
        ordered_keys = []
        ref = "VARQ" if "VARQ" in per_method else methods_present[0]
        seen = set()
        for fn in per_method.get(ref, []):
            key = video_key(fn) if mtype == "video" else (idx_key(fn) or fn)
            if key not in seen:
                ordered_keys.append(key); seen.add(key)
        for key in groups:
            if key not in seen:
                ordered_keys.append(key); seen.add(key)

        samples = []
        for gi, key in enumerate(ordered_keys):
            g = groups[key]
            # any filename to derive metadata
            anyfn = next(iter(g["fn"].values()))
            prompt = None; caption = None
            if mtype == "video":
                pm = vid_prompts.get(q, {})
                idxm = re.search(r"prompt(\d+)", anyfn)
                if idxm:
                    prompt = pm.get(str(int(idxm.group(1))))
            elif mid.startswith("Infinity") and "Star" not in mid:
                gp = inf_prompts.get(q, {})
                gm = None
                for fn in g["fn"].values():
                    gm = re.search(r"group(\d+)", fn)
                    if gm:
                        break
                if gm:
                    prompt = gp.get(gm.group(1))
            # metric caption from scores (match by iters_img token)
            sc = scores.get(q, {})
            it = re.search(r"(iters\d+_img\d+)", anyfn)
            if it and it.group(1) in sc:
                p, marg = sc[it.group(1)]
                caption = f"VARQ PSNR {p:.1f} dB &nbsp;<span class='pos'>(+{marg:.1f} dB vs. best baseline)</span>"
            samples.append({
                "prompt": prompt,
                "caption": caption,
                "media": g["media"],
            })
        model_entry["samples"][q] = samples

    manifest["models"].append(model_entry)

out = os.path.join(REPO, "manifest.json")
json.dump(manifest, open(out, "w"), indent=1, ensure_ascii=False)
# summary
for me in manifest["models"]:
    ns = {q: len(me["samples"][q]) for q in me["bits"]}
    print(f"{me['label']:20s} type={me['type']:5s} methods={me['methods']} bits={me['bits']} nsamp={ns}")
print("wrote", out)
