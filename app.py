# app.py
import re, json, hashlib, math, google.generativeai as genai
import streamlit as st

# ──────────────────────────────
# CONFIG
# ──────────────────────────────
st.set_page_config(page_title="Visual Memory — ReCollection", page_icon="🌀", layout="centered")
st.title("🌀 Visual Memory (ReCollection × Data Humanism)")

# Set Gemini API key
genai.configure(api_key=st.secrets.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE"))

# ──────────────────────────────
# 1. INPUT
# ──────────────────────────────
story = st.text_area(
    "Whisper your memory (a few sentences work best)",
    "Yesterday was my birthday. I met childhood friends after years; we laughed, took photos, and shared cake.",
    height=140,
)
go = st.button("Generate Visual Memory")

# ──────────────────────────────
# 2. FEATURE EXTRACTION
# ──────────────────────────────
t = story.strip()
seed_text = t or "empty"
seed = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16) % 10**9
tl = t.lower()

L_POS = ["joy","happy","happiness","love","laugh","smile","proud","grateful","peace","serene","calm","beautiful","celebrate","birthday","friends","together","hug","kiss","success","fun"]
L_NEG = ["sad","cry","alone","lonely","fear","anxious","stress","angry","regret","loss","lost","breakup","hurt","pain","miss","grief","tired"]
L_HIGH = ["party","dance","festival","rush","screamed","crowd","concert","goal","celebration","fireworks"]
L_LOW  = ["quiet","still","slow","breeze","soft","silent","night","dawn","sunset","walk","beach","reading","tea","coffee"]
L_SOC  = ["friends","family","together","team","crowd","group","party","reunion","gathering"]
L_NOST = ["yesterday","childhood","memories","remember","nostalgia","nostalgic","school","college","old","grandma","album","photo"]

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

# ──────────────────────────────
# 3. PROMPT BUILDER (Gemini)
# ──────────────────────────────
def build_visual_prompt(story, valence, arousal, social, nostalgia):
    base = (
        "A cinematic generative artwork inspired by Weidi Zhang’s 'ReCollection' and Giorgia Lupi’s data humanism — "
        "depicting memories as glowing particles and soft smoke-like silhouettes, blending art and emotion."
    )

    # Symbolic element
    if any(k in story.lower() for k in ["birthday","cake","party","friends"]):
        symbol = "a small glowing birthday cake at the center"
    elif any(k in story.lower() for k in ["beach","ocean","sea","waves"]):
        symbol = "a glowing seashell radiating warmth"
    elif any(k in story.lower() for k in ["loss","alone","lonely","grief"]):
        symbol = "a dim lamp near a solitary figure"
    elif any(k in story.lower() for k in ["travel","journey","road","flight","train"]):
        symbol = "a faint horizon fading into light trails"
    elif any(k in story.lower() for k in ["school","childhood","photo","memories"]):
        symbol = "soft silhouettes of children and a glowing photo frame"
    elif any(k in story.lower() for k in ["rain","window","reflection","night"]):
        symbol = "a glowing windowpane with droplets reflecting memory"
    else:
        symbol = "a luminous core representing the essence of memory"

    # Mood palette
    if valence > 0.3 and arousal > 0.5:
        mood = "warm ambers and golden tones symbolizing happiness and reunion"
    elif valence > 0.3 and nostalgia > 0.5:
        mood = "pastel peach and soft candlelight tones evoking warmth and memory"
    elif valence < -0.3 and nostalgia > 0.5:
        mood = "muted violet and silver hues expressing bittersweet emotion"
    elif valence < -0.3:
        mood = "cool desaturated blues evoking isolation and distance"
    else:
        mood = "neutral beige and grey gradients representing calm recollection"

    # Composition
    if social > 0.5:
        composition = "multiple humanoid silhouettes softly dissolving into fog and light"
    else:
        composition = "a single solitary silhouette surrounded by drifting particles"

    # Smoke / diffusion emphasis
    texture = (
        "made of luminous smoke, ethereal mist, and memory dust — like decaying photographs reforming in air. "
        "Soft diffusion, fog particles, and glowing edges enhance a dreamlike sense of time and emotion."
    )

    final_prompt = (
        f"{base} Scene: {composition}, illuminated by {symbol}. "
        f"The mood is {mood}. The aesthetic is emotional, abstract, and cinematic — {texture} "
        "The image should look like an AI recollection of a fading human memory, not literal or realistic."
    )
    return final_prompt

prompt_text = build_visual_prompt(t, valence, arousal, social, nostalgia)

# ──────────────────────────────
# 4. GENERATE IMAGE (Gemini)
# ──────────────────────────────
if go:
    st.markdown("### 🪞 Generated Prompt")
    st.code(prompt_text, language="markdown")

    try:
        model = genai.GenerativeModel("imagen-3.0")  # for Gemini image generation
        with st.spinner("Reconstructing your visual memory..."):
            result = model.generate_image(prompt=prompt_text)
            image_data = result.image
            st.image(image_data, caption="✨ ReCollection-inspired Memory", use_column_width=True)
    except Exception as e:
        st.error(f"Gemini API error: {e}")

    st.markdown("---")
    st.caption(
        f"**Emotional signature:** "
        f"Valence {valence:.2f} | Arousal {arousal:.2f} | Social {social:.2f} | Nostalgia {nostalgia:.2f}"
    )

else:
    st.info("Type your memory and click **Generate Visual Memory** to create a smoke-like emotional reconstruction.")
