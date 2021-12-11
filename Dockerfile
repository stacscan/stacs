FROM python:3.9-alpine

# Allow build-time specification of version.
ARG VERSION

# Keep things friendly.
LABEL org.opencontainers.image.title="STACS"
LABEL org.opencontainers.image.description="Static Token And Credential Scanner"
LABEL org.opencontainers.image.url="https://www.github.com/stacscan/stacs"
LABEL org.opencontainers.image.version=$VERSION

# Install STACS into the container.
WORKDIR /opt/stacs
COPY requirements.txt setup.py setup.cfg ./
COPY stacs ./stacs
RUN apk add --no-cache git gcc musl-dev libarchive-dev libarchive && \
    pip install --no-cache-dir .

# Clone the latest STACS rules into the rules directory to enable out of the box use.
# This can be mounted over using a volume mount to allow more specific rules to be
# loaded. The same is true for "ignore-lists". Finally, there is a "cache" directory
# configured as a mount to allow scans which need a lot of disk space to mount a scratch
# volume so that Docker doesn't run out of disk :)
RUN mkdir -p /mnt/stacs/input /mnt/stacs/rules /mnt/stacs/ignore /mnt/stacs/cache && \
    git clone https://www.github.com/stacscan/stacs-rules /mnt/stacs/rules

# Define a volume to allow mounting a local directory to scan.
VOLUME /mnt/stacs/input
VOLUME /mnt/stacs/rules
VOLUME /mnt/stacs/ignore
VOLUME /mnt/stacs/cache

# Clean up.
RUN apk del --purge gcc musl-dev git

# Default to running stacs with the volume mounts.
ENTRYPOINT ["stacs"]
CMD [ \
    "--rule-pack", "/mnt/stacs/rules/credential.json", \
    "--cache-directory", "/mnt/stacs/cache", \
    "/mnt/stacs/input" \
]
