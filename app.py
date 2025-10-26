import os, json, textwrap
import streamlit as st
from dotenv import load_dotenv

# ---------- Setup ----------
load_dotenv()  # loads .env if present
st.set_page_config(page_title="Dream/Memory Doodler", page_icon="🌙", layout="centered")
st.title("🌙 Dream / Memory Doodler (Streamlit + Gemini + p5.js)")

# Try to import Gemini
USE_GEMINI = True
try:
    import google.generativeai as genai
except Exception:
    USE_GEMINI = False

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if USE_GEMINI and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ---------- UI ----------
prompt = st.text_area(
    "Describe your memory/dream/incident",
    value="I had my birthday yesterday and met a lot of childhood friends — it was a memorable birthday for me.",
    height=120,
    help="One or two sentences is enough."
)

colA, colB = st.columns(2)
with colA:
    do_generate = st.button("Generate")
with colB:
    st.caption("Press the button to (re)generate the visual.")

# Default schema (used on first load or as fallback)
default_schema = {
    "emotion": "warm nostalgia",
    "intensity": 0.8,
    "palette": ["#F79892", "#FFD482", "#C0A5D7"],
    "nodes": 10,
    "caption": "October 25 — Old friends, new laughter"
}
schema = default_schema.copy()

# ---------- LLM call -> JSON schema ----------
if do_generate and USE_GEMINI and GEMINI_API_KEY:
    sys_prompt = (open("identity.txt").read().strip()
                  if os.path.exists("identity.txt") else
                  "Return only valid JSON with keys: emotion, intensity, palette, nodes, caption.")
    user_prompt = f"User memory:\n{prompt}\n\nReturn only the JSON. No prose."

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content([sys_prompt, user_prompt])
        text = resp.text.strip()
        if text.startswith("```"):
            # Strip any code fences
            text = text.strip("`")
            i, j = text.find("{"), text.rfind("}")
            text = text[i:j+1]
        parsed = json.loads(text)

        # Minimal validation / coercion
        schema = {
            "emotion": str(parsed.get("emotion", default_schema["emotion"]))[:40],
            "intensity": float(parsed.get("intensity", default_schema["intensity"])),
            "palette": (parsed.get("palette", default_schema["palette"]) or default_schema["palette"])[:3],
            "nodes": int(parsed.get("nodes", default_schema["nodes"])),
            "caption": str(parsed.get("caption", default_schema["caption"]))[:64],
        }
        # Clamp sensible ranges
        schema["intensity"] = max(0.0, min(1.0, schema["intensity"]))
        schema["nodes"] = max(3, min(20, schema["nodes"]))
    except Exception as e:
        st.warning(f"Gemini parse error; using fallback. ({e})")

# ---------- Embed p5.js ----------
from streamlit.components.v1 import html as st_html

p5_html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    html, body {{ margin:0; padding:0; background:#faf7f5; }}
    #wrap {{ position:relative; width:900px; margin:0 auto; }}
    #btnsave {{
      position:absolute; top:12px; right:12px; z-index:10;
      padding:8px 12px; border:1px solid #d9cbb9; border-radius:8px; background:#fff;
      font-family:system-ui, -apple-system, Segoe UI, Roboto, sans-serif; cursor:pointer;
    }}
    #caption {{
      position:absolute; bottom:10px; right:16px; color:rgba(70,60,65,0.85); font-size:18px;
      font-family:Georgia, serif; pointer-events:none;
      text-shadow:0 1px 0 rgba(255,255,255,0.4);
    }}
    canvas {{ border-radius:12px; box-shadow:0 10px 30px rgba(0,0,0,0.06); }}
  </style>
</head>
<body>
  <div id="wrap">
    <button id="btnsave" onclick="savePNG()">Download PNG</button>
    <div id="p5mount"></div>
    <div id="caption"></div>
  </div>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.4/p5.min.js"></script>
  <script>
    const SCHEMA = {json.dumps(schema)};

    function savePNG() {{
      const c = document.querySelector('canvas');
      if (!c) return;
      const link = document.createElement('a');
      link.download = 'memory_doodle.png';
      link.href = c.toDataURL('image/png');
      link.click();
    }}

    let centerPos, orbitR, nodes = [];
    new p5((p) => {{
      p.setup = function() {{
        const c = p.createCanvas(900, 900);
        c.parent(document.getElementById('p5mount'));
        centerPos = p.createVector(p.width/2, p.height/2);
        orbitR = Math.min(p.width, p.height) * 0.28;
        const N = Math.max(3, Math.min(20, SCHEMA.nodes || 10));
        for (let i=0;i<N;i++) {{
          const a = p.TWO_PI * i / N - p.PI/2;
          nodes.push({{ a, phase: Math.random()*Math.PI*2 }});
        }}
        document.getElementById('caption').textContent = SCHEMA.caption || '';
      }};

      p.draw = function() {{
        drawBackgroundGradient(p, SCHEMA.palette || ["#F79892","#FFD482","#C0A5D7"]);
        p.noFill();

        // Ripples
        p.push();
        p.translate(centerPos.x, centerPos.y);
        const t = p.frameCount * 0.01;
        for (let i=0; i<6; i++) {{
          const r = p.map((t + i*0.35)%1, 0,1, orbitR*0.9, orbitR*1.6);
          p.stroke(255,215,130, p.map(r, orbitR*0.9, orbitR*1.6, 90, 0));
          p.strokeWeight(1.25);
          p.circle(0,0, r*2);
        }}
        p.pop();

        // Threads
        p.stroke(230,180,90,120);
        p.strokeWeight(1.3);
        for (let i=0;i<nodes.length;i++) {{
          const ax = centerPos.x + orbitR * Math.cos(nodes[i].a);
          const ay = centerPos.y + orbitR * Math.sin(nodes[i].a);
          p.line(centerPos.x, centerPos.y, ax, ay);
          const j = (i+1)%nodes.length;
          const bx = centerPos.x + orbitR * Math.cos(nodes[j].a);
          const by = centerPos.y + orbitR * Math.sin(nodes[j].a);
          p.bezier(ax,ay,
                   p.lerp(ax,centerPos.x,0.25), p.lerp(ay,centerPos.y,0.25),
                   p.lerp(bx,centerPos.x,0.25), p.lerp(by,centerPos.y,0.25),
                   bx,by);
        }}

        // Center glow
        drawGlow(p, centerPos.x, centerPos.y, Math.min(p.width,p.height)*0.16, p.color(255,195,80,130));
        p.fill(255,190,70,200); p.noStroke();
        p.circle(centerPos.x, centerPos.y, Math.min(p.width,p.height)*0.11);

        // Nodes (with breathing)
        const baseBreathe = 0.02 + (SCHEMA.intensity ? SCHEMA.intensity*0.02 : 0.016);
        for (let i=0;i<nodes.length;i++) {{
          const a = nodes[i].a;
          const bx = centerPos.x + orbitR * Math.cos(a);
          const by = centerPos.y + orbitR * Math.sin(a);
          const breathe = 4 * Math.sin(p.frameCount*baseBreathe + nodes[i].phase);
          const x = bx + breathe * Math.cos(a) * 2;
          const y = by + breathe * Math.sin(a) * 2;

          p.noFill();
          p.stroke(130,90,60,70);
          p.strokeWeight(2);
          p.circle(x+2, y+2, 56);

          p.fill(255,205,120,170);
          p.stroke(140,90,60,120);
          p.strokeWeight(1.8);
          p.circle(x, y, 46);
        }}
      }};
    }});

    function drawBackgroundGradient(p, palette) {{
      const coral = p.color(palette[0] || "#F79892");
      const gold  = p.color(palette[1] || "#FFD482");
      const lav   = p.color(palette[2] || "#C0A5D7");

      for (let y=0; y<p.height; y++) {{
        const f = y / p.height;
        const c = p.lerpColor(coral, gold, f);
        p.stroke(c); p.line(0,y,p.width,y);
      }}
      p.noStroke();
      for (let r=0; r<600; r++) {{
        const a = p.map(r,0,600,110,0);
        p.fill(p.red(lav), p.green(lav), p.blue(lav), a*0.3);
        p.circle(p.width*0.85, p.height*0.15, r);
      }}
      // Paper noise
      p.loadPixels();
      for (let i=0; i<p.pixels.length; i+=4) {{
        const n = (Math.random()*16)-8;
        p.pixels[i]   = Math.max(0, Math.min(255, p.pixels[i] + n));
        p.pixels[i+1] = Math.max(0, Math.min(255, p.pixels[i+1] + n));
        p.pixels[i+2] = Math.max(0, Math.min(255, p.pixels[i+2] + n));
      }}
      p.updatePixels();
    }}

    function drawGlow(p, x, y, radius, col) {{
      p.noStroke();
      for (let r=radius; r>0; r-=6) {{
        const a = p.map(r,0,radius,220,0);
        p.fill(p.red(col), p.green(col), p.blue(col), a*0.5);
        p.circle(x,y,r*2);
      }}
    }}
  </script>
</body>
</html>
"""
st.components.v1.html(p5_html, height=980, scrolling=False)

st.divider()
st.subheader("Schema used")
st.json(schema)
st.caption("This app converts your text to a visual schema (via Gemini if available) and renders it live with p5.js in the browser.")
