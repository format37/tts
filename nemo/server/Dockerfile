FROM nemo:latest
WORKDIR /
COPY requirements.txt /
RUN pip install -r requirements.txt
COPY server.py /
ENTRYPOINT ["python3"]
CMD ["server.py"]