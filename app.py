# app.py
# Visual Memory — p5.js on canvas (smoke-like silhouettes × data-humanism)
# No cloud APIs. Deterministic visuals. Birthday → cake symbol.

import re, math, hashlib, json, streamlit as st
from streamlit.components.v1 import html as components_html

st.set_page_config(page_title="Visual Memory — Canvas", page_icon="🌀", layout="centered")
st.title("🌀 Visual Memory (smoke silhouettes × data-humanism) — Canvas")

# ──────────────────────────────────────
# 1) INPUTS
# ──────────────────────────────────────
story = st.text_area(
    "Whisper your memory (a few sentences work best)",
    "Yesterday was my birthday. I met childhood friends after years; we laughed, took photos, and shared cake.",
    height=140,
    help="Describe the moment; the canvas adapts to emotion, socialness, and nostalgia."
)
col1, col2, col3 = st.columns([1,1,1])
with col1:
    motion = st.slider("Motion (0 = still)", 0.0, 1.0, 0.0, 0.05,
                       help="Keep at 0 for no flicker. >0 adds gentle breathing.")
with col2:
    smoke = st.slider("Smoke density", 0.2, 1.0, 0.7, 0.05)
with col3:
    brightness = st.slider("Glow brightness", 0.2, 1.2, 0.9, 0.05)

go = st.button("Generate")

# ──────────────────────────────────────
# 2) TEXT → FEATURES (valence/arousal/social/nostalgia) + fragments
# ──────────────────────────────────────
t = story.strip()
seed_text = (t + f"|{motion:.2f}|{smoke:.2f}|{brightness:.2f}") or "empty"
seed = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16) % (2**31 - 1)
tl = f" {t.lower()} "

L_POS = ["joy","happy","happiness","love","laugh","smile","grateful","peace","calm","celebrate","birthday","together","hug","success","fun","warm"]
L_NEG = ["sad","cry","alone","lonely","fear","anxious","stress","angry","regret","loss","breakup","hurt","pain","miss","grief","tired","cold"]
L_HIGH= ["party","dance","festival","rush","crowd","concert","goal","celebration","fireworks","cheer","scream"]
L_LOW = ["quiet","still","slow","breeze","soft","silent","night","dawn","sunset","walk","reading","tea","coffee","calm"]
L_SOC = ["friends","family","together","team","crowd","group","party","reunion","gathering","classmates","colleagues"]
L_NOS = ["yesterday","childhood","memories","remember","nostalgia","nostalgic","school","college","old","album","photo","grandma","grandfather"]

def score(words): return sum(2 for w in words if f" {w} " in tl)
sig = lambda x: 1/(1+math.exp(-x/4))
valence   = max(-1.0, min(1.0, (sig(score(L_POS)-score(L_NEG)) - 0.5)*2))
arousal   = max(0.0, min(1.0, sig(score(L_HIGH)-score(L_LOW))))
social    = max(0.0, min(1.0, sig(score(L_SOC))))
nostalgia = max(0.0, min(1.0, sig(score(L_NOS))))

# floating word fragments
STOP = set("""a an the and or of for to from is are was were be being been this that those these i me my we our you your he she they them his her their in on at by with without into out about over under after before again more most such very just not no yes it's its""".split())
frags_list = [w for w in re.findall(r"[A-Za-z]{3,}", t) if w.lower() not in STOP][:10]
if not frags_list:
    frags_list = ["memory","moment","echo","warmth","friends","smile"]

# palette by mood
def mood_palette(v,a,n):
    if v > 0.3 and a > 0.5: return ["#1a1a1e","#FFC979","#FF9DA3"]       # joy & energy
    if v > 0.3 and n > 0.5: return ["#17171a","#F8D7B8","#D9C6E6"]       # warm nostalgia
    if v < -0.3 and n > 0.5: return ["#15151a","#BDA7D6","#AEB3C2"]      # bittersweet
    if v < -0.3: return ["#131317","#9AB0C2","#6C7A89"]                  # cool muted
    return ["#121215","#E3DCD2","#C8D8C6"]                               # calm neutral

BG, P1, P2 = mood_palette(valence, arousal, nostalgia)

# symbolic core object selection
def choose_symbol(s:str):
    s=s.lower()
    if any(k in s for k in ["birthday","cake","party","friends"]): return "cake"
    if any(k in s for k in ["beach","ocean","sea","waves"]):       return "shell"
    if any(k in s for k in ["loss","alone","lonely","grief"]):     return "lamp"
    if any(k in s for k in ["school","childhood","photo"]):        return "frame"
    if any(k in s for k in ["rain","window","reflection","night"]):return "window"
    if any(k in s for k in ["travel","journey","road","flight","train"]): return "horizon"
    return "core"
symbol = choose_symbol(t)

# build schema for JS
schema = {
    "seed": seed,
    "palette": [BG, P1, P2],
    "fragments": frags_list,
    "valence": round(valence,3),
    "arousal": round(arousal,3),
    "social": round(social,3),
    "nostalgia": round(nostalgia,3),
    "motion": float(motion),
    "smoke": float(smoke),
    "brightness": float(brightness),
    "scene": "group" if social>0.45 else "portrait",
    "symbol": symbol,
    "story": t
}

# ──────────────────────────────────────
# 3) p5.js template (no flicker; deterministic)
# ──────────────────────────────────────
SCHEMA_JS = json.dumps(schema, ensure_ascii=True, separators=(",",":"))

p5_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  html,body {{ margin:0; padding:0; background:#0b0b0d; }}
  #card {{
    width:980px; height:980px; margin:24px auto; position:relative; overflow:hidden;
    background:#0f0f12; border-radius:28px; box-shadow:0 16px 40px rgba(0,0,0,.35), 0 2px 10px rgba(0,0,0,.2);
  }}
  #chrome {{
    position:absolute; top:0; left:0; right:0; height:64px; display:flex; align-items:center; gap:10px; padding:0 18px;
    color:#e8e6e3; font:13px system-ui; background:linear-gradient(180deg, rgba(255,255,255,.08), rgba(255,255,255,.02));
    border-top-left-radius:28px; border-top-right-radius:28px;
  }}
  .dot {{ width:7px; height:7px; border-radius:50%; background:#4a4a50; }}
  #p5mount {{ position:absolute; top:64px; left:0; right:0; bottom:56px; }}
  #footer {{
    position:absolute; left:0; right:0; bottom:0; height:56px; display:flex; align-items:center; justify-content:space-between;
    padding:0 16px; color:#c8c6c3; font:11px system-ui; background:linear-gradient(0deg, rgba(255,255,255,.06), rgba(255,255,255,0));
    border-bottom-left-radius:28px; border-bottom-right-radius:28px;
  }}
  #btnsave {{ margin-left:auto; padding:6px 10px; border:1px solid #3a3a40; border-radius:8px; background:#15151a; color:#ddd; cursor:pointer; }}
</style>
</head>
<body>
<div id="card">
  <div id="chrome">
    <div class="dot"></div><div class="dot"></div><div class="dot"></div>
    <div><b>Visual Memory</b> — canvas</div>
    <button id="btnsave" onclick="savePNG()">Save PNG</button>
  </div>
  <div id="p5mount"></div>
  <div id="footer">
    <div id="metaLeft"></div>
    <div id="metaRight"></div>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.4/p5.min.js"></script>
<script>
const S = {SCHEMA_JS};

function savePNG(){ const c=document.querySelector('canvas'); if(!c) return;
  const a=document.createElement('a'); a.download='visual_memory.png'; a.href=c.toDataURL('image/png'); a.click(); }

document.getElementById('metaLeft').textContent  = (S.story||'').slice(0,92);
document.getElementById('metaRight').textContent = `seed:${S.seed} · v:{schema['valence']} a:{schema['arousal']} s:{schema['social']}`;

new p5((p)=>{
  const W=980, H=980, inner={{x:0, y:64, w:980, h:980-64-56}};
  const [BG, P1, P2] = (S.palette||["#121215","#E3DCD2","#C8D8C6"]).map(h=>p.color(h));
  const MOTION=S.motion||0, SMK=S.smoke||0.7, BR=S.brightness||0.9;
  p.randomSeed(S.seed||1); p.noiseSeed(S.seed||1);

  // -------- Helpers
  function lerpC(a,b,t){{ return p.lerpColor(a,b,t); }}
  function deterSeries(n,a=1997,b=1789){{ const o=[]; for(let i=0;i<n;i++)o.push([(i%a)/a, ((i*37)%b)/b]); return o; }}

  // -------- Layers
  function bgPlate(){{
    p.noStroke(); p.fill(BG); p.rect(inner.x, inner.y, inner.w, inner.h);
    // very subtle vertical vignette
    for(let y=inner.y;y<inner.y+inner.h;y++){{ const t=(y-inner.y)/inner.h;
      const c=lerpC(p.color(12,12,16), p.color(22,22,28), t);
      p.stroke(c); p.line(inner.x,y, inner.x+inner.w,y);
    }}
  }}

  function dataScanlines(){{
    p.push();
    const bands = 6 + Math.round(6*S.arousal);
    for(let b=0;b<bands;b++){{ const y = inner.y + inner.h*(0.15 + 0.7*(b+0.5)/bands);
      const col = lerpC(P1,P2, b/bands);
      p.stroke(p.red(col),p.green(col),p.blue(col), 24 + 42*S.arousal);
      p.strokeWeight(4 + 7*S.arousal);
      const x1=inner.x+36, x4=inner.x+inner.w-36;
      const x2=p.lerp(x1,x4,0.33), x3=p.lerp(x1,x4,0.66);
      const y1=y + 18*p.noise(b+0.11), y4=y + 18*p.noise(b+0.22);
      const y2=y - (16+26*S.arousal)*p.noise(b+1.2);
      const y3=y + (16+26*S.arousal)*p.noise(b+2.3);
      p.noFill(); p.bezier(x1,y1, x2,y2, x3,y3, x4,y4);
    }}
    p.pop();
  }}

  function radialTicks(cx,cy,r){{
    p.push(); p.noFill(); p.stroke(220,220,230, 90); p.strokeWeight(1.2);
    const ticks = 24 + Math.round(24*S.nostalgia);
    p.circle(cx,cy, r*2);
    for(let i=0;i<ticks;i++){{ const a=-p.HALF_PI + i/ticks*p.TWO_PI;
      p.line(cx+(r*0.95)*Math.cos(a), cy+(r*0.95)*Math.sin(a),
             cx+(r*1.05)*Math.cos(a), cy+(r*1.05)*Math.sin(a));
    }}
    p.pop();
  }}

  // Smoke silhouette spray (portrait/group)
  function silhouettes(){{
    p.push(); p.blendMode(p.SCREEN);
    const actors = (S.scene==="group") ? (5 + Math.round(6*S.social)) : 1;
    const ptsPer = Math.floor(6000 + 9000*SMK + 6000*S.nostalgia);
    const jitter = deterSeries(ptsPer, 2333, 1999);

    const anchors=[];
    if (actors>1){{ const yBase=inner.y+inner.h*0.62;
      for(let i=0;i<actors;i++){{ const t=(i+0.5)/actors;
        const x=inner.x+inner.w*(0.12 + 0.76*t + 0.02*p.noise(i*0.7));
        const y=yBase - 60*Math.sin(t*Math.PI) + 28*p.noise(100+i);
        anchors.push({{x,y,scale:0.9+0.6*p.noise(200+i)}}); }}
    }}else{{ anchors.push({{x: inner.x+inner.w*(0.44+0.18*p.noise(11)), y: inner.y+inner.h*(0.50+0.06*p.noise(22)), scale:1.2+0.4*S.arousal}}); }}

    for(const a of anchors){{ const headR=44*a.scale, shW=120*a.scale, shH=60*a.scale;
      for(let i=0;i<ptsPer;i++){{ const jx=(jitter[i][0]-0.5), jy=(jitter[i][1]-0.5);
        const rx=a.x + jx*(shW*2.2), ry=a.y + jy*(headR*3.0);
        const dHead=p.dist(rx,ry, a.x, a.y-headR*0.6)/headR;
        const dSh=Math.hypot((rx-a.x)/(shW*0.7), (ry-(a.y+shH*0.1))/(shH*0.75));
        if (dHead<1.1 || dSh<1.0){{ // inside shape
          const n1=p.noise(0.006*rx,0.006*ry), n2=p.noise(0.012*rx+13,0.012*ry);
          const erode = (n1*0.6 + n2*0.4);
          if (erode < 0.34 + 0.56*Math.min(1, Math.max(Math.abs(dHead-1.0), Math.abs(dSh-1.0)))){{
            const col=lerpC(P1,P2, 0.35+0.45*S.valence*0.5);
            p.noStroke(); p.fill(p.red(col),p.green(col),p.blue(col), 120*(0.55+0.35*S.nostalgia)*BR);
            p.circle(rx,ry, 0.8 + 2.4*(1-erode) + 0.6*S.arousal);
          }}
        }}
      }}
    }}
    p.pop();
  }}

  // Symbolic core (cake, lamp, etc.)
  function symbolCore(cx,cy){{
    const base = Math.min(inner.w,inner.h)*(0.10 + 0.06*S.arousal);
    const glow = lerpC(P1,P2, 0.35+0.4*S.arousal);
    // Glow
    p.noStroke();
    for(let i=6;i>0;i--){{ const rad=base*(i/6); const a=160*(i/6)*BR;
      p.fill(p.red(glow),p.green(glow),p.blue(glow), a);
      p.circle(cx,cy, rad*2);
    }}
    // Symbol
    if (S.symbol==="cake"){{ // rounded cake + candles
      const w=base*1.1, h=base*0.6, r=10;
      p.fill(255,240,210, 220); p.rect(cx-w/2, cy-h/2, w, h, r);
      const candles = 3 + Math.round(2*S.social);
      for(let i=0;i<candles;i++){{ const x=cx - w*0.3 + (i/(candles-1||1))*w*0.6;
        p.stroke(150,120,110,220); p.strokeWeight(2); p.line(x, cy-h*0.2, x, cy-h*0.45);
        p.noStroke(); p.fill(255,210,120, 230); p.ellipse(x, cy-h*0.52, 8, 12);
      }}
    }} else if (S.symbol==="lamp"){{ p.fill(235,235,245,220); p.triangle(cx-14,cy-6, cx+14,cy-6, cx,cy-30); p.rect(cx-3,cy-6,6,20); }}
      else if (S.symbol==="shell"){{ p.noFill(); p.stroke(240,230,220,200); p.strokeWeight(2);
        for(let k=0;k<6;k++) p.arc(cx,cy, base*0.4+ k*10, base*0.3+ k*8, -p.PI, 0);
      }}
      else if (S.symbol==="frame"){{ p.noFill(); p.stroke(240,230,220,220); p.strokeWeight(3); p.rect(cx-base*0.5, cy-base*0.4, base, base*0.8, 6); }}
      else if (S.symbol==="window"){{ p.noFill(); p.stroke(230,230,240,210); p.strokeWeight(2);
        p.rect(cx-base*0.55, cy-base*0.35, base*1.1, base*0.7, 8);
        p.line(cx, cy-base*0.35, cx, cy+base*0.35); p.line(cx-base*0.55, cy, cx+base*0.55, cy);
      }}
      else if (S.symbol==="horizon"){{ p.noFill(); p.stroke(230,230,240,210); p.strokeWeight(2); p.arc(cx, cy+base*0.2, base*1.8, base*1.2, 0, p.PI); }}
  }}

  // Floating text fragments
  function textFragments(cx,cy){{
    const list=(S.fragments||[]).slice(0, S.social>0.6?10:6);
    const R=Math.min(inner.w,inner.h)*(0.24 + 0.10*S.nostalgia);
    p.textAlign(p.CENTER,p.CENTER); p.textSize(14+2*S.social);
    p.fill(230,228,226, 155);
    for(let i=0;i<list.length;i++){{ const a=-p.HALF_PI + i/list.length*p.TWO_PI + 0.18*(S.valence<0?-1:1);
      const x=cx + R*Math.cos(a), y=cy + R*Math.sin(a);
      p.text(list[i], x, y);
    }}
  }}

  p.setup = function(){{
    const c=p.createCanvas(W,H); c.parent(document.getElementById('p5mount'));
    if (MOTION<=0) p.noLoop(); // no flicker by default
  }};

  p.draw = function(){{
    const cx = inner.x + inner.w*(0.42 + 0.22*S.social);
    const cy = inner.y + inner.h*(0.50 + 0.14*(S.nostalgia-0.5));
    bgPlate();
    silhouettes();            // smoke “humans”
    dataScanlines();          // data-humanism bands
    symbolCore(cx,cy);        // cake / symbol
    radialTicks(cx,cy, Math.min(inner.w,inner.h)*(0.10 + 0.06*S.arousal)*1.0);
    textFragments(cx,cy);

    if (MOTION>0){{ setTimeout(()=>p.redraw(), Math.max(600, 2000 - 1400*MOTION)); p.noLoop(); }}
  }};
});
</script>
</body>
</html>
"""

# ──────────────────────────────────────
# 4) RENDER
# ──────────────────────────────────────
if go:
    components_html(p5_html, height=1060, scrolling=False)
else:
    st.info("Type your memory and click **Generate**. The canvas renders smoke-like silhouettes with subtle data-humanism. "
            "Deterministic by default; raise Motion for gentle breathing.\n\n"
            "Birthday memories automatically replace the circle with a glowing cake.")
