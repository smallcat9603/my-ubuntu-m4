FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    sudo \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash smallcat && echo "smallcat ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# default user
USER smallcat
WORKDIR /home/smallcat
