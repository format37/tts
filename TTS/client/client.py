import requests
import argparse
import os
import sys
import wave
import io
import re


def split_text_into_chunks(text, max_chars=1500):
    """Split text into chunks by paragraphs, staying under max_chars per chunk."""
    # Split by double newlines (paragraphs)
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ''

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Skip markdown headers and formatting-only lines
        if re.match(r'^#{1,6}\s', para) or para.startswith('*') and para.endswith('*') and len(para) < 50:
            continue
        if re.match(r'^\{.*\}$', para):  # Skip {new page} etc
            continue
        if para == '---':
            continue

        if len(current_chunk) + len(para) + 2 > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            current_chunk = current_chunk + '\n\n' + para if current_chunk else para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def concatenate_wav_files(wav_buffers, output_path):
    """Concatenate multiple WAV byte buffers into a single WAV file."""
    if not wav_buffers:
        return

    params = None
    all_frames = []

    for buf in wav_buffers:
        buf.seek(0)
        with wave.open(buf, 'rb') as w:
            if params is None:
                params = w.getparams()
            all_frames.append(w.readframes(w.getnframes()))

    with wave.open(output_path, 'wb') as out:
        out.setparams(params)
        for frames in all_frames:
            out.writeframes(frames)


def generate_speech(text, language='ru', reference_file='asmr_0.wav', output_file='output.wav'):
    url = 'http://localhost:5000/tts'
    chunks = split_text_into_chunks(text)
    total = len(chunks)
    print(f"Split text into {total} chunks")

    wav_buffers = []

    for i, chunk in enumerate(chunks):
        print(f"[{i+1}/{total}] Generating audio ({len(chunk)} chars)...")

        payload = {
            'text': chunk,
            'language': language,
            'reference_file': reference_file
        }

        try:
            response = requests.post(url, json=payload, timeout=600)

            if response.status_code == 200:
                wav_buffers.append(io.BytesIO(response.content))
                print(f"[{i+1}/{total}] OK")
            else:
                error_msg = response.json().get('error', 'Unknown error')
                print(f"[{i+1}/{total}] Error: {error_msg}")

        except requests.exceptions.RequestException as e:
            print(f"[{i+1}/{total}] Connection error: {str(e)}")

    if wav_buffers:
        concatenate_wav_files(wav_buffers, output_file)
        print(f"Audio saved as {output_file} ({len(wav_buffers)}/{total} chunks)")
    else:
        print("No audio generated")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate speech from a text file')
    parser.add_argument('text_file', help='Path to a text file containing the text to speak')
    parser.add_argument('--language', '-l', default='ru', help='Language code (default: ru)')
    parser.add_argument('--reference', '-r', default='asmr_0.wav', help='Reference audio file (default: asmr_0.wav)')
    parser.add_argument('--output', '-o', default=None, help='Output WAV file (default: <input_name>.wav)')
    args = parser.parse_args()

    if not os.path.isfile(args.text_file):
        print(f"Error: file not found: {args.text_file}")
        sys.exit(1)

    with open(args.text_file, 'r', encoding='utf-8') as f:
        text = f.read().strip()

    if not text:
        print("Error: text file is empty")
        sys.exit(1)

    output_file = args.output or os.path.splitext(args.text_file)[0] + '.wav'
    generate_speech(text, language=args.language, reference_file=args.reference, output_file=output_file)
