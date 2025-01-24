# Container name
CONTAINER_NAME="tts-server"

# Stop and remove existing container if it exists
docker stop $CONTAINER_NAME >/dev/null 2>&1
docker rm $CONTAINER_NAME >/dev/null 2>&1

# Create shared directory
mkdir -p ./share

# Run new container with name
docker run --rm -it -d -p 5000:5000 --gpus '"device=1"' \
    --name $CONTAINER_NAME \
    -v "$(pwd)/share:/root/.local/share" \
    -v "$(pwd)/references:/root/TTS/TTS/server/references" \
    tts
