from flask import Flask, request, render_template, jsonify
import openai  # Assuming Gemini API is part of OpenAI's platform
from datetime import datetime
import os

app = Flask(__name__)

# Set up the Gemini API key (replace with actual API key)
openai.api_key = "your_api_key"

def generate_image(prompt):
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    return response['data'][0]['url']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    scenario = request.form['scenario']
    emotion = request.form['emotion']
    date = datetime.now().strftime("%b %d, %Y")
    
    # Combine inputs into a prompt for the image generation
    prompt = f"Create a dreamy, emotional scene based on the following scenario: {scenario}. The emotion is {emotion}. Represent the memory visually with appropriate colors and objects."
    
    # Generate the image using the Gemini API
    image_url = generate_image(prompt)
    
    return render_template('result.html', image_url=image_url, date=date, emotion=emotion)

if __name__ == '__main__':
    app.run(debug=True)
