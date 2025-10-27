import re, json, hashlib, math
import streamlit as st
import google.generativeai as genai
from vertexai import init as vertexai_init
from vertexai.preview.vision_models import ImageGenerationModel

# ──────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────
st.set_page_config(page_title="Visual Memory — ReCollection-inspired", page_icon="🌀", layout="centered")
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

motion = st.slider("Motion (0 = still)", 0.0, 1.0, 0.0, 0.05)
go = st.button("Generate")

# ──────────────────────────────────────
# 2) Text → schema with expressive axes
# ──────────────────────────────────────
t = story.strip()
seed_text = (t + f"|{motion:.2f}") or "empty"
seed = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16) % 10**9
tl = t.lower()

# Sentiment lexicons
L_POS = ["joy", "happy", "happiness", "love", "laugh", "smile", "grateful", "peace", "calm", "celebrate", "birthday", "friends", "together", "hug", "success", "fun"]
L_NEG = ["sad", "cry", "alone", "lonely", "fear", "anxious", "stress", "angry", "regret", "loss", "hurt", "pain", "miss", "grief", "tired"]
L_HIGH = ["ecstatic", "rush", "party", "dance", "screamed", "wild", "storm", "fireworks", "concert", "goal", "race", "rollercoaster"]
L_LOW = ["quiet", "still", "slow", "breeze", "gentle", "soft", "silent", "night", "dawn", "sunset", "walk", "beach", "rain", "reading"]
L_SOC = ["friends", "family", "together", "team", "crowd", "group", "party", "reunion", "gathering"]
L_NOST = ["yesterday", "childhood", "memories", "remember", "nostalgia", "old", "photo", "photos"]

# Score function
def score(words): 
    return sum(2 if f" {w} " in f" {tl} " else 0 for w in words)

val_raw = score(L_POS) - score(L_NEG)      # >0 = positive
aro_raw = score(L_HIGH) - score(L_LOW)     # >0 = energetic
soc_raw = score(L_SOC) 
nos_raw = score(L_NOST)

# Sigmoid function for scaling
def sig(x): return 1/(1+math.exp(-x/4))

valence   = max(-1.0, min(1.0, (sig(val_raw)-0.5)*2))
arousal   = max(0.0, min(1.0, sig(aro_raw)))
social    = max(0.0, min(1.0, sig(soc_raw)))
nostalgia = max(0.0, min(1.0, sig(nos_raw)))

# ──────────────────────────────────────
# 3) PROMPT BUILDER
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
    elif any(k in story.lower() for k in ["school", "childhood", "photo", "memories"]):
        symbol = "soft silhouettes of children and a glowing photo frame"
    else:
        symbol = "a luminous core representing the essence of memory"

    # Mood palette
    if valence > 0.3 and arousal > 0.5:
        mood = "warm ambers and golden tones symbolizing happiness and reunion"
    elif valence < -0.3 and nostalgia > 0.5:
        mood = "muted violet and silver hues expressing bittersweet emotion"
    else:
        mood = "neutral beige and grey gradients representing calm recollection"

    # Composition
    if social > 0.5:
        composition = "multiple humanoid silhouettes softly dissolving into fog and light"
    else:
        composition = "a single solitary silhouette surrounded by drifting particles"

    return (
        f"{base} Scene: {composition}, illuminated by {symbol}. "
        f"Color palette: {mood}. "
        f"Aesthetic: dreamlike, fog and particulate diffusion, edges softly eroded like a decaying photograph reforming in air."
    )

# ──────────────────────────────────────
# 4) IMAGE GENERATION (USING GEMINI)
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
        aspect_ratio=aspect_ratio,
        guidance_scale=guidance,
        seed=seed_val if seed_val is not None else None,
        safety_filter_level="block_few",    
    )
    return resp.images[0] if resp else None

# ──────────────────────────────────────
# 5) GENERATE VISUAL MEMORY
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
