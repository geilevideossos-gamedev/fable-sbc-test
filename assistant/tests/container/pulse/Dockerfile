FROM debian:trixie-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends pulseaudio pulseaudio-utils \
    && rm -rf /var/lib/apt/lists/*
