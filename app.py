# ──────────────────────────────
load_dotenv()
st.set_page_config(page_title="Dream/Memory Doodler", page_icon="🌙", layout="centered")
st.title("🌙 Dream / Memory Doodler")
st.title("🌙 Dream / Memory Doodler — Data Humanism Edition")

# ──────────────────────────────
# Gemini setup (safe + fallback)
@@ -48,12 +48,12 @@
def local_schema_from_text(text: str, default_schema: dict) -> dict:
    t = text.lower()
    EMO = {
        "joy": ["happy", "fun", "birthday", "party", "smile", "laugh"],
        "nostalgia": ["childhood", "old", "school", "remember", "reunion"],
        "calm": ["calm", "peace", "quiet", "relax"],
        "love": ["love", "together", "family", "friends"],
        "sad": ["sad", "alone", "miss", "cry", "loss"],
        "anxiety": ["stress", "worried", "fear", "nervous"],
        "joy": ["happy", "fun", "birthday", "party", "smile", "laugh", "celebrat"],
        "nostalgia": ["childhood", "old", "school", "remember", "reunion", "yesterday", "past"],
        "calm": ["calm", "peace", "quiet", "relax", "serene"],
        "love": ["love", "together", "family", "friends", "hug", "bond"],
        "sad": ["sad", "alone", "miss", "cry", "loss", "goodbye"],
        "anxiety": ["stress", "worried", "fear", "nervous", "anxious"],
    }
    counts = {e: sum(t.count(k) for k in kws) for e, kws in EMO.items()}
    emotion = max(counts, key=counts.get) if any(counts.values()) else "nostalgia"
@@ -63,19 +63,26 @@ def local_schema_from_text(text: str, default_schema: dict) -> dict:
    intensity = min(1.0, 0.4 + 0.1 * exclaim + 0.05 * caps)

    PALETTES = {
        "joy": ["#FFD482", "#F79892", "#F5B3FF"],
        "nostalgia": ["#F7C6B3", "#EBD8C3", "#C0A5D7"],
        "calm": ["#B9E3FF", "#DDEBF2", "#BFD6C7"],
        "love": ["#FFB3C1", "#FFDDE1", "#FFF0F3"],
        "sad": ["#9DB4C0", "#6C7A89", "#C7D3DD"],
        "anxiety": ["#A3B1C6", "#D6D6D6", "#8A9DB0"],
        "joy": ["#FFD482", "#F79892", "#F5B3FF"],        # warm gold/coral/lilac
        "nostalgia": ["#F7C6B3", "#EBD8C3", "#C0A5D7"],  # peach/parchment/lavender
        "calm": ["#B9E3FF", "#DDEBF2", "#BFD6C7"],       # sky/mist/sage
        "love": ["#FFB3C1", "#FFDDE1", "#FFF0F3"],       # soft rose tones
        "sad": ["#9DB4C0", "#6C7A89", "#C7D3DD"],        # cool greys/blues
        "anxiety": ["#A3B1C6", "#D6D6D6", "#8A9DB0"],    # muted tense blues
    }
    palette = PALETTES.get(emotion, default_schema["palette"])

    nodes = 6 if "friend" in t else 4
    for w in ["friends", "family", "group", "team", "all"]:
    # people scale → nodes
    nodes = 6 if "friend" in t or "friends" in t else 4
    for w in ["friends", "family", "group", "team", "all", "crowd", "class"]:
        if w in t:
            nodes += 2
    # rough count hints
    for m in re.findall(r"\b(\d{1,2})\b", t):
        try:
            nodes = max(nodes, int(m))
        except:
            pass
    nodes = max(3, min(20, nodes))

    caption = "A day to remember"
@@ -88,7 +95,7 @@ def local_schema_from_text(text: str, default_schema: dict) -> dict:

    return {
        "emotion": emotion,
        "intensity": round(intensity, 2),
        "intensity": round(float(intensity), 2),
        "palette": palette,
        "nodes": int(nodes),
        "caption": caption,
@@ -149,7 +156,7 @@ def run_llm(text: str):
    schema = llm_schema if llm_schema else local_schema_from_text(prompt, default_schema)

# ──────────────────────────────
# p5.js visualization (no 'key'; force remount via schema hash in DOM)
# p5.js visualization — multiple motifs (no 'key' needed)
# ──────────────────────────────
schema_hash = hashlib.md5(json.dumps(schema, sort_keys=True).encode()).hexdigest()
schema_js = json.dumps(schema, ensure_ascii=True, separators=(",", ":"))
@@ -173,10 +180,15 @@ def run_llm(text: str):
  font-family:Georgia,serif;pointer-events:none;text-shadow:0 1px 0 rgba(255,255,255,0.4);
}}
canvas {{border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,0.06);}}
.badge {{
  position:absolute;top:12px;left:12px;background:#fff;border:1px solid #e6d9c8;border-radius:8px;
  padding:6px 10px;font:12px/1.1 system-ui;color:#665a50;opacity:.85;
}}
</style>
</head>
<body>
<div id='wrap' data-schema-hash='{schema_hash}'>
  <div class='badge' id='modeBadge'></div>
  <button id='btnsave' onclick='savePNG()'>Download PNG</button>
  <div id='p5mount'></div>
  <div id='caption'></div>
@@ -186,98 +198,221 @@ def run_llm(text: str):
<script>
const SCHEMA = {schema_js};

// deterministic seed
function hashString(s){{ let h=2166136261>>>0; for(let i=0;i<s.length;i++){{ h^=s.charCodeAt(i); h=Math.imul(h,16777619); }} return h>>>0; }}
const SEED=hashString((SCHEMA.caption||'')+'|'+(SCHEMA.emotion||'')+'|'+(SCHEMA.nodes||'')+'|'+JSON.stringify(SCHEMA.palette||[]));
const LAYOUT=(SEED%3),RIPPLE_COUNT=4+(SEED%5),THREAD_OPACITY=80+(SEED%60),BG_ANGLE=(SEED%360)*Math.PI/180,BREATH_BASE=0.015+(SCHEMA.intensity?SCHEMA.intensity*0.025:0.02);
const SEED = hashString((SCHEMA.caption||'')+'|'+(SCHEMA.emotion||'')+'|'+(SCHEMA.nodes||'')+'|'+JSON.stringify(SCHEMA.palette||[]));

// choose motif from emotion + seed
function chooseMode(emotion, seed){{
  const e = (emotion||'').toLowerCase();
  if (e.includes('joy') || e.includes('love')) return (seed%2===0) ? 'PETAL_ROSACE' : 'SPIRAL_RIBBON';
  if (e.includes('calm')) return (seed%3===0) ? 'FLOW_FIELD' : 'SPIRAL_RIBBON';
  if (e.includes('anxiety')) return (seed%2===0) ? 'MOSAIC_GRID' : 'CONSTELLATION_WEB';
  if (e.includes('sad')) return (seed%2===0) ? 'ARC_TIMELINE' : 'MOSAIC_GRID';
  if (e.includes('nostalgia')) return (seed%3===0) ? 'SPIRAL_RIBBON' : 'ARC_TIMELINE';
  // default: vary by seed
  const modes = ['CONSTELLATION_WEB','SPIRAL_RIBBON','FLOW_FIELD','MOSAIC_GRID','PETAL_ROSACE','ARC_TIMELINE'];
  return modes[seed % modes.length];
}}
const MODE = chooseMode(SCHEMA.emotion, SEED);

document.getElementById('modeBadge').textContent = MODE.replaceAll('_',' ').toLowerCase();
document.getElementById('caption').textContent = SCHEMA.caption || '';

function col(p, hex){{ return p.color(hex||'#888'); }}

let centerPos,orbitR,nodes=[];
new p5((p)=>{{
  p.setup=function(){{
  p.setup = function(){{
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
    const c = p.createCanvas(900,900);
    c.parent(document.getElementById('p5mount'));
  }};

    document.getElementById('caption').textContent=SCHEMA.caption||'';
  p.draw = function(){{
    p.background(250,247,245);
    switch(MODE){{
      case 'CONSTELLATION_WEB': drawConstellation(p); break;
      case 'SPIRAL_RIBBON':     drawSpiralRibbon(p);  break;
      case 'FLOW_FIELD':        drawFlowField(p);     break;
      case 'MOSAIC_GRID':       drawMosaicGrid(p);    break;
      case 'PETAL_ROSACE':      drawPetalRosace(p);   break;
      case 'ARC_TIMELINE':      drawArcTimeline(p);   break;
    }}
  }};
}});

// ───────────────── MOTIFS ─────────────────

// 1) Constellation Web (friends, connections)
function drawConstellation(p){{
  const [A,B,C] = SCHEMA.palette.map(h=>col(p,h));
  const N = Math.max(3, Math.min(20, SCHEMA.nodes||8));
  const R = Math.min(p.width,p.height)*0.32;
  const cx=p.width/2, cy=p.height/2;

  // soft background gradient
  for (let y=0;y<p.height;y++){{ const f=y/(p.height-1); const cc=p.lerpColor(A,B,f); p.stroke(cc); p.line(0,y,p.width,y); }}
  // lavender tint
  p.noStroke(); for (let r=0;r<600;r++){{ const a=p.map(r,0,600,110,0); p.fill(C.levels[0],C.levels[1],C.levels[2],a*0.3); p.circle(p.width*0.85,p.height*0.15,r); }}

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
  p.noFill(); p.stroke(230,180,90,90); p.strokeWeight(1.4);
  const pts=[];
  for (let i=0;i<N;i++){{ 
    const a=p.TWO_PI*i/N - p.HALF_PI; 
    const r=R*(0.85 + 0.2*p.noise(SEED*0.001+i*0.2+p.frameCount*0.002)); 
    pts.push([cx+r*Math.cos(a), cy+r*Math.sin(a)]);
  }}
  // links
  for (let i=0;i<N;i++){{ 
    const a=pts[i], b=pts[(i+1)%N];
    p.line(cx,cy,a[0],a[1]);
    p.bezier(a[0],a[1], p.lerp(a[0],cx,0.25),p.lerp(a[1],cy,0.25),
             p.lerp(b[0],cx,0.25),p.lerp(b[1],cy,0.25), b[0],b[1]);
  }}
  // nodes
  for (let i=0;i<N;i++){{ 
    const q=pts[i]; 
    const breathe = 3*Math.sin(p.frameCount*(0.015+SCHEMA.intensity*0.02) + i);
    p.noFill(); p.stroke(130,90,60,70); p.circle(q[0]+2,q[1]+2,46);
    p.fill(255,205,120,170); p.stroke(140,90,60,120); p.circle(q[0]+breathe*0.6,q[1]+breathe*0.6,38);
  }}
  // center glow
  drawGlow(p, cx,cy, Math.min(p.width,p.height)*0.14, p.color(255,195,80,130));
}}

// 2) Spiral Ribbon (recollection)
function drawSpiralRibbon(p){{
  const [A,B,C] = SCHEMA.palette.map(h=>col(p,h));
  const cx=p.width/2, cy=p.height/2;
  // paper-like background
  for (let y=0;y<p.height;y++){{ const f=y/(p.height-1); const cc=p.lerpColor(A,B,f*0.7+0.15); p.stroke(cc); p.line(0,y,p.width,y); }}
  // spiral bands
  p.noFill();
  const turns = 6 + (SEED%4);
  const maxR = Math.min(p.width,p.height)*0.42;
  for (let t=0;t<turns;t++){{ 
    p.beginShape();
    for (let a=0;a<Math.PI*2*1.6; a+=0.03){{ 
      const r = (a/(Math.PI*2*1.6)) * maxR + 12*p.noise(t*0.1 + a*0.3 + SEED);
      const x=cx + r*Math.cos(a + t*0.15), y=cy + r*Math.sin(a + t*0.15);
      const cc = p.lerpColor(B,C, (t/turns));
      p.stroke(cc.levels[0],cc.levels[1],cc.levels[2], 90);
      p.vertex(x,y);
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
    p.endShape();
  }}
  // index marks (like monotype)
  p.stroke(80,60,50,60);
  for (let i=0;i<18;i++){{ p.line(80+i*44,120, 80+i*44,140+p.random(-6,6)); }}
  drawGlow(p,cx,cy, Math.min(p.width,p.height)*0.12, p.color(255,200,90,90));
}}

// 3) Flow Field / River (calm)
function drawFlowField(p){{
  const [A,B,C] = SCHEMA.palette.map(h=>col(p,h));
  // soft laminar gradient
  for (let y=0;y<p.height;y++){{ const f=y/(p.height-1); const cc=p.lerpColor(A,B,f); p.stroke(cc); p.line(0,y,p.width,y); }}
  p.noFill();
  const cols=60, rows=60;
  const scale = 10 + SCHEMA.intensity*30;
  for (let j=0;j<rows;j++){{ 
    let x=40, y=30+j*(p.height-60)/rows;
    p.beginShape();
    for (let i=0;i<cols;i++){{ 
      const a = p.noise((x+SEED)*0.002, (y+SEED)*0.002) * p.TWO_PI*2;
      const v = p.createVector(Math.cos(a), Math.sin(a));
      x += v.x*scale; y += v.y*scale*0.6;
      const cc = p.lerpColor(B,C, i/cols);
      p.stroke(cc.levels[0],cc.levels[1],cc.levels[2], 70);
      p.vertex(x,y);
    }}
    p.endShape();
  }}
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
// 4) Mosaic Grid (busy scenes / fragments)
function drawMosaicGrid(p){{
  const [A,B,C] = SCHEMA.palette.map(h=>col(p,h));
  const margin=60, w=p.width-2*margin, h=p.height-2*margin;
  const cells = 6 + (SCHEMA.nodes||8); // more nodes ⇒ more cells
  const cw = w/cells, ch = h/cells;
  // parchment
  p.noStroke(); p.fill(245,240,233); p.rect(margin-10,margin-10,w+20,h+20,12);
  for (let y=0;y<cells;y++){{ 
    for (let x=0;x<cells;x++){{ 
      const f = p.noise(SEED*0.001+x*0.22,y*0.22+p.frameCount*0.003);
      const cc = f<0.33?A:(f<0.66?B:C);
      p.fill(cc.levels[0],cc.levels[1],cc.levels[2], 140);
      const pad = 3 + (1+SCHEMA.intensity*8)*p.noise(x*0.4,y*0.4);
      p.rect(margin+x*cw+pad, margin+y*ch+pad, cw-2*pad, ch-2*pad, 4);
    }}
  }};
}});
  }}
}}

// 5) Petal Rosace (joy/love/celebration)
function drawPetalRosace(p){{
  const [A,B,C] = SCHEMA.palette.map(h=>col(p,h));
  const cx=p.width/2, cy=p.height/2;
  const petals = 8 + (SEED%8);
  const rings = 3 + (SCHEMA.nodes? Math.floor((SCHEMA.nodes-3)/4):2);
  // linen bg
  for (let y=0;y<p.height;y++){{ const f=y/(p.height-1); const cc=p.lerpColor(A,B,f*0.6+0.2); p.stroke(cc); p.line(0,y,p.width,y); }}
  // petals
  p.noFill();
  for (let r=1;r<=rings;r++){{ 
    const R = r * (Math.min(p.width,p.height)*0.12);
    for (let i=0;i<petals;i++){{ 
      const a = p.TWO_PI*i/petals + (p.frameCount*0.002);
      const px = cx + R*Math.cos(a), py = cy + R*Math.sin(a);
      const qx = cx + (R*0.4)*Math.cos(a+0.6), qy = cy + (R*0.4)*Math.sin(a+0.6);
      const cc = p.lerpColor(B,C, r/rings);
      p.stroke(cc.levels[0],cc.levels[1],cc.levels[2], 120);
      p.strokeWeight(1.6);
      p.bezier(cx,cy, qx,qy, qx, qy, px,py);
    }}
  }}
  // confetti dots
  p.noStroke();
  for (let i=0;i<60;i++){{ 
    const rr = Math.random()*Math.min(p.width,p.height)*0.45;
    const aa = Math.random()*p.TWO_PI;
    const cc = [A,B,C][i%3];
    p.fill(cc.levels[0],cc.levels[1],cc.levels[2], 150);
    p.circle(cx+rr*Math.cos(aa), cy+rr*Math.sin(aa), 4+Math.random()*6);
  }}
}}

function drawBackground(p,palette){{
  const c1=p.color(palette[0]), c2=p.color(palette[1]), c3=p.color(palette[2]);
  for(let y=0;y<p.height;y++){{ const f=y/(p.height-1); const col=p.lerpColor(c1,c2,f); p.stroke(col); p.line(0,y,p.width,y); }}
  p.noStroke(); for(let r=0;r<600;r++){{ const a=p.map(r,0,600,110,0); p.fill(p.red(c3),p.green(c3),p.blue(c3),a*0.3); p.circle(p.width*0.85,p.height*0.15,r); }}
// 6) Arc Timeline (milestones)
function drawArcTimeline(p){{
  const [A,B,C] = SCHEMA.palette.map(h=>col(p,h));
  const cx=p.width/2, cy=p.height*0.72;
  const layers = 6 + (SEED%5);
  // gradient sky
  for (let y=0;y<p.height;y++){{ const f=y/(p.height-1); const cc=p.lerpColor(A,B,f); p.stroke(cc); p.line(0,y,p.width,y); }}
  // arcs
  p.noFill();
  const base = Math.min(p.width,p.height)*0.2;
  for (let i=0;i<layers;i++){{ 
    const r = base + i*22;
    const cc = p.lerpColor(B,C, i/layers);
    p.stroke(cc.levels[0],cc.levels[1],cc.levels[2], 120);
    p.strokeWeight(2);
    const jitter = (SCHEMA.intensity||0.6)*0.25;
    const a1 = -Math.PI + i*0.04 - jitter;
    const a2 = -0.1 + jitter;
    p.arc(cx,cy,r*2,r*2, a1, a2);
    // tick (event)
    p.stroke(90,70,60,120); p.strokeWeight(1.2);
    p.line(cx-r*Math.cos(1.1), cy-r*Math.sin(1.1), cx-(r+10)*Math.cos(1.1), cy-(r+10)*Math.sin(1.1));
  }}
  // anchor
  p.noStroke(); p.fill(80,60,50,60); p.rect(cx-3, cy-30, 6, 60, 3);
}}

function drawGlow(p,x,y,radius,col){{
  p.noStroke(); for(let r=radius;r>0;r-=6){{ const a=p.map(r,0,radius,220,0); p.fill(p.red(col),p.green(col),p.blue(col),a*0.5); p.circle(x,y,r*2); }}
// ─────────── shared helpers ───────────
function drawGlow(p,x,y,rad,col){{
  p.noStroke();
  for (let r=rad; r>0; r-=6){{ const a=p.map(r,0,rad,220,0); p.fill(p.red(col),p.green(col),p.blue(col), a*0.5); p.circle(x,y,r*2); }}
}}

function savePNG(){{
@@ -289,16 +424,16 @@ def run_llm(text: str):
</html>
"""

# Render (no 'key' argument)
# Render (no 'key' argument in your Streamlit build)
try:
    components_html("<div style='padding:6px;font:14px system-ui'>Loading canvas…</div>", height=40, scrolling=False)
    components_html("<div style='padding:6px;font:14px system-ui'>Rendering…</div>", height=40, scrolling=False)
    components_html(p5_html, height=980, scrolling=False)
except Exception as e:
    st.error("⚠️ Failed to render p5.js canvas. See details below.")
    st.exception(e)
    st.write("schema:", schema)
    st.write("p5_html length:", len(p5_html))
    st.code(p5_html[:600], language="html")
    st.code(p5_html[:800], language="html")

# Debug
with st.expander("Gemini debug"):
