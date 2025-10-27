# app.py
import re, json, hashlib, math
import streamlit as st
from streamlit.components.v1 import html as components_html

st.set_page_config(page_title="Visual Memory — ReCollection-inspired", page_icon="🌀", layout="centered")
st.title("🌀 Visual Memory (ReCollection-inspired)")

# ──────────────────────────────────────
# 1) INPUT: story only
# ──────────────────────────────────────
story = st.text_area(
    "Whisper your memory (a few sentences work best)",
    "Yesterday was my birthday. I met childhood friends after years; we laughed, took photos, and shared cake.",
    height=140,
)
go = st.button("Generate")

# ──────────────────────────────────────
# 2) Text → schema with expressive axes
# ──────────────────────────────────────
t = story.strip()
seed_text = t if t else "empty"
seed = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16) % 10**9
tl = t.lower()

# Simple lexicons (no external deps)
L_POS = ["joy","happy","happiness","love","laugh","laughs","laughed","smile","smiled","proud","grateful","peace","serene","calm","relief","beautiful","celebrate","birthday","friends","together","hug","kiss","wedding","success","win"]
L_NEG = ["sad","cry","cried","alone","lonely","fear","anxious","anxiety","stress","angry","regret","loss","lost","breakup","hurt","pain","miss","funeral","argument","fight","tired"]
L_HIGH = ["ecstatic","thrill","rush","party","dance","sprint","screamed","wild","storm","fireworks","concert","crowd","festival","goal","race","rollercoaster","adrenaline"]
L_LOW  = ["quiet","still","slow","breeze","gentle","soft","silent","night","dawn","sunset","walk","beach","library","rain","reading","meditate","tea","coffee"]
L_SOC  = ["friends","family","together","team","we","us","crowd","group","party","colleagues","classmates","reunion","gathering"]
L_NOST = ["yesterday","childhood","years ago","old","remember","memory","memories","reminisce","nostalgia","nostalgic","school","college","grandma","grandfather","album","photo","photos","vintage"]

def score(words):
    # cheap token presence; weights duplicate hits mildly
    return sum(2 if f" {w} " in f" {tl} " else 0 for w in words)

val_raw = score(L_POS) - score(L_NEG)      # >0 = positive
aro_raw = score(L_HIGH) - score(L_LOW)     # >0 = energetic
soc_raw = score(L_SOC)
nos_raw = score(L_NOST)

def sig(x): return 1/(1+math.exp(-x/4))
valence   = max(-1.0, min(1.0, (sig(val_raw)-0.5)*2))
arousal   = max(0.0, min(1.0, sig(aro_raw)))
social    = max(0.0, min(1.0, sig(soc_raw)))
nostalgia = max(0.0, min(1.0, sig(nos_raw)))

# Palettes keyed by valence/arousal/nostalgia
if valence > 0.25 and arousal >= 0.5:
    palette = ["#FFD482", "#F79892", "#C0A5D7"]                 # joyful-vibrant
elif valence > 0.25 and arousal < 0.5:
    palette = ["#FBE8C7", "#CFE8FF", "#C7D3E1"]                 # gentle-warm
elif valence < -0.25 and nostalgia > 0.5:
    palette = ["#E7D7C9", "#CDB4DB", "#A3A3B3"]                 # bittersweet
elif valence < -0.25:
    palette = ["#B0B7C3", "#8EA6B4", "#6B7685"]                 # cool-muted
elif nostalgia > 0.5:
    palette = ["#F7C6B3", "#EBD8C3", "#C0A5D7"]                 # nostalgic
else:
    palette = ["#D8E3E7", "#F0E6EF", "#C7D9C4"]                 # neutral-soft

# Keywords/fragments
stop = set("""a an the and or of for to from is are was were be being been this that those these i me my we our you your he she they them his her their in on at by with without into out about over under after before again more most such very just not no yes as it's it's""".split())
tokens = re.findall(r"[A-Za-z]{3,}", t)
salient = [w for w in tokens if w.lower() not in stop]
seen, keywords = set(), []
for w in salient:
    wl = w.lower()
    if wl not in seen:
        seen.add(wl); keywords.append(w)
    if len(keywords) >= 10: break
if not keywords:
    keywords = ["memory","moment","trace","echo","warmth","smile"]

# Visual knobs (deterministic from text)
plate_count   = int(3 + round(2 + 3*arousal + 2*nostalgia))         # 5–10
band_count    = int(4 + round(2 + 4*arousal))                       # 6–10
grain_density = int(5000 + 9000*nostalgia)                          # 5k–14k
tilt_range    = 0.10 + 0.35*arousal                                 # 0.1–0.45 rad
noise_amp     = 0.15 + 0.35*arousal                                 # slitscan wobble
kernel_mode   = "burst" if arousal>0.65 else ("ring" if nostalgia>0.6 else "disc")
text_ring     = "dense" if social>0.6 else "sparse"

schema = {
    "seed": seed,
    "palette": palette,
    "caption": "Visual Memory",
    "subtitle": "data-humanism × recollection",
    "fragments": keywords,
    "story": t,
    # expressive axes
    "valence": round(valence,3),
    "arousal": round(arousal,3),
    "social": round(social,3),
    "nostalgia": round(nostalgia,3),
    # knobs
    "plates": plate_count,
    "bands": band_count,
    "grain": grain_density,
    "tilt": tilt_range,
    "noiseAmp": noise_amp,
    "kernelMode": kernel_mode,
    "textRing": text_ring
}

# ──────────────────────────────────────
# 3) p5.js page template
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
    margin-left:auto;
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
document.getElementById('metaRight').textContent = `seed:${SCHEMA.seed} · v:${SCHEMA.valence} a:${SCHEMA.arousal}`;

new p5((p)=>{
  const W=980, H=980;
  const inner = {x:0, y:68, w:W, h:H-68-64};
  const [A,B,C] = (SCHEMA.palette||["#DDD","#AAA","#888"]).map(h=>p.color(h));
  const seed = SCHEMA.seed||1;
  p.randomSeed(seed); p.noiseSeed(seed);

  const PLATES = SCHEMA.plates||7;
  const BANDS  = SCHEMA.bands||7;
  const GRAIN  = SCHEMA.grain||9000;
  const TILT   = SCHEMA.tilt||0.25;
  const NOISEA = SCHEMA.noiseAmp||0.3;
  const KM     = SCHEMA.kernelMode||"disc";
  const TRING  = SCHEMA.textRing||"sparse";
  const VAL    = SCHEMA.valence||0;
  const ARO    = SCHEMA.arousal||0;
  const NOS    = SCHEMA.nostalgia||0;
  const SOC    = SCHEMA.social||0;

  function bgEditorial(){
    for(let y=inner.y; y<inner.y+inner.h; y++){
      const t=(y-inner.y)/(inner.h);
      const cc=p.lerpColor(A,B, t*0.9 + 0.05);
      p.stroke(cc); p.line(inner.x, y, inner.x+inner.w, y);
    }
    // paper grain
    p.push(); p.noStroke(); p.blendMode(p.MULTIPLY);
    for(let i=0;i<GRAIN;i++){
      const x=p.random(inner.x, inner.x+inner.w);
      const y=p.random(inner.y, inner.y+inner.h);
      p.fill(0,0,0, p.random(3, 6+NOS*6));
      p.circle(x,y,p.random(0.6,1.4+NOS*0.6));
    }
    p.pop();
  }

  function monotypePlates(){
    p.push(); p.blendMode(p.MULTIPLY);
    for(let i=0;i<PLATES;i++){
      const cx = inner.x + inner.w* (0.18 + 0.64*p.random());
      const cy = inner.y + inner.h* (0.18 + 0.64*p.random());
      const baseR = Math.min(inner.w,inner.h) * p.random(0.10 + 0.06*ARO, 0.22 + 0.1*ARO);
      const colr = [A,B,C][i%3];
      const rot = p.random(-TILT, TILT) * (VAL< -0.25 ? 1.2 : 1);
      p.push();
      p.translate(cx,cy); p.rotate(rot);
      const layers = 2 + Math.round(1 + 2*NOS);
      for(let k=0;k<layers;k++){
        p.noStroke();
        const alpha = 120 - k*28 + NOS*15;
        p.fill(p.red(colr),p.green(colr),p.blue(colr), alpha);
        p.beginShape();
        const n = 14 + Math.round(ARO*8);
        for(let a=0;a<n;a++){
          const t=a/n*p.TWO_PI;
          const r = baseR * (0.85 + 0.22*p.noise(i*10 + a*0.7 + p.frameCount*0.0004*(0.2+ARO)));
          p.vertex(r*Math.cos(t), r*Math.sin(t));
        }
        p.endShape(p.CLOSE);
      }
      const dots = 80 + Math.round(120*NOS);
      for(let d=0; d<dots; d++){
        const rx = p.random(-baseR, baseR), ry = p.random(-baseR, baseR);
        if (p.dist(rx,ry,0,0) < baseR*1.02){
          p.noStroke(); p.fill(30,20,10, 16 + NOS*14);
          p.circle(rx,ry,p.random(1,2.4 + ARO*0.6));
        }
      }
      p.pop();
    }
    p.pop();
  }

  function slitscanBands(){
    p.push();
    for(let b=0;b<BANDS;b++){
      const baseY = inner.y + inner.h*(0.12 + 0.76*(b+0.5)/BANDS);
      const thick = 6 + 10*ARO*p.noise(b*0.4 + p.frameCount*0.002*(0.2+ARO));
      const cc = p.lerpColor(B,C, b/BANDS);
      p.stroke(p.red(cc),p.green(cc),p.blue(cc), 60 + 50*ARO);
      p.strokeWeight(thick);
      p.noFill();

      const x1=inner.x+40, x4=inner.x+inner.w-40;
      const x2=p.lerp(x1,x4, 0.33), x3=p.lerp(x1,x4, 0.66);
      const wob = 18 + 38*NOISEA;
      const y1=baseY + wob*p.noise(b+0.11);
      const y4=baseY + wob*p.noise(b+0.22);
      const y2=baseY - (18+36*ARO)*p.noise(b+1.2);
      const y3=baseY + (18+36*ARO)*p.noise(b+2.3);
      p.bezier(x1,y1, x2,y2, x3,y3, x4,y4);
    }
    p.pop();
  }

  function kernel(){
    const cx = inner.x + inner.w*(0.40 + 0.24*SOC); // shift right as social increases
    const cy = inner.y + inner.h*(0.50 + 0.16*(NOS-0.5));
    const base = Math.min(inner.w,inner.h)*(0.10 + 0.06*ARO);

    function glow(x,y,r,col,repeat=5){
      p.noStroke();
      for(let i=repeat;i>0;i--){
        const rad = r*(i/repeat);
        const a = 180*(i/repeat);
        p.fill(p.red(col),p.green(col),p.blue(col), a);
        p.circle(x,y,rad*2);
      }
    }

    const glowCol = p.lerpColor(A,B, 0.3+0.4*ARO);
    if (SCHEMA.kernelMode === "ring"){
      glow(cx,cy, base*1.1, glowCol, 6);
      p.noFill(); p.stroke(90,70,60,90 + NOS*40); p.strokeWeight(1.6);
      p.circle(cx,cy, base*2.0);
      const ticks = 24 + Math.round(24*NOS);
      for(let i=0;i<ticks;i++){
        const a = -p.HALF_PI + i/ticks*p.TWO_PI;
        const r1=base*0.95, r2=base*1.05;
        p.line(cx+r1*Math.cos(a), cy+r1*Math.sin(a), cx+r2*Math.cos(a), cy+r2*Math.sin(a));
      }
    } else if (SCHEMA.kernelMode === "burst"){
      glow(cx,cy, base*1.0, glowCol, 4);
      p.push(); p.translate(cx,cy); p.noFill();
      const rays = 30 + Math.round(40*ARO);
      for(let i=0;i<rays;i++){
        const a = p.TWO_PI*i/rays + 0.02*p.frameCount*(0.2+ARO);
        const r = base*(1.2 + 1.4*ARO*p.noise(i*0.3));
        p.stroke(80,60,50,120);
        p.strokeWeight(1.2);
        p.line(0,0, r*Math.cos(a), r*Math.sin(a));
      }
      p.pop();
      p.noStroke(); p.fill(255,210,140,220); p.circle(cx,cy, base*0.6);
    } else { // disc
      glow(cx,cy, base*1.2, glowCol, 5);
      p.noStroke(); p.fill(255,205,120,220); p.circle(cx,cy, base*0.9);
    }
  }

  function fragments(){
    const frAll = (SCHEMA.fragments||[]);
    const fr = frAll.slice(0, (TRING==="dense"?10:6));
    if (!fr.length) return;

    p.textAlign(p.CENTER,p.CENTER);
    p.textSize(14 + 2*SOC);
    p.fill(70,55,48, 140 + 40*NOS);

    const cx = inner.x + inner.w*(0.40 + 0.24*SOC);
    const cy = inner.y + inner.h*(0.50 + 0.16*(NOS-0.5));
    const baseR = Math.min(inner.w,inner.h) * (0.22 + 0.12*NOS);

    for(let i=0;i<fr.length;i++){
      const a = -p.HALF_PI + i/fr.length * p.TWO_PI + 0.18*(VAL<0?-1:1);
      const wob = 10*Math.sin(p.frameCount*(0.004 + 0.0006*i) * (0.2+ARO) + i);
      const x = cx + (baseR+wob)*Math.cos(a);
      const y = cy + (baseR+wob)*Math.sin(a);
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
    st.info("Type your memory and click **Generate**. The card adapts to valence, arousal, socialness, and nostalgia; visuals are deterministic per story.")
