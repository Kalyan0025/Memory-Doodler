import requests

# Replace this with your actual API key from identity.txt
api_key = "your_actual_gemini_api_key_here"  # Ensure you place the real key here

# Check if API key is loaded correctly
if not api_key:
    print("Error: API key is missing or incorrect!")
else:
    print("API key is loaded correctly.")

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
data = {
    "prompt": "A beautiful sunset over the ocean."  # Example prompt
}

# Add print statements to confirm script execution
print("Sending request to Gemini API...")

try:
    # Send the POST request to Gemini API
    response = requests.post(url, headers=headers, json=data)
    
    # Print the status code for debugging
    print(f"Response status code: {response.status_code}")
    
    # Check if the status code is 200 (success)
    if response.status_code == 200:
        print("Image generated successfully!")
        print("Response:", response.json())  # Print the JSON response
    else:
        print(f"Error: {response.status_code} - {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
