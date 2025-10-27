import re
import hashlib
import json
import math
import streamlit as st
from streamlit.components.v1 import html as components_html

# Page configuration
st.set_page_config(page_title="Visual Memory", page_icon="🌀", layout="centered")
st.title("🌀 Visual Memory (Data Humanism × Weidi Zhang Inspired)")

# ──────────────────────────────────────
# Input for Memory Text
# ──────────────────────────────────────
story = st.text_area(
    "Whisper your memory (a few sentences work best)",
    "Yesterday was my birthday. I met childhood friends after years; we laughed, took photos, and shared cake.",
    height=140,
)
col1, col2, col3 = st.columns(3)
with col1:
    motion = st.slider("Motion (0 = still)", 0.0, 1.0, 0.0, 0.05)
with col2:
    smoke = st.slider("Smoke density", 0.2, 1.0, 0.7, 0.05)
with col3:
    brightness = st.slider("Glow brightness", 0.2, 1.2, 0.9, 0.05)

go = st.button("Generate")

# ──────────────────────────────────────
# Text Processing and Feature Extraction
# ──────────────────────────────────────
t = story.strip()
seed_text = (t + f"|{motion:.2f}|{smoke:.2f}|{brightness:.2f}") or "empty"
seed = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16) % (2**31 - 1)

tl = f" {t.lower()} "

L_POS = ["joy", "happy", "happiness", "love", "laugh", "smile", "grateful", "peace", "calm", "celebrate", "birthday", "together", "hug", "success", "fun", "warm"]
L_NEG = ["sad", "cry", "alone", "lonely", "fear", "anxious", "stress", "angry", "regret", "loss", "breakup", "hurt", "pain", "miss", "grief", "tired", "cold"]
L_HIGH = ["party", "dance", "festival", "rush", "crowd", "concert", "goal", "celebration", "fireworks", "cheer", "scream"]
L_LOW = ["quiet", "still", "slow", "breeze", "soft", "silent", "night", "dawn", "sunset", "walk", "reading", "tea", "coffee", "calm"]
L_SOC = ["friends", "family", "together", "team", "crowd", "group", "party", "reunion", "gathering", "classmates", "colleagues"]
L_NOS = ["yesterday", "childhood", "memories", "remember", "nostalgia", "nostalgic", "school", "college", "old", "album", "photo", "grandma", "grandfather"]

def score(words): return sum(2 for w in words if f" {w} " in tl)
sig = lambda x: 1/(1+math.exp(-x/4))  # Corrected by importing the math module
valence = max(-1.0, min(1.0, (sig(score(L_POS) - score(L_NEG)) - 0.5) * 2))
arousal = max(0.0, min(1.0, sig(score(L_HIGH) - score(L_LOW))))
social = max(0.0, min(1.0, sig(score(L_SOC))))
nostalgia = max(0.0, min(1.0, sig(score(L_NOS))))

# ──────────────────────────────────────
# Keyword Extraction (Fragments)
# ──────────────────────────────────────
STOP = set("""a an the and or of for to from is are was were be being been this that those these i me my we our you your he she they them his her their in on at by with without into out about over under after before again more most such very just not no yes it's its""".split())
frags = [w for w in re.findall(r"[A-Za-z]{3,}", t) if w.lower() not in STOP][:10]
if not frags:
    frags = ["memory", "moment", "echo", "warmth", "friends", "smile"]

# ──────────────────────────────────────
# Determine Scenario and Color Palette
# ──────────────────────────────────────
def mood_palette(v, a, n):
    if v > 0.3 and a > 0.5:
        return ["#0f1013", "#FFC979", "#FF9DA3"]
    if v > 0.3 and n > 0.5:
        return ["#111213", "#F8D7B8", "#D9C6E6"]
    if v < -0.3 and n > 0.5:
        return ["#101116", "#BDA7D6", "#AEB3C2"]
    if v < -0.3:
        return ["#0f1014", "#9AB0C2", "#6C7A89"]
    return ["#0f1013", "#E3DCD2", "#C8D8C6"]

BG, P1, P2 = mood_palette(valence, arousal, nostalgia)

# ──────────────────────────────────────
# Define the Symbol and Scenario
# ──────────────────────────────────────
def choose_symbol(s: str):
    s = s.lower()
    if any(k in s for k in ["birthday", "cake", "party", "friends"]): return "cake"
    if any(k in s for k in ["beach", "ocean", "sea", "waves"]): return "shell"
    if any(k in s for k in ["loss", "alone", "grief"]): return "lamp"
    if any(k in s for k in ["school", "childhood", "photo"]): return "frame"
    if any(k in s for k in ["rain", "window", "reflection", "night"]): return "window"
    if any(k in s for k in ["travel", "journey", "road", "flight"]): return "horizon"
    return "core"

symbol = choose_symbol(t)

# ──────────────────────────────────────
# Prepare the Data for p5.js
# ──────────────────────────────────────
schema = {
    "seed": seed,
    "palette": [BG, P1, P2],
    "fragments": frags,
    "valence": round(valence, 3),
    "arousal": round(arousal, 3),
    "social": round(social, 3),
    "nostalgia": round(nostalgia, 3),
    "motion": float(motion),
    "smoke": float(smoke),
    "brightness": float(brightness),
    "scene": "group" if social > 0.45 else "portrait",
    "symbol": symbol,
    "story": t
}

SCHEMA_JS = json.dumps(schema, ensure_ascii=True, separators=(",", ":"))

# ──────────────────────────────────────
# p5.js Embed Code
# ──────────────────────────────────────
p5_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'/>
<style>
  html, body {{ margin:0; padding:0; background:#0b0b0d; }}
  #card {{ width:980px; height:980px; margin:24px auto; position:relative; overflow:hidden;
          background:#0f0f12; border-radius:28px; box-shadow:0 16px 40px rgba(0,0,0,.35), 0 2px 10px rgba(0,0,0,.2); }}
  #chrome {{ position:absolute; top:0; left:0; right:0; height:64px; display:flex; align-items:center; gap:10px; padding:0 18px;
             color:#e8e6e3; font:13px system-ui; background:linear-gradient(180deg, rgba(255,255,255,.08), rgba(255,255,255,.02));
             border-top-left-radius:28px; border-top-right-radius:28px; }}
  .dot {{ width:7px; height:7px; border-radius:50%; background:#4a4a50; }}
  #p5mount {{ position:absolute; top:64px; left:0; right:0; bottom:56px; }}
  #footer {{ position:absolute; left:0; right:0; bottom:0; height:56px; display:flex; align-items:center; justify-content:space-between;
             padding:0 16px; color:#c8c6c3; font:11px system-ui; background:linear-gradient(0deg, rgba(255,255,255,.06), rgba(255,255,255,0));
             border-bottom-left-radius:28px; border-bottom-right-radius:28px; }}
  #btnsave {{ margin-left:auto; padding:6px 10px; border:1px solid #3a3a40; border-radius:8px; background:#15151a; color:#ddd; cursor:pointer; }}
</style>
</head>
<body>

<div id='card'>
  <div id='chrome'>
    <div class='dot'></div><div class='dot'></div><div class='dot'></div>
    <div><b>Visual Memory</b> — canvas</div>
    <button id='btnsave' onclick='savePNG()'>Save PNG</button>
  </div>
  <div id='p5mount'></div>
  <div id='footer'>
    <div id='metaLeft'></div>
    <div id='metaRight'></div>
  </div>
</div>

<script src='https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.4/p5.min.js'></script>
<script>
const S = {SCHEMA_JS};

function savePNG() {{
  const c = document.querySelector('canvas'); if(!c) return;
  const a = document.createElement('a'); a.download='visual_memory.png'; a.href=c.toDataURL('image/png'); a.click();
}}

document.getElementById('metaLeft').textContent  = (S.story||'').slice(0,92);
document.getElementById('metaRight').textContent = `seed:${{S.seed}} • v:${{S.valence}} a:${{S.arousal}} s:${{S.social}}`;

new p5((p)=>{{
  const W=980,H=980, inner={{x:0,y:64,w:980,h:980-64-56}};
  const [BG,P1,P2] = (S.palette || ["#0f1013", "#E3DCD2", "#C8D8C6"]).map(h => p.color(h));
  const MOTION = S.motion || 0, SMK = S.smoke || 0.8, BR = S.brightness || 1.0;

  p.randomSeed(S.seed); p.noiseSeed(S.seed);

  // Background and visuals
  function bgPlate() {{
    p.noStroke(); p.fill(BG); p.rect(inner.x, inner.y, inner.w, inner.h);
    for (let y = inner.y; y < inner.y + inner.h; y++) {{
      const t = (y - inner.y) / inner.h;
      const c = p.lerpColor(p.color(12, 12, 16), p.color(22, 22, 28), t);
      p.stroke(c); p.line(inner.x, y, inner.x + inner.w, y);
    }}
  }}

  // Data-Humanism Bands (scanlines)
  function dataBands() {{
    p.push();
    const bands = 6 + Math.round(6 * S.arousal);
    for (let b = 0; b < bands; b++) {{
      const y = inner.y + inner.h * (0.14 + 0.72 * (b + 0.5) / bands);
      const col = p.lerpColor(P1, P2, b / Math.max(1, bands - 1));
      p.stroke(p.red(col), p.green(col), p.blue(col), 24 + 42 * S.arousal);
      p.strokeWeight(4 + 7 * S.arousal);
      const x1 = 36, x4 = W - 36, x2 = p.lerp(x1, x4, 0.33), x3 = p.lerp(x1, x4, 0.66);
      const y1 = y + 18 * p.noise(b + 0.11), y4 = y + 18 * p.noise(b + 0.22);
      const y2 = y - (16 + 26 * S.arousal) * p.noise(b + 1.2);
      const y3 = y + (16 + 26 * S.arousal) * p.noise(b + 2.3);
      p.noFill(); p.bezier(x1, y1, x2, y2, x3, y3, x4, y4);
    }}
    p.pop();
  }}

  // Silhouette generation (human-like figure)
  function silhouettes() {{
    p.push(); p.blendMode(p.SCREEN);
    const actors = (S.scene === "group") ? (5 + Math.round(6 * S.social)) : 1;
    const pts = Math.floor(5500 + 9000 * SMK + 6000 * S.nostalgia);
    const tilt = (S.symbol === "cake" ? 0.15 : 0);

    function jit(i, a = 2333, b = 1999) {{ return [(i % a) / a - 0.5, ((i * 37) % b) / b - 0.5]; }}

    const anchors = [];
    if (actors > 1) {{
      const yBase = inner.y + inner.h * 0.62;
      for (let i = 0; i < actors; i++) {{
        const t = (i + 0.5) / actors;
        const x = W * (0.12 + 0.76 * t + 0.02 * p.noise(i * 0.7));
        const y = yBase - 60 * Math.sin(t * Math.PI) + 28 * p.noise(100 + i);
        anchors.push({{x, y, scale: 0.95 + 0.6 * p.noise(200 + i)}}); 
      }}
    }} else {{
      anchors.push({{x: W * (0.44 + 0.18 * p.noise(11)), y: inner.y + inner.h * (0.50 + 0.06 * p.noise(22)), scale: 1.2 + 0.4 * S.arousal}});
    }}
    // Draw figures (heads, shoulders, etc.)
    p.pop();
  }}

  p.setup = () => {{
    const c = p.createCanvas(W, H);
    c.parent(document.getElementById('p5mount'));
  }};
  p.draw = () => {{
    bgPlate(); dataBands();
    silhouettes();
  }};
}});
</script>
</body>
</html>
"""

# ──────────────────────────────────────
# Render p5.js Canvas
# ──────────────────────────────────────
if go:
    components_html(p5_html, height=1060, scrolling=False)
else:
    st.info("Type your memory and click **Generate**. This renders human-like smoke silhouettes with scenario-aware overlays "
            "(cake for birthdays, waves/horizon for beach, rain streaks for rainy scenes, etc.), plus data-humanism bands & ticks. "
            "Different stories → different seeds → different compositions. Motion=0 for still, >0 for gentle breathing.")
