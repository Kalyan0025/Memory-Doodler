import requests

# Replace this with your actual API key from identity.txt
api_key = "gen-lang-client-0836528117"  # Ensure you place the real key here

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
data = {
    "prompt": "A beautiful sunset over the ocean."  # Example prompt
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    print("Image generated:", response.json())
else:
    print(f"Error: {response.status_code} - {response.text}")
