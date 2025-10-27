import requests

# Replace this with your actual API key from identity.txt
api_key = "gen-lang-client-0836528117"  # Ensure you place the real key here

# Print a message to verify that the script is starting
print("Starting the script...")

# Check if API key is being read correctly
if not api_key:
    print("API key is missing or incorrect!")
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

# Add a print statement to check if the request is sent properly
print("Sending request to Gemini API...")

try:
    # Send the POST request to Gemini API
    response = requests.post(url, headers=headers, json=data)
    
    # Print status code for debugging
    print("Response status code:", response.status_code)
    
    # Check if the status code is 200 (success)
    if response.status_code == 200:
        print("Image generated successfully!")
        print("Response:", response.json())  # Print the JSON response
    else:
        print(f"Error: {response.status_code} - {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
