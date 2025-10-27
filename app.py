# app.py
# Visual Memory — smoke-like silhouettes × data-humanism (Vertex AI Imagen 3)

import re, math, hashlib
import streamlit as st

# -----------------------------
# Optional Vertex AI imports
# -----------------------------
VERTEX_OK = True
try:
    from vertexai import init as vertexai_init
    from vertexai.preview.vision_models import ImageGenerationModel
except Exception:
    VERTEX_OK = False

st.set_page_config(page_title="Visual Memory — Data Humanism", page_icon="🌀", layout="centered")
st.title("🌀 Visual Memory (smoke silhouettes × data-humanism)")

# -----------------------------
# Inputs
# -----------------------------
story = st.text_area(
    "Whisper your memory (a few sentences work best)",
    "Yesterday was my birthday. I met childhood friends after years; we laughed, took photos, and shared cake.",
    height=150,
)
colA, colB, colC = st.columns(3)
with colA:
    aspect = st.selectbox("Aspect ratio", ["1:1", "4:5", "3:2", "16:9"], index=0)
with colB:
    guidance = st.slider("Style guidance", 0, 100, 55)
with colC:
    deterministic = st.checkbox("Deterministic (seed from story)", True)

go = st.button("Generate")

# -----------------------------
# Emotional features
# -----------------------------
t = (story or "").strip()
seed = int(hashlib.sha256((t or "empty").encode()).hexdigest(), 16) % (2**31 - 1)
tl = f" {t.lower()} "

L_POS = ["joy","happy","happiness","love","laugh","smile","grateful","peace","calm","celebrate","birthday","together","hug","success","fun"]
L_NEG = ["sad","cry","alone","lonely","fear","anxious","stress","angry","regret","loss","breakup","hurt","pain","miss","grief","tired"]
L_HIGH= ["party","dance","festival","rush","crowd","concert","goal","celebration","fireworks"]
L_LOW = ["quiet","still","slow","breeze","soft","silent","night","dawn","sunset","walk","reading","tea","coffee"]
L_SOC = ["friends","family","together","team","crowd","group","party","reunion","gathering"]
L_NOS = ["yesterday","childhood","memories","remember","nostalgia","nostalgic","school","college","old","album","photo"]

def score(words): return sum(2 for w in words if f" {w} " in tl)
sig = lambda x: 1/(1+math.exp(-x/4))
valence   = max(-1.0, min(1.0, (sig(score(L_POS)-score(L_NEG))-0.5)*2))
arousal   = max(0.0, min(1.0, sig(score(L_HIGH)-score(L_LOW))))
social    = max(0.0, min(1.0, sig(score(L_SOC))))
nostalgia = max(0.0, min(1.0, sig(score(L_NOS))))

# lightweight keyword fragments for subtle on-image “text dust”
STOP = set("""a an the and or of for to from is are was were be being been this that those these i me my we our you your he she they them his her their in on at by with without into out about over under after before again more most such very just not no yes it's its""".split())
frags = [w for w in re.findall(r"[A-Za-z]{3,}", t) if w.lower() not in STOP][:8]
frag_text = ", ".join(frags) if frags else "memory, moment, echo"

# -----------------------------
# Prompt builder (no artist names)
# -----------------------------
def choose_symbol(s: str) -> str:
    s = s.lower()
    if any(k in s for k in ["birthday","cake","party","friends"]):
        return "a small glowing birthday cake at the center (replacing any dial)"
    if any(k in s for k in ["beach","ocean","sea","waves"]):
        return "a seashell with concentric water ripples at the center"
    if any(k in s for k in ["loss","alone","lonely","grief"]):
        return "a dim bedside lamp near the figure"
    if any(k in s for k in ["school","childhood","photo","memories"]):
        return "a faint glowing photo frame"
    if any(k in s for k in ["rain","window","reflection","night"]):
        return "a glowing windowpane with soft droplets"
    if any(k in s for k in ["travel","journey","road","flight","train"]):
        return "a distant horizon arc with gentle light trails"
    return "an abstract luminous core"

def mood_palette(v, a, n) -> str:
    if v > 0.3 and a > 0.5: return "warm ambers and candlelight golds with soft peach undertones"
    if v > 0.3 and n > 0.5: return "pastel peach, ivory, and champagne tones"
    if v < -0.3 and n > 0.5: return "muted violet, silver, and cool gray"
    if v < -0.3: return "desaturated cool blues and smoke gray"
    return "balanced neutral beiges with faint peach and gray"

def composition(soc) -> str:
    return ("multiple faint humanoid silhouettes gathered together, bodies leaning toward each other"
            if soc > 0.5 else
            "a single solitary silhouette suspended in memory dust")

def build_prompt(story, v, a, s, n, fragments):
    return (
        "Cinematic generative image of a human memory rendered as softly glowing particles and smoke-like silhouettes. "
        f"Scene: {composition(s)}, illuminated by {choose_symbol(story)}. "
        f"Color palette: {mood_palette(v,a,n)}. "
        "Aesthetic: dreamlike, fog and particulate diffusion, edges softly eroded like a decaying photograph reforming in air. "
        "Subtle data-humanism layer integrated into the scene: gentle horizontal scanlines, faint concentric radial ticks, "
        f"and a few tiny floating word fragments from the memory (“{fragments}”), blended into the atmosphere (no harsh UI). "
        "Dark background with a central bloom of light; no logos; no big readable text; not photorealistic."
    )

prompt_text = build_prompt(t, valence, arousal, social, nostalgia, frag_text)

# -----------------------------
# Vertex AI call
# -----------------------------
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
    if not resp or not getattr(resp, "images", None):
        raise RuntimeError("No image returned.")
    img_obj = resp.images[0]
    # SDKs differ: try both attrs
    return getattr(img_obj, "_image_bytes", None) or getattr(img_obj, "image_bytes", None)

# -----------------------------
# Run
# -----------------------------
if go:
    st.subheader("Generated Prompt")
    st.code(prompt_text)

    try:
        if not VERTEX_OK:
            raise RuntimeError("google-cloud-aiplatform / Vertex AI SDK not available. Install it and restart.")
        img_bytes = generate_with_vertex(
            prompt=prompt_text,
            aspect_ratio=aspect,
            guidance=guidance,
            seed_val=seed if deterministic else None
        )
        st.image(img_bytes, caption="Reconstructed Visual Memory", use_column_width=True)
    except Exception as e:
        st.error(f"Image generation error: {e}")
        st.caption("Make sure Vertex AI is enabled, you're authenticated, and `.streamlit/secrets.toml` has GCP_PROJECT_ID & GCP_LOCATION.")
    st.markdown("---")
    st.caption(f"Valence {valence:.2f} • Arousal {arousal:.2f} • Social {social:.2f} • Nostalgia {nostalgia:.2f}")
else:
    st.info("Type your memory and click **Generate**. The image blends smoke-like human silhouettes with subtle data-humanism motifs.\n"
            "Tip: for birthdays, the circular dial is replaced with a glowing cake automatically.")
