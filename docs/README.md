# LLM AirSim Swarm Controller

一个集成了 LLM（大语言模型）、SDF（有符号距离函数）和 AirSim 仿真环境的无人机群控制系统。

## 功能特性

- **LLM 驱动的形状生成**：用自然语言描述 3D 形状，自动生成 SDF 代码
- **自动路点规划**：基于 SDF 计算最优的无人机编队队形
- **AirSim 仿真集成**：与 AirSim 无缝集成，支持实时群体控制
- **人工势场法（APF）**：实现无人机之间的避碰和编队保持
- **交互模式**：支持命令行交互式控制

## 项目结构

```
airsim_swarm_llm/
├── llm_client.py           # LLM API 客户端和 SDF 生成器
├── airsim_controller.py    # AirSim 通信接口
├── swarm_controller.py     # 点分配和 APF 控制器
├── sdf_executor.py         # SDF 代码执行器
├── integrated_controller.py # 主集成控制器
├── config.py               # 配置文件
├── examples.py             # 使用示例
├── requirements.txt        # Python 依赖
└── README.md              # 本文件
```

## 安装

### 前提条件

- Python 3.8+
- AirSim 已安装并运行
- 有效的 LLM API 密钥（OpenAI 或兼容的 API）

### 安装步骤

1. 克隆或下载此项目

2. 安装 Python 依赖：
```bash
pip install -r requirements.txt
```

3. 配置 LLM API：
```bash
# 设置环境变量
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 或您的 API 端点
export LLM_MODEL="gpt-3.5-turbo"  # 或其他模型
```

4. 启动 AirSim：
   - 打开 AirSim 应用程序
   - 设置多无人机模式
   - 配置无人机名称（Drone1, Drone2 等）

## 快速开始

### 基本用法

```python
from integrated_controller import LLMAirSimSwarmController

# 创建控制器
controller = LLMAirSimSwarmController(
    drone_names=["Drone1", "Drone2", "Drone3", "Drone4"],
    airsim_ip="127.0.0.1",
    verbose=True
)

# 准备任务：形状描述 -> SDF 生成 -> 路点规划
if controller.prepare_mission("A cube with 2 unit sides", num_points=4):
    # 开始执行任务
    controller.start_mission()
    
    # 让任务运行 30 秒
    import time
    time.sleep(30)
    
    # 停止任务并降落
    controller.stop_mission()
```

### 交互式模式

```python
from integrated_controller import LLMAirSimSwarmController

controller = LLMAirSimSwarmController(
    drone_names=["Drone1", "Drone2", "Drone3", "Drone4"]
)

# 进入交互模式
controller.interactive_mode()
```

交互模式命令：
- `shape <描述>` - 生成形状和路点
- `start` - 启动任务
- `stop` - 停止任务
- `status` - 显示当前状态
- `quit` - 退出

## 核心组件

### 1. LLM 客户端（llm_client.py）

处理与 LLM API 的通信：

```python
from llm_client import LLMClient, SDFGenerator

# 创建客户端
client = LLMClient()

# 生成 SDF 代码
generator = SDFGenerator(client)
code = generator.generate_sdf_code("A cylinder shape")
```

### 2. AirSim 控制器（airsim_controller.py）

管理与 AirSim 的无人机通信：

```python
from airsim_controller import AirSimSwarmController

swarm = AirSimSwarmController(
    drone_names=["Drone1", "Drone2", "Drone3", "Drone4"]
)

swarm.connect_all("127.0.0.1")
swarm.arm_all()
swarm.takeoff_all(5.0)

# 获取当前位置
positions = swarm.get_positions()

# 设置速度命令
import numpy as np
velocities = np.array([[0.5, 0, 0], [0, 0.5, 0], ...])
swarm.set_velocities(velocities, duration=0.1)

swarm.land_all()
swarm.disarm_all()
```

### 3. 群体控制器（swarm_controller.py）

实现路点规划和 APF 控制：

```python
from swarm_controller import PointDistributor, APFSwarmController

# SDF 函数定义
def sdf_func(points):
    from sdf import sphere
    f = sphere(2)
    return f(points)

# 路点规划
distributor = PointDistributor(sdf_func)
waypoints = distributor.generate_points(num_points=8)

# APF 控制
controller = APFSwarmController()
controller.distribute_goals(current_poses, goal_poses)
velocities = controller.get_control(current_poses)
```

### 4. SDF 执行器（sdf_executor.py）

安全执行 LLM 生成的 SDF 代码：

```python
from sdf_executor import SDFExecutor

executor = SDFExecutor()

code = """
from sdf import sphere, box
f = sphere(2) & box(3)
"""

sdf_func = executor.create_sdf_function(code)

# 评估 SDF
import numpy as np
points = np.array([[0, 0, 0], [1, 1, 1]])
values = sdf_func(points)
```

## 配置

编辑 `config.py` 自定义参数：

```python
# LLM 配置
LLM_CONFIG = {
    "api_key": "your-api-key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
}

# AirSim 配置
AIRSIM_CONFIG = {
    "ip": "127.0.0.1",
    "drones": {
        "Drone1": {"start_pos": [0, 0, 0]},
        "Drone2": {"start_pos": [1, 0, 0]},
        ...
    }
}

# APF 控制参数
SWARM_CONTROL_CONFIG = {
    "p_cohesion": 1.0,
    "p_separation": 1.0,
    "max_vel": 1.0,
    "min_dist": 0.5,
}
```

## 使用示例

查看 `examples.py` 获取完整示例：

```bash
python examples.py
```

示例包括：
1. 基本用法
2. 交互模式
3. 连续形状
4. 自定义参数
5. 各种形状描述
6. 错误处理

## 支持的 SDF 形状

所有 [sdf 库](https://github.com/fogleman/sdf.git) 支持的形状：

基本形状：
- `sphere(radius)` - 球体
- `box(size)` - 立方体
- `rounded_box(size, radius)` - 圆角立方体
- `torus(major_radius, minor_radius)` - 圆环
- `capsule(p1, p2, radius)` - 胶囊形
- `cylinder(radius)` - 圆柱
- `pyramid(size)` - 金字塔
- 等等...

操作：
- 并集：`a | b`
- 差集：`a - b`
- 交集：`a & b`
- 平移：`.translate((x, y, z))`
- 缩放：`.scale(factor)`
- 旋转：`.rotate(angle, axis)`

## 工作流程

```
┌─────────────────────────┐
│  自然语言描述 (NLP)     │
│  例：A sphere with...   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  LLM API 调用           │
│  生成 SDF Python 代码   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  SDF 执行器             │
│  执行代码获取 f 函数    │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  点分配器               │
│  生成优化的路点队形     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  APF 控制器             │
│  计算每架无人机速度     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  AirSim 接口            │
│  发送指令到无人机       │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  AirSim 仿真            │
│  无人机执行运动         │
└─────────────────────────┘
```

## 故障排除

### 无法连接到 AirSim
- 确保 AirSim 已启动并配置为多无人机模式
- 检查 IP 地址和端口是否正确
- 确保防火墙未阻止连接

### LLM API 错误
- 检查 API 密钥是否有效
- 验证 API 基础 URL 是否正确
- 检查网络连接

### SDF 代码执行失败
- 检查 sdf 库是否已正确安装
- 验证 LLM 生成的代码语法
- 查看错误消息获取详细信息

### 路点生成问题
- 确保 SDF 函数返回有效的数值
- 检查点分配器的边界设置
- 尝试增加采样点数

## API 文档

### LLMAirSimSwarmController

主要接口类：

```python
controller = LLMAirSimSwarmController(
    drone_names: List[str],
    airsim_ip: str = "127.0.0.1",
    llm_api_key: str = None,
    llm_base_url: str = None,
    llm_model: str = None,
    verbose: bool = True
)

# 方法
controller.describe_shape(description: str) -> bool
controller.generate_waypoints(num_points: int = None) -> bool
controller.prepare_mission(shape_description: str, num_points: int = None) -> bool
controller.start_mission() -> bool
controller.stop_mission()
controller.interactive_mode()
```

## 贡献

欢迎提交问题和改进建议！

## 许可证

本项目采用 MIT 许可证。

## 相关项目

- [flock_gpt](https://github.com/your-repo/flock_gpt) - ROS 基础的无人机群控制
- [NeLV](https://github.com/your-repo/NeLV) - LLM API 集成框架
- [AirSim](https://github.com/microsoft/AirSim) - 无人机仿真平台
- [sdf](https://github.com/fogleman/sdf) - 有符号距离函数库

## 参考文献

- Artificial Potential Field Method for Swarm Robotics
- Large Language Models for Code Generation
- Signed Distance Functions for 3D Shape Representation
