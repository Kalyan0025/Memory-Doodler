import os, json, re, hashlib
import streamlit as st
from dotenv import load_dotenv
from streamlit.components.v1 import html as components_html

# ──────────────────────────────
# Setup
# ──────────────────────────────
load_dotenv()
st.set_page_config(page_title="Dream/Memory Doodler", page_icon="🌙", layout="centered")
st.title("🌙 Dream / Memory Doodler")

# ──────────────────────────────
# Gemini setup (safe + fallback)
# ──────────────────────────────
USE_GEMINI = True
try:
    import google.generativeai as genai
except Exception:
    USE_GEMINI = False

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PREF_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")

available_models, chosen_model = [], None
if USE_GEMINI and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        for m in genai.list_models():
            if "generateContent" in getattr(m, "supported_generation_methods", []):
                if "flash" in m.name and "exp" not in m.name:
                    available_models.append(m.name)
        for c in (PREF_MODEL, f"models/{PREF_MODEL}"):
            if c in available_models:
                chosen_model = c
                break
        if not chosen_model and available_models:
            chosen_model = available_models[0]
    except Exception as e:
        st.warning(f"Model listing failed; fallback. ({e})")
        chosen_model = None
else:
    chosen_model = None

# ──────────────────────────────
# Helpers
# ──────────────────────────────
def stable_int_seed(s: str) -> int:
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return int(h[:8], 16)

PRODUCT_VOCAB = {
    "bottle": ["bottle", "water", "drink", "perfume", "shampoo"],
    "cake": ["cake", "birthday cake", "candles"],
    "phone": ["phone", "iphone", "android", "mobile"],
    "car": ["car", "auto", "vehicle"],
    "bag": ["bag", "handbag", "backpack", "tote"],
    "book": ["book", "novel", "textbook"],
    "camera": ["camera", "dslr"],
    "flower": ["flower", "bouquet", "rose", "tulip"],
    "guitar": ["guitar", "music"],
    "laptop": ["laptop", "macbook", "computer"],
}

THEME_HINTS = {
    "moon": ["moon", "lunar", "space", "astronaut"],
    "beach": ["beach", "ocean", "sea", "waves"],
    "party": ["party", "birthday", "celebration", "dj"],
    "school": ["school", "class", "teacher", "exam"],
    "family": ["family", "parents", "kids"],
}

EMO_PALETTES = {
    "joy": ["#FFD482", "#F79892", "#F5B3FF"],
    "nostalgia": ["#F7C6B3", "#EBD8C3", "#C0A5D7"],
    "calm": ["#B9E3FF", "#DDEBF2", "#BFD6C7"],
    "love": ["#FFB3C1", "#FFDDE1", "#FFF0F3"],
    "sad": ["#9DB4C0", "#6C7A89", "#C7D3DD"],
    "anxiety": ["#A3B1C6", "#D6D6D6", "#8A9DB0"],
}

COLOR_PSYCH = {
    "joy": {"human": "#FFC857", "product": "#EA7A70", "accent": "#B388EB"},
    "nostalgia": {"human": "#D6A48E", "product": "#BCAAA4", "accent": "#A78BCC"},
    "calm": {"human": "#90CAF9", "product": "#A5D6A7", "accent": "#B0BEC5"},
    "love": {"human": "#FF9EAA", "product": "#FFCDD2", "accent": "#F8BBD0"},
    "sad": {"human": "#78909C", "product": "#90A4AE", "accent": "#B0BEC5"},
    "anxiety": {"human": "#8FA3BF", "product": "#B0B7C3", "accent": "#9AA9B8"},
}

def extract_entities(text: str):
    t = text.lower()
    human_tokens = ["friend", "friends", "people", "crowd", "family", "we", "us", "team"]
    humans = 1 + sum(t.count(tok) for tok in human_tokens)
    humans = max(1, min(12, humans))

    products = []
    for key, kws in PRODUCT_VOCAB.items():
        if any(k in t for k in kws):
            products.append(key)
    if not products and ("birthday" in t or "party" in t):
        products.append("cake")

    theme = None
    for name, kws in THEME_HINTS.items():
        if any(k in t for k in kws):
            theme = name
            break

    return {"humans": humans, "products": products[:6], "theme": theme}

# ──────────────────────────────
# Local fallback schema generator
# ──────────────────────────────
def local_schema_from_text(text: str, default_schema: dict) -> dict:
    t = text.lower()
    EMO = {
        "joy": ["happy", "fun", "birthday", "party", "smile", "laugh"],
        "nostalgia": ["childhood", "old", "school", "remember", "reunion"],
        "calm": ["calm", "peace", "quiet", "relax"],
        "love": ["love", "together", "family", "friends"],
        "sad": ["sad", "alone", "miss", "cry", "loss"],
        "anxiety": ["stress", "worried", "fear", "nervous"],
    }
    counts = {e: sum(t.count(k) for k in kws) for e, kws in EMO.items()}
    emotion = max(counts, key=counts.get) if any(counts.values()) else "nostalgia"

    exclaim = t.count("!")
    caps = sum(1 for w in re.findall(r"[A-Z]{2,}", text) if len(w) > 2)
    intensity = min(1.0, 0.35 + 0.1 * exclaim + 0.05 * caps)

    palette = EMO_PALETTES.get(emotion, default_schema["palette"])[:3]

    ent = extract_entities(text)
    nodes = max(3, min(20, ent["humans"] + len(ent["products"]) + 2))

    caption = default_schema.get("caption", "A day to remember")
    if "birthday" in t and "friend" in t:
        caption = "Old friends, new laughter"
    elif "birthday" in t:
        caption = "A day that glowed"
    elif "reunion" in t or "childhood" in t:
        caption = "Back to where we began"

    seed = stable_int_seed(text.strip())

    # grid stays constant (square-ish) but cell motifs depend on narration
    cells = max(4, min(16, ent["humans"] + max(1, len(ent["products"])) ))
    cols = min(4, max(2, int(round(cells ** 0.5))))
    rows = (cells + cols - 1) // cols
    motifs = []

    # populate motifs: prioritize humans, then products, then abstract
    for _ in range(ent["humans"]):
        motifs.append({"kind": "human"})
    for k in ent["products"]:
        motifs.append({"kind": f"product:{k}"})
    while len(motifs) < rows * cols:
        motifs.append({"kind": "abstract"})

    return {
        "emotion": emotion,
        "intensity": round(float(intensity), 2),
        "palette": palette,
        "nodes": int(nodes),
        "caption": caption[:64],
        "seed": seed,
        "grid": {"rows": rows, "cols": cols},
        "motifs": motifs[: rows * cols],
        "theme": ent["theme"] or "generic",
    }

# ──────────────────────────────
# UI
# ──────────────────────────────
prompt = st.text_area(
    "Describe your memory or dream",
    "I had my birthday yesterday and met a lot of childhood friends — we laughed, cut a cake, and took photos under the moon.",
    height=120,
)

left, right = st.columns([1, 1])
with left:
    do_generate = st.button("Generate")
with right:
    lock_grid = st.checkbox("Lock grid layout across runs", value=True, help="Keeps row/col constant; motifs still change by narration.")

# ──────────────────────────────
# Defaults
# ──────────────────────────────
default_schema = {
    "emotion": "nostalgia",
    "intensity": 0.8,
    "palette": ["#F79892", "#FFD482", "#C0A5D7"],
    "nodes": 10,
    "caption": "October 25 — Old friends, new laughter",
    "seed": stable_int_seed("default"),
    "grid": {"rows": 3, "cols": 3},
    "motifs": [{"kind": "abstract"}] * 9,
    "theme": "generic",
}

schema = default_schema.copy()

# ──────────────────────────────
# Gemini call + fallback
# ──────────────────────────────
def run_llm(text: str):
    if not (GEMINI_API_KEY and chosen_model):
        return None
    try:
        model = genai.GenerativeModel(chosen_model)
        system_hint = (
            "Return ONLY JSON with keys: emotion (string), intensity (0..1), "
            "palette (array of 3 hex strings), nodes (int 3..20), caption (<=64 chars), "
            "seed (int), grid (object with rows, cols), motifs (array of {kind:string}), theme (string). "
            "Kinds allowed: human | abstract | product:(bottle|cake|phone|car|bag|book|camera|flower|guitar|laptop)."
        )
        resp = model.generate_content([system_hint, f"Memory:\n{text}"])
        raw = (resp.text or "").strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            i, j = raw.find("{"), raw.rfind("}")
            raw = raw[i:j+1]
        data = json.loads(raw)
        out = {
            "emotion": str(data.get("emotion", schema["emotion"]))[:40],
            "intensity": max(0.0, min(1.0, float(data.get("intensity", schema["intensity"])))),
            "palette": (data.get("palette", schema["palette"]) or schema["palette"])[:3],
            "nodes": max(3, min(20, int(data.get("nodes", schema["nodes"])))),
            "caption": str(data.get("caption", schema["caption"]))[:64],
            "seed": int(data.get("seed", stable_int_seed(text))),
            "grid": {
                "rows": max(2, min(4, int(data.get("grid", {}).get("rows", 3)))),
                "cols": max(2, min(4, int(data.get("grid", {}).get("cols", 3)))),
            },
            "motifs": data.get("motifs", []),
            "theme": str(data.get("theme", "generic"))[:24],
        }
        if not out["motifs"]:
            # build via local if LLM omitted
            local = local_schema_from_text(text, default_schema)
            out["motifs"] = local["motifs"]
            if lock_grid:
                out["grid"] = local["grid"]
        return out
    except Exception:
        st.info("💡 Using local generator (Gemini quota reached or offline).")
        return None

if do_generate:
    llm_schema = run_llm(prompt)
    schema = llm_schema if llm_schema else local_schema_from_text(prompt, default_schema)
    if lock_grid:
        # normalize to stable 3x3 for consistent framing if desired
        schema["grid"]["rows"] = min(4, max(2, schema["grid"]["rows"]))
        schema["grid"]["cols"] = min(4, max(2, schema["grid"]["cols"]))

# ──────────────────────────────
# p5.js visualization
# ──────────────────────────────
schema_hash = hashlib.md5(json.dumps(schema, sort_keys=True).encode()).hexdigest()
schema_js = json.dumps(schema, ensure_ascii=True, separators=(",", ":"))

p5_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<meta name='x-schema-hash' content='{schema_hash}'>
<style>
html,body {{margin:0;padding:0;background:#faf7f5;}}
#wrap {{position:relative;width:900px;margin:0 auto;}}
#btnsave {{
  position:absolute;top:12px;right:12px;z-index:10;
  padding:8px 12px;border:1px solid #d9cbb9;border-radius:8px;background:#fff;
  font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;cursor:pointer;
}}
#caption {{
  position:absolute;bottom:10px;right:16px;color:rgba(70,60,65,0.85);font-size:18px;
  font-family:Georgia,serif;pointer-events:none;text-shadow:0 1px 0 rgba(255,255,255,0.4);
}}
canvas {{border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,0.06);}}
</style>
</head>
<body>
<div id='wrap' data-schema-hash='{schema_hash}'>
  <button id='btnsave' onclick='savePNG()'>Download PNG</button>
  <div id='p5mount'></div>
  <div id='caption'></div>
</div>

<script src='https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.4/p5.min.js'></script>
<script>
const SCHEMA = {schema_js};

function hashString(s){{ let h=2166136261>>>0; for(let i=0;i<s.length;i++){{ h^=s.charCodeAt(i); h=Math.imul(h,16777619); }} return h>>>0; }}
const SEED=hashString((SCHEMA.caption||'')+'|'+(SCHEMA.emotion||'')+'|'+(SCHEMA.nodes||'')+'|'+JSON.stringify(SCHEMA.palette||[]));
const LAYOUT=(SEED%3),RIPPLE_COUNT=4+(SEED%5),THREAD_OPACITY=80+(SEED%60),BG_ANGLE=(SEED%360)*Math.PI/180,BREATH_BASE=0.015+(SCHEMA.intensity?SCHEMA.intensity*0.025:0.02);

let centerPos,orbitR,nodes=[];
new p5((p)=>{{
  p.setup=function(){{
    p.randomSeed(SEED); p.noiseSeed(SEED);
    const c=p.createCanvas(900,900); c.parent(document.getElementById('p5mount'));
    centerPos=p.createVector(p.width/2,p.height/2);
    orbitR=Math.min(p.width,p.height)*(0.22+(SEED%8)*0.01);
    const N=Math.max(3,Math.min(20,SCHEMA.nodes||10));

    if(LAYOUT===0) {{
      for(let i=0;i<N;i++) {{
        const a=p.TWO_PI*i/N-p.PI/2;
        const rJit=orbitR*(0.9+p.random()*0.2);
        nodes.push({{x:centerPos.x+rJit*Math.cos(a),y:centerPos.y+rJit*Math.sin(a),phase:p.random(p.TWO_PI)}});
      }}
    }} else if(LAYOUT===1) {{
      const step=orbitR*(1.0/N);
      for(let i=0;i<N;i++) {{
        const a=(i*0.9)+(SEED%10)*0.03; const r=step*(i+3);
        nodes.push({{x:centerPos.x+r*Math.cos(a),y:centerPos.y+r*Math.sin(a),phase:p.random(p.TWO_PI)}});
      }}
    }} else {{
      const clusters=2+(SEED%2);
