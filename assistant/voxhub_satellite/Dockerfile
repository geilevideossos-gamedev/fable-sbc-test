ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/opt/voxhub \
    VOXHUB_LVA_DIR=/app

COPY app/voxhub_satellite /opt/voxhub/voxhub_satellite

WORKDIR /app
ENTRYPOINT []
CMD ["/app/.venv/bin/python3", "-m", "voxhub_satellite"]

ARG BUILD_ARCH
ARG BUILD_VERSION
LABEL \
    io.hass.name="VoxHub Satellite" \
    io.hass.description="Assist voice satellite for the VoxHub hub with LEDs, mute switch and exposure guard" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version="${BUILD_VERSION}"
