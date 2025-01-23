import requests
import os

def upload_reference_file(file_path, api_url="http://localhost:5000"):
    """
    Upload a reference audio file to the TTS server
    
    Args:
        file_path (str): Path to the audio file
        api_url (str): Base URL of the API server
    
    Returns:
        dict: Server response
    """
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Prepare the file and filename for upload
    files = {
        'file': open(file_path, 'rb')
    }
    
    data = {
        'filename': os.path.basename(file_path)
    }
    
    try:
        response = requests.post(
            f"{api_url}/upload_reference",
            files=files,
            data=data
        )
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Error uploading file: {str(e)}")
        raise
    finally:
        files['file'].close()

if __name__ == "__main__":
    # Upload kompot.wav
    try:
        result = upload_reference_file("kompot.wav")
        print(f"Upload successful: {result}")
    except Exception as e:
        print(f"Upload failed: {str(e)}")
