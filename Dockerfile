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
    ssh \
    less \
    htop \
    unzip \
    automake \
    cmake \
    git \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    openjdk-17-jdk \
    build-essential \
    openmpi-bin \
    libopenmpi-dev \
    ruby \
    metis \
    gnuplot \
    npm \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash smallcat && echo "smallcat ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER smallcat
WORKDIR /home/smallcat

# test kubernetes
# COPY test/mpi-hello.c .
# RUN mpicc mpi-hello.c -o mpi-hello
# CMD ["mpirun", "-np", "2", "./mpi-hello"]
# CMD ["sleep", "infinity"]
