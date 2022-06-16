# FROM nemo:latest
FROM nvcr.io/nvidia/nemo:22.04
WORKDIR /
COPY requirements.txt /
RUN pip install -r requirements.txt
COPY server.py /
ENTRYPOINT ["python3"]
CMD ["server.py"]