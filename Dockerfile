FROM ubuntu:22.04

# 安装必要工具
RUN apt-get update && apt-get install -y \
    sudo \
    bash \
    && rm -rf /var/lib/apt/lists/*

# 创建用户 smallcat 并赋予 sudo 权限
RUN useradd -m -s /bin/bash smallcat && echo "smallcat ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# 设置默认用户
USER smallcat
WORKDIR /home/smallcat
