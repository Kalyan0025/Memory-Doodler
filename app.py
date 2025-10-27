import re, json, hashlib, math
import streamlit as st
import google.generativeai as genai
from vertexai import init as vertexai_init
from vertexai.preview.vision_models import ImageGenerationModel

# ──────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────
st.set_page_config(page_title="Visual Memory — ReCollection", page_icon="🌀", layout="centered")
st.title("🌀 Visual Memory (ReCollection × Data Humanism)")

# Configure Gemini API key
genai.configure(api_key=st.secrets.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE"))

# ──────────────────────────────────────
# INPUT: User Memory
# ──────────────────────────────────────
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

go = st.button("Generate Visual Memory")

# ──────────────────────────────────────
# FEATURE EXTRACTION
# ──────────────────────────────────────
t = story.strip()
seed_text = (t + f"|{motion:.2f}|{smoke:.2f}|{brightness:.2f}") or "empty"
seed = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16) % (2**31 - 1)

# Positive and Negative Word Lists for Scoring
L_POS = ["joy", "happy", "happiness", "love", "laugh", "smile", "grateful", "peace", "calm", "celebrate", "birthday", "together", "hug", "success", "fun"]
L_NEG = ["sad", "cry", "alone", "lonely", "fear", "anxious", "stress", "angry", "regret", "loss", "breakup", "hurt", "pain", "miss", "grief", "tired"]
L_HIGH = ["party", "dance", "festival", "rush", "screamed", "crowd", "concert", "goal", "celebration", "fireworks"]
L_LOW = ["quiet", "still", "slow", "breeze", "gentle", "soft", "silent", "night", "dawn", "sunset", "walk", "beach", "library", "rain", "reading", "meditate", "tea", "coffee"]
L_SOC = ["friends", "family", "together", "team", "crowd", "group", "party", "reunion", "gathering"]
L_NOST = ["yesterday", "childhood", "memories", "remember", "nostalgia", "nostalgic", "school", "college", "old", "grandma", "album", "photo", "photos", "vintage"]

def score(words): 
    return sum(2 if f" {w} " in f" {t.lower()} " else 0 for w in words)

# Emotional Scores
val_raw = score(L_POS) - score(L_NEG)
aro_raw = score(L_HIGH) - score(L_LOW)
soc_raw = score(L_SOC) 
nos_raw = score(L_NOST)

# Sigmoid function for scaling
def sig(x): return 1/(1+math.exp(-x/4))

valence = max(-1.0, min(1.0, (sig(val_raw)-0.5)*2))
arousal = max(0.0, min(1.0, sig(aro_raw)))
social = max(0.0, min(1.0, sig(soc_raw)))
nostalgia = max(0.0, min(1.0, sig(nos_raw)))

# ──────────────────────────────────────
# PROMPT BUILDER FOR GEMINI
# ──────────────────────────────────────
def build_visual_prompt(story, valence, arousal, social, nostalgia):
    base = (
        "A cinematic generative artwork inspired by Weidi Zhang’s 'ReCollection' and Giorgia Lupi’s data humanism — "
        "depicting memories as glowing particles and soft smoke-like silhouettes, blending art and emotion."
    )
    
    # Symbolic element
    if any(k in story.lower() for k in ["birthday", "cake", "party", "friends"]):
        symbol = "a small glowing birthday cake at the center"
    elif any(k in story.lower() for k in ["beach", "ocean", "sea", "waves"]):
        symbol = "a glowing seashell radiating warmth"
    elif any(k in story.lower() for k in ["loss", "alone", "lonely", "grief"]):
        symbol = "a dim lamp near a solitary figure"
    elif any(k in story.lower() for k in ["travel", "journey", "road", "flight", "train"]):
        symbol = "a faint horizon fading into light trails"
    elif any(k in story.lower() for k in ["school", "childhood", "photo", "memories"]):
        symbol = "soft silhouettes of children and a glowing photo frame"
    elif any(k in story.lower() for k in ["rain", "window", "reflection", "night"]):
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

    return (
        f"{base} Scene: {composition}, illuminated by {symbol}. "
        f"Color palette: {mood}. "
        f"Aesthetic: dreamlike, fog and particulate diffusion, edges softly eroded like a decaying photograph reforming in air. "
        f"Subtle data-humanism layer integrated into the scene: gentle horizontal scanlines, faint concentric radial ticks, "
        f"and a few tiny floating word fragments from the memory (“{', '.join(story.split())}”), blended into the atmosphere (no harsh UI)."
        f" Dark background with a central bloom of light; no logos; no big readable text; not photorealistic."
    )

# ──────────────────────────────────────
# IMAGE GENERATION USING GEMINI
# ──────────────────────────────────────
def generate_with_vertex(prompt: str, aspect_ratio: str, guidance: int, seed_val: int|None):
    project_id = st.secrets.get("GCP_PROJECT_ID")
    location   = st.secrets.get("GCP_LOCATION", "us-central1")
    if not project_id:
        raise RuntimeError("Missing GCP_PROJECT_ID in .streamlit/secrets.toml")
    vertexai_init(project=project_id, location=location)
    model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
    resp = model.generate_images(
        prompt=prompt,
        number_of_images=1,
        aspect_ratio=aspect_ratio,     # "1:1","4:5","3:2","16:9"
        guidance_scale=guidance,       # 0–100
        seed=seed_val if seed_val is not None else None,
        safety_filter_level="block_few",    
    )
    return resp.images[0] if resp else None

# ──────────────────────────────────────
# GENERATE IMAGE (Gemini)
# ──────────────────────────────────────
if go:
    prompt_text = build_visual_prompt(t, valence, arousal, social, nostalgia)
    st.markdown("### 🪞 Generated Prompt")
    st.code(prompt_text, language="markdown")
    
    try:
        model = genai.GenerativeModel("imagen-3.0")
        with st.spinner("Reconstructing your visual memory..."):
            result = model.generate_images(prompt=prompt_text, num_images=1)
            image_data = result[0]
            st.image(image_data, caption="✨ ReCollection-inspired Memory", use_column_width=True)

        img_bytes = generate_with_vertex(
            prompt=prompt_text,
            aspect_ratio="1:1", 
            guidance=60, 
            seed_val=seed if True else None
        )
        st.image(img_bytes, caption="Reconstructed Visual Memory", use_column_width=True)

    except Exception as e:
        st.error(f"Gemini API error: {e}")
        st.error(f"Image generation error: {e}")
        st.caption("Make sure Vertex AI is enabled, you're authenticated, and `.streamlit/secrets.toml` has GCP_PROJECT_ID & GCP_LOCATION.")

else:
    st.info("Type your memory and click **Generate Visual Memory** to create a smoke-like emotional reconstruction.")
