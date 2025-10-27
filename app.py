import os, json, re, hashlib
import streamlit as st
from dotenv import load_dotenv
from streamlit.components.v1 import html as components_html

# ──────────────────────────────
# Setup
# ──────────────────────────────
load_dotenv()
st.set_page_config(page_title="Dream/Memory Doodler", page_icon="🌙", layout="wide")

# ──────────────────────────────
# Custom CSS - Dark Doodled Mode
# ──────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@400;600;700&family=Patrick+Hand&family=Kalam:wght@300;400;700&display=swap');

/* Global dark mode styling */
.stApp {
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
}

/* Hide default Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Custom header */
.main-header {
    text-align: center;
    margin: 2rem 0 3rem 0;
    padding-bottom: 2rem;
    border-bottom: 3px dashed rgba(78, 205, 196, 0.3);
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
}

.main-title {
    font-family: 'Caveat', cursive;
    font-size: 4rem;
    font-weight: 700;
    color: #f0f0f0;
    margin-bottom: 0.5rem;
    letter-spacing: 2px;
    text-shadow: 3px 3px 6px rgba(0,0,0,0.7);
    transform: rotate(-1deg);
}

.main-subtitle {
    font-family: 'Kalam', cursive;
    font-size: 1.2rem;
    color: #4ecdc4;
    font-style: italic;
    transform: rotate(0.5deg);
}

/* Section styling */
.stTextArea, .stTextInput {
    font-family: 'Kalam', cursive !important;
}

.stTextArea textarea {
    background: #1e1e1e !important;
    color: #e0e0e0 !important;
    border: 3px dashed #4ecdc4 !important;
    border-radius: 15px !important;
    font-family: 'Kalam', cursive !important;
    font-size: 1.1rem !important;
    padding: 1.5rem !important;
    min-height: 200px !important;
}

.stTextInput input {
    background: #1e1e1e !important;
    color: #e0e0e0 !important;
    border: 2px dashed #4ecdc4 !important;
    border-radius: 12px !important;
    font-family: 'Kalam', cursive !important;
    font-size: 1rem !important;
    padding: 0.8rem !important;
}

.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #45b7d1 !important;
    box-shadow: 0 0 20px rgba(78, 205, 196, 0.3) !important;
}

/* Button styling */
.stButton button {
    width: 100% !important;
    padding: 1.2rem 2rem !important;
    background: linear-gradient(135deg, #4ecdc4 0%, #45b7d1 100%) !important;
    color: #1a1a1a !important;
    border: 3px solid #333 !important;
    border-radius: 15px !important;
    font-family: 'Caveat', cursive !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    box-shadow: 4px 4px 0px #333 !important;
    transition: all 0.3s ease !important;
}

.stButton button:hover {
    transform: translate(-2px, -2px) rotate(-1deg) !important;
    box-shadow: 6px 6px 0px #333 !important;
}

/* Expander styling */
.streamlit-expanderHeader {
    background: #252525 !important;
    color: #4ecdc4 !important;
    border: 2px dashed #444 !important;
    border-radius: 12px !important;
    font-family: 'Caveat', cursive !important;
    font-size: 1.3rem !important;
}

.streamlit-expanderContent {
    background: #1e1e1e !important;
    border: 2px dashed #444 !important;
    border-radius: 0 0 12px 12px !important;
    color: #b0b0b0 !important;
}

/* JSON styling */
code {
    background: #1e1e1e !important;
    color: #4ecdc4 !important;
    border: 2px dashed #444 !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    font-family: 'Courier New', monospace !important;
}

/* Labels */
label {
    font-family: 'Caveat', cursive !important;
    font-size: 1.4rem !important;
    color: #4ecdc4 !important;
    font-weight: 600 !important;
}

/* Metadata cards */
.metadata-card {
    background: #252525;
    border: 3px dashed #444;
    border-radius: 15px;
    padding: 1.5rem;
    text-align: center;
    transition: all 0.3s ease;
    margin: 0.5rem;
}

.metadata-card:hover {
    transform: rotate(-2deg) scale(1.05);
    border-color: #4ecdc4;
}

.metadata-label {
    font-family: 'Kalam', cursive;
    font-size: 0.9rem;
    color: #888;
    margin-bottom: 0.5rem;
}

.metadata-value {
    font-family: 'Caveat', cursive;
    font-size: 2rem;
    font-weight: 700;
    color: #4ecdc4;
}

/* Doodle decorations */
.doodle-icon {
    display: inline-block;
    animation: wiggle 2s ease-in-out infinite;
}

@keyframes wiggle {
    0%, 100% { transform: rotate(-5deg); }
    50% { transform: rotate(5deg); }
}

/* Subtle background animation */
@keyframes pulse {
    0%, 100% { opacity: 0.05; }
    50% { opacity: 0.1; }
}

.stApp::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle at 20% 50%, rgba(78, 205, 196, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(69, 183, 209, 0.1) 0%, transparent 50%);
    animation: pulse 4s ease-in-out infinite;
    pointer-events: none;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────
# Header
# ──────────────────────────────
st.markdown("""
<div class="main-header">
    <div class="main-title">✏️ Dream / Memory Doodler</div>
    <div class="main-subtitle">~ a gentle visual journaling assistant inspired by data humanism ~</div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────
# UI Layout
# ──────────────────────────────
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<span class="doodle-icon">🌙</span>', unsafe_allow_html=True)
    prompt = st.text_area(
        "Share Your Memory",
        "I had my birthday yesterday and met a lot of childhood friends — it was a memorable birthday for me.",
        height=200,
        help="Tell me about a memory, dream, or moment you'd like to capture..."
    )
    
    date = st.text_input("Date of the memory", "October 25, 2025")
    do_generate = st.button("✨ Transform into Memory DNA ✨")

with col2:
    st.markdown('<span class="doodle-icon">🎨</span>', unsafe_allow_html=True)
    st.markdown("**Memory DNA Output**")

default_schema = {
    "emotion": "nostalgia",
    "intensity": 0.8,
    "palette": ["#F79892", "#FFD482", "#C0A5D7"],
    "nodes": 10,
    "caption": "October 25 — Old friends, new laughter",
    "summary": "Special day",
}
schema = default_schema.copy()

# ──────────────────────────────
# Gemini call + fallback
# ──────────────────────────────
def run_llm(text: str):
    if not (GEMINI_API_KEY and chosen_model):
        return None
    try:
        model = genai.GenerativeModel(chosen_model)
        system_hint = (
            "Return ONLY JSON with keys: emotion (string), intensity (0..1), "
            "palette (array of 3 hex strings), nodes (int 3..20), caption (<=64 chars), summary (<=3 words)."
        )
        resp = model.generate_content([system_hint, f"Memory:\n{text}"])
        raw = (resp.text or "").strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            i, j = raw.find("{"), raw.rfind("}")
            raw = raw[i:j+1]
        data = json.loads(raw)
        out = {
            "emotion": str(data.get("emotion", schema["emotion"]))[:40],
            "intensity": max(0.0, min(1.0, float(data.get("intensity", schema["intensity"])))),
            "palette": (data.get("palette", schema["palette"]) or schema["palette"])[:3],
            "nodes": max(3, min(20, int(data.get("nodes", schema["nodes"])))),
            "caption": str(data.get("caption", schema["caption"]))[:64],
            "summary": str(data.get("summary", "Special day"))[:64],
        }
        return out
    except Exception:
        st.info("💡 Using local generator (Gemini quota reached or offline).")
        return None

if do_generate:
    with st.spinner("🎨 Creating your memory DNA..."):
        llm_schema = run_llm(prompt)
        schema = llm_schema if llm_schema else local_schema_from_text(prompt, default_schema)

# Display metadata in col2
with col2:
    st.json(schema)
    
    # Metadata grid
    meta_col1, meta_col2 = st.columns(2)
    with meta_col1:
        st.markdown(f"""
        <div class="metadata-card">
            <div class="metadata-label">~ emotion ~</div>
            <div class="metadata-value">{schema['emotion']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metadata-card">
            <div class="metadata-label">~ nodes ~</div>
            <div class="metadata-value">{schema['nodes']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with meta_col2:
        st.markdown(f"""
        <div class="metadata-card">
            <div class="metadata-label">~ intensity ~</div>
            <div class="metadata-value">{schema['intensity']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        complexity = "low" if schema['nodes'] < 7 else "medium" if schema['nodes'] < 14 else "high"
        st.markdown(f"""
        <div class="metadata-card">
            <div class="metadata-label">~ complexity ~</div>
            <div class="metadata-value">{complexity}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Caption and Summary
    st.markdown(f"""
    <div class="caption-display">
        "{date} — {schema['caption']}"
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="caption-display">
        Summary: {schema['summary']}
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────
# p5.js visualization
# ──────────────────────────────
st.markdown("---")
st.markdown("### 🎨 Your Memory Doodle")

schema_hash = hashlib.md5(json.dumps(schema, sort_keys=True).encode()).hexdigest()
schema_js = json.dumps(schema, ensure_ascii=True, separators=(",", ":"))

p5_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<meta name='x-schema-hash' content='{schema_hash}'>
<style>
html,body {{margin:0;padding:0;background:#1a1a1a;}}
#wrap {{position:relative;width:900px;margin:0 auto;}}
#btnsave {{
  position:absolute;top:12px;right:12px;z-index:10;
  padding:10px 16px;border:3px solid #4ecdc4;border-radius:12px;
  background:linear-gradient(135deg, #4ecdc4 0%, #45b7d1 100%);
  color:#1a1a1a;font-family:'Caveat',cursive;font-size:1.2rem;font-weight:700;
  cursor:pointer;box-shadow:3px 3px 0px #333;transition:all 0.3s ease;
}}
#btnsave:hover {{
  transform:translate(-2px,-2px);box-shadow:5px 5px 0px #333;
}}
#caption {{
  position:absolute;bottom:10px;right:16px;color:rgba(240,240,240,0.9);font-size:18px;
  font-family:'Kalam',cursive;pointer-events:none;text-shadow:2px 2px 4px rgba(0,0,0,0.8);
}}
#summary {{
  position:absolute;bottom:35px;right:16px;color:rgba(78,205,196,0.9);font-size:14px;
  font-family:'Kalam',cursive;text-shadow:2px 2px 4px rgba(0,0,0,0.8);
}}
canvas {{border-radius:15px;box-shadow:0 10px 40px rgba(0,0,0,0.8);border:3px dashed #333;}}
</style>
</head>
<body>
<div id='wrap' data-schema-hash='{schema_hash}'>
  <button id='btnsave' onclick='savePNG()'>💾 Download PNG</button>
  <div id='p5mount'></div>
  <div id='caption'>{date} — {schema['caption']}</div>
  <div id='summary'>{schema['summary']}</div>
</div>

<script src='https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.4/p5.min.js'></script>
<script>
const SCHEMA = {schema_js};

function hashString(s){{ let h=2166136261>>>0; for(let i=0;i<s.length;i++){{ h^=s.charCodeAt(i); h=Math.imul(h,16777619); }} return h>>>0; }}
const SEED=hashString((SCHEMA.caption||'')+'|'+(SCHEMA.emotion||'')+'|'+(SCHEMA.nodes||'')+'|'+JSON.stringify(SCHEMA.palette||[]));
const LAYOUT=(SEED%3),RIPPLE_COUNT=4+(SEED%5),THREAD_OPACITY=80+(SEED%60),BG_ANGLE=(SEED%360)*Math.PI/180,BREATH_BASE=0.015+(SCHEMA.intensity?SCHEMA.intensity*0.025:0.02);

let centerPos,orbitR,nodes=[];
new p5((p)=>{{
  p.setup=function(){{
    p.randomSeed(SEED); p.noiseSeed(SEED);
    const c=p.createCanvas(900,900); c.parent(document.getElementById('p5mount'));
    centerPos=p.createVector(p.width/2,p.height/2);
    orbitR=Math.min(p.width,p.height)*(0.22+(SEED%8)*0.01);
    const N=Math.max(3,Math.min(20,SCHEMA.nodes||10));

    if(LAYOUT===0) {{
      for(let i=0;i<N;i++) {{
        const a=p.TWO_PI*i/N-p.PI/2;
        const rJit=orbitR*(0.9+p.random()*0.2);
        nodes.push({{x:centerPos.x+rJit*Math.cos(a),y:centerPos.y+rJit*Math.sin(a),phase:p.random(p.TWO_PI)}});
      }}
    }} else if(LAYOUT===1) {{
      const step=orbitR*(1.0/N);
      for(let i=0;i<N;i++) {{
        const a=(i*0.9)+(SEED%10)*0.03; const r=step*(i+3);
        nodes.push({{x:centerPos.x+r*Math.cos(a),y:centerPos.y+r*Math.sin(a),phase:p.random(p.TWO_PI)}});
      }}
    }} else {{
      const clusters=2+(SEED%2);
      const centers=[];
      for(let k=0;k<clusters;k++) {{
        const ang=(k/clusters)*p.TWO_PI+0.6*(SEED%7);
        const rad=orbitR*0.6;
        centers.push({{x:centerPos.x+rad*Math.cos(ang),y:centerPos.y+rad*Math.sin(ang)}});
      }}
      for(let i=0;i<N;i++) {{
        const cidx=i%clusters; const cx=centers[cidx].x, cy=centers[cidx].y;
        const r=50+p.random(80), a=p.random(p.TWO_PI);
        nodes.push({{x:cx+r*Math.cos(a),y:cy+r*Math.sin(a),phase:p.random(p.TWO_PI)}});
      }}
    }}

    document.getElementById('caption').textContent=SCHEMA.caption||'';
    document.getElementById('summary').textContent=SCHEMA.summary||'';
  }};

  p.draw=function(){{
    drawBackground(p,SCHEMA.palette||['#F79892','#FFD482','#C0A5D7']);
    p.noFill();

    // ripples
    p.push(); p.translate(centerPos.x,centerPos.y);
    const t=p.frameCount*0.01;
    for(let i=0;i<RIPPLE_COUNT;i++) {{
      const baseIn=orbitR*0.85, baseOut=orbitR*1.65;
      const r=p.map((t+i*0.25)%1,0,1,baseIn,baseOut);
      p.stroke(255,215,130,p.map(r,baseIn,baseOut,90,0));
      p.strokeWeight(1.25); p.circle(0,0,r*2);
    }}
    p.pop();

    // threads
    p.stroke(230,180,90,THREAD_OPACITY); p.strokeWeight(1.3);
    for(let i=0;i<nodes.length;i++) {{
      const a=nodes[i]; const b=nodes[(i+1)%nodes.length];
      p.line(centerPos.x,centerPos.y,a.x,a.y);
      p.bezier(a.x,a.y,
               p.lerp(a.x,centerPos.x,0.25), p.lerp(a.y,centerPos.y,0.25),
               p.lerp(b.x,centerPos.x,0.25), p.lerp(b.y,centerPos.y,0.25),
               b.x,b.y);
    }}

    // center glow
    drawGlow(p,centerPos.x,centerPos.y,Math.min(p.width,p.height)*0.16,p.color(255,195,80,130));
    p.fill(255,190,70,200); p.noStroke();
    p.circle(centerPos.x,centerPos.y,Math.min(p.width,p.height)*0.11);

    // nodes
    for(let i=0;i<nodes.length;i++) {{
      const n=nodes[i]; const breathe=4*Math.sin(p.frameCount*BREATH_BASE+n.phase);
      const vx=n.x+breathe*0.8, vy=n.y+breathe*0.8;
      p.noFill(); p.stroke(130,90,60,70); p.strokeWeight(2); p.circle(vx+2,vy+2,54);
      p.fill(255,205,120,170); p.stroke(140,90,60,120); p.strokeWeight(1.8); p.circle(vx,vy,44);
    }}
  }};
}});

function drawBackground(p,palette){{
  const c1=p.color(palette[0]), c2=p.color(palette[1]), c3=p.color(palette[2]);
  for(let y=0;y<p.height;y++){{ const f=y/(p.height-1); const col=p.lerpColor(c1,c2,f); p.stroke(col); p.line(0,y,p.width,y); }}
  p.noStroke(); for(let r=0;r<600;r++){{ const a=p.map(r,0,600,110,0); p.fill(p.red(c3),p.green(c3),p.blue(c3),a*0.3); p.circle(p.width*0.85,p.height*0.15,r); }}
}}

function drawGlow(p,x,y,radius,col){{
  p.noStroke(); for(let r=radius;r>0;r-=6){{ const a=p.map(r,0,radius,220,0); p.fill(p.red(col),p.green(col),p.blue(col),a*0.5); p.circle(x,y,r*2); }}
}}

function savePNG(){{
  const c=document.querySelector('canvas'); if(!c) return;
  const link=document.createElement('a'); link.download='memory_doodle.png'; link.href=c.toDataURL('image/png'); link.click();
}}
</script>
</body>
</html>
"""

# Render canvas
try:
    components_html(p5_html, height=980, scrolling=False)
except Exception as e:
    st.error("⚠️ Failed to render p5.js canvas.")
    st.exception(e)

# Debug expander
with st.expander("🔧 Debug Info"):
    st.write("**Chosen model:**", chosen_model)
    if available_models:
        st.json(available_models)
    st.write("**Current schema:**")
    st.json(schema)
