import os, json, hashlib
import streamlit as st
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import requests
import io

# ──────────────────────────────
# Setup
# ──────────────────────────────
st.set_page_config(page_title="Dream/Memory Doodler", page_icon="🌙", layout="centered")
st.title("🌙 Dream / Memory Doodler — Visual Journal")

# ──────────────────────────────
# File upload and text input
# ──────────────────────────────
narration = st.text_area("Enter your narration", "Describe your memory or dream...")
date = st.text_input("Enter the date", "October 25")

# ──────────────────────────────
# Generate visual journal
# ──────────────────────────────
def generate_journal_image(narration, date):
    # Create a base image
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color=(255, 255, 255))  # white background
    draw = ImageDraw.Draw(img)

    # Add visual design (abstract, colorful, or whatever your app generates)
    draw.rectangle([50, 50, 750, 550], outline="orange", width=6)  # just a simple design

    # Add date and narration text at the bottom
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Example font
    try:
        font = ImageFont.truetype(font_path, 36)  # You can replace this with any font you prefer
    except IOError:
        font = ImageFont.load_default()  # fallback if the font file is not available

    # Set the padding
    text = f"{date} - {narration}"

    # Add the text to the image (bottom-left corner)
    text_width, text_height = draw.textsize(text, font=font)
    position = (width - text_width - 30, height - text_height - 30)
    draw.text(position, text, font=font, fill=(255, 255, 255))  # white color

    return img

# Generate the image
if st.button("Generate Visual Journal"):
    journal_image = generate_journal_image(narration, date)
    st.image(journal_image, caption="Your Visual Journal Entry", use_column_width=True)
