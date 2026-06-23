# bll operator console — CPU-only web app. The GPU/alignment lives in ollama,
# reached over HTTP, so this image never needs CUDA or a model baked in.
FROM python:3.12-slim

WORKDIR /app

# Install the package + web extra. fugashi/pysubs2/simplemma/pykakasi/wordfreq
# all ship manylinux wheels, so no build toolchain or system MeCab is required.
COPY pyproject.toml ./
COPY bll ./bll
RUN pip install --no-cache-dir ".[web]"

COPY deploy/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# All bll state (DB, campaigns, JMdict cache, backups) under one volume.
ENV XDG_DATA_HOME=/data \
    PYTHONUNBUFFERED=1 \
    BLL_WAIT=60
VOLUME ["/data"]
EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
