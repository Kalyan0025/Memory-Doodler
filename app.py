import os, json, re, textwrap
import streamlit as st
from dotenv import load_dotenv
import datetime

# ──────────────────────────────
# 1️⃣ Setup
# ──────────────────────────────
load_dotenv()
st.set_page_config(page_title="Dream/Memory Doodler", page_icon="🌙", layout="centered")
st.title("🌙 Dream / Memory Doodler")

# ──────────────────────────────
# 2️⃣ Gemini setup (safe + fallback)
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
                if "flash" in m.name and "exp" not in m.name:  # only light models
                    available_models.append(m.name)
        pref = [PREF_MODEL, f"models/{PREF_MODEL}"]
        fallbacks = [
            "gemini-1.5-flash-latest", "models/gemini-1.5-flash-latest",
            "gemini-1.5-flash-002", "models/gemini-1.5-flash-002"
        ]
        for c in pref + fallbacks:
            if c in available_models:
                chosen_model = c; break
        if not chosen_model and available_models:
            chosen_model = available_models[0]
    except Exception as e:
        st.warning(f"Model listing failed; fallback. ({e})")
        chosen_model = None
else:
    chosen_model = None

# ──────────────────────────────
# 3️⃣ Local heuristic schema generator (offline fallback)
# ──────────────────────────────
def local_schema_from_text(text: str, default_schema: dict) -> dict:
    t = text.lower()
    EMO = {
        "joy": ["happy","fun","birthday","party","smile","laugh"],
        "nostalgia": ["childhood","old","school","remember","reunion"],
        "calm": ["calm","peace","quiet","relax"],
        "love": ["love","together","family","friends"],
        "sad": ["sad","alone","miss","cry","loss"],
        "anxiety": ["stress","worried","fear","nervous"],
    }
    counts = {e: sum(t.count(k) for k in kws) for e,kws in EMO.items()}
    emotion = max(counts, key=counts.get) if any(counts.values()) else "nostalgia"

    exclaim = t.count("!")
    caps = sum(1 for w in re.findall(r"[A-Z]{2,}", text) if len(w)>2)
    intensity = min(1.0, 0.4 + 0.1*exclaim + 0.05*caps)

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
    for w in ["friends","family","group","team","all"]:
        if w in t: nodes += 2
    nodes = max(3, min(20, nodes))

    caption = "A day to remember"
    if "birthday" in t and "friend" in t:
        caption = "Old friends, new laughter"
    elif "birthday" in t:
        caption = "A day that glowed"
    elif "reunion" in t or "childhood" in t:
        caption = "Back to where we began"

    EMO_LABEL = {
        "joy":"joy","nostalgia":"warm nostalgia","calm":"calm",
        "love":"tenderness","sad":"soft sorrow","anxiety":"uneasy"
    }
    return {
        "emotion": EMO_LABEL.get(emotion, "nostalgia"),
        "intensity": round(intensity,2),
        "palette": palette,
        "nodes": int(nodes),
        "caption": caption
    }

# ──────────────────────────────
# 4️⃣ UI input
# ──────────────────────────────
prompt = st.text_area(
    "Describe your memory/dream/incident",
    value="I had my birthday yesterday and met a lot of childhood friends — it was a memorable birthday for me.",
    height=120,
)

date_value = datetime.date(2025, 10, 26)

date = st.date_input(
    "Pick a date",
    value=date_value
)

colA, colB = st.columns(2)
with colA:
    do_generate = st.button("Generate")
with colB:
    st.caption("Write any memory — happy, calm, or nostalgic.")

# ──────────────────────────────
# 5️⃣ Default schema
# ──────────────────────────────
default_schema = {
    "emotion": "warm nostalgia",
    "intensity": 0.8,
    "palette": ["#F79892", "#FFD482", "#C0A5D7"],
    "nodes": 10,
    "caption": "October 25 — Old friends, new laughter"
}
schema = default_schema.copy()

# ──────────────────────────────
# 6️⃣ Gemini JSON call with safe fallback
# ──────────────────────────────
def run_llm(text: str):
    if not (GEMINI_API_KEY and chosen_model):
        return None
    sys_prompt = (open("identity.txt").read().strip()
                  if os.path.exists("identity.txt")
                  else "Return only valid JSON with keys: emotion, intensity, palette, nodes, caption.")
    user_prompt = f"User memory:\n{text}\n\nReturn only the JSON. No prose."
    try:
        model = genai.GenerativeModel(chosen_model)
        resp = model.generate_content([sys_prompt, user_prompt])
        raw = (resp.text or "").strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            i, j = raw.find("{"), raw.rfind("}")
            raw = raw[i:j+1]
        parsed = json.loads(raw)
        return {
            "emotion": str(parsed.get("emotion","nostalgia"))[:40],
            "intensity": max(0.0, min(1.0, float(parsed.get("intensity",0.8)))),
            "palette": parsed.get("palette", default_schema["palette"])[:3],
            "nodes": max(3, min(20, int(parsed.get("nodes",10)))),
            "caption": str(parsed.get("caption","Memory Doodle"))[:64],
        }
    except Exception as e:
        st.info("💡 Using local generator (Gemini quota reached or offline).")
        return None

if do_generate:
    llm_schema = run_llm(prompt)
    schema = llm_schema if llm_schema else local_schema_from_text(prompt, default_schema)

# ──────────────────────────────
# 7️⃣ p5.js visualization
# ──────────────────────────────
from streamlit.components.v1 import html as st_html

p5_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  html, body {{ margin:0; padding:0; background:#faf7f5; }}
  #wrap {{ position:relative; width:900px; margin:0 auto; }}
  #btnsave {{
    position:absolute; top:12px; right:12px; z-index:10;
    padding:8px 12px; border:1px solid #d9cbb9; border-radius:8px; background:#fff;
    font-family:system-ui, -apple-system, Segoe UI, Roboto, sans-serif; cursor:pointer;
  }}
  #caption {{
    position:absolute; bottom:10px; right:16px; color:rgba(70,60,65,0.85); font-size:18px;
    font-family:Georgia, serif; pointer-events:none;
    text-shadow:0 1px 0 rgba(255,255,255,0.4);
  }}
  canvas {{ border-radius:12px; box-shadow:0 10px 30px rgba(0,0,0,0.06); }}
</style>
</head>
<body>
<div id="wrap">
  <button id="btnsave" onclick="savePNG()">Download PNG</button>
  <div id="p5mount"></div>
  <div id="caption"></div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.4/p5.min.js"></script>
<script>
const SCHEMA = {json.dumps(schema)};

function savePNG() {{
  const c = document.querySelector('canvas');
  if (!c) return;
  const link = document.createElement('a');
  link.download = 'memory_doodle.png';
  link.href = c.toDataURL('image/png');
  link.click();
}}

let centerPos, orbitR, nodes = [];
new p5((p) => {{
  p.setup = function() {{
    const c = p.createCanvas(900, 900);
    c.parent(document.getElementById('p5mount'));
    centerPos = p.createVector(p.width/2, p.height/2);
    orbitR = Math.min(p.width, p.height) * 0.28;
    const N = Math.max(3, Math.min(20, SCHEMA.nodes || 10));
    for (let i=0;i<N;i++) {{
      const a = p.TWO_PI * i / N - p.PI/2;
      nodes.push({{ a, phase: Math.random()*Math.PI*2 }});
    }}
    document.getElementById('caption').textContent = SCHEMA.caption || '';
  }};

  p.draw = function() {{
    drawBackgroundGradient(p, SCHEMA.palette || ["#F79892","#FFD482","#C0A5D7"]);
    p.noFill();

    p.push();
    p.translate(centerPos.x, centerPos.y);
    const t = p.frameCount * 0.01;
    for (let i=0; i<6; i++) {{
      const r = p.map((t + i*0.35)%1, 0,1, orbitR*0.9, orbitR*1.6);
      p.stroke(255,215,130, p.map(r, orbitR*0.9, orbitR*1.6, 90, 0));
      p.strokeWeight(1.25);
      p.circle(0,0, r*2);
    }}
    p.pop();

    p.stroke(230,180,90,120);
    p.strokeWeight(1.3);
    for (let i=0;i<nodes.length;i++) {{
      const ax = centerPos.x + orbitR * Math.cos(nodes[i].a);
      const ay = centerPos.y + orbitR * Math.sin(nodes[i].a);
      p.line(centerPos.x, centerPos.y, ax, ay);
    }}

    drawGlow(p, centerPos.x, centerPos.y, Math.min(p.width,p.height)*0.16, p.color(255,195,80,130));
    p.fill(255,190,70,200); p.noStroke();
    p.circle(centerPos.x, centerPos.y, Math.min(p.width,p.height)*0.11);

    const baseBreathe = 0.02 + (SCHEMA.intensity ? SCHEMA.intensity*0.02 : 0.016);
    for (let i=0;i<nodes.length;i++) {{
      const a = nodes[i].a;
      const bx = centerPos.x + orbitR * Math.cos(a);
      const by = centerPos.y + orbitR * Math.sin(a);
      const breathe = 4 * Math.sin(p.frameCount*baseBreathe + nodes[i].phase);
      const x = bx + breathe * Math.cos(a) * 2;
      const y = by + breathe * Math.sin(a) * 2;
      p.noFill();
      p.stroke(130,90,60,70);
      p.strokeWeight(2);
      p.circle(x+2, y+2, 56);
      p.fill(255,205,120,170);
      p.stroke(140,90,60,120);
      p.strokeWeight(1.8);
      p.circle(x, y, 46);
    }}
  }};
}});

function drawBackgroundGradient(p, palette) {{
  const c1 = p.color(palette[0] || "#F79892");
  const c2 = p.color(palette[1] || "#FFD482");
  const c3 = p.color(palette[2] || "#C0A5D7");
  for (let y=0; y<p.height; y++) {{
    const f = y / p.height;
    const c = p.lerpColor(c1, c2, f);
    p.stroke(c); p.line(0,y,p.width,y);
  }}
  p.noStroke();
  for (let r=0; r<600; r++) {{
    const a = p.map(r,0,600,110,0);
    p.fill(p.red(c3), p.green(c3), p.blue(c3), a*0.3);
    p.circle(p.width*0.85, p.height*0.15, r);
  }}
}}

function drawGlow(p,x,y,radius,col) {{
  p.noStroke();
  for (let r=radius; r>0; r-=6) {{
    const a = p.map(r,0,radius,220,0);
    p.fill(p.red(col), p.green(col), p.blue(col), a*0.5);
    p.circle(x,y,r*2);
  }}
}}
</script>
</body>
</html>
"""
st.components.v1.html(p5_html, height=980, scrolling=False)
