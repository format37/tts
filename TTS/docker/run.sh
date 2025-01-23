mkdir -p ./share
docker run --rm -it -d -p 5000:5000 --gpus '"device=0"' \
    -v "$(pwd)/share:/root/.local/share" \
    -v "$(pwd)/references:/root/TTS/TTS/server/references" \
    tts