import os, json, re, hashlib
import streamlit as st
from dotenv import load_dotenv
from streamlit.components.v1 import html as components_html
from PIL import Image, ImageDraw, ImageFont
import requests

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
    intensity = min(1.0, 0.4 + 0.1 * exclaim + 0.05 * caps)

    PALETTES = {
        "joy": ["#FFD482", "#F79892", "#F5B3FF"],
        "nostalgia": ["#F7C6B3", "#EBD8C3", "#C0A5D7"],
        "calm": ["#B9E3FF", "#DDEBF2", "#BFD6C7"],
        "love": ["#FFB3C1", "#FFDDE1", "#FFF0F3"],
        "sad": ["#9DB4C0", "#6C7A89", "#C7D3DD"],
        "anxiety": ["#A3B1C6", "#D6D6D6", "#8A9DB0"],
    }
    palette = PALETTES.get(emotion, default_schema["palette"])

    nodes = 6 if "friend" in t else 4
    for w in ["friends", "family", "group", "team", "all"]:
        if w in t:
            nodes += 2
    nodes = max(3, min(20, nodes))

    caption = "A day to remember"
    if "birthday" in t and "friend" in t:
        caption = "Old friends, new laughter"
    elif "birthday" in t:
        caption = "A day that glowed"
    elif "reunion" in t or "childhood" in t:
        caption = "Back to where we began"

    seed = stable_int_seed(text.strip())

    # grid stays constant (square-ish) but cell motifs depend on narration
    cells = max(4, min(16, len(extract_entities(text)["humans"]) + max(1, len(extract_entities(text)["products"])) ))
    cols = min(4, max(2, int(round(cells ** 0.5))))
    rows = (cells + cols - 1) // cols
    motifs = []

    # populate motifs: prioritize humans, then products, then abstract
    for _ in range(len(extract_entities(text)["humans"])):
        motifs.append({"kind": "human"})
    for k in extract_entities(text)["products"]:
        motifs.append({"kind": f"product:{k}"})
    while len(motifs) < rows * cols:
        motifs.append({"kind": "abstract"})

    return {
        "emotion": emotion,
        "intensity": round(intensity, 2),
        "palette": palette,
        "nodes": int(nodes),
        "caption": caption[:64],
        "seed": seed,
        "grid": {"rows": rows, "cols": cols},
        "motifs": motifs[: rows * cols],
        "theme": extract_entities(text)["theme"] or "generic",
    }

# ──────────────────────────────
# UI
# ──────────────────────────────
prompt = st.text_area(
    "Describe your memory or dream",
    "I had my birthday yesterday and met a lot of childhood friends — it was a memorable birthday for me.",
    height=120,
)
do_generate = st.button("Generate")

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
# p5.js visualization (no 'key'; force remount via schema hash in DOM)
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
      const centers=[];
      for(let k=0;k<clusters;k++) {{
        const ang=(k/clusters)*p.TWO_PI+0.6*(SEED%7);
        const rad=orbitR*0.6;
        centers.push({{x:centerPos.x+rad*Math.cos(ang),y:centerPos.y+rad*Math.sin(ang)}});
      }}
      for(let i=0;i<N;i++) {{
        const cidx=i%clusters; const cx=centers[cidx].x, cy=centers[cidx].y;
        const r=50+p.random(80), a=p.random(p.TWO_PI);
        nodes.push({{x:cx+r*Math.cos(a),y:cy+r*Math.sin(a),phase:p.random(p.TWO_PI)}});
      }}
    }}

    document.getElementById('caption').textContent=SCHEMA.caption||'';
  }};

  p.draw=function(){{
    drawBackground(p,SCHEMA.palette||['#F79892','#FFD482','#C0A5D7']);
    p.noFill();

    // ripples
    p.push(); p.translate(centerPos.x,centerPos.y);
    const t=p.frameCount*0.01;
    for(let i=0;i<RIPPLE_COUNT;i++) {{
      const baseIn=orbitR*0.85, baseOut=orbitR*1.65;
      const r=p.map((t+i*0.25)%1,0,1,baseIn,baseOut);
      p.stroke(255,215,130,p.map(r,baseIn,baseOut,90,0));
      p.strokeWeight(1.25); p.circle(0,0,r*2);
    }}
    p.pop();

    // threads
    p.stroke(230,180,90,THREAD_OPACITY); p.strokeWeight(1.3);
    for(let i=0;i<nodes.length;i++) {{
      const a=nodes[i]; const b=nodes[(i+1)%nodes.length];
      p.line(centerPos.x,centerPos.y,a.x,a.y);
      p.bezier(a.x,a.y,
               p.lerp(a.x,centerPos.x,0.25), p.lerp(a.y,centerPos.y,0.25),
               p.lerp(b.x,centerPos.x,0.25), p.lerp(b.y,centerPos.y,0.25),
               b.x,b.y);
    }}

    // center glow
    drawGlow(p,centerPos.x,centerPos.y,Math.min(p.width,p.height)*0.16,p.color(255,195,80,130));
    p.fill(255,190,70,200); p.noStroke();
    p.circle(centerPos.x,centerPos.y,Math.min(p.width,p.height)*0.11);

    // nodes
    for(let i=0;i<nodes.length;i++) {{
      const n=nodes[i]; const breathe=4*Math.sin(p.frameCount*BREATH_BASE+n.phase);
      const vx=n.x+breathe*0.8, vy=n.y+breathe*0.8;
      p.noFill(); p.stroke(130,90,60,70); p.strokeWeight(2); p.circle(vx+2,vy+2,54);
      p.fill(255,205,120,170); p.stroke(140,90,60,120); p.strokeWeight(1.8); p.circle(vx,vy,44);
    }}
  }};
}});

function drawBackground(p,palette){{  const c1=p.color(palette[0]), c2=p.color(palette[1]), c3=p.color(palette[2]);  for(let y=0;y<p.height;y++){{ const f=y/(p.height-1); const col=p.lerpColor(c1,c2,f); p.stroke(col); p.line(0,y,p.width,y); }}  p.noStroke(); for(let r=0;r<600;r++){{ const a=p.map(r,0,600,110,0); p.fill(p.red(c3),p.green(c3),p.blue(c3),a*0.3); p.circle(p.width*0.85,p.height*0.15,r); }}}

function drawGlow(p,x,y,radius,col){{  p.noStroke(); for(let r=radius;r>0;r-=6){{ const a=p.map(r,0,radius,220,0); p.fill(p.red(col),p.green(col),p.blue(col),a*0.5); p.circle(x,y,r*2); }} }}

function savePNG(){{  const c=document.querySelector('canvas'); if(!c) return;  const link=document.createElement('a'); link.download='memory_doodle.png'; link.href=c.toDataURL('image/png'); link.click();}}

</script>
</body>
</html>
"""

# Render (no 'key' argument)
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
