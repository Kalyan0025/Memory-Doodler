import re, json, hashlib
import streamlit as st
from streamlit.components.v1 import html as components_html

# Set page config
st.set_page_config(page_title="Visual Memory — ReCollection-inspired", page_icon="🌀", layout="centered")
st.title("🌀 Visual Memory (ReCollection-inspired)")

# -------------------------------
# 1) INPUTS: story only
# -------------------------------
story = st.text_area(
    "Whisper your memory (a few sentences work best)",
    "Yesterday was my birthday. I met childhood friends after years; we laughed, took photos, and shared cake.",
    height=140,
)
go = st.button("Generate")

# -------------------------------
# 2) Minimal text processing → schema
# -------------------------------
t = story.strip()
seed_text = t if t else "empty"
seed = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16) % 10**9

# tiny sentiment-ish palette
tl = t.lower()
if any(k in tl for k in ["birthday","friends","laugh","joy","love","celebrat"]):
    palette = ["#FFD482", "#F79892", "#C0A5D7"]        # warm, celebratory
elif any(k in tl for k in ["calm","quiet","beach","walk","breeze","serene"]):
    palette = ["#B9E3FF", "#DDEBF2", "#BFD6C7"]        # cool, calm
else:
    palette = ["#F7C6B3", "#EBD8C3", "#C0A5D7"]        # nostalgic

# pull 6–10 salient words for fragment overlay
stop = set("""a an the and or of for to from is are was were be being been this that those these i me my we our you your he she they them his her their in on at by with without into out about over under after before again more most such very just not no yes as it's it's""".split())
tokens = re.findall(r"[A-Za-z]{3,}", t)
salient = [w for w in tokens if w.lower() not in stop]
# prefer unique words, keep order, cap to 10
seen, keywords = set(), []
for w in salient:
    wl = w.lower()
    if wl not in seen:
        seen.add(wl)
        keywords.append(w)
    if len(keywords) >= 10:
        break
if not keywords:
    keywords = ["memory","moment","trace","echo","warmth","smile"]

# -------------------------------
# 3) p5.js page (token replacement)
# -------------------------------
SCHEMA = {
    "seed": seed,
    "palette": palette,
    "caption": "Visual Memory",
    "subtitle": "Data-Humanism Inspired",
    "fragments": keywords,
    "story": t,
}

SCHEMA_JS = json.dumps(SCHEMA, ensure_ascii=True, separators=(",", ":"))
schema_hash = hashlib.md5(json.dumps(SCHEMA, sort_keys=True).encode()).hexdigest()

p5_template = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="x-schema-hash" content="__HASH__"/>
<style>
  html,body { margin:0; padding:0; background:#faf7f5; }
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
  <div id="footer"><div id="metaLeft"></div><div id="metaRight"></div></div>
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
document.getElementById('metaLeft').textContent  = (SCHEMA.story||'').slice(0,80);
document.getElementById('metaRight').textContent = 'seed:'+SCHEMA.seed;

function col(p,hex){ return p.color(hex||"#888"); }

new p5((p)=>{
  const W=980, H=980;
  const inner = {x:0, y:68, w:W, h:H-68-64}; // drawable area inside chrome/footer
  const [A,B,C] = SCHEMA.palette.map(h=>col(p,h));
  const seed = SCHEMA.seed||1;
  p.randomSeed(seed); p.noiseSeed(seed);

  function bgEditorial(){
    // soft gradient wash
    for(let y=inner.y; y<inner.y+inner.h; y++){
      const t=(y-inner.y)/(inner.h);
      const cc=p.lerpColor(A,B, t*0.9 + 0.05);
      p.stroke(cc); p.line(inner.x, y, inner.x+inner.w, y);
    }
    // paper grain
    p.push(); p.noStroke(); p.blendMode(p.MULTIPLY);
    for(let i=0;i<9000;i++){
      const x=p.random(inner.x, inner.x+inner.w);
      const y=p.random(inner.y, inner.y+inner.h);
      p.fill(0,0,0, p.random(4,9));
      p.circle(x,y,p.random(0.6,1.2));
    }
    p.pop();
  }

  function monotypePlates(){
    p.push(); p.blendMode(p.MULTIPLY);
    const plates = 4 + (SCHEMA.fragments?.length||6)%3;
    for(let i=0;i<plates;i++){
      const cx = inner.x + inner.w* (0.25 + 0.5*p.random());
      const cy = inner.y + inner.h* (0.25 + 0.5*p.random());
      const baseR = Math.min(inner.w,inner.h) * p.random(0.12,0.26);
      const colr = [A,B,C][i%3];
      const rot = p.random(-0.25,0.25);
      p.push();
      p.translate(cx,cy); p.rotate(rot);
      for(let k=0;k<3;k++){
        p.noStroke();
        p.fill(p.red(colr),p.green(colr),p.blue(colr), 115 - k*28);
        p.beginShape();
        const n = 16;
        for(let a=0;a<n;a++){
          const t=a/n*p.TWO_PI;
          const r = baseR * (0.85 + 0.22*p.noise(i*10 + a*0.7 + p.frameCount*0.0004));
          p.vertex(r*Math.cos(t), r*Math.sin(t));
        }
        p.endShape(p.CLOSE);
      }
      // ink freckles
      for(let d=0; d<140; d++){
        const rx = p.random(-baseR, baseR), ry = p.random(-baseR, baseR);
        if (p.dist(rx,ry,0,0) < baseR*1.02){
          p.noStroke(); p.fill(30,20,10,22);
          p.circle(rx,ry,p.random(1,2.6));
        }
      }
      p.pop();
    }
    p.pop();
  }

  function slitscanBands(){
    p.push();
    const bands = 7;
    for(let b=0;b<bands;b++){
      const y0 = inner.y + inner.h*(0.15 + 0.7*b/bands);
      const thick = 7 + 9 * p.noise(b*0.3 + (p.frameCount*0.002)*(SCHEMA.energy||0.2));
      const cc = p.lerpColor(B,C, b/bands);
      p.stroke(p.red(cc),p.green(cc),p.blue(cc), 70);
      p.strokeWeight(thick);
      p.noFill();
      // gentle bezier wave
      const x1=inner.x+40, x4=inner.x+inner.w-40;
      const x2=p.lerp(x1,x4, 0.33), x3=p.lerp(x1,x4, 0.66);
      const y1=y0 + 16*p.noise(b+0.1), y4=y0 + 16*p.noise(b+0.2);
      const y2=y0 - 26*p.noise(b+1.2), y3=y0 + 26*p.noise(b+2.3);
      p.bezier(x1,y1, x2,y2, x3,y3, x4,y4);
    }
    p.pop();
  }

  function kernel(){
    const cx = inner.x + inner.w*0.52;
    const cy = inner.y + inner.h*0.62;
    const base = Math.min(inner.w,inner.h)*0.12;
    function glow(x,y,r,col){ p.noStroke();
      for(let rad=r; rad>0; rad-=6){
        const a=p.map(rad,0,r,200,0);
        p.fill(p.red(col),p.green(col),p.blue(col), a*0.5);
        p.circle(x,y,rad*2);
      }
    }
    glow(cx,cy, base*1.0, p.color(255,205,120,125));
    p.noStroke(); p.fill(255,205,120,220); p.circle(cx,cy, base*0.9);

    // delicate ticks around—temporal feel without a ruler
    p.noFill(); p.stroke(90,70,60,70); p.strokeWeight(1.2);
    p.circle(cx,cy, base*2.0);
    const ticks = 36;
    for(let i=0;i<ticks;i++){
      const a = -p.HALF_PI + i/ticks*p.TWO_PI;
      const r1=base*0.95, r2=base*1.05;
      p.line(cx+r1*Math.cos(a), cy+r1*Math.sin(a),
             cx+r2*Math.cos(a), cy+r2*Math.sin(a));
    }
  }

  function fragments(){
    const fr = (SCHEMA.fragments||[]).slice(0,10);
    p.textAlign(p.CENTER,p.CENTER);
    p.textSize(14); p.fill(70,55,48,155);
    const cx = inner.x + inner.w*0.52;
    const cy = inner.y + inner.h*0.62;
    for(let i=0;i<fr.length;i++){
      const a = -p.HALF_PI + i/fr.length * p.TWO_PI + 0.25;
      const R = Math.min(inner.w,inner.h) * (0.23 + 0.18*p.noise(i*0.3));
      const wob = 10*Math.sin(p.frameCount*(0.004 + 0.0005*i) * (SCHEMA.energy||0.2) + i);
      const x = cx + (R+wob)*Math.cos(a);
      const y = cy + (R+wob)*Math.sin(a);
      p.text(fr[i], x, y);
    }
  }

  p.setup = function(){
    const c = p.createCanvas(W,H);
    c.parent(document.getElementById('p5mount'));
  };

  p.draw = function(){
    bgEditorial();
    monotypePlates();
    slitscanBands();
    kernel();
    fragments();
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
)

if go:
    components_html(p5_html, height=1060, scrolling=False)
else:
    st.info("Type your memory and click **Generate**. The card adapts to your memory’s emotional tone; visuals will vary accordingly.")
