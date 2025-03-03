ARG BASE=nvidia/cuda:11.8.0-base-ubuntu22.04
FROM ${BASE}

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y --no-install-recommends \
    gcc g++ make python3 python3-dev python3-pip python3-venv python3-wheel \
    espeak-ng libsndfile1-dev git && rm -rf /var/lib/apt/lists/*
RUN pip3 install llvmlite --ignore-installed

# Install Dependencies:
RUN pip3 install torch torchaudio --extra-index-url https://download.pytorch.org/whl/cu118
RUN rm -rf /root/.cache/pip

# Clone TTS repository:
WORKDIR /root
RUN git clone https://github.com/coqui-ai/TTS.git
WORKDIR /root/TTS

RUN make install

# Set environment variable to automatically accept the license
ENV COQUI_TOS_AGREED=1

# Create updated patch file to fix the weights_only issue in PyTorch 2.6+
COPY add_safe_globals.py /root/add_safe_globals.py

# Copy the modified API server
COPY api_server.py /root/TTS/TTS/server/api_server.py

ENTRYPOINT ["python3"]
CMD ["/root/TTS/TTS/server/api_server.py"]