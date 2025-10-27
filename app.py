import os, json, re, textwrap
import streamlit as st
import datetime
from dotenv import load_dotenv

# ──────────────────────────────
# 1️⃣ Setup
# ──────────────────────────────
load_dotenv()
st.set_page_config(page_title="Dream/Memory Doodler", page_icon="🌙", layout="centered")
st.title("🌙 Dream / Memory Doodler")

# ──────────────────────────────
# 2️⃣ User Input (Data-Driven)
# ──────────────────────────────
prompt = st.text_area(
    "Describe your memory/dream/incident",
    value="I had my birthday yesterday and met a lot of childhood friends — it was a memorable birthday for me.",
    height=120,
)

date_value = datetime.date(2025, 10, 26)
date = st.date_input("Pick a date", value=date_value)

# ──────────────────────────────
# 3️⃣ Data-Driven Schema Generation
# ──────────────────────────────
def local_schema_from_text(text: str, date: datetime.date, default_schema: dict) -> dict:
    # Extract relevant data from the text (nodes, date, etc.)
    words = text.split()
    nodes = len(words)  # Number of people or entities based on the text (simple example)
    event_type = "birthday" if "birthday" in text.lower() else "reunion"
    
    palette = ["#FFD482", "#F79892", "#C0A5D7"] if event_type == "birthday" else ["#B9E3FF", "#DDEBF2", "#BFD6C7"]
    
    caption = f"Event on {date.strftime('%B %d, %Y')}"
    
    return {
        "date": date,
        "nodes": nodes,
        "event_type": event_type,
        "caption": caption,
        "palette": palette
    }

# Default schema (example)
default_schema = {
    "date": datetime.date(2025, 10, 26),
    "nodes": 6,
    "event_type": "birthday",
    "caption": "Old friends, new laughter",
    "palette": ["#FFD482", "#F79892", "#C0A5D7"]
}
schema = default_schema.copy()

if st.button("Generate"):
    schema = local_schema_from_text(prompt, date, default_schema)

# ──────────────────────────────
# 4️⃣ p5.js Visualization with Data Influence
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
