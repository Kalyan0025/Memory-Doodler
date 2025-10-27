import re
import json
import hashlib
import math
import streamlit as st
from streamlit.components.v1 import html as components_html
from datetime import datetime

# ──────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────
st.set_page_config(page_title="Memory Doodler — Visual Memory Card", page_icon="🧠", layout="centered")
st.title("🧠 Visual Memory Card (Data-Humanism Inspired)")

# ──────────────────────────────────────
# 1) INPUT: Memory Story and Date
# ──────────────────────────────────────
story = st.text_area(
    "Whisper your memory (a few sentences work best)",
    "Yesterday was my birthday. I met childhood friends after years; we laughed, took photos, and shared cake.",
    height=140,
)
date_input = st.date_input("Enter the date of your memory", datetime.today())
go = st.button("Generate")

# ──────────────────────────────────────
# 2) Minimal text processing → schema
# ──────────────────────────────────────
t = story.strip()
seed_text = t if t else "empty"
seed = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16) % 10**9

# Color palette logic based on the story's sentiment
tl = t.lower()
if any(k in tl for k in ["birthday", "friends", "laugh", "joy", "love", "celebrat"]):
    palette = ["#FFD482", "#F79892", "#C0A5D7"]  # warm, celebratory
elif any(k in tl for k in ["calm", "quiet", "beach", "walk", "breeze", "serene"]):
    palette = ["#B9E3FF", "#DDEBF2", "#BFD6C7"]  # cool, calm
else:
    palette = ["#F7C6B3", "#EBD8C3", "#C0A5D7"]  # nostalgic

# Pull 6–10 salient words for fragment overlay
stop = set("""a an the and or of for to from is are was were be being been this that those these i me my we our you your he she they them his her their in on at by with without into out about over under after before again more most such very just not no yes as it's it's""".split())
tokens = re.findall(r"[A-Za-z]{3,}", t)
salient = [w for w in tokens if w.lower() not in stop]
# Prefer unique words, keep order, cap to 10
seen, keywords = set(), []
for w in salient:
    wl = w.lower()
    if wl not in seen:
        seen.add(wl)
        keywords.append(w)
    if len(keywords) >= 10:
        break
if not keywords:
    keywords = ["memory", "moment", "trace", "echo", "warmth", "smile"]

# ──────────────────────────────────────
# 3) Schema with emotion data and visual attributes
# ──────────────────────────────────────
schema = {
    "seed": seed,
    "palette": palette,
    "caption": "Visual Memory",
    "subtitle": "ReCollection-inspired Memory",
    "fragments": keywords,
    "story": t,
    "date": date_input.strftime("%Y-%m-%d"),  # Date formatted for display
    "summary_words": ", ".join(keywords[:5]),  # First few summary words from memory
}

# ──────────────────────────────────────
# 4) p5.js page (token replacement for JS)
# ──────────────────────────────────────
SCHEMA_JS = json.dumps(schema, ensure_ascii=True, separators=(",", ":"))
schema_hash = hashlib.md5(json.dumps(schema, sort_keys=True).encode()).hexdigest()

p5_template = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="x-schema-hash" content="__HASH__"/>
<style>
  html,body { margin:0; padding:0; background:#0f1115; }
  #card {
    width: 980px; height: 980px; margin: 24px auto;
    background: #faf7f5;
    border-radius: 28px;
    box-shadow: 0 16px 40px rgba(0,0,0,0.20), 0 2px 10px rgba(0,0,0,0.08);
    position: relative; overflow: hidden;
  }
  #chrome {
    position:absolute; top:0; left:0; right:0; height: 68px;
    background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(255,255,255,0.60));
    border-top-left-radius: 28px; border-top-right-radius: 28px;
    display:flex; align-items:center; gap:10px; padding:0 18px;
    color:#5b524a; font: 14px/1.2 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  }
  .dot { width:10px; height:10px; border-radius:50%; background:#e6d7c6; }
  #title { font-weight:600; letter-spacing:.2px; }
  #subtitle { opacity:.65; margin-left:6px; }
  #p5mount { position:absolute; top:68px; left:0; right:0; bottom:64px; }
  #footer {
    position:absolute; left:0; right:0; bottom:0; height:64px;
    display:flex; align-items:center; justify-content:space-between;
    padding:0 16px; color:#6a5e55; font: 12px system-ui;
    background: linear-gradient(0deg, rgba(255,255,255,0.94), rgba(255,255,255,0));
    border-bottom-left-radius: 28px; border-bottom-right-radius: 28px;
  }
  #btnsave {
    padding:6px 10px; border:1px solid #e6d9c8; border-radius:8px; background:#fff; cursor:pointer;
    font:12px system-ui; color:#5c5047;
  }
  #date, #summary {
    position: absolute;
    bottom: 20px;
    right: 20px;
    color: #5b524a;
    font: 14px system-ui;
  }
</style>
</head>
<body>
<div id="card">
  <div id="chrome">
    <div class="dot"></div><div class="dot"></div><div class="dot"></div>
    <div id="title">__CAPTION__</div><div id="subtitle">— __SUBTITLE__</div>
    <button id="btnsave" onclick="savePNG()">Save PNG</button>
  </div>
  <div id="p5mount"></div>
  <div id="footer">
    <div id="date">Memory Date: __DATE__</div>
    <div id="summary">Summary: __SUMMARY__</div>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.4/p5.min.js"></script>
<script>
const SCHEMA = __SCHEMA__;

function savePNG(){
  const c=document.querySelector('canvas'); if(!c) return;
  const a=document.createElement('a'); a.download='visual_memory.png'; a.href=c.toDataURL('image/png'); a.click();
}

document.getElementById('title').textContent = SCHEMA.caption || 'Memory';
document.getElementById('subtitle').textContent = SCHEMA.subtitle || '';
document.getElementById('date').textContent = `Memory Date: ${SCHEMA.date}`;
document.getElementById('summary').textContent = `Summary: ${SCHEMA.summary_words}`;

function col(p,hex){ return p.color(hex||"#888"); }

new p5((p)=>{
  const W=980, H=980;
  const inner = {x:0, y:68, w:W, h:H-68-64}; // drawable area inside chrome/footer
  const [A,B,C] = SCHEMA.palette.map(h=>col(p,h));
  const seed = SCHEMA.seed||1;
  p.randomSeed(seed); p.noiseSeed(seed);

  function bgEditorial(){
    for(let y=inner.y; y<inner.y+inner.h; y++){
      const t=(y-inner.y)/(inner.h);
      const cc=p.lerpColor(A,B, t*0.9 + 0.05);
      p.stroke(cc); p.line(inner.x, y, inner.x+inner.w, y);
    }
    p.push(); p.noStroke(); p.blendMode(p.MULTIPLY);
    for(let i=0;i<9000;i++){
      const x=p.random(inner.x, inner.x+inner.w);
      const y=p.random(inner.y, inner.y+inner.h);
      p.fill(0,0,0, p.random(4,9));
      p.circle(x,y,p.random(0.6,1.2));
    }
    p.pop();
  }

  function drawReunion(){
    bgEditorial();
    p.fill(255, 205, 120, 120);
    p.circle(W / 2, H / 2, 200);
  }

  p.setup = function(){
    const c = p.createCanvas(W,H);
    c.parent(document.getElementById('p5mount'));
  };

  p.draw = function(){
    drawReunion();
  };
});
</script>
</body>
</html>
"""

p5_html = (
    p5_template
    .replace("__HASH__", schema_hash)
    .replace("__SCHEMA__", SCHEMA_JS)
    .replace("__CAPTION__", "Visual Memory")
    .replace("__SUBTITLE__", "ReCollection-inspired")
    .replace("__DATE__", schema["date"])
    .replace("__SUMMARY__", schema["summary_words"])
)

if go:
    components_html(p5_html, height=1060, scrolling=False)
else:
    st.info("Type your memory and click **Generate**. The card adapts to valence, arousal, socialness, and nostalgia; visuals are deterministic per story.")
