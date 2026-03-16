# TTS
This tts engine is based on [Coqui TTS](https://github.com/coqui-ai/TTS). For more information, check out their [documentation](https://docs.coqui.ai/en/latest/).

## Features
- Multi-language support with high-quality speech synthesis
- Voice cloning capabilities to replicate specific voice characteristics
- GPU-accelerated processing for fast inference
- Implemented as a Flask server for easy API integration
- Dockerized deployment for simple setup and scalability

## Limitations

XTTS v2 has a **400-token limit** per text segment (~400 characters for Russian). The server preprocesses text by splitting long sentences, and the parallel client splits by paragraph. Keep individual requests under 400 chars to avoid CUDA errors.

## Docker

### Build
```bash
cd docker
docker build -t tts .
```

### Run single server
```bash
cd docker
bash run.sh            # starts tts-server on port 5000
```

### Run 3 parallel servers
```bash
cd docker
bash run.sh            # port 5000

# Additional instances:
for i in 2 3; do
  docker run -d -p $((4999+i)):5000 --gpus '"device=0"' \
    --name tts-server-$i \
    -v "$(pwd)/share:/root/.local/share" \
    -v "$(pwd)/references:/root/TTS/TTS/server/references" \
    --restart always tts
done
```

## Client scripts

### Single file TTS
```bash
cd client
python client.py <text_file> -l <lang> [-r <reference.wav>] [-o <output.wav>]
```
Splits text into chunks, sends to server on port 5000, outputs a single WAV.

### Parallel chapter processing
```bash
cd client
python parallel_client.py -l <lang> [-r <reference.wav>] [-o <output_dir>] [-m <book.mp3>]
```
Expects chapters in `ch*/draft-v1.md`. Distributes across 3 servers (ports 5000-5002), generates per-chapter WAVs, merges into a single MP3.

### Upload reference voice
```bash
cd client
python upload_reference.py
```
Uploads a reference WAV to the server for voice cloning. Edit the script to set the filename.
