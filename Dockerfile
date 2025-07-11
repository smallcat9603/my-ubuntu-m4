FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    sudo \
    bash \
    iputils-ping \
    curl \
    wget \
    net-tools \
    iproute2 \
    dnsutils \
    vim \
    less \
    htop \
    unzip \
    git \
    python3 \
    python3-pip \
    nodejs \
    npm \
    openjdk-17-jdk \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash smallcat && echo "smallcat ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Default user
USER smallcat
WORKDIR /home/smallcat
