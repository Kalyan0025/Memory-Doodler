import re, json, hashlib
import streamlit as st
from streamlit.components.v1 import html as components_html

st.set_page_config(page_title="Memory Doodler — Visual Memory Card", page_icon="🧠", layout="centered")
st.title("🧠 Visual Memory Card (Data-Humanism Inspired)")

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
        show_legend = st.checkbox("Show legend", value=False)  # default OFF for a clean card
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
    "joy": ["#FFD482", "#F79892", "#F5B3FF"],        # warm, celebratory
    "nostalgia": ["#F7C6B3", "#EBD8C3", "#C0A5D7"],  # soft archival
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
    "caption": "Birthday with childhood friends",
    "subtitle": "A visual memory card",
}

# -------------------------------
# 3) HTML + p5.js (token replacement so JS templates stay intact)
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
  html,body { margin:0; padding:0; background:#f4efe9; }
  #card {
    width: 900px; height: 900px; margin: 0 auto;
    background: #faf7f5;
    border-radius: 28px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.06), 0 2px 6px rgba(0,0,0,0.03);
    position: relative; overflow: hidden;
  }
  #chrome {
    position:absolute; top:0; left:0; right:0; height: 64px;
    background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(255,255,255,0.65));
    border-top-left-radius: 28px; border-top-right-radius: 28px;
    display:flex; align-items:center; gap:10px; padding:0 16px;
    color:#655a51; font: 13px/1.2 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  }
  .dot { width:10px; height:10px; border-radius:50%; background:#e6d7c6; }
  #title { font-weight:600; letter-spacing:.2px; }
  #subtitle { opacity:.65; margin-left:6px; }
  #p5mount { position:absolute; top:64px; left:0; right:0; bottom:56px; }
  #footer {
    position:absolute; left:0; right:0; bottom:0; height:56px;
    display:flex; align-items:center; justify-content:flex-end;
    padding:0 16px; color:#6a5e55; font: 12px system-ui;
    background: linear-gradient(0deg, rgba(255,255,255,0.9), rgba(255,255,255,0));
    border-bottom-left-radius: 28px; border-bottom-right-radius: 28px;
  }
  #legend {
    position:absolute; left:14px; top:80px; background:#ffffffdd; border:1px solid #e8dccb; border-radius:10px;
    padding:10px 12px; font:12px/1.25 system-ui, -apple-system, Segoe UI, Roboto, sans-serif; color:#574b42;
    display:none;
  }
  .row { display:flex; gap:8px; align-items:center; }
  .sw { width:10px; height:10px; border-radius:50%; display:inline-block; }
  #btnsave {
    position:absolute; top:16px; right:16px; z-index:5; padding:6px 10px; border:1px solid #e6d9c8; border-radius:8px; background:#fff; cursor:pointer;
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
  <div id="footer">Attendees ≈ <span id="attc"></span> • Energy <span id="eng"></span></div>
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

function col(p,hex){ return p.color(hex||"#888"); }
function lerpColorRGBA(p,c1,c2,t){ const cc=p.lerpColor(c1,c2,t); return p.color(p.red(cc),p.green(cc),p.blue(cc), 120); }

document.getElementById('attc').textContent = SCHEMA.attendees;
document.getElementById('eng').textContent  = (SCHEMA.energy||0).toFixed(2);

new p5((p)=>{
  let W=900, H=900, cx=W/2, cy=(H-120)/2 + 64; // inside card chrome/footer
  const [A,B,C] = SCHEMA.palette.map(h=>col(p,h));

  function bgPaper(){
    for(let y=64;y<H-56;y++){
      const t=(y-64)/(H-120); const cc=p.lerpColor(A,B,t*0.9 + 0.05);
      p.stroke(cc); p.line(0,y,W,y);
    }
    p.noStroke();
    for(let r=0;r<600;r++){
      const a=p.map(r,0,600,110,0);
      p.fill(p.red(C),p.green(C),p.blue(C),a*0.35);
      p.circle(W*0.84, H*0.30, r);
    }
  }

  function relationRing(){
    // Tiny ticks = years known; colored tick = last met (angularized)
    const yrs = Math.max(1, SCHEMA.years_known||6);
    const last = Math.max(0, SCHEMA.years_since||0);
    const R = Math.min(W,H)*0.12;
    p.noFill(); p.stroke(90,70,60,60); p.strokeWeight(1.5); p.circle(cx,cy,R*2);
    for (let i=0;i<yrs;i++){
      const a = -p.HALF_PI + i/yrs * p.TWO_PI;
      const x1=cx+(R-6)*Math.cos(a), y1=cy+(R-6)*Math.sin(a);
      const x2=cx+(R+6)*Math.cos(a), y2=cy+(R+6)*Math.sin(a);
      p.stroke(90,70,60,70); p.line(x1,y1,x2,y2);
    }
    if (last>0){
      const frac=Math.min(1, last/yrs);
      const a = -p.HALF_PI + (1-frac)*p.TWO_PI;
      const x1=cx+(R-10)*Math.cos(a), y1=cy+(R-10)*Math.sin(a);
      const x2=cx+(R+10)*Math.cos(a), y2=cy+(R+10)*Math.sin(a);
      p.stroke(255,120,60,170); p.strokeWeight(2.2); p.line(x1,y1,x2,y2);
    }
  }

  function clusterLayout(){
    const G = SCHEMA.groups; const R = Math.min(W,H)*0.30; const centers=[];
    for (let i=0;i<G.length;i++){
      const a = -p.HALF_PI + i*(p.TWO_PI/G.length);
      centers.push([cx + R*Math.cos(a), cy + R*Math.sin(a)]);
    }
    const N = Math.max(3, Math.min(48, SCHEMA.attendees||8));
    const per = Math.max(1, Math.floor(N/G.length)); const rem = N - per*G.length;
    const counts = centers.map((_,i)=> per + (i<rem?1:0));
    return { centers, counts };
  }

  function drawGlow(x,y,rad,col){
    p.noStroke();
    for (let r=rad; r>0; r-=6){
      const a=p.map(r,0,rad,200,0);
      p.fill(p.red(col),p.green(col),p.blue(col), a*0.5);
      p.circle(x,y,r*2);
    }
  }

  function drawCard(){
    bgPaper();

    // moments ring (glyphs) — compact, not “table-like”
    const ringR = Math.min(W,H)*0.42;
    const icons={cake:"🍰", toast:"🥂", photos:"📸", dance:"💃", gift:"🎁", laughter:"😄"};
    const ms = SCHEMA.moments||[];
    p.textAlign(p.CENTER,p.CENTER); p.textSize(18);
    for (let i=0;i<ms.length;i++){
      const a=i/Math.max(1,ms.length) * p.TWO_PI - p.PI/2 + 0.28;
      const x=cx + ringR*Math.cos(a), y=cy + ringR*Math.sin(a);
      p.noStroke(); p.fill(80,60,50,155);
      p.text(icons[ms[i]]||"•", x, y);
    }

    // center "you" + relation ring
    const energy = SCHEMA.energy||0.6;
    const baseR = 44 + energy*22;
    drawGlow(cx,cy, baseR*0.9, p.color(255,205,120,120));
    p.noStroke(); p.fill(255,205,120,210); p.circle(cx,cy, baseR*0.8);
    relationRing();
    p.fill(90,70,60,160); p.textAlign(p.CENTER,p.CENTER); p.textSize(13); p.text("You", cx, cy);

    // groups & nodes (minimal lines, editorial style)
    const obj = clusterLayout(); const centers=obj.centers, counts=obj.counts;
    let labels = "__LABELS__".split("|").filter(Boolean); let labelIdx=0;

    for (let g=0; g<centers.length; g++){
      const gx=centers[g][0], gy=centers[g][1];
      p.noStroke(); p.fill(90,70,60,130); p.textAlign(p.CENTER,p.BOTTOM); p.textSize(12);
      p.text((SCHEMA.groups||['Group'])[g], gx, gy-52);

      drawGlow(gx,gy, 46, p.color(255,195,80,60));

      const n=counts[g]; const r=68 + 18*(g%2);
      for (let i=0;i<n;i++){
        const a=i/Math.max(1,n) * p.TWO_PI - p.HALF_PI + (g*0.28);
        const jx=gx + r*Math.cos(a); const jy=gy + r*Math.sin(a);

        // light connective stroke
        p.stroke(190,150,90, 70); p.strokeWeight(1.2);
        p.line(cx,cy, jx,jy);

        // occasional intra-cluster arcs
        if (i%4===0 && n>4){
          const k=(i+2)%n;
          const bx=gx + r*Math.cos(k/Math.max(1,n)*p.TWO_PI - p.HALF_PI + (g*0.28));
          const by=gy + r*Math.sin(k/Math.max(1,n)*p.TWO_PI - p.HALF_PI + (g*0.28));
          p.stroke(170,135,88, 60);
          p.bezier(jx,jy, p.lerp(jx,gx,0.32), p.lerp(jy,gy,0.32),
                          p.lerp(bx,gx,0.32), p.lerp(by,gy,0.32), bx,by);
        }

        // node (friend)
        p.noStroke();
        const cc = lerpColorRGBA(p, col(p,"#FFE2A1"), col(p,"#F5B3FF"), (g%2)*0.45 + (i/Math.max(1,n))*0.18);
        const breathe=2*Math.sin(p.frameCount*(0.010+energy*0.018) + i + g*3);
        p.circle(jx, jy, 22 + breathe);

        if (SHOW_NAMES && labels.length>0 && labelIdx<labels.length){
          p.fill(90,70,60,150); p.textAlign(p.CENTER,p.TOP); p.textSize(10);
          p.text(labels[labelIdx], jx, jy+13); labelIdx++;
        }
      }
    }
  }

  function drawLegend(){
    if (!SHOW_LEGEND) return;
    const el = document.getElementById('legend'); el.style.display='block';
    const sw = (hex)=>`<span class="sw" style="background:${hex}"></span>`;
    el.innerHTML = `
      <div class="row"><strong>Legend</strong></div>
      <div class="row">${sw(SCHEMA.palette[0])} Background tone (emotion)</div>
      <div class="row">${sw('#FFC973')} Center = You & relation ring</div>
      <div class="row">${sw('#E0B66D')} Threads = connections</div>
      <div class="row">● Clusters = groups (${SCHEMA.groups.join(', ')})</div>
      <div class="row">◎ Moments ring: ${SCHEMA.moments.join(', ')}</div>
    `;
  }

  p.setup = function(){
    const c = p.createCanvas(W,H); c.parent(document.getElementById('p5mount'));
    drawLegend();
    document.getElementById('title').textContent = SCHEMA.caption || 'Memory';
    document.getElementById('subtitle').textContent = SCHEMA.subtitle || '';
  };
  p.draw = function(){ drawCard(); };
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
    .replace("__CAPTION__", schema["caption"])
    .replace("__SUBTITLE__", schema["subtitle"])
)

if go:
    components_html(p5_html, height=980, scrolling=False)
else:
    st.info("Describe the scene and click **Generate**. This version renders a clean, data-humanism-style **visual memory card** (no top timeline).")
