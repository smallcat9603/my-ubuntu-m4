# Dockerfile
FROM mpioperator/mpi-pi:latest

WORKDIR /app

# 安装 Python 依赖
RUN pip install --no-cache-dir \
    prefect==2.19.3 \
    prefect-kubernetes==0.5.1 \
    qiskit==1.1.0 \
    qiskit-aer==0.14.1 \
    numpy==1.26.4 \
    psij-python==0.11.0 \
    psij-kubernetes==0.11.0

# 复制我们的脚本到镜像中
COPY mpi_script.py flow_psij.py /app/

