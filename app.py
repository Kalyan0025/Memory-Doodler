import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from PIL import Image
from io import BytesIO

# Function to get API key from identity.txt
def get_api_key():
    with open("identity.txt", "r") as f:
        return f.read().strip()  # Reads the API key from identity.txt

# Function to load bot rules from bot_rules.xml
def load_bot_rules():
    # Parse the XML file
    tree = ET.parse('bot_rules.xml')
    root = tree.getroot()

    # Extract elements from the XML
    role = root.find('Role').text
    goal = root.find('Goal').text
    rules = root.find('Rules').text
    knowledge = root.find('Knowledge').text
    specialized_actions = root.find('SpecializedActions').text
    guidelines = root.find('Guidelines').text

    # Return bot rules as a dictionary
    return {
        "Role": role,
        "Goal": goal,
        "Rules": rules,
        "Knowledge": knowledge,
        "SpecializedActions": specialized_actions,
        "Guidelines": guidelines
    }

# Function to generate image using the Gemini API
def generate_image(prompt):
    api_key = get_api_key()

    # Check if the API key is correctly loaded
    if not api_key:
        st.error("API key is missing or incorrect!")
        return None

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent"  # Correct API URL
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Prepare the request payload
    data = {
        "prompt": prompt,
        "temperature": 0.7,  # You can adjust this as needed
        "maxOutputTokens": 1024  # You can adjust the number of tokens if needed
    }

    try:
        # Send the POST request to Gemini API
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raises an error for 4xx/5xx responses

        if response.status_code == 200:
            # Extract the image URL from the response (adjust if structure differs)
            response_data = response.json()
            if 'content' in response_data and 'image_url' in response_data['content']:
                return response_data['content']['image_url']
            else:
                st.error(f"Error: Image URL not found in response. {response_data}")
                return None
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error making request: {e}")
        return None

# Streamlit front-end
def main():
    # Load the bot's rules from XML
    bot_rules = load_bot_rules()

    st.title("DreamDoodler - Visual Journal")

    # Display the bot's role and goal (optional, for debugging or information)
    st.write(f"**Bot Role**: {bot_rules['Role']}")
    st.write(f"**Bot Goal**: {bot_rules['Goal']}")

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
