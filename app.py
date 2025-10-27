import re
import json
import hashlib
import math
import streamlit as st
from streamlit.components.v1 import html as components_html

# ──────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────
st.set_page_config(page_title="Memory Doodler — Visual Memory Card", page_icon="🧠", layout="centered")
st.title("🧠 Visual Memory Card (Data-Humanism Inspired)")

# ──────────────────────────────────────
# 1) INPUT: Memory Story and Emotion Data
# ──────────────────────────────────────
story = st.text_area(
    "Whisper your memory (a few sentences work best)",
    "Yesterday was my birthday. I met childhood friends after years; we laughed, took photos, and shared cake.",
    height=140,
)
motion = st.slider("Motion (0 = still)", 0.0, 1.0, 0.0, 0.05)
go = st.button("Generate")

# ──────────────────────────────────────
# 2) Text Processing → Feature Extraction → Schema
# ──────────────────────────────────────
t = story.strip()
seed_text = t if t else "empty"
seed_text = (t + f"|{motion:.2f}") or "empty"
seed = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16) % 10**9
tl = t.lower()

# Define sentiment lexicons
L_POS = ["joy", "happy", "happiness", "love", "laugh", "smile", "grateful", "peace", "calm", "celebrate", "birthday", "friends", "together", "hug", "success", "fun"]
L_NEG = ["sad", "cry", "alone", "lonely", "fear", "anxious", "stress", "angry", "regret", "loss", "hurt", "pain", "miss", "grief", "tired"]
L_HIGH = ["ecstatic", "rush", "party", "dance", "screamed", "wild", "storm", "fireworks", "concert", "goal", "race", "rollercoaster"]
L_LOW = ["quiet", "still", "slow", "breeze", "gentle", "soft", "silent", "night", "dawn", "sunset", "walk", "beach", "rain", "reading"]

# Calculate sentiment scores
def score(words): 
    return sum(2 if f" {w} " in f" {tl} " else 0 for w in words)

val_raw = score(L_POS) - score(L_NEG)  # >0 = positive
aro_raw = score(L_HIGH) - score(L_LOW)  # >0 = energetic
valence = max(-1.0, min(1.0, (val_raw - 0.5) * 2))
arousal = max(0.0, min(1.0, aro_raw / 2))
social = max(0.0, min(1.0, score(["friends", "family", "together"]) / 10))
nostalgia = max(0.0, min(1.0, score(["childhood", "memories", "nostalgia"]) / 10))

# ──────────────────────────────────────
# 3) p5.js Code with Token Replacement
# ──────────────────────────────────────

def build_visual_prompt():
    return {
        "valence": round(valence, 3),
        "arousal": round(arousal, 3),
        "social": round(social, 3),
        "nostalgia": round(nostalgia, 3),
        "story": story,
        "motion": motion,
    }

# Convert the visual prompt to JSON
visual_prompt = build_visual_prompt()

# Display the JSON in Streamlit
st.json(visual_prompt)

# ──────────────────────────────────────
# 4) p5.js Integration with Streamlit (using Streamlit Components)
# ──────────────────────────────────────
# Embed the p5.js code as HTML (via streamlit.components.v1.html)
SCHEMA_JS = json.dumps(visual_prompt, separators=(",", ":"))

p5_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <meta name="x-schema-hash" content="__HASH__"/>
    <style>
        html, body {{ margin:0; padding:0; background:#0f1115; }}
        #card {{ width: 980px; height: 980px; margin: 24px auto; background: #faf7f5; border-radius: 28px; box-shadow: 0 16px 40px rgba(0,0,0,0.20); }}
        #chrome {{ position:absolute; top:0; left:0; right:0; height: 64px; background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(255,255,255,0.60)); border-top-left-radius: 28px; }}
        #p5mount {{ position:absolute; top:64px; left:0; right:0; bottom:56px; }}
        #footer {{ position:absolute; left:0; right:0; bottom:0; height:56px; display:flex; justify-content:space-between; padding:0 16px; color:#6a5e55; font: 12px system-ui; }}
    </style>
</head>
<body>
    <div id="card">
        <div id="chrome">
            <div id="title">Visual Memory</div><div id="subtitle">ReCollection-inspired</div>
        </div>
        <div id="p5mount"></div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.4/p5.min.js"></script>
    <script>
    const SCHEMA = __SCHEMA__;

    new p5((p) => {{
        const W=980, H=980;
        const inner = {{x:0, y:64, w:W, h:H-64-56}};
        const [A,B,C] = (SCHEMA.palette||["#FFD482", "#F79892", "#C0A5D7"]).map(h=>p.color(h));
        const valence = SCHEMA.valence || 0;
        const arousal = SCHEMA.arousal || 0;
        const social = SCHEMA.social || 0;
        const nostalgia = SCHEMA.nostalgia || 0;

        p.setup = function() {{
            const c = p.createCanvas(W, H);
            c.parent(document.getElementById('p5mount'));
        }};

        p.draw = function() {{
            p.background(0);

            // Example: Create circles based on emotion data
            p.fill(255, 100 + valence * 100, 100 + arousal * 100);
            p.ellipse(W / 2, H / 2, 300 + nostalgia * 200, 300 + social * 200);

            // Example of using "motion" value to add dynamic changes
            if (SCHEMA.motion > 0) {{
                p.fill(255, 50, 50, 150);
                p.circle(p.mouseX, p.mouseY, 50 + SCHEMA.motion * 20);
            }}
        }};
    }});
    </script>
</body>
</html>
"""

p5_html = p5_html.replace("__HASH__", hashlib.md5(SCHEMA_JS.encode()).hexdigest())
p5_html = p5_html.replace("__SCHEMA__", SCHEMA_JS)

if go:
    components_html(p5_html, height=1060, scrolling=False)
else:
    st.info("Type your memory and click **Generate**. The card adapts to valence, arousal, socialness, and nostalgia; visuals are deterministic per story.")
