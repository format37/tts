import torch
from TTS.api import TTS
from flask import Flask, request, send_file
import io
import logging
import os

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get device
device = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {device}")

# Init TTS with XTTS v2
try:
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
except Exception as e:
    logger.error(f"Failed to initialize TTS model: {str(e)}")
    raise

@app.route('/tts', methods=['POST'])
def generate_speech():
    try:
        # Get text and language from request
        data = request.get_json()
        if not data or 'text' not in data:
            return {'error': 'No text provided'}, 400
        
        text = data['text']
        language = data.get('language', 'ru')  # Default to Russian if not specified
        reference_file = data.get('reference_file', 'alex.wav')  # Default to alex.wav if not specified
        
        # Construct the full path to the reference file
        source_path = f"./TTS/server/references/{reference_file}"
        
        # Check if the reference file exists
        if not os.path.exists(source_path):
            return {'error': f'Reference file {reference_file} not found'}, 404
        
        # Generate audio
        wav_bytes = io.BytesIO()
                
        tts.tts_to_file(
            text=text,
            speaker_wav=source_path,
            language=language,
            file_path=wav_bytes
        )
        
        wav_bytes.seek(0)
        return send_file(
            wav_bytes,
            mimetype='audio/wav',
            as_attachment=True,
            download_name='output.wav'
        )

    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}")
        return {'error': str(e)}, 500

@app.route('/test', methods=['GET'])
def test():
    return {'status': 'ok', 'message': 'TTS API server is running'}, 200

@app.route('/upload_reference', methods=['POST'])
def upload_reference():
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return {'error': 'No file provided'}, 400
        
        file = request.files['file']
        filename = request.form.get('filename')
        
        # Check if filename was provided
        if not filename:
            return {'error': 'No filename provided'}, 400
            
        # Ensure the references directory exists
        references_dir = "./TTS/server/references"
        os.makedirs(references_dir, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(references_dir, filename)
        file.save(file_path)
        
        logger.info(f"Successfully saved reference file: {filename}")
        return {'status': 'success', 'message': f'File {filename} uploaded successfully'}, 200
        
    except Exception as e:
        logger.error(f"Error uploading reference file: {str(e)}")
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)