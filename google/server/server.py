from flask import Flask, request
import logging
import os
# import uuid
# import io
from google.cloud import texttospeech


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting server")

app = Flask(__name__)


def tts(text, language='en-US', model = 'en-US-Neural2-F', speed=1):

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'api.json'
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=language,
        name=model)

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speed
    )

    response = client.synthesize_speech(input = synthesis_input, voice = voice, audio_config = audio_config)
    return response.audio_content

@app.route("/test")
def call_test():
    return "get ok"


@app.route("/inference", methods=['POST'])
def call_inference():
    data = request.get_json()
    text = data['text']
    language = data['language']
    model = data['model']
    speed = float(data['speed'])
    return tts(text,language,model,speed)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=os.environ.get('PORT', ''))