import re, math, hashlib, json, streamlit as st
from streamlit.components.v1 import html as components_html

st.set_page_config(page_title="Visual Memory — Canvas", page_icon="🌀", layout="centered")
st.title("🌀 Visual Memory (smoke silhouettes × data-humanism) — Canvas")

# ───────────── INPUTS ─────────────
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

# ───────────── TEXT FEATURES ─────────────
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

STOP = set("""a an the and or of for to from is are was were be being been this that those these i me my we our you your he she they them his her their in on at by with without into out about over under after before again more most such very just not no yes it's its""".split())
frags_list = [w for w in re.findall(r"[A-Za-z]{3,}", t) if w.lower() not in STOP][:10]
if not frags_list:
    frags_list = ["memory","moment","echo","warmth","friends","smile"]

def mood_palette(v,a,n):
    if v > 0.3 and a > 0.5: return ["#1a1a1e","#FFC979","#FF9DA3"]
    if v > 0.3 and n > 0.5: return ["#17171a","#F8D7B8","#D9C6E6"]
    if v < -0.3 and n > 0.5: return ["#15151a","#BDA7D6","#AEB3C2"]
    if v < -0.3: return ["#131317","#9AB0C2","#6C7A89"]
    return ["#121215","#E3DCD2","#C8D8C6"]

BG, P1, P2 = mood_palette(valence, arousal, nostalgia)

def choose_symbol(s:str):
    s=s.lower()
    if any(k in s for k in ["birthday","cake","party","friends"]): return "cake"
    if any(k in s for k in ["beach","ocean","sea","waves"]): return "shell"
    if any(k in s for k in ["loss","alone","lonely","grief"]): return "lamp"
    if any(k in s for k in ["school","childhood","photo"]): return "frame"
    if any(k in s for k in ["rain","window","reflection","night"]): return "window"
    if any(k in s for k in ["travel","journey","road","flight","train"]): return "horizon"
    return "core"

symbol = choose_symbol(t)

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
SCHEMA_JS = json.dumps(schema, ensure_ascii=True, separators=(",",":"))

# ───────────── p5.js EMBED ─────────────
p5_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'/>
<style>
  html,body {{ margin:0; padding:0; background:#0b0b0d; }}
  #card {{ width:980px; height:980px; margin:24px auto; position:relative;
          overflow:hidden; background:#0f0f12; border-radius:28px;
          box-shadow:0 16px 40px rgba(0,0,0,.35), 0 2px 10px rgba(0,0,0,.2); }}
  #chrome {{ position:absolute; top:0; left:0; right:0; height:64px;
             display:flex; align-items:center; gap:10px; padding:0 18px;
             color:#e8e6e3; font:13px system-ui;
             background:linear-gradient(180deg, rgba(255,255,255,.08),
             rgba(255,255,255,.02)); border-top-left-radius:28px;
             border-top-right-radius:28px; }}
  .dot {{ width:7px; height:7px; border-radius:50%; background:#4a4a50; }}
  #p5mount {{ position:absolute; top:64px; left:0; right:0; bottom:56px; }}
  #footer {{ position:absolute; left:0; right:0; bottom:0; height:56px;
             display:flex; align-items:center; justify-content:space-between;
             padding:0 16px; color:#c8c6c3; font:11px system-ui;
             background:linear-gradient(0deg, rgba(255,255,255,.06),
             rgba(255,255,255,0)); border-bottom-left-radius:28px;
             border-bottom-right-radius:28px; }}
  #btnsave {{ margin-left:auto; padding:6px 10px;
              border:1px solid #3a3a40; border-radius:8px;
              background:#15151a; color:#ddd; cursor:pointer; }}
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
  const c = document.querySelector('canvas');
  if (!c) return;
  const a = document.createElement('a');
  a.download = 'visual_memory.png';
  a.href = c.toDataURL('image/png');
  a.click();
}}

document.getElementById('metaLeft').textContent  = (S.story||'').slice(0,92);
document.getElementById('metaRight').textContent = `seed:${{S.seed}} • v:${{S.valence}} a:${{S.arousal}} s:${{S.social}}`;

new p5((p)=>{{
  const [BG, P1, P2] = (S.palette||["#121215","#E3DCD2","#C8D8C6"]).map(h=>p.color(h));
  p.setup = ()=>{{
    p.createCanvas(980,980).parent(document.getElementById('p5mount'));
    p.noLoop();
  }};
  p.draw = ()=>{{
    p.background(BG);
    const cx=490, cy=490;
    for(let r=400;r>0;r-=4){{
      const col=p.lerpColor(P1,P2,r/400);
      p.noStroke(); p.fill(p.red(col),p.green(col),p.blue(col),8);
      p.circle(cx,cy,r*2);
    }}
    p.textAlign(p.CENTER,p.CENTER);
    p.textSize(20);
    p.fill(240,220,210,180);
    const words=S.fragments||[];
    for(let i=0;i<words.length;i++){{
      const a=i*0.6283;
      const x=cx+Math.cos(a)*p.random(200,300);
      const y=cy+Math.sin(a)*p.random(200,300);
      p.text(words[i],x,y);
    }}
  }};
}});
</script>
</body>
</html>
"""

# ───────────── RENDER ─────────────
if go:
    components_html(p5_html, height=1060, scrolling=False)
else:
    st.info("Type your memory and click **Generate**. The canvas renders smoke-like silhouettes "
            "with subtle data-humanism aesthetics. Birthday memories automatically use a glowing cake. "
            "Deterministic output — raise Motion for gentle animation.")
