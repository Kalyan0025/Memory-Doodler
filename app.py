import re, json, hashlib
import streamlit as st
from streamlit.components.v1 import html as components_html

st.set_page_config(page_title="Memory Doodler — Curated Aesthetics", page_icon="🎨", layout="centered")
st.title("🎨 Visual Memory Card — Curated Aesthetics (p5.js)")

# ─────────────────────────────────────────────────────────────
# INPUTS
# ─────────────────────────────────────────────────────────────
txt = st.text_area(
    "Tell me about the memory",
    "Yesterday was my birthday. I met childhood friends, we cut cake, laughed a lot, and took photos.",
    height=120,
)

colA, colB = st.columns([1,1])
with colA:
    style = st.selectbox(
        "Aesthetic",
        [
            "Risograph Collage",
            "Isotype Bloom",
            "Ink Arc Weave",
        ],
        help="Pick the look; we’ll keep motion subtle."
    )
    show_names = st.checkbox("Use detected names (if found)", value=True)
    show_legend = st.checkbox("Show micro-legend", value=False)
with colB:
    attendees_override = st.number_input("Attendees (approx.)", min_value=0, max_value=60, value=0, step=1, help="0 = auto")
    energy = st.slider("Energy (subtle motion)", 0.0, 1.0, 0.45)
    custom_palette = st.text_input("Palette (3 hex, comma-sep, optional)", "")

go = st.button("Generate")

# ─────────────────────────────────────────────────────────────
# LIGHT NLP / SCHEMA
# ─────────────────────────────────────────────────────────────
t = txt.lower()
nums = [int(n) for n in re.findall(r"\b(\d{1,2})\b", t)]
attendees = attendees_override or (max(6, min(40, nums[-1])) if nums else (14 if any(k in t for k in ["friends","reunion","party"]) else 8))
attendees = max(3, min(60, attendees))

# groups
groups = []
if any(x in t for x in ["school","childhood","class"]): groups.append("School")
if "college" in t or "university" in t: groups.append("College")
if any(x in t for x in ["neighbour","neighbor","hood","block"]): groups.append("Neighborhood")
if not groups: groups = ["Friends"]

# moments
moments_vocab = {
    "cake": ["cake","candles","cut"],
    "toast": ["toast","cheers","raise"],
    "photos": ["photo","selfie","picture","camera"],
    "dance": ["dance","dancing","groove"],
    "gift": ["gift","present"],
    "laughter": ["laugh","laughter","funny","joke"],
}
moments = [k for k, kws in moments_vocab.items() if any(w in t for w in kws)]
if not moments: moments = ["laughter"]

# names
labels = []
if show_names:
    for w in re.findall(r"\b[A-Z][a-z]{2,}\b", txt):
        if w.lower() not in {"yesterday","i"}:
            labels.append(w)
labels = list(dict.fromkeys(labels))[:attendees-1]

# palette
if custom_palette.strip():
    parts = [p.strip() for p in custom_palette.split(",") if p.strip()]
    if len(parts) >= 3:
        pal = parts[:3]
    else:
        pal = ["#FFD482","#F79892","#C0A5D7"]
else:
    if any(k in t for k in ["birthday","party","friends","celebrat"]):
        pal = ["#FFD482","#F79892","#C0A5D7"]   # warm riso-esque
    elif any(k in t for k in ["calm","quiet","walk","beach"]):
        pal = ["#B9E3FF","#DDEBF2","#BFD6C7"]   # cool calm
    else:
        pal = ["#F7C6B3","#EBD8C3","#C0A5D7"]   # nostalgic neutral

schema = {
    "style": style,
    "attendees": attendees,
    "groups": groups,
    "moments": moments,
    "labels": labels,
    "energy": float(energy),
    "palette": pal,
    "caption": "Visual Memory Card",
    "subtitle": style,
}

# ─────────────────────────────────────────────────────────────
# p5.js TEMPLATE (token replacement so ${...} in JS is safe)
# ─────────────────────────────────────────────────────────────
schema_hash = hashlib.md5(json.dumps(schema, sort_keys=True).encode()).hexdigest()
SCHEMA_JS = json.dumps(schema, ensure_ascii=True, separators=(",", ":"))

p5_template = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<meta name='x-schema-hash' content='__HASH__'>
<style>
  html,body { margin:0; padding:0; background:#f2efe9; }
  #card {
    width: 900px; height: 900px; margin: 0 auto;
    background: #faf7f5;
    border-radius: 28px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.06), 0 2px 6px rgba(0,0,0,0.03);
    position: relative; overflow: hidden;
  }
  #chrome {
    position:absolute; top:0; left:0; right:0; height: 60px;
    background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(255,255,255,0.6));
    border-top-left-radius: 28px; border-top-right-radius: 28px;
    display:flex; align-items:center; gap:10px; padding:0 16px;
    color:#5b524a; font: 13px/1.2 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  }
  .dot { width:10px; height:10px; border-radius:50%; background:#e6d7c6; }
  #title { font-weight:600; letter-spacing:.2px; }
  #subtitle { opacity:.65; margin-left:6px; }
  #p5mount { position:absolute; top:60px; left:0; right:0; bottom:50px; }
  #footer {
    position:absolute; left:0; right:0; bottom:0; height:50px;
    display:flex; align-items:center; justify-content:flex-end;
    padding:0 16px; color:#6a5e55; font: 12px system-ui;
    background: linear-gradient(0deg, rgba(255,255,255,0.92), rgba(255,255,255,0));
    border-bottom-left-radius: 28px; border-bottom-right-radius: 28px;
  }
  #legend {
    position:absolute; left:14px; top:72px; background:#ffffffdd; border:1px solid #e8dccb; border-radius:10px;
    padding:10px 12px; font:12px/1.25 system-ui, -apple-system, Segoe UI, Roboto, sans-serif; color:#574b42;
    display:none;
  }
  .row { display:flex; gap:8px; align-items:center; }
  .sw { width:10px; height:10px; border-radius:50%; display:inline-block; }
  #btnsave {
    position:absolute; top:14px; right:16px; z-index:5; padding:6px 10px; border:1px solid #e6d9c8; border-radius:8px; background:#fff; cursor:pointer;
    font:12px system-ui; color:#5c5047;
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
  <div id="legend"></div>
  <div id="p5mount"></div>
  <div id="footer"><span id="meta"></span></div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.4/p5.min.js"></script>
<script>
const SCHEMA = __SCHEMA__;
const SHOW_LEGEND = __SHOW_LEGEND__;
const SHOW_NAMES = __SHOW_NAMES__;

function savePNG(){
  const c=document.querySelector('canvas'); if(!c) return;
  const a=document.createElement('a'); a.download='memory_card.png'; a.href=c.toDataURL('image/png'); a.click();
}
function meta(s){ document.getElementById('meta').textContent = s; }
function col(p,hex){ return p.color(hex||"#888"); }
function lerpColorRGBA(p,c1,c2,t){ const cc=p.lerpColor(c1,c2,t); return p.color(p.red(cc),p.green(cc),p.blue(cc), 120); }

document.getElementById('title').textContent = SCHEMA.caption || 'Memory';
document.getElementById('subtitle').textContent = SCHEMA.subtitle || '';
meta(`Attendees ≈ ${SCHEMA.attendees} • Energy ${((SCHEMA.energy||0)*100|0)/100}`);

new p5((p)=>{
  let W=900, H=900, cx=W/2, cy=(H-110)/2 + 60;
  const [A,B,C] = SCHEMA.palette.map(h=>col(p,h));

  function bgPaper(){
    // soft editorial gradient + paper grain
    for(let y=60;y<H-50;y++){
      const t=(y-60)/(H-110); const cc=p.lerpColor(A,B, t*0.9 + 0.05);
      p.stroke(cc); p.line(0,y,W,y);
    }
    p.noFill(); p.push(); p.blendMode(p.MULTIPLY);
    for (let i=0;i<8000;i++){
      const x=Math.random()*W, y=60 + Math.random()*(H-110);
      const g=p.random(15,25);
      p.stroke(0,0,0, p.random(3,8)); p.point(x,y);
    }
    p.pop();
  }

  // ───────────────── Aesthetics
  function risographCollage(){
    bgPaper();
    p.push(); p.blendMode(p.MULTIPLY);

    const blobs = 5 + Math.floor((SCHEMA.attendees||8)/4);
    for (let i=0;i<blobs;i++){
      const baseR = Math.min(W,H)*p.random(0.10,0.22);
      const ox = cx + Math.cos(i*2.1)*p.random(90,180);
      const oy = cy + Math.sin(i*1.7)*p.random(90,180);
      const colr = [A,B,C][i%3];
      for(let k=0;k<3;k++){
        p.noStroke(); p.fill(p.red(colr),p.green(colr),p.blue(colr), 110 - k*25);
        p.beginShape();
        const pts = 14;
        for (let a=0;a<pts;a++){
          const t=a/pts*p.TWO_PI;
          const r = baseR * (0.85 + 0.25*p.noise(i*10 + a*0.7 + p.frameCount*0.0005));
          p.vertex(ox + r*Math.cos(t), oy + r*Math.sin(t));
        }
        p.endShape(p.CLOSE);
      }
      // halftone/dither dots
      for (let d=0; d<120; d++){
        const rx = ox + p.random(-baseR, baseR);
        const ry = oy + p.random(-baseR, baseR);
        const rad = p.random(1,2.6);
        if (p.dist(rx,ry,ox,oy) < baseR*1.05){
          p.noStroke(); p.fill(30,20,10,25);
          p.circle(rx,ry,rad);
        }
      }
    }
    p.pop();

    // focal “You”
    drawYouBadge();
    // sprinkle moments as small stamps
    stampMoments();
  }

  function isotypeBloom(){
    bgPaper();
    const N = Math.max(3, Math.min(60, SCHEMA.attendees||12));
    const rings = Math.ceil(N/12);
    const step = Math.min(W,H)*0.10;

    // stems & dots (countable)
    let idx=0;
    for (let r=1;r<=rings;r++){
      const per = Math.min(12, N-(r-1)*12);
      for (let i=0;i<per;i++){
        const a = -p.HALF_PI + i/per * p.TWO_PI;
        const px = cx + r*step*Math.cos(a);
        const py = cy + r*step*Math.sin(a);
        p.stroke(100,85,75,90); p.strokeWeight(1.6);
        p.line(cx, cy, px, py);
        const cc = [A,B,C][(r+i)%3];
        p.noStroke(); p.fill(p.red(cc),p.green(cc),p.blue(cc), 200);
        p.circle(px, py, 10 + 2*Math.sin((idx++)*0.3 + p.frameCount*0.01*(SCHEMA.energy||0)));
      }
    }

    // tiny group tickers
    p.textAlign(p.CENTER,p.BOTTOM); p.fill(90,70,60,150); p.textSize(12);
    const G=SCHEMA.groups||["Friends"];
    for (let g=0; g<G.length; g++){
      const ang=-p.HALF_PI + g*(p.TWO_PI/G.length);
      const gx=cx + (rings+0.4)*step*Math.cos(ang);
      const gy=cy + (rings+0.4)*step*Math.sin(ang);
      p.text(G[g], gx, gy);
    }

    drawYouBadge();
    stampMoments();
  }

  function inkArcWeave(){
    bgPaper();
    p.push(); p.blendMode(p.MULTIPLY);
    const layers = 18;
    for (let i=0;i<layers;i++){
      const t = i/layers;
      const cc = p.lerpColor(A,C,t);
      p.stroke(p.red(cc),p.green(cc),p.blue(cc), 60);
      p.noFill();
      p.strokeWeight(1.4);
      const R = Math.min(W,H)*(0.18 + 0.28*t);
      const start = -p.PI + t*0.7, end = -0.1 - t*0.3;
      p.arc(cx, cy, R*2, R*2, start, end);

      // bleed-like offsets
      p.stroke(p.red(cc),p.green(cc),p.blue(cc), 28);
      p.arc(cx+2, cy+1, R*2, R*2, start+0.04, end+0.04);
    }
    p.pop();

    // sparse crossing threads (friends)
    const N = Math.max(3, Math.min(60, SCHEMA.attendees||12));
    const R2 = Math.min(W,H)*0.34;
    for (let i=0;i<N;i++){
      const a1 = -p.PI + i/N * p.TWO_PI;
      const a2 = a1 + p.random(-0.8,0.8);
      const x1=cx + R2*Math.cos(a1), y1=cy + R2*Math.sin(a1);
      const x2=cx + R2*Math.cos(a2), y2=cy + R2*Math.sin(a2);
      p.stroke(100,80,70,70); p.strokeWeight(1);
      p.bezier(x1,y1, p.lerp(x1,cx,0.3), p.lerp(y1,cy,0.3),
                     p.lerp(x2,cx,0.3), p.lerp(y2,cy,0.3), x2,y2);
    }

    drawYouBadge();
    stampMoments();
  }

  // ───────────────── helpers
  function drawYouBadge(){
    const baseR = 44 + (SCHEMA.energy||0.5)*18;
    drawGlow(cx,cy, baseR*0.95, p.color(255,205,120,120));
    p.noStroke(); p.fill(255,205,120,220); p.circle(cx,cy, baseR*0.8);
    p.fill(90,70,60,170); p.textAlign(p.CENTER,p.CENTER); p.textSize(13); p.text("You", cx, cy);
  }
  function drawGlow(x,y,rad,col){
    p.noStroke();
    for (let r=rad; r>0; r-=6){
      const a=p.map(r,0,rad,200,0);
      p.fill(p.red(col),p.green(col),p.blue(col), a*0.50);
      p.circle(x,y,r*2);
    }
  }
  function stampMoments(){
    const ringR = Math.min(W,H)*0.44;
    const icons={cake:"🍰", toast:"🥂", photos:"📸", dance:"💃", gift:"🎁", laughter:"😄"};
    const ms = SCHEMA.moments||[];
    p.textAlign(p.CENTER,p.CENTER); p.textSize(18);
    for (let i=0;i<ms.length;i++){
      const a=i/Math.max(1,ms.length) * p.TWO_PI - p.PI/2 + 0.22;
      const x=cx + ringR*Math.cos(a), y=cy + ringR*Math.sin(a);
      p.noStroke(); p.fill(80,60,50,155);
      p.text(icons[ms[i]]||"•", x, y);
    }
  }

  function drawLegend(){
    if (!__SHOW_LEGEND__) return;
    const el = document.getElementById('legend'); el.style.display='block';
    const sw = (hex)=>`<span class="sw" style="background:${hex}"></span>`;
    el.innerHTML = `
      <div class="row"><strong>Legend</strong></div>
      <div class="row">${sw(SCHEMA.palette[0])} Background tone</div>
      <div class="row">${sw('#FFC973')} Center = You</div>
      <div class="row">◎ Moments ring: ${SCHEMA.moments.join(', ')}</div>
      <div class="row">Style: ${SCHEMA.style}</div>
    `;
  }

  // ───────────────── run
  function drawStyle(){
    if (SCHEMA.style === "Risograph Collage")      risographCollage();
    else if (SCHEMA.style === "Isotype Bloom")     isotypeBloom();
    else                                           inkArcWeave();
  }

  p.setup = function(){
    const c = p.createCanvas(W,H); c.parent(document.getElementById('p5mount'));
    drawLegend();
  };
  p.draw = function(){ drawStyle(); };
});
</script>
</body>
</html>
"""

labels_str = "|".join(schema["labels"])
p5_html = (
    p5_template
    .replace("__HASH__", schema_hash)
    .replace("__SCHEMA__", SCHEMA_JS)
    .replace("__SHOW_LEGEND__", "true" if show_legend else "false")
    .replace("__SHOW_NAMES__", "true" if show_names else "false")
    .replace("__CAPTION__", schema["caption"])
    .replace("__SUBTITLE__", schema["subtitle"])
)

if go:
    components_html(p5_html, height=980, scrolling=False)
else:
    st.info("Pick an **Aesthetic** and click **Generate**. You can also paste a custom 3-color palette like `#FFB300,#F6511D,#7FB800`.")
