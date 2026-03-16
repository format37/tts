import torch
from flask import Flask, request, send_file
import io
import re
import logging as local_logging
import os

# Initialize Flask app
app = Flask(__name__)

# Configure logging
local_logging.basicConfig(
    level=local_logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        local_logging.StreamHandler()  # Log to stdout/stderr for Docker
    ]
)

logger = local_logging.getLogger(__name__)

# Fix the PyTorch 2.6+ weights_only issue by adding the required classes to safe globals
try:
    import torch.serialization
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import XttsAudioConfig
    
    # Add both classes to safe globals
    torch.serialization.add_safe_globals([XttsConfig, XttsAudioConfig])
    logger.info("Applied PyTorch serialization fix for XttsConfig and XttsAudioConfig")
except Exception as e:
    logger.warning(f"Failed to apply serialization fix: {str(e)}")

# Monkey patch torch.load to use weights_only=False by default
original_torch_load = torch.load

def patched_torch_load(f, map_location=None, pickle_module=None, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return original_torch_load(f, map_location=map_location, pickle_module=pickle_module, **kwargs)

# Replace torch.load with our patched version
torch.load = patched_torch_load
logger.info("Patched torch.load to use weights_only=False by default")

# Get device
device = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {device}")

from TTS.api import TTS

# Init TTS with XTTS v2
try:
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    logger.info("Successfully initialized TTS model")
except Exception as e:
    logger.error(f"Failed to initialize TTS model: {str(e)}")
    raise

def split_long_sentence(sentence, max_chars=250):
    """Split a sentence that's too long at natural break points."""
    if len(sentence) <= max_chars:
        return [sentence]

    chunks = []
    # Split at em-dash, semicolon, comma+space — in that priority
    delimiters = [' — ', '; ', ', ']

    remaining = sentence
    while len(remaining) > max_chars:
        best_pos = -1
        best_delim = ''
        for delim in delimiters:
            # Find the last occurrence of delimiter before max_chars
            pos = remaining.rfind(delim, 0, max_chars)
            if pos > best_pos:
                best_pos = pos
                best_delim = delim

        if best_pos > 0:
            chunks.append(remaining[:best_pos + len(best_delim)].strip())
            remaining = remaining[best_pos + len(best_delim):].strip()
        else:
            # No good break point found, force split at max_chars on a space
            pos = remaining.rfind(' ', 0, max_chars)
            if pos > 0:
                chunks.append(remaining[:pos].strip())
                remaining = remaining[pos:].strip()
            else:
                # No space found, just split hard
                chunks.append(remaining[:max_chars].strip())
                remaining = remaining[max_chars:].strip()

    if remaining:
        chunks.append(remaining.strip())

    return chunks


def preprocess_text(text):
    """Split text into chunks safe for XTTS (under 400 tokens each)."""
    # Split into sentences first (by period, !, ?)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        result.extend(split_long_sentence(sentence))
    return ' '.join(result)


@app.route('/tts', methods=['POST'])
def generate_speech():
    try:
        logger.info("Generate speech endpoint called")
        # Get text and language from request
        data = request.get_json()
        if not data or 'text' not in data:
            return {'error': 'No text provided'}, 400

        text = data['text']
        logger.info(f"Text length: {len(text)} chars")
        language = data.get('language', 'ru')  # Default to Russian if not specified
        logger.info(f"Language: {language}")
        reference_file = data.get('reference_file', 'alex.wav')  # Default to alex.wav if not specified
        # Construct the full path to the reference file
        source_path = f"./TTS/server/references/{reference_file}"
        # Check if the reference file exists
        if not os.path.exists(source_path):
            reference_file = 'alex.wav'
            source_path = f"./TTS/server/references/{reference_file}"
        logger.info(f"Reference file: {reference_file}")

        # Check if the reference file exists
        if not os.path.exists(source_path):
            return {'error': f'Reference file {reference_file} not found'}, 404

        # Preprocess text to split long sentences
        text = preprocess_text(text)
        logger.info(f"Preprocessed text length: {len(text)} chars")

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
    logger.info(f"Test endpoint called. Using device: {device}")
    return {'status': 'ok', 'message': 'TTS API server is running'}, 200

@app.route('/upload_reference', methods=['POST'])
def upload_reference():
    try:
        logger.info("Upload reference endpoint called")
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
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)