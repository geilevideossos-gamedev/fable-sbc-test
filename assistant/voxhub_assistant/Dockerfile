ARG BUILD_FROM
FROM ${BUILD_FROM}

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

# pulseaudio-utils: parec/pacat (default audio path through the Supervisor's PulseAudio)
# alsa-utils + libasound2-plugins: arecord/aplay via the ALSA pulse plugin (alternative)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        pulseaudio-utils \
        alsa-utils \
        libasound2-plugins \
        ca-certificates \
        tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/venv

COPY requirements.txt requirements-local-wakeword.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# Optional in-process openWakeWord (wake_word_engine: local). Fail-soft: if the wheels
# are unavailable for this platform the image still builds and the default Wyoming
# engine keeps working.
ARG INSTALL_LOCAL_WAKEWORD=true
RUN if [ "${INSTALL_LOCAL_WAKEWORD}" = "true" ]; then \
        pip install -r /tmp/requirements-local-wakeword.txt \
        || echo "WARNING: openwakeword not installed; wake_word_engine 'local' is unavailable"; \
    fi

COPY app/voxhub_assistant /app/voxhub_assistant
COPY run.sh /run.sh
RUN chmod a+x /run.sh

WORKDIR /app
CMD ["/run.sh"]

ARG BUILD_ARCH
ARG BUILD_VERSION
LABEL \
    io.hass.name="VoxHub Assistant" \
    io.hass.description="Claude-based voice assistant for the VoxHub CM4" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version="${BUILD_VERSION}"
