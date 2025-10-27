import streamlit as st
import requests
from datetime import datetime
from PIL import Image
from io import BytesIO

# Function to get API key from identity.txt
def get_api_key():
    with open("identity.txt", "r") as f:
        return f.read().strip()

# Function to generate image using the Gemini API
def generate_image(prompt):
    api_key = get_api_key()

    # Check if the API key is correctly loaded
    if not api_key:
        st.error("API key is missing or incorrect!")
        return None

    url = "https://api.gemini.com/v1/generate"  # Replace with correct Gemini API URL
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024"  # Or the size you prefer
    }

    try:
        # Send the POST request to Gemini API
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raises an error for 4xx/5xx responses

        if response.status_code == 200:
            return response.json()['data'][0]['url']
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error making request: {e}")
        return None

# Streamlit front-end
def main():
    st.title("DreamDoodler - Visual Journal")

    # User inputs
    st.write("Please describe your dream, memory, or scenario:")
    scenario = st.text_area("Scenario Description")
    
    st.write("What emotion does it evoke?")
    emotion = st.text_input("Emotion (e.g., joyful, nostalgic, sad, etc.)")

    # Generate button
    if st.button("Generate Visual"):
        if scenario and emotion:
            date = datetime.now().strftime("%b %d, %Y")
            prompt = f"Create a dreamy, emotional scene based on the following scenario: {scenario}. The emotion is {emotion}. Represent the memory visually with appropriate colors and objects."
            image_url = generate_image(prompt)

            if image_url:
                # Display the image
                st.image(image_url, caption=f"Generated Image - {date}", use_column_width=True)
                st.write(f"Date: {date}")
                st.write(f"Emotion: {emotion}")
                
                # Provide a download button
                response = requests.get(image_url)
                img = Image.open(BytesIO(response.content))
                img_path = "generated_image.png"
                img.save(img_path)

                with open(img_path, "rb") as file:
                    st.download_button(
                        label="Download Image",
                        data=file,
                        file_name="dream_visual.png",
                        mime="image/png"
                    )
        else:
            st.error("Please provide both scenario and emotion.")

if __name__ == "__main__":
    main()
