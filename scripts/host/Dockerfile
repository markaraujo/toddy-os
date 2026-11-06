# QEMU runs a real guest kernel; this container only packages host tooling.
FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    qemu-system-x86 qemu-utils ovmf seabios cloud-image-utils ca-certificates \
    && dpkg-query -W > /host-packages.tsv && rm -rf /var/lib/apt/lists/*
