# 使用 Prefect 和 Psi/J 构建可移植的混合量子-HPC工作流

本文档提供了一个最小化但完整的端到端示例，演示了如何使用 **Prefect** 作为工作流编排引擎，并结合 **Psi/J** 库，在 Kubernetes 上调度一个具备后端可移植性的混合高性能计算（HPC）和量子计算任务。

## 概念架构

我们将构建一个三阶段的工作流：

1.  **经典并行预处理 (MPI Job)**: 使用 Psi/J 提交一个并行的 MPI 作业，模拟为量子算法计算所需的参数。
2.  **量子计算模拟 (Kubernetes Job)**: Prefect 接收来自 MPI 任务的输出参数，并使用这些参数在常规的 Kubernetes Pod 中运行一个 Qiskit 量子电路模拟。
3.  **结果分析 (Kubernetes Job)**: 对量子模拟的结果进行简单的分析和打印。

这种架构的核心优势在于 **可移植性**。通过使用 Psi/J，我们的工作流逻辑与底层作业调度器（Kubernetes, Slurm, PBS等）完全解耦。

---

## 1. 先决条件

在开始之前，请确保您已安装并配置好：

- 一个正在运行的 Kubernetes 集群。
- `kubectl` 已配置好并指向该集群。
- **MPI Operator** 已安装到您的集群中。
- **Prefect** 已安装在您的本地机器 (`pip install prefect`)。
- **Docker** 已安装，并且您有一个可以推送镜像的 Docker 仓库（例如 Docker Hub, GCR, ECR）。

---

## 2. 项目文件结构

在您的项目目录中，创建以下文件：

```
.
├── Dockerfile
├── flow_psij.py            # 使用 Psi/J 的可移植工作流
├── mpi_script.py           # MPI 并行计算脚本
└── prefect.yaml            # Prefect 部署配置文件
```

---

## 3. 文件内容

### 3.1 `mpi_script.py`

这是一个使用 `mpi4py` 的 Python 脚本。它将被 MPI Operator 的 `mpirun` 命令调用。它模拟了多个进程并行计算，然后由 rank 0 进程将最终结果以 JSON 格式打印到标准输出（stdout）。

```python
# mpi_script.py
import numpy as np
from mpi4py import MPI
import json
import time

# 一个模拟复杂计算的虚拟函数
def find_optimal_parameter(rank):
    """每个 rank 模拟搜索一个最优参数。"""
    np.random.seed(rank)
    time.sleep(2) # 模拟工作负载
    # 在真实场景中，这可能是一个复杂的优化或搜索算法
    return np.random.random() * np.pi

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# 每个 rank 计算一个本地参数
local_param = find_optimal_parameter(rank)

# 将所有参数聚集到根进程 (rank 0)
all_params = comm.gather(local_param, root=0)

# 根进程格式化结果并打印到 stdout
if rank == 0:
    # 在真实的 VQE 算法中，你可能会对参数进行平均或选择最优值
    # 这里我们简单地选择前两个作为量子电路的 theta 和 phi 角度
    result = {
        "status": "success",
        "theta": all_params[0] if len(all_params) > 0 else None,
        "phi": all_params[1] if len(all_params) > 1 else None,
    }
    # 这个 print 语句至关重要，Prefect 将读取此 stdout
    print(json.dumps(result))
```

### 3.2 `flow_psij.py`

这是定义 Prefect 工作流的核心文件。它使用 **Psi/J (Portable Submission Interface for Jobs)** 库来提交 MPI 作业，从而避免了任何特定于 Kubernetes 的代码。

```python
# flow_psij.py
import json
from prefect import flow, task
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# 导入 Psi/J
from psij import Job, JobSpec, JobExecutor

# 任务1: 使用 Psi/J 启动 MPI 作业
@task(name="Launch MPI Preprocessing with Psi/J", retries=2)
def launch_mpi_task_psij(num_workers: int = 4) -> dict:
    """
    使用 Psi/J 创建并运行一个 MPI 作业。这个任务是后端无关的。
    """
    print("Submitting job via Psi/J to the 'kubernetes' backend.")

    # 1. 使用 Psi/J 的通用 API 来描述作业
    spec = JobSpec(
        executable="python3",
        arguments=["/app/mpi_script.py"],
        # 指定并行作业的属性
        attributes={
            "process_count": num_workers,
            "launch_type": "mpi"
        },
        stdout_path="stdout.txt" # 让 Psi/J 帮我们捕获输出
    )
    job = Job(spec)

    # 2. 获取一个 Executor，并指定后端
    # !!! 这是唯一需要根据环境改变的地方 !!!
    # 要迁移到 Slurm, 只需改为 jex = JobExecutor.get("slurm")
    jex = JobExecutor.get("kubernetes")

    # 3. 提交作业并等待
    jex.submit(job)
    print(f"Job {job.id} submitted. Waiting for completion...")
    job.wait(timeout=300)

    # 4. 从 Psi/J 捕获的 stdout 中读取结果
    output = job.get_output()
    result_line = output.strip().split("\n")[-1]
    return json.loads(result_line)

# 任务2: 运行量子模拟 (此任务不变)
@task(name="Run Quantum Simulation")
def run_quantum_simulation(params: dict) -> dict:
    if params.get("status") != "success":
        raise ValueError("MPI preprocessing failed.")

    theta = params.get("theta", 0)
    phi = params.get("phi", 0)

    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.rz(phi, 1)
    qc.rx(theta, 0)
    qc.measure([0, 1], [0, 1])

    simulator = AerSimulator()
    compiled_circuit = transpile(qc, simulator)
    result = simulator.run(compiled_circuit, shots=1024).result()
    counts = result.get_counts(qc)
    return counts

# 任务3: 分析结果 (此任务不变)
@task(name="Analyze Results")
def analyze_results(counts: dict):
    print("Quantum simulation finished.")
    print(f"Measurement counts: {counts}")
    most_frequent = max(counts, key=counts.get)
    print(f"The most frequent state was: |{most_frequent}>")

# 主工作流
@flow(name="Portable Hybrid Quantum-HPC Workflow (Psi/J)")
def hybrid_workflow_psij(image_name: str, num_mpi_workers: int = 4):
    """
    一个使用 Psi/J 的可移植的混合工作流。
    """
    print(f"Starting portable hybrid workflow with image: {image_name}")
    mpi_result = launch_mpi_task_psij(num_workers=num_mpi_workers)
    quantum_counts = run_quantum_simulation(params=mpi_result)
    analyze_results(counts=quantum_counts)
```

### 3.3 `Dockerfile`

我们需要在 Docker 镜像中添加 `psij-python` 和它的 Kubernetes 插件。

```dockerfile
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
```

---

## 4. 部署与执行

### 4.1 `prefect.yaml`

这个部署文件现在指向我们的 Psi/J 工作流。

```yaml
# prefect.yaml
name: Portable Hybrid Quantum-HPC Workflow
description: A portable Quantum-HPC workflow using Prefect and Psi/J.
version: 1.0

# 入口点指向我们的 Psi/J 工作流
entrypoint: flow_psij.py:hybrid_workflow_psij

parameters:
  # !!! 重要: 替换为您自己的镜像名称 !!!
  image_name: your-dockerhub-username/prefect-mpi-hpc:latest
  num_mpi_workers: 4
  
work_pool:
  name: k8s-pool
  work_queue_name: null
  job_variables:
    image: "{{ image_name }}"
    namespace: "default"
```

### 4.2 构建与部署步骤

1.  **构建并推送 Docker 镜像**:
    ```bash
    export DOCKER_IMAGE="your-dockerhub-username/prefect-mpi-hpc:latest"
    docker build -t $DOCKER_IMAGE .
    docker push $DOCKER_IMAGE
    ```

2.  **设置 Prefect Kubernetes 工作池**: (如果尚未完成)
    ```bash
    prefect work-pool create --type kubernetes k8s-pool
    ```

3.  **部署工作流**:
    ```bash
    prefect deploy
    ```

4.  **启动 Prefect Agent**:
    ```bash
    prefect agent start --pool k8s-pool
    ```

### 4.3 运行和监控

您可以通过 UI 或 CLI 触发运行。

```bash
# 通过 CLI 运行部署
prefect deployment run "Portable Hybrid Quantum-HPC Workflow/hybrid-workflow-psij"
```
在幕后，Prefect Agent 会执行 `flow_psij.py`，调用 Psi/J，Psi/J 再去创建 `MPIJob`。整个过程对用户来说是透明的，但代码现在已经具备了迁移到其他计算环境的能力。
