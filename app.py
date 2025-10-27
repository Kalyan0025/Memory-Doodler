import os
import requests
import mimetypes
import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

# Get API key (ensure it's loaded properly)
api_key = "your_actual_gemini_api_key_here"  # Use your actual API key here

def save_binary_file(file_name, data):
    """Function to save binary data to a file"""
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"File saved to: {file_name}")

def generate_image(user_prompt):
    """Function to generate image using the Gemini API"""
    client = genai.Client(api_key=api_key)
    
    model = "gemini-2.5-flash-image"  # Your model
    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=user_prompt)],  # Directly use the 'text' parameter
        ),
    ]
    
    generate_content_config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"]  # Expecting IMAGE and TEXT responses
    )

    file_index = 0  # Counter for multiple image files
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if (
            chunk.candidates is None
            or chunk.candidates[0].content is None
            or chunk.candidates[0].content.parts is None
        ):
            continue
        
        # Checking if inline data exists (image binary data)
        if chunk.candidates[0].content.parts[0].inline_data:
            inline_data = chunk.candidates[0].content.parts[0].inline_data
            file_name = f"generated_image_{file_index}"  # Increment file name if multiple images are generated
            file_index += 1
            file_extension = mimetypes.guess_extension(inline_data.mime_type)
            save_binary_file(f"{file_name}{file_extension}", inline_data.data)
            return f"{file_name}{file_extension}"
        else:
            print(chunk.text)  # Print any error message if the image data is not available

def main():
    st.title("DreamDoodler - Visual Journal")

    # User input
    scenario = st.text_area("Scenario Description")
    emotion = st.text_input("Emotion (e.g., joyful, nostalgic, sad, etc.)")

    # Generate button
    if st.button("Generate Visual"):
        if scenario and emotion:
            # Create the prompt based on user input
            prompt = f"Create a dreamy, emotional scene based on the following scenario: {scenario}. The emotion is {emotion}."
            # Call the image generation function
            image_file = generate_image(prompt)

            if image_file:
                # Open and display the generated image in Streamlit
                image = Image.open(image_file)
                st.image(image, caption="Generated Image", use_column_width=True)

                # Provide download button for the generated image
                with open(image_file, "rb") as file:
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
