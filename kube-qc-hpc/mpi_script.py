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
