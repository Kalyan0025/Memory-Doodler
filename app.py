import os, json, re, hashlib, random
import streamlit as st
from dotenv import load_dotenv
from streamlit.components.v1 import html as components_html

# ──────────────────────────────
# Setup
# ──────────────────────────────
load_dotenv()
st.set_page_config(page_title="Dream/Memory Doodler", page_icon="🌙", layout="centered")
st.title("🌙 Dream / Memory Doodler — Data Humanism Grid Edition")

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
    # very light heuristic person count
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
# Local fallback schema generator (now richer + grid)
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

left, right = st.columns([1,1])
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

function hashString(s){ let h=2166136261>>>0; for(let i=0;i<s.length;i++){ h^=s.charCodeAt(i); h=Math.imul(h,16777619); } return h>>>0; }
const SEED = SCHEMA.seed ?? hashString((SCHEMA.caption||'')+'|'+(SCHEMA.emotion||''));
const RNG  = mulberry32(SEED);

function mulberry32(a){ return function(){ var t = a += 0x6D2B79F5; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; } }

function pick(arr){ return arr[Math.floor(RNG()*arr.length)] }

new p5((p)=>{
  let centerPos, orbitR;
  p.setup = function(){
    p.randomSeed(SEED); p.noiseSeed(SEED);
    const c=p.createCanvas(900,900); c.parent(document.getElementById('p5mount'));
    centerPos=p.createVector(p.width/2,p.height/2);
    orbitR=Math.min(p.width,p.height)*0.24;
    document.getElementById('caption').textContent=SCHEMA.caption||'';
  };

  p.draw = function(){
    drawBackground(p, SCHEMA.palette||['#F79892','#FFD482','#C0A5D7']);
    drawGrid(p);
    drawMotifs(p);
    drawHalo(p);
  };
});

function drawBackground(p,palette){
  const c1=p.color(palette[0]), c2=p.color(palette[1]), c3=p.color(palette[2]);
  for(let y=0;y<p.height;y++){ const f=y/(p.height-1); const col=p.lerpColor(c1,c2,f); p.stroke(col); p.line(0,y,p.width,y); }
  p.noStroke(); for(let r=0;r<600;r++){ const a=p.map(r,0,600,110,0); p.fill(p.red(c3),p.green(c3),p.blue(c3),a*0.3); p.circle(p.width*0.83,p.height*0.17,r); }
}

function drawGrid(p){
  const rows = SCHEMA.grid?.rows || 3, cols = SCHEMA.grid?.cols || 3;
  const margin = 80, W = p.width - margin*2, H = p.height - margin*2;
  const cellW = W/cols, cellH = H/rows;
  p.push();
  p.translate(margin, margin);
  p.noFill(); p.stroke(120,90,70,80); p.strokeWeight(1);
  for(let r=0;r<=rows;r++){ p.line(0, r*cellH, W, r*cellH); }
  for(let c=0;c<=cols;c++){ p.line(c*cellW, 0, c*cellW, H); }
  p.pop();
}

function drawMotifs(p){
  const rows = SCHEMA.grid?.rows || 3, cols = SCHEMA.grid?.cols || 3;
  const margin = 80, W = p.width - margin*2, H = p.height - margin*2;
  const cellW = W/cols, cellH = H/rows;
  const motifs = (SCHEMA.motifs||[]);
  const emo = (SCHEMA.emotion||'nostalgia');
  const colors = getPsychColors(emo);

  p.push();
  p.translate(margin, margin);
  for(let idx=0; idx<rows*cols; idx++){
    const r = Math.floor(idx/cols), c = idx%cols;
    const cx = c*cellW + cellW/2; const cy = r*cellH + cellH/2;

    const kind = motifs[idx]?.kind || 'abstract';
    const seedCell = hashString(kind + '|' + idx + '|' + SEED);
    const RNGc = mulberry32(seedCell);

    const s = Math.min(cellW, cellH) * (0.65 + RNGc()*0.15);

    if(kind.startsWith('product:')){
      const name = kind.split(':')[1];
      drawProduct(p, name, cx, cy, s, colors.product, colors.accent, RNGc);
    } else if(kind === 'human'){
      drawHuman(p, cx, cy, s, colors.human, RNGc);
    } else {
      drawAbstract(p, cx, cy, s, colors.accent, RNGc);
    }
  }
  p.pop();
}

function getPsychColors(emo){
  const table = {
    joy:   {human:'#FFC857', product:'#EA7A70', accent:'#B388EB'},
    nostalgia:{human:'#D6A48E', product:'#BCAAA4', accent:'#A78BCC'},
    calm:  {human:'#90CAF9', product:'#A5D6A7', accent:'#B0BEC5'},
    love:  {human:'#FF9EAA', product:'#FFCDD2', accent:'#F8BBD0'},
    sad:   {human:'#78909C', product:'#90A4AE', accent:'#B0BEC5'},
    anxiety:{human:'#8FA3BF', product:'#B0B7C3', accent:'#9AA9B8'}
  };
  return table[emo] || table['nostalgia'];
}

function drawHuman(p, x, y, s, col, RNGc){
  p.push();
  p.translate(x,y);
  p.noFill(); p.stroke(50,40,35,120); p.strokeWeight(2);
  // aura
  for(let r=s*0.6; r>0; r-=s*0.08){ p.stroke(50,40,35, p.map(r,0,s*0.6,180,10)); p.circle(0,0, r*2); }
  // body
  p.fill(col); p.noStroke();
  p.circle(0, -s*0.22, s*0.22);                // head
  p.rect(-s*0.08, -s*0.22, s*0.16, s*0.35, s*0.08); // torso
  // limbs (minimalist)
  p.rect(-s*0.16, -s*0.02, s*0.12, s*0.08, s*0.04); // left arm
  p.rect( s*0.04, -s*0.02, s*0.12, s*0.08, s*0.04); // right arm
  p.rect(-s*0.12,  s*0.18, s*0.1,  s*0.16, s*0.04); // left leg
  p.rect( s*0.02,  s*0.18, s*0.1,  s*0.16, s*0.04); // right leg
  // micro face hint
  p.fill(255,255,255,140); p.ellipse(0,-s*0.24, s*0.12, s*0.08);
  p.fill(0,0,0,120); p.ellipse(-s*0.03,-s*0.24, s*0.02, s*0.02); p.ellipse(s*0.03,-s*0.24, s*0.02, s*0.02);
  p.pop();
}

function drawProduct(p, name, x, y, s, col, accent, RNGc){
  p.push(); p.translate(x,y);
  p.noFill(); p.stroke(60,45,40,90); p.strokeWeight(1.5);
  p.circle(0,0, s*0.9);
  p.fill(col); p.noStroke();
  if(name==='bottle'){
    p.rect(-s*0.14,-s*0.25, s*0.28, s*0.5, s*0.12);
    p.rect(-s*0.06,-s*0.33, s*0.12, s*0.1, s*0.04);
  } else if(name==='cake'){
    p.rect(-s*0.2, s*0.05, s*0.4, s*0.18, s*0.06);
    p.rect(-s*0.18,-s*0.06, s*0.36, s*0.12, s*0.06);
    p.fill(accent); p.triangle(0,-s*0.18, -s*0.02,-s*0.05, s*0.02,-s*0.05);
  } else if(name==='phone'){
    p.rect(-s*0.16,-s*0.26, s*0.32, s*0.52, s*0.06);
    p.fill(255,255,255,90); p.rect(-s*0.12,-s*0.2, s*0.24, s*0.4, s*0.04);
  } else if(name==='car'){
    p.rect(-s*0.22, 0, s*0.44, s*0.12, s*0.06);
    p.rect(-s*0.16,-s*0.08, s*0.32, s*0.08, s*0.06);
    p.fill(40,40,40,160); p.circle(-s*0.14, s*0.12, s*0.12); p.circle(s*0.14, s*0.12, s*0.12);
  } else if(name==='bag'){
    p.rect(-s*0.2,-s*0.1, s*0.4, s*0.3, s*0.06);
    p.noFill(); p.stroke(col); p.strokeWeight(4); p.arc(0,-s*0.13, s*0.28, s*0.2, Math.PI, 0);
  } else if(name==='book'){
    p.rect(-s*0.2,-s*0.14, s*0.4, s*0.28, s*0.02);
    p.fill(255,255,255,200); p.rect(-s*0.18,-s*0.12, s*0.36, s*0.24);
  } else if(name==='camera'){
    p.rect(-s*0.22,-s*0.12, s*0.44, s*0.24, s*0.04);
    p.fill(255,255,255,200); p.circle(0,0, s*0.22);
  } else if(name==='flower'){
    for(let i=0;i<8;i++){ let a=i*Math.PI/4; p.ellipse(Math.cos(a)*s*0.16, Math.sin(a)*s*0.16, s*0.18, s*0.10); }
    p.fill(255,215,120,220); p.circle(0,0, s*0.16);
  } else if(name==='guitar'){
    p.ellipse(-s*0.08,0, s*0.28, s*0.22); p.ellipse(s*0.08,0, s*0.22, s*0.18);
    p.rect(-s*0.02,-s*0.28, s*0.04, s*0.28);
  } else if(name==='laptop'){
    p.rect(-s*0.22,0, s*0.44, s*0.12, s*0.03); p.rect(-s*0.2,-s*0.16, s*0.4, s*0.16, s*0.03);
  } else {
    drawAbstract(p,0,0,s,col,RNGc);
  }
  p.pop();
}

function drawAbstract(p, x, y, s, col, RNGc){
  p.push();
  p.translate(x,y);
  p.noFill(); p.stroke(60,45,40,100); p.circle(0,0, s*0.9);
  p.noFill(); p.stroke(col); p.strokeWeight(2);
  for(let i=0;i<5;i++){
    const a = (RNGc()*Math.PI*2);
    p.bezier(-s*0.3, Math.sin(a)*s*0.2,
             -s*0.1, Math.cos(a)*s*0.25,
              s*0.1, Math.sin(a)*s*0.25,
              s*0.3, Math.cos(a)*s*0.2);
  }
  p.pop();
}

function drawHalo(p){
  const cx=p.width*0.5, cy=p.height*0.5, radius=Math.min(p.width,p.height)*0.14;
  p.noStroke();
  for(let r=radius; r>0; r-=6){
    const a=p.map(r,0,radius,180,0);
    p.fill(255,195,80, a*0.5);
    p.circle(cx,cy,r*2);
  }
}

function savePNG(){
  const c=document.querySelector('canvas'); if(!c) return;
  const link=document.createElement('a'); link.download='memory_doodle.png'; link.href=c.toDataURL('image/png'); link.click();
}
</script>
</body>
</html>
"""

# Render
try:
    components_html("<div style='padding:6px;font:14px system-ui'>Loading canvas…</div>", height=40, scrolling=False)
    components_html(p5_html, height=980, scrolling=False)
except Exception as e:
    st.error("⚠️ Failed to render p5.js canvas. See details below.")
    st.exception(e)
    st.write("schema:", schema)
    st.write("p5_html length:", len(p5_html))
    st.code(p5_html[:600], language="html")

# Debug
with st.expander("Gemini debug"):
    st.write("Chosen model:", chosen_model)
    if available_models:
        st.json(available_models)
    st.json(schema)
