# app.py
import re, json, hashlib, math
import streamlit as st
from streamlit.components.v1 import html as components_html

st.set_page_config(page_title="Visual Memory — ReCollection Silhouettes", page_icon="🌀", layout="centered")
st.title("🌀 Visual Memory (ReCollection × Data Humanism)")

# ──────────────────────────────────────
# 1) Inputs
# ──────────────────────────────────────
story = st.text_area(
    "Whisper your memory (a few sentences work best)",
    "Yesterday was my birthday. I met childhood friends after years; we laughed, took photos, and shared cake.",
    height=140,
)
motion = st.slider("Motion (0 = still)", 0.0, 1.0, 0.0, 0.05)
go = st.button("Generate")

# ──────────────────────────────────────
# 2) Text → features
# ──────────────────────────────────────
t = story.strip()
seed_text = (t + str(motion)).strip() or "empty"
seed = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16) % 10**9
tl = t.lower()

# tiny lexicons
L_POS = ["joy","happy","happiness","love","laugh","smile","proud","grateful","peace","serene","calm","relief","beautiful","celebrate","birthday","together","hug","kiss","wedding","success","win"]
L_NEG = ["sad","cry","alone","lonely","fear","anxious","anxiety","stress","angry","regret","loss","lost","breakup","hurt","pain","miss","funeral","argument","fight","tired"]
L_HIGH = ["ecstatic","thrill","rush","party","dance","screamed","wild","storm","fireworks","concert","crowd","festival","goal","race","rollercoaster","adrenaline"]
L_LOW  = ["quiet","still","slow","breeze","gentle","soft","silent","night","dawn","sunset","walk","beach","library","rain","reading","meditate","tea","coffee"]
L_SOC  = ["friends","family","together","team","we","us","crowd","group","party","colleagues","classmates","reunion","gathering"]
L_NOST = ["yesterday","childhood","years ago","remember","memory","memories","reminisce","nostalgia","nostalgic","school","college","grandma","grandfather","album","photo","photos","vintage"]

def score(words): return sum(2 if f" {w} " in f" {tl} " else 0 for w in words)
val_raw = score(L_POS) - score(L_NEG)
aro_raw = score(L_HIGH) - score(L_LOW)
soc_raw = score(L_SOC)
nos_raw = score(L_NOST)

def sig(x): return 1/(1+math.exp(-x/4))
valence   = max(-1.0, min(1.0, (sig(val_raw)-0.5)*2))
arousal   = max(0.0, min(1.0, sig(aro_raw)))
social    = max(0.0, min(1.0, sig(soc_raw)))
nostalgia = max(0.0, min(1.0, sig(nos_raw)))

# base palettes (emotion → wash). Silhouette is monochrome filmic; colors glaze on top.
if valence > 0.3 and arousal >= 0.55:
    palette = ["#EFF1F5", "#FFD482", "#F79892"]                 # bright joy
elif valence > 0.3:
    palette = ["#EFF1F5", "#FBE8C7", "#CFE8FF"]                 # gentle warm
elif valence < -0.3 and nostalgia > 0.5:
    palette = ["#EDEDED", "#CDB4DB", "#A3A3B3"]                 # bittersweet violet
elif valence < -0.3:
    palette = ["#EDEDED", "#B0B7C3", "#6B7685"]                 # cool muted
elif nostalgia > 0.5:
    palette = ["#EFEAE6", "#F7C6B3", "#C0A5D7"]                 # sepia nostalgia
else:
    palette = ["#F0F0F0", "#D8E3E7", "#C7D9C4"]                 # neutral-soft

# fragments
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

# knobs
grain_density = int(6000 + 10000*nostalgia)
bands  = int(5 + round(4 + 3*arousal))
tilt   = 0.12 + 0.3*arousal
kernel = "ring" if nostalgia>0.6 else ("burst" if arousal>0.65 else "disc")
text_density = "dense" if social>0.6 else "sparse"
scene_mode = "group" if social>0.45 else "portrait"  # choose silhouette composition

schema = {
    "seed": seed,
    "palette": palette,
    "story": t,
    "fragments": keywords,
    "valence": round(valence,3),
    "arousal": round(arousal,3),
    "social": round(social,3),
    "nostalgia": round(nostalgia,3),
    "grain": grain_density,
    "bands": bands,
    "tilt": tilt,
    "kernel": kernel,
    "textDensity": text_density,
    "scene": scene_mode,
    "motion": float(motion),
}

# ──────────────────────────────────────
# 3) p5 template (silhouette spray + card)
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
  html,body { margin:0; padding:0; background:#0b0b0d; }
  #card {
    width: 980px; height: 980px; margin: 24px auto;
    background: #0f0f12; /* dark theater */
    border-radius: 28px;
    box-shadow: 0 16px 40px rgba(0,0,0,0.35), 0 2px 10px rgba(0,0,0,0.2);
    position: relative; overflow: hidden;
  }
  #chrome {
    position:absolute; top:0; left:0; right:0; height: 64px;
    background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));
    border-top-left-radius: 28px; border-top-right-radius: 28px;
    display:flex; align-items:center; gap:10px; padding:0 18px;
    color:#e8e6e3; font: 13px/1.2 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
  }
  .dot { width:7px; height:7px; border-radius:50%; background:#4a4a50; }
  #title { font-weight:600; letter-spacing:.3px; }
  #subtitle { opacity:.65; margin-left:6px; }
  #p5mount { position:absolute; top:64px; left:0; right:0; bottom:56px; }
  #footer {
    position:absolute; left:0; right:0; bottom:0; height:56px;
    display:flex; align-items:center; justify-content:space-between;
    padding:0 16px; color:#c8c6c3; font: 11px system-ui;
    background: linear-gradient(0deg, rgba(255,255,255,0.06), rgba(255,255,255,0));
    border-bottom-left-radius: 28px; border-bottom-right-radius: 28px;
  }
  #btnsave {
    margin-left:auto;
    padding:6px 10px; border:1px solid #3a3a40; border-radius:8px; background:#15151a; cursor:pointer;
    font:12px system-ui; color:#ddd;
  }
</style>
</head>
<body>
<div id="card">
  <div id="chrome">
    <div class="dot"></div><div class="dot"></div><div class="dot"></div>
    <div id="title">Visual Memory</div><div id="subtitle">— ReCollection silhouettes</div>
    <button id="btnsave" onclick="savePNG()">Save PNG</button>
  </div>
  <div id="p5mount"></div>
  <div id="footer"><div id="metaLeft"></div><div id="metaRight"></div></div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.4/p5.min.js"></script>
<script>
const S = __SCHEMA__;

function savePNG(){
  const c=document.querySelector('canvas'); if(!c) return;
  const a=document.createElement('a'); a.download='visual_memory.png'; a.href=c.toDataURL('image/png'); a.click();
}
document.getElementById('metaLeft').textContent  = (S.story||'').slice(0,90);
document.getElementById('metaRight').textContent = `seed:${S.seed} · v:${S.valence} a:${S.arousal} s:${S.social}`;

new p5((p)=>{
  const W=980, H=980;
  const inner = {x:0, y:64, w:W, h:H-64-56};
  const [P0,P1,P2] = (S.palette||["#F0F0F0","#CCCCCC","#AAAAAA"]).map(h=>p.color(h));
  const MOTION = S.motion||0;
  p.randomSeed(S.seed||1); p.noiseSeed(S.seed||1);

  // Precompute deterministic points for spray / grain to avoid flicker
  function deterSeries(n, a=997, b=1493){ const out=[]; for(let i=0;i<n;i++){ out.push([(i%a)/a, ((i*37)%b)/b]); } return out; }

  // ——— Background film plate (monochrome) + color glaze
  function bg(){
    p.noStroke();
    // dark plate
    p.fill(12,12,16);
    p.rect(inner.x, inner.y, inner.w, inner.h);
    // editorial glaze
    for(let y=inner.y; y<inner.y+inner.h; y++){
      const t=(y-inner.y)/(inner.h);
      const c = p.lerpColor(p.color(12,12,16), p.color(24,24,30), t);
      p.stroke(c); p.line(inner.x, y, inner.x+inner.w, y);
    }
    // emotion color wash (screen)
    p.push(); p.blendMode(p.SCREEN);
    const wash = p.lerpColor(P1,P2, 0.45+0.3*S.arousal);
    for(let y=inner.y; y<inner.y+inner.h; y+=2){
      p.stroke(p.red(wash),p.green(wash),p.blue(wash), 12 + 30*Math.max(0,S.valence));
      p.line(inner.x, y, inner.x+inner.w, y);
    }
    p.pop();

    // paper grain
    const G = S.grain||9000; const pts = deterSeries(G);
    p.push(); p.noStroke(); p.blendMode(p.MULTIPLY);
    for(let i=0;i<G;i++){
      const x = inner.x + pts[i][0]*inner.w;
      const y = inner.y + pts[i][1]*inner.h;
      p.fill(255,255,255, 6); // subtle speckle on dark
      p.circle(x,y, 0.6 + (i%17)/17 * 1.6);
    }
    p.pop();
  }

  // ——— Human-like silhouettes (portrait or group), spray + erosion
  // Built from primitive “head+shoulder” blobs; edges eroded with Worley-ish noise.
  function silhouetteLayer(){
    p.push(); p.blendMode(p.SCREEN);
    const baseAlpha = 205; // brightness of “memory dust”
    const actors = (S.scene === "group") ? (5 + Math.round(7*S.social)) : 1;

    // Layout anchors
    const anchors = [];
    if (S.scene === "group"){
      // Curve across mid-lower canvas
      const yBase = inner.y + inner.h*0.62;
      for(let i=0;i<actors;i++){
        const t = (i+0.5)/actors;
        const x = inner.x + inner.w*(0.12 + 0.76*t + 0.02*p.noise(i*0.7));
        const y = yBase - 60*Math.sin(t*Math.PI) + 28*p.noise(100+i);
        const scale = 0.9 + 0.6*p.noise(200+i);
        anchors.push({x,y,scale});
      }
    }else{
      // Single off-center portrait
      const x = inner.x + inner.w*(0.42 + 0.18*p.noise(11));
      const y = inner.y + inner.h*(0.48 + 0.06*p.noise(22));
      anchors.push({x,y,scale:1.2+0.4*S.arousal});
    }

    // Spray painter using deterministic jitter
    const sprayPts = 9000 + Math.floor(8000*S.arousal) + Math.floor(7000*S.nostalgia);
    const jitter = deterSeries(sprayPts, 1997, 1789);

    for(const a of anchors){
      const headR = 44*a.scale;
      const shoulderW = 120*a.scale, shoulderH = 60*a.scale;

      for(let i=0;i<sprayPts;i++){
        const jx = (jitter[i][0]-0.5), jy = (jitter[i][1]-0.5);
        // sample radial region around head/shoulder
        const rx = a.x + jx*(shoulderW*2.2);
        const ry = a.y + jy*(headR*3.0);

        // shape mask: head circle + shoulder ellipse (soft union)
        const dHead = p.dist(rx,ry, a.x, a.y-headR*0.6) / headR;
        const dSh   = Math.hypot((rx-a.x)/(shoulderW*0.7), (ry-(a.y+shoulderH*0.1))/(shoulderH*0.75));
        let inside = (dHead<1.1) || (dSh<1.0);

        if (inside){
          // edge erosion via Worley-ish noise (gives grainy dissolving edges)
          const nx = 0.006*rx, ny=0.006*ry;
          const n1 = p.noise(nx,ny), n2 = p.noise(nx*2.1,ny*2.1+13);
          const erode = (n1*0.6 + n2*0.4);
          const edge  = Math.min(Math.abs(dHead-1.0), Math.abs(dSh-1.0));
          if (erode < 0.35 + 0.55*edge){ // drop some dots near edges
            const a255 = baseAlpha * (0.55 + 0.35*S.nostalgia);
            p.noStroke(); p.fill(235,235,245, a255 * (0.35 + 0.65*erode));
            p.circle(rx,ry, 1.0 + 2.6*(1-erode) + 0.8*S.arousal);
          }
        }
      }
    }
    p.pop();
  }

  // ——— Scan bands (Data Humanism)
  function bands(){
    p.push();
    for(let b=0;b<(S.bands||7);b++){
      const baseY = inner.y + inner.h*(0.14 + 0.72*(b+0.5)/(S.bands||7));
      const cc = p.lerpColor(P1,P2, b/((S.bands||7)));
      p.stroke(p.red(cc),p.green(cc),p.blue(cc), 38 + 40*S.arousal);
      p.strokeWeight(5 + 8*S.arousal);
      p.noFill();
      const x1=inner.x+36, x4=inner.x+inner.w-36;
      const x2=p.lerp(x1,x4, 0.33), x3=p.lerp(x1,x4, 0.66);
      const y1=baseY + 22*p.noise(b+0.11), y4=baseY + 22*p.noise(b+0.22);
      const y2=baseY - (18+28*S.arousal)*p.noise(b+1.2);
      const y3=baseY + (18+28*S.arousal)*p.noise(b+2.3);
      p.bezier(x1,y1, x2,y2, x3,y3, x4,y4);
    }
    p.pop();
  }

  // ——— Kernel + ticks (timefeel)
  function kernel(){
    const cx = inner.x + inner.w*(0.42 + 0.22*S.social);
    const cy = inner.y + inner.h*(0.50 + 0.14*(S.nostalgia-0.5));
    const base = Math.min(inner.w,inner.h)*(0.10 + 0.06*S.arousal);
    const glowCol = p.lerpColor(P0,P1, 0.35+0.4*S.arousal);

    function glow(x,y,r,col,repeat=5){
      p.noStroke();
      for(let i=repeat;i>0;i--){
        const rad = r*(i/repeat);
        const a = 160*(i/repeat);
        p.fill(p.red(col),p.green(col),p.blue(col), a);
        p.circle(x,y,rad*2);
      }
    }

    if (S.kernel === "ring"){
      glow(cx,cy, base*1.1, glowCol, 6);
      p.noFill(); p.stroke(220,220,230, 120); p.strokeWeight(1.4);
      p.circle(cx,cy, base*2.0);
      const ticks = 24 + Math.round(24*S.nostalgia);
      for(let i=0;i<ticks;i++){
        const a = -p.HALF_PI + i/ticks*p.TWO_PI;
        const r1=base*0.95, r2=base*1.05;
        p.line(cx+r1*Math.cos(a), cy+r1*Math.sin(a), cx+r2*Math.cos(a), cy+r2*Math.sin(a));
      }
    } else if (S.kernel === "burst"){
      glow(cx,cy, base*1.0, glowCol, 4);
      p.push(); p.translate(cx,cy); p.noFill();
      const rays = 30 + Math.round(40*S.arousal);
      for(let i=0;i<rays;i++){
        const a = p.TWO_PI*i/rays;
        const r = base*(1.2 + 1.4*S.arousal*p.noise(i*0.3));
        p.stroke(220,220,230,110);
        p.strokeWeight(1.2);
        p.line(0,0, r*Math.cos(a), r*Math.sin(a));
      }
      p.pop();
      p.noStroke(); p.fill(250,230,180,220); p.circle(cx,cy, base*0.6);
    } else {
      glow(cx,cy, base*1.2, glowCol, 5);
      p.noStroke(); p.fill(250,225,170,215); p.circle(cx,cy, base*0.9);
    }
  }

  // ——— Text fragments around the kernel
  function fragments(){
    const list = (S.fragments||[]).slice(0, S.textDensity==="dense"?10:6);
    if (!list.length) return;
    const cx = inner.x + inner.w*(0.42 + 0.22*S.social);
    const cy = inner.y + inner.h*(0.50 + 0.14*(S.nostalgia-0.5));
    const R  = Math.min(inner.w,inner.h) * (0.24 + 0.10*S.nostalgia);
    p.textAlign(p.CENTER,p.CENTER);
    p.textSize(14 + 2*S.social);
    p.fill(230,228,226, 160);
    for(let i=0;i<list.length;i++){
      const a = -p.HALF_PI + i/list.length * p.TWO_PI + 0.18*(S.valence<0?-1:1);
      const x = cx + R*Math.cos(a);
      const y = cy + R*Math.sin(a);
      p.text(list[i], x, y);
    }
  }

  p.setup = function(){
    const c = p.createCanvas(W,H);
    c.parent(document.getElementById('p5mount'));
    if (MOTION<=0) p.noLoop(); // default: still
  };

  p.draw = function(){
    bg();
    silhouetteLayer();   // <— human-like “dust” figures
    bands();
    kernel();
    fragments();

    if (MOTION>0){ setTimeout(()=>p.redraw(), Math.max(600, 2000 - 1400*MOTION)); p.noLoop(); }
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
)

if go:
    components_html(p5_html, height=1060, scrolling=False)
else:
    st.info("Type your memory and click **Generate**. The piece composes a monochrome human-like silhouette (portrait or group) with a data-humanist card. Motion is off by default (no flicker).")
