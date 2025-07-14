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
