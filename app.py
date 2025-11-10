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
# Session state defaults (auto-generate on type)
# ──────────────────────────────
if "schema" not in st.session_state:
    st.session_state.schema = {
        "emotion": "nostalgia",
        "intensity": 0.8,
        "palette": ["#F79892", "#FFD482", "#C0A5D7"],
        "nodes": 10,
        "caption": "October 25 — Old friends, new laughter",
        "summary": "Special day",
    }
if "date" not in st.session_state:
    st.session_state.date = "October 25, 2025"
if "auto_mode" not in st.session_state:
    st.session_state.auto_mode = True
if "prompt_text" not in st.session_state:
    st.session_state.prompt_text = (
        "I had my birthday yesterday and met a lot of childhood friends — "
        "it was a memorable birthday for me."
    )

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

/* Inputs */
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

/* Button */
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

/* Expander */
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

/* JSON */
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

/* Palette row */
.palette-container {
    display: flex;
    gap: 1rem;
    margin: 1rem 0;
}
.color-swatch {
    flex: 1;
    height: 80px;
    border-radius: 12px;
    border: 3px solid #333;
    box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    transition: all 0.3s ease;
}
.color-swatch:hover { transform: translateY(-5px) rotate(5deg); }

/* Caption */
.caption-display {
    background: #252525;
    border: 3px dashed #444;
    border-radius: 15px;
    padding: 1.5rem;
    margin: 1rem 0;
    font-family: 'Kalam', cursive;
    font-size: 1.3rem;
    color: #b0b0b0;
    text-align: center;
    font-style: italic;
    transform: rotate(-0.5deg);
}

/* Doodle icons */
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
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
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
# Gemini setup (safe + fallback)
# ──────────────────────────────
USE_GEMINI = True
try:
    import google.generativeai as genai
except Exception:
    USE_GEMINI = False

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PREF_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")

available_models, chosen_model = [], None
if USE_GEMINI and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        for m in genai.list_models():
            if "generateContent" in getattr(m, "supported_generation_methods", []):
                if "flash" in m.name and "exp" not in m.name:
                    available_models.append(m.name)
        for c in (PREF_MODEL, f"models/{PREF_MODEL}"):
            if c in available_models:
                chosen_model = c
                break
        if not chosen_model and available_models:
            chosen_model = available_models[0]
    except Exception as e:
        st.warning(f"Model listing failed; fallback. ({e})")
        chosen_model = None
else:
    chosen_model = None

# ──────────────────────────────
# Local fallback schema generator
# ──────────────────────────────
def local_schema_from_text(text: str, default_schema: dict) -> dict:
    t = text.lower()
    EMO = {
        "joy": ["happy", "fun", "birthday", "party", "smile", "laugh"],
        "nostalgia": ["childhood", "old", "school", "remember", "reunion"],
        "calm": ["calm", "peace", "quiet", "relax"],
        "love": ["love", "together", "family", "friends"],
        "sad": ["sad", "alone", "miss", "cry", "loss"],
        "anxiety": ["stress", "worried", "fear", "nervous"],
    }
    counts = {e: sum(t.count(k) for k in kws) for e, kws in EMO.items()}
    emotion = max(counts, key=counts.get) if any(counts.values()) else "nostalgia"

    exclaim = t.count("!")
    caps = sum(1 for w in re.findall(r"[A-Z]{2,}", text) if len(w) > 2)
    intensity = min(1.0, 0.4 + 0.1 * exclaim + 0.05 * caps)

    PALETTES = {
        "joy": ["#FFD482", "#F79892", "#F5B3FF"],
        "nostalgia": ["#F7C6B3", "#EBD8C3", "#C0A5D7"],
        "calm": ["#B9E3FF", "#DDEBF2", "#BFD6C7"],
        "love": ["#FFB3C1", "#FFDDE1", "#FFF0F3"],
        "sad": ["#9DB4C0", "#6C7A89", "#C7D3DD"],
        "anxiety": ["#A3B1C6", "#D6D6D6", "#8A9DB0"],
    }
    palette = PALETTES.get(emotion, default_schema["palette"])

    nodes = 6 if "friend" in t else 4
    for w in ["friends", "family", "group", "team", "all"]:
        if w in t:
            nodes += 2
    nodes = max(3, min(20, nodes))

    caption = "A day to remember"
    if "birthday" in t and "friend" in t:
        caption = "Old friends, new laughter"
    elif "birthday" in t:
        caption = "A day that glowed"
    elif "reunion" in t or "childhood" in t:
        caption = "Back to where we began"

    summary = "Special day"
    if "birthday" in t:
        summary = "Birthday memories"
    elif "friend" in t:
        summary = "Friend reunion"
    elif "childhood" in t:
        summary = "Nostalgic moments"

    return {
        "emotion": emotion,
        "intensity": round(intensity, 2),
        "palette": palette,
        "nodes": int(nodes),
        "caption": caption,
        "summary": summary,
    }

# ──────────────────────────────
# LLM runner (Gemini) with fallback
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
            "emotion": str(data.get("emotion", st.session_state.schema["emotion"]))[:40],
            "intensity": max(0.0, min(1.0, float(data.get("intensity", st.session_state.schema["intensity"])))),
            "palette": (data.get("palette", st.session_state.schema["palette"]) or st.session_state.schema["palette"])[:3],
            "nodes": max(3, min(20, int(data.get("nodes", st.session_state.schema["nodes"])))),
            "caption": str(data.get("caption", st.session_state.schema["caption"]))[:64],
            "summary": str(data.get("summary", "Special day"))[:64],
        }
        return out
    except Exception:
        # Silent fallback; the UI still works via local generator
        return None

# ──────────────────────────────
# Update callback (auto-generate)
# ──────────────────────────────
def update_schema_from_prompt():
    text = st.session_state.get("prompt_text", "").strip()
    date_val = st.session_state.get("date_text", st.session_state.date)
    st.session_state.date = date_val

    llm_schema = run_llm(text) if (GEMINI_API_KEY and chosen_model) else None
    new_schema = llm_schema if llm_schema else local_schema_from_text(text, st.session_state.schema)

    if "caption" in new_schema:
        new_schema["caption"] = new_schema["caption"][:64]
    st.session_state.schema = new_schema

# ──────────────────────────────
# UI Layout - Two Columns
# ──────────────────────────────
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<span class="doodle-icon">🌙</span>', unsafe_allow_html=True)

    st.checkbox("Auto-generate as I type", key="auto_mode", value=True)

    st.text_area(
        "Share Your Memory",
        st.session_state.prompt_text,
        height=200,
        key="prompt_text",
        on_change=update_schema_from_prompt if st.session_state.auto_mode else None,
        help="Tell me about a memory, dream, or moment you'd like to capture..."
    )

    st.text_input(
        "Date of the memory",
        st.session_state.date,
        key="date_text",
        on_change=update_schema_from_prompt if st.session_state.auto_mode else None,
    )

    # Manual button if auto-mode is off
    if not st.session_state.auto_mode:
        if st.button("✨ Transform into Memory DNA ✨"):
            update_schema_from_prompt()

with col2:
    st.markdown('<span class="doodle-icon">🎨</span>', unsafe_allow_html=True)
    st.markdown("**Memory DNA Output**")

# Use current session schema/date
schema = st.session_state.schema
date = st.session_state.date

# Display metadata in col2
with col2:
    st.json(schema)

    st.markdown("**Color Palette**")
    st.markdown(f"""
    <div class="palette-container">
        <div class="color-swatch" style="background: {schema['palette'][0]};"></div>
        <div class="color-swatch" style="background: {schema['palette'][1]};"></div>
        <div class="color-swatch" style="background: {schema['palette'][2]};"></div>
    </div>
    """, unsafe_allow_html=True)

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

    st.markdown(f"""
    <div class="caption-display">
        "{date} — {schema['caption']}"
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────
# Paper.js visualization
# ──────────────────────────────
st.markdown("---")
st.markdown("### 🎨 Your Memory Doodle (Paper.js)")

schema_hash = hashlib.md5(json.dumps(schema, sort_keys=True).encode()).hexdigest()
schema_js = json.dumps(schema, ensure_ascii=True, separators=(",", ":"))

paper_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<meta name='x-schema-hash' content='{schema_hash}'>
<style>
  html,body {{ margin:0; padding:0; background:#1a1a1a; }}
  #wrap {{ position:relative; width:900px; margin:0 auto; }}
  #btnsave {{
    position:absolute; top:12px; right:12px; z-index:10;
    padding:10px 16px; border:3px solid #4ecdc4; border-radius:12px;
    background:linear-gradient(135deg, #4ecdc4 0%, #45b7d1 100%);
    color:#1a1a1a; font-family:'Caveat',cursive; font-size:1.2rem; font-weight:700;
    cursor:pointer; box-shadow:3px 3px 0px #333; transition:all 0.3s ease;
  }}
  #btnsave:hover {{ transform:translate(-2px,-2px); box-shadow:5px 5px 0px #333; }}
  #caption {{
    position:absolute; bottom:10px; right:16px; color:rgba(240,240,240,0.9); font-size:18px;
    font-family:'Kalam',cursive; pointer-events:none; text-shadow:2px 2px 4px rgba(0,0,0,0.8);
  }}
  #summary {{
    position:absolute; bottom:35px; right:16px; color:rgba(78,205,196,0.9); font-size:14px;
    font-family:'Kalam',cursive; text-shadow:2px 2px 4px rgba(0,0,0,0.8);
  }}
  canvas {{ border-radius:15px; box-shadow:0 10px 40px rgba(0,0,0,0.8); border:3px dashed #333; }}
</style>

<!-- Paper.js -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/paper.js/0.12.15/paper-full.min.js"></script>

<!-- Pass schema to window so PaperScript can read it -->
<script>window.SCHEMA = {schema_js};</script>
</head>
<body>
  <div id="wrap">
    <button id="btnsave" onclick="savePNG()">💾 Download PNG</button>
    <canvas id="paper-canvas" resize width="900" height="900"></canvas>
    <div id="caption">{date} — {schema['caption']}</div>
    <div id="summary">{schema['summary']}</div>
  </div>

  <!-- PaperScript -->
  <script type="text/paperscript" canvas="paper-canvas">
    // Read schema from window
    var schema = window.SCHEMA || {{
      palette: ['#F79892', '#FFD482', '#C0A5D7'],
      intensity: 0.8,
      nodes: 10
    }};

    // ---- Parameters derived from schema ----
    var strokeCol  = schema.palette && schema.palette[0] ? schema.palette[0] : '#e4141b';
    var accentCol  = schema.palette && schema.palette[1] ? schema.palette[1] : '#FFD482';
    var glowCol    = schema.palette && schema.palette[2] ? schema.palette[2] : '#C0A5D7';
    var points     = Math.max(3, Math.min(40, (schema.nodes || 10) * 2));
    var length     = 28 + Math.round( (1 - Math.min(1, Math.max(0, schema.intensity || 0))) * 14 );
    var strokeW    = 10 + Math.round( (schema.intensity || 0.5) * 12 );
    var wiggleAmp  = 4 + Math.round( (schema.intensity || 0.5) * 8 );

    // ---- Background gradient ----
    var bg = new Path.Rectangle(view.bounds);
    bg.fillColor = {{
      gradient: {{
        stops: [
          [new Color(0.10, 0.10, 0.10), 0.0],
          [new Color(0.18, 0.18, 0.18), 1.0]
        ]
      }},
      origin: view.bounds.topLeft,
      destination: view.bounds.bottomRight
    }};

    // soft corner glow
    var glow = new Path.Circle(view.bounds.topRight + [-view.bounds.width*0.15, view.bounds.height*0.10], Math.min(view.bounds.width, view.bounds.height)*0.45);
    glow.fillColor = new Color(glowCol);
    glow.fillColor.alpha = 0.06;

    // ---- Follow path ----
    var path = new Path({{ strokeColor: strokeCol, strokeWidth: strokeW, strokeCap: 'round' }});
    var start = view.center / [10, 1];

    for (var i = 0; i < points; i++) {{
      path.add(start + new Point(i * length, 0));
    }}

    // Trails
    var trailCount = 4;
    var trails = [];
    for (var t = 0; t < trailCount; t++) {{
      var tr = new Path({{ strokeColor: new Color(strokeCol), strokeWidth: Math.max(1, strokeW - (t+1)*2), strokeCap: 'round' }});
      tr.opacity = 0.12 - t * 0.02;
      for (var i = 0; i < points; i++) tr.add(path.segments[i].point.clone());
      trails.push(tr);
    }}

    function onMouseMove(event) {{
      path.firstSegment.point = event.point;
      for (var i = 0; i < points - 1; i++) {{
        var segment = path.segments[i];
        var nextSegment = segment.next;
        var vector = segment.point - nextSegment.point;
        vector.length = length;
        nextSegment.point = segment.point - vector;
      }}
      path.smooth({{ type: 'continuous' }});

      for (var t = 0; t < trails.length; t++) {{
        var tr = trails[t];
        for (var i = 0; i < points; i++) {{
          var target = path.segments[i].point;
          var curr   = tr.segments[i].point;
          tr.segments[i].point = curr + (target - curr) * (0.10 - t*0.015);
        }}
        tr.smooth({{ type: 'continuous' }});
      }}
    }}

    function onMouseDown(event) {{
      path.fullySelected = true;
      path.strokeColor = accentCol;
      for (var t = 0; t < trails.length; t++) {{
        trails[t].strokeColor = accentCol;
      }}
    }}

    function onMouseUp(event) {{
      path.fullySelected = false;
      path.strokeColor = strokeCol;
      for (var t = 0; t < trails.length; t++) {{
        trails[t].strokeColor = strokeCol;
      }}
    }}

    // Idle breathing
    var theta = 0;
    function onFrame(event) {{
      theta += (schema.intensity || 0.5) * 0.02 + 0.01;
      var wobble = Math.sin(theta) * wiggleAmp;

      var base = view.center + new Point( Math.cos(theta*1.3)*wobble, Math.sin(theta)*wobble );
      path.firstSegment.point = path.firstSegment.point * 0.94 + base * 0.06;

      for (var i = 0; i < points - 1; i++) {{
        var segment = path.segments[i];
        var nextSegment = segment.next;
        var vector = segment.point - nextSegment.point;
        vector.length = length;
        nextSegment.point = segment.point - vector;
      }}
      path.smooth({{ type: 'continuous' }});

      for (var t = 0; t < trails.length; t++) {{
        var tr = trails[t];
        for (var i = 0; i < points; i++) {{
          var target = path.segments[i].point;
          var curr   = tr.segments[i].point;
          tr.segments[i].point = curr + (target - curr) * (0.04 - t*0.006);
        }}
        tr.smooth({{ type: 'continuous' }});
      }}
    }}
  </script>

  <!-- Export as PNG -->
  <script>
    function savePNG() {{
      var canvas = document.getElementById('paper-canvas');
      if (!canvas) return;
      const link = document.createElement('a');
      link.download = 'memory_doodle.png';
      link.href = canvas.toDataURL('image/png');
      link.click();
    }}
  </script>
</body>
</html>
"""

# Render canvas
try:
    components_html(paper_html, height=980, scrolling=False)
except Exception as e:
    st.error("⚠️ Failed to render Paper.js canvas.")
    st.exception(e)

# Debug
with st.expander("🔧 Debug Info"):
    st.write("**Chosen model:**", chosen_model)
    if available_models:
        st.json(available_models)
    st.write("**Current schema:**")
    st.json(schema)
