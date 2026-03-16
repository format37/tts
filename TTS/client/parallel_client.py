#!/usr/bin/env python3
"""Parallel TTS client that processes chapters across multiple TTS server instances."""

import requests
import argparse
import glob
import io
import os
import re
import subprocess
import sys
import wave
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

SERVERS = [
    'http://localhost:5000/tts',
    'http://localhost:5001/tts',
    'http://localhost:5002/tts',
]

# Max chars per TTS request — XTTS has 400-token limit.
# Russian text averages ~1.5 chars per token, so 400 chars is safe.
MAX_CHUNK_CHARS = 400


def split_long_text(text, max_chars=MAX_CHUNK_CHARS):
    """Split text at natural break points to stay under max_chars."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    delimiters = ['. ', '! ', '? ', ' — ', '; ', ', ']
    remaining = text

    while len(remaining) > max_chars:
        best_pos = -1
        for delim in delimiters:
            pos = remaining.rfind(delim, 0, max_chars)
            if pos > best_pos:
                best_pos = pos + len(delim)

        if best_pos <= 0:
            pos = remaining.rfind(' ', 0, max_chars)
            best_pos = pos if pos > 0 else max_chars

        chunks.append(remaining[:best_pos].strip())
        remaining = remaining[best_pos:].strip()

    if remaining:
        chunks.append(remaining)

    return chunks


def split_chapter(text):
    """Split chapter into TTS-safe chunks, preserving paragraph boundaries."""
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Skip markdown formatting
        if re.match(r'^#{1,6}\s', para):
            continue
        if para == '---':
            continue
        if re.match(r'^\{.*\}$', para):
            continue
        if re.match(r'^\*[^*]+\*$', para) and len(para) < 50:
            continue

        # Split long paragraphs into safe chunks
        chunks.extend(split_long_text(para))

    return chunks


def generate_audio(server_url, text, language, reference_file, timeout=300):
    """Send text to a TTS server and return WAV bytes."""
    payload = {
        'text': text,
        'language': language,
        'reference_file': reference_file
    }
    response = requests.post(server_url, json=payload, timeout=timeout)
    if response.status_code == 200:
        return response.content
    else:
        error = response.json().get('error', 'Unknown error')
        raise RuntimeError(error)


def concatenate_wav(wav_data_list, output_path):
    """Concatenate WAV byte strings into a single WAV file."""
    params = None
    all_frames = []
    for data in wav_data_list:
        with wave.open(io.BytesIO(data), 'rb') as w:
            if params is None:
                params = w.getparams()
            all_frames.append(w.readframes(w.getnframes()))

    with wave.open(output_path, 'wb') as out:
        out.setparams(params)
        for frames in all_frames:
            out.writeframes(frames)


def process_chapter(chapter_path, server_url, output_dir, language, reference_file, progress):
    """Process a single chapter: split, TTS each chunk, concatenate."""
    chapter_name = os.path.basename(os.path.dirname(chapter_path))

    with open(chapter_path, 'r', encoding='utf-8') as f:
        text = f.read().strip()

    chunks = split_chapter(text)
    if not chunks:
        progress['done'] += 1
        return None

    wav_data_list = []
    total_chunks = len(chunks)
    consecutive_errors = 0

    for i, chunk in enumerate(chunks):
        progress['status'] = f"{chapter_name}: {i+1}/{total_chunks} ({len(chunk)}ch)"
        print_progress(progress)

        try:
            wav_data = generate_audio(server_url, chunk, language, reference_file)
            wav_data_list.append(wav_data)
            consecutive_errors = 0
        except Exception as e:
            progress['errors'] += 1
            consecutive_errors += 1
            err_short = str(e)[:60]
            progress['status'] = f"{chapter_name}: {i+1}/{total_chunks} ERR: {err_short}"
            print_progress(progress)

            # If server is dead (CUDA crash), stop trying
            if consecutive_errors >= 3:
                progress['status'] = f"{chapter_name}: SERVER DEAD, saving {len(wav_data_list)} chunks"
                print_progress(progress)
                break

    output_path = None
    if wav_data_list:
        output_path = os.path.join(output_dir, f"{chapter_name}.wav")
        concatenate_wav(wav_data_list, output_path)

    progress['done'] += 1
    ok = len(wav_data_list)
    progress['status'] = f"{chapter_name}: DONE {ok}/{total_chunks}"
    print_progress(progress)
    return output_path


def print_progress(progress):
    """Print a progress indicator line."""
    done = progress['done']
    total = progress['total']
    errors = progress['errors']
    status = progress['status']
    bar_len = 30
    filled = int(bar_len * done / total) if total > 0 else 0
    bar = '#' * filled + '-' * (bar_len - filled)
    line = f"\r[{bar}] {done}/{total} | err:{errors} | {status}"
    sys.stdout.write(f"{line:<120}")
    sys.stdout.flush()


def merge_to_mp3(wav_files, output_mp3):
    """Merge WAV files into a single MP3 using ffmpeg."""
    if not wav_files:
        print("\nNo WAV files to merge")
        return

    list_path = output_mp3 + '.list.txt'
    with open(list_path, 'w') as f:
        for wav in wav_files:
            f.write(f"file '{os.path.abspath(wav)}'\n")

    cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', list_path,
        '-codec:a', 'libmp3lame', '-qscale:a', '2',
        output_mp3
    ]

    print(f"\nMerging {len(wav_files)} chapters into {output_mp3}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(list_path)

    if result.returncode == 0:
        size_mb = os.path.getsize(output_mp3) / (1024 * 1024)
        print(f"Created {output_mp3} ({size_mb:.1f} MB)")
    else:
        print(f"ffmpeg error: {result.stderr}")


def main():
    parser = argparse.ArgumentParser(description='Parallel TTS client for chapters')
    parser.add_argument('--language', '-l', default='ru', help='Language code (default: ru)')
    parser.add_argument('--reference', '-r', default='asmr_0.wav', help='Reference audio file')
    parser.add_argument('--output', '-o', default='output', help='Output directory (default: output)')
    parser.add_argument('--mp3', '-m', default='book.mp3', help='Final MP3 filename (default: book.mp3)')
    args = parser.parse_args()

    chapter_files = sorted(glob.glob('ch*/draft-v1.md'))
    if not chapter_files:
        print("No chapter files found (expected ch*/draft-v1.md)")
        sys.exit(1)

    # Preview chunk counts
    print(f"Found {len(chapter_files)} chapters, {len(SERVERS)} servers")
    total_chunks = 0
    for i, ch in enumerate(chapter_files):
        with open(ch, 'r') as f:
            chunks = split_chapter(f.read())
        total_chunks += len(chunks)
        server = SERVERS[i % len(SERVERS)]
        port = server.split(':')[2].split('/')[0]
        print(f"  {ch}: {len(chunks)} chunks -> :{port}")
    print(f"Total: {total_chunks} chunks, max {MAX_CHUNK_CHARS} chars each")

    os.makedirs(args.output, exist_ok=True)

    progress = {'done': 0, 'total': len(chapter_files), 'errors': 0, 'status': 'starting...'}

    print(f"\nGenerating...")
    start_time = time.time()

    output_files = [None] * len(chapter_files)

    with ThreadPoolExecutor(max_workers=len(SERVERS)) as executor:
        futures = {}
        for i, chapter_path in enumerate(chapter_files):
            server_url = SERVERS[i % len(SERVERS)]
            future = executor.submit(
                process_chapter,
                chapter_path, server_url, args.output,
                args.language, args.reference, progress
            )
            futures[future] = i

        for future in as_completed(futures):
            idx = futures[future]
            try:
                output_files[idx] = future.result()
            except Exception as e:
                progress['errors'] += 1
                progress['done'] += 1
                print(f"\nChapter {idx+1} failed: {e}")

    elapsed = time.time() - start_time
    print(f"\n\nDone in {elapsed/60:.1f} min | {progress['done']}/{progress['total']} chapters | {progress['errors']} errors")

    wav_files = [f for f in output_files if f is not None]
    if wav_files:
        mp3_path = os.path.join(args.output, args.mp3)
        merge_to_mp3(wav_files, mp3_path)

    print("Done!")


if __name__ == '__main__':
    main()
