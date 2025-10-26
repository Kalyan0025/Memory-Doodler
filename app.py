import re, json, hashlib
import streamlit as st
from streamlit.components.v1 import html as components_html

st.set_page_config(page_title="Dream/Memory Doodler — Reunion Map", page_icon="🎂", layout="centered")
st.title("🎂 Memory Doodler — Reunion Map (Data-Humanism)")

# -------------------------------
# 1) INPUTS
# -------------------------------
txt = st.text_area(
    "Tell me about the memory",
    "Yesterday was my birthday. I met a lot of childhood friends and it felt like a reunion—so much laughter, cake, and photos.",
    height=120,
)

with st.expander("Optional details (tune the visual)"):
    col1, col2, col3 = st.columns(3)
    with col1:
        attendees_override = st.number_input("Attendees (approx.)", min_value=0, max_value=48, value=0, step=1, help="0 = auto-detect")
        energy = st.slider("Energy / vibe", 0.0, 1.0, 0.75, help="Controls motion/size accents")
    with col2:
        years_known = st.number_input("Years known (avg.)", min_value=0, max_value=40, value=0, step=1, help="0 = auto-detect")
        years_since_last = st.number_input("Years since last meet", min_value=0, max_value=20, value=0, step=1, help="0 = auto-detect")
    with col3:
        show_legend = st.checkbox("Show legend", value=True)
        show_names = st.checkbox("Use detected labels (if any)", value=True)

go = st.button("Generate")

# -------------------------------
# 2) VERY SMALL NLP (offline)
# -------------------------------
t = txt.lower()

nums = [int(n) for n in re.findall(r"\b(\d{1,2})\b", t)]
attendees = attendees_override or (max(6, min(28, nums[-1])) if nums else (12 if any(k in t for k in ["friends","reunion","party"]) else 8))
attendees = max(3, min(48, attendees))

yk = years_known or (20 if any(k in t for k in ["childhood","school","class"]) else (10 if any(k in t for k in ["college","university"]) else 6))
ylm = years_since_last or (2 if any(k in t for k in ["reunion","after years","long time"]) else 0)

groups = []
if any(x in t for x in ["school","childhood","class"]): groups.append("School")
if "college" in t or "university" in t: groups.append("College")
if "neighbour" in t or "neighbor" in t or "hood" in t: groups.append("Neighborhood")
if not groups: groups = ["Friends"]

moments_vocab = {
    "cake": ["cake","cut","candles"],
    "toast": ["toast","cheers","raise"],
    "photos": ["photo","selfie","picture","camera"],
    "dance": ["dance","dancing","groove"],
    "gift": ["gift","present"],
    "laughter": ["laugh","laughter","funny","joke"],
}
moments = [k for k, kws in moments_vocab.items() if any(w in t for w in kws)]
if not moments: moments = ["laughter"]

labels = []
if show_names:
    for w in re.findall(r"\b[A-Z][a-z]{2,}\b", txt):
        if w.lower() not in {"yesterday","i"}:
            labels.append(w)
labels = list(dict.fromkeys(labels))[:attendees-1]

palette = {
    "joy": ["#FFD482", "#F79892", "#F5B3FF"],
    "nostalgia": ["#F7C6B3", "#EBD8C3", "#C0A5D7"],
}
pal = palette["joy"] if any(k in t for k in ["birthday","party","friends"]) else palette["nostalgia"]

schema = {
    "attendees": attendees,
    "years_known": int(yk),
    "years_since": int(ylm),
    "groups": groups,
    "moments": moments,
    "energy": float(energy),
    "labels": labels,
    "palette": pal,
    "caption": "Birthday with childhood friends — Reunion Map",
}

# -------------------------------
# 3) HTML + p5.js (use token replacement, NOT f-strings)
# -------------------------------
schema_hash = hashlib.md5(json.dumps(schema, sort_keys=True).encode()).hexdigest()
SCHEMA_JS = json.dumps(schema, ensure_ascii=True, separators=(",", ":"))

p5_template = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<meta name='x-schema-hash' content='__HASH__'>
<style>
  html,body { margin:0; padding:0; background:#faf7f5; }
  #wrap { position:relative; width:900px; margin:0 auto; }
  canvas { border-radius:12px; box-shadow:0 10px 30px rgba(0,0,0,0.06); }
  #caption { position:absolute; bottom:10px; right:16px; color:#5b4f46; font:17px Georgia,serif; opacity:.9; }
  #legend {
    position:absolute; left:14px; top:12px; background:#ffffffcc; border:1px solid #e8dccb; border-radius:10px;
    padding:10px 12px; font:12px/1.25 system-ui, -apple-system, Segoe UI, Roboto, sans-serif; color:#574b42;
  }
  .row { display:flex; gap:8px; align-items:center; }
  .sw { width:10px; height:10px; border-radius:50%; display:inline-block; }
  #btnsave {
    position:absolute; top:12px; right:12px; z-index:5; padding:6px 10px; border:1px solid #e6d9c8; border-radius:8px; background:#fff; cursor:pointer;
    font:12px system-ui;
  }
</style>
</head>
<body>
<div id="wrap">
  <button id="btnsave" onclick="savePNG()">Download PNG</button>
  <div id="p5mount"></div>
  <div id="caption"></div>
  <div id="legend" style="display:none"></div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.4/p5.min.js"></script>
<script>
const SCHEMA = __SCHEMA__;
const SHOW_LEGEND = __SHOW_LEGEND__;

function savePNG(){
  const c=document.querySelector('canvas'); if(!c) return;
  const a=document.createElement('a'); a.download='reunion_map.png'; a.href=c.toDataURL('image/png'); a.click();
}

function col(p,hex){ return p.color(hex||"#888"); }
function lerpColorRGBA(p,c1,c2,t){ const cc=p.lerpColor(c1,c2,t); return p.color(p.red(cc),p.green(cc),p.blue(cc), 120); }

new p5((p)=>{
  let W=900,H=900, cx=W/2, cy=H*0.56;
  const [A,B,C] = SCHEMA.palette.map(h=>col(p,h));

  function bgPaper(){
    for(let y=0;y<H;y++){ const t=y/(H-1); const cc=p.lerpColor(A,B,t*0.9); p.stroke(cc); p.line(0,y,W,y); }
    p.noStroke(); for(let r=0;r<600;r++){ const a=p.map(r,0,600,110,0); p.fill(p.red(C),p.green(C),p.blue(C),a*0.35); p.circle(W*0.85,H*0.18,r); }
  }
  function timelineStrip(){
    const y=120, mL=70, mR=W-70;
    p.stroke(90,70,60,80); p.strokeWeight(2); p.line(mL,y,mR,y);
    const nTicks = Math.max(4, Math.min(20, SCHEMA.years_known||6));
    for(let i=0;i<=nTicks;i++){ const x=p.map(i,0,nTicks,mL,mR); p.stroke(90,70,60,70); p.line(x,y-8,x,y+8); }
    if ((SCHEMA.years_since||0)>0){ const frac=Math.min(1,(SCHEMA.years_since)/(SCHEMA.years_known||1)); const xm=p.lerp(mL,mR,1-frac);
      p.stroke(255,120,60,160); p.strokeWeight(2.5); p.line(xm,y-12,xm,y+12);
      p.noStroke(); p.fill(255,120,60,160); p.textAlign(p.CENTER,p.TOP); p.textSize(11); p.text("last met", xm, y+16); }
    p.noStroke(); p.fill(90,70,60,120); p.textAlign(p.LEFT,p.TOP); p.textSize(12); p.text(`Years known: ~${SCHEMA.years_known||'—'}`, mL, y-26);
  }
  function clusterLayout(){
    const G = SCHEMA.groups; const R = Math.min(W,H)*0.28; const centers=[];
    for (let i=0;i<G.length;i++){ const a=-p.HALF_PI + i*(p.TWO_PI/G.length); centers.push([cx + R*Math.cos(a), cy + R*Math.sin(a)]); }
    const N = Math.max(3, Math.min(48, SCHEMA.attendees||8));
    const per = Math.max(1, Math.floor(N/G.length)); const rem = N - per*G.length;
    const counts = centers.map((_,i)=> per + (i<rem?1:0));
    return { centers, counts };
  }
  function drawGlow(p,x,y,rad,col){ p.noStroke(); for (let r=rad; r>0; r-=6){ const a=p.map(r,0,rad,200,0); p.fill(p.red(col),p.green(col),p.blue(col), a*0.5); p.circle(x,y,r*2); } }
  function drawReunion(){
    bgPaper(); timelineStrip();
    const ringR = Math.min(W,H)*0.4; const icons={cake:"🍰", toast:"🥂", photos:"📸", dance:"💃", gift:"🎁", laughter:"😄"};
    const ms = SCHEMA.moments||[]; p.textAlign(p.CENTER,p.CENTER); p.textSize(20);
    for (let i=0;i<ms.length;i++){ const a=i/Math.max(1,ms.length) * p.TWO_PI - p.PI/2 + 0.3; const x=cx + ringR*Math.cos(a), y=cy + ringR*Math.sin(a);
      p.noStroke(); p.fill(80,60,50,150); p.text(icons[ms[i]]||"•", x, y); }
    const obj = clusterLayout(); const centers=obj.centers, counts=obj.counts; const energy=SCHEMA.energy||0.6; const baseR=48 + energy*22;
    drawGlow(p,cx,cy, baseR*0.9, p.color(255,205,120,120)); p.noStroke(); p.fill(255,205,120,210); p.circle(cx,cy, baseR*0.8);
    p.fill(90,70,60,160); p.textAlign(p.CENTER,p.CENTER); p.textSize(13); p.text("You", cx, cy);
    let labels = "__LABELS__".split("|").filter(Boolean); let labelIdx=0;
    for (let g=0; g<centers.length; g++){ const gx=centers[g][0], gy=centers[g][1];
      p.noStroke(); p.fill(90,70,60,130); p.textAlign(p.CENTER,p.BOTTOM); p.textSize(12); p.text((SCHEMA.groups||['Group'])[g], gx, gy-56);
      drawGlow(p,gx,gy, 52, p.color(255,195,80,70));
      const n=counts[g]; const r=72 + 22*(g%2);
      for (let i=0;i<n;i++){ const a=i/Math.max(1,n) * p.TWO_PI - p.HALF_PI + (g*0.3); const jx=gx + r*Math.cos(a); const jy=gy + r*Math.sin(a);
        p.stroke(230,180,90, 90); p.strokeWeight(1.4); p.line(cx,cy, jx,jy);
        if (i%3===0 && n>3){ const k=(i+2)%n; const bx=gx + r*Math.cos(k/Math.max(1,n)*p.TWO_PI - p.HALF_PI + (g*0.3)); const by=gy + r*Math.sin(k/Math.max(1,n)*p.TWO_PI - p.HALF_PI + (g*0.3));
          p.stroke(200,160,95, 70); p.bezier(jx,jy, p.lerp(jx,gx,0.3), p.lerp(jy,gy,0.3), p.lerp(bx,gx,0.3), p.lerp(by,gy,0.3), bx,by); }
        p.noStroke(); const cc = lerpColorRGBA(p, col(p,"#FFE2A1"), col(p,"#F5B3FF"), (g%2)*0.5 + (i/Math.max(1,n))*0.2);
        const breathe=2.5*Math.sin(p.frameCount*(0.012+energy*0.02) + i + g*3); p.circle(jx, jy, 24 + breathe);
        if (__SHOW_NAMES__ && labels.length>0 && labelIdx<labels.length){ p.fill(90,70,60,150); p.textAlign(p.CENTER,p.TOP); p.textSize(10); p.text(labels[labelIdx], jx, jy+14); labelIdx++; }
      }
    }
  }
  function drawLegend(){
    if (!__SHOW_LEGEND__) return;
    const el = document.getElementById('legend'); el.style.display='block';
    const sw = (hex)=>`<span class="sw" style="background:${hex}"></span>`;
    el.innerHTML = `
      <div class="row"><strong>Legend</strong></div>
      <div class="row">${sw(SCHEMA.palette[0])} Background tone (emotion)</div>
      <div class="row">${sw('#FFC973')} Center = You</div>
      <div class="row">${sw('#E0B66D')} Threads = connections</div>
      <div class="row">● Clusters = groups (${SCHEMA.groups.join(', ')})</div>
      <div class="row">🏷 Names (if detected)</div>
      <div class="row">★ Timeline (top): years known & “last met”</div>
      <div class="row">◎ Moments ring: ${SCHEMA.moments.join(', ')}</div>
      <div class="row"><em>Attendees ≈ ${SCHEMA.attendees}, Energy = ${SCHEMA.energy}</em></div>
    `;
  }
  p.setup = function(){ const c = p.createCanvas(W,H); c.parent(document.getElementById('p5mount')); drawLegend(); };
  p.draw = function(){ drawReunion(); document.getElementById('caption').textContent = SCHEMA.caption || ''; };
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
    .replace("__LABELS__", labels_str)
)

if go:
    components_html(p5_html, height=980, scrolling=False)
else:
    st.info("Describe the scene and click **Generate**. This builds a *Reunion Map*: groups, connections, timeline, and highlight moments.")
