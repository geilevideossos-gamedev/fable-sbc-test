ARG KICAD_BASE=kicad/kicad:10.0
FROM ${KICAD_BASE}
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-numpy python3-shapely \
    && rm -rf /var/lib/apt/lists/*
