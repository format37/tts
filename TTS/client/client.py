import requests
import json

def generate_speech(text, language='ru', reference_file='alex.wav'):
    # API endpoint
    url = 'http://localhost:5000/tts'
    
    # Request payload
    payload = {
        'text': text,
        'language': language,
        'reference_file': reference_file
    }
    
    try:
        # Send POST request
        response = requests.post(url, json=payload)
        
        # Check if request was successful
        if response.status_code == 200:
            # Save the audio file
            output_filename = 'output.wav'
            with open(output_filename, 'wb') as f:
                f.write(response.content)
            print(f"Audio saved as {output_filename}")
        else:
            print(f"Error: {response.json().get('error', 'Unknown error')}")
            
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {str(e)}")

if __name__ == "__main__":
    # Example Russian text
    text = "Привет, как дела?"
    
    # Generate speech
    generate_speech(text)
