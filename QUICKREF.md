# 快速参考指南

## 目录结构

```
airsim_swarm_llm/
├── 核心代码（7 个文件）
│   ├── llm_client.py                    # LLM API 客户端和 SDF 生成器
│   ├── airsim_controller.py             # AirSim 无人机控制接口
│   ├── swarm_controller.py              # 群体控制和路点规划
│   ├── sdf_executor.py                  # SDF 代码执行器
│   ├── integrated_controller.py         # 主集成控制器 ⭐ 从这里开始
│   ├── config.py                        # 配置管理
│   └── __init__.py                      # Python 包初始化
│
├── 工具和脚本（3 个文件）
│   ├── quickstart.py                    # 快速启动脚本 🚀
│   ├── diagnose.py                      # 诊断和故障排除工具
│   └── examples.py                      # 6 个完整的使用示例
│
├── 配置文件（2 个文件）
│   ├── requirements.txt                 # Python 依赖
│   └── settings.json                    # AirSim 配置样本
│
└── 文档（4 个文件）
    ├── README.md                        # 完整使用指南 📖
    ├── INSTALL.md                       # 详细安装说明
    ├── PROJECT_SUMMARY.md               # 项目总结
    └── QUICKREF.md                      # 本文件
```

## 快速开始（3 步）

### 1️⃣ 验证安装
```bash
python diagnose.py
```

如果有缺失，按提示安装依赖：
```bash
pip install -r requirements.txt
```

### 2️⃣ 设置 LLM API
```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY = "sk-..."
$env:OPENAI_BASE_URL = "https://api.openai.com/v1"
$env:LLM_MODEL = "gpt-3.5-turbo"

# Linux/Mac (Bash)
export OPENAI_API_KEY="sk-..."
export OPENAI_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-3.5-turbo"
```

### 3️⃣ 启动 AirSim 并运行
```bash
# 方式 1：交互模式
python quickstart.py --interactive

# 方式 2：运行示例
python quickstart.py -e 1

# 方式 3：自定义脚本
python your_script.py
```

## 常用命令

### 诊断和测试
```bash
# 完整诊断
python diagnose.py

# 快速检查
python quickstart.py --check

# 测试 API 连接
python quickstart.py --test
```

### 交互模式
```bash
python quickstart.py --interactive

# 命令行输入
> shape A cube
> start
> status
> stop
> quit
```

### 运行示例
```bash
# 所有示例
python examples.py

# 特定示例（1-5）
python quickstart.py -e 1    # 基本用法
python quickstart.py -e 4    # 自定义参数
```

## 最小可工作示例

```python
from integrated_controller import LLMAirSimSwarmController
import time

# 创建控制器
controller = LLMAirSimSwarmController(
    drone_names=["Drone1", "Drone2", "Drone3", "Drone4"],
    verbose=True
)

# 准备任务
if controller.prepare_mission("A sphere", num_points=4):
    # 启动任务
    controller.start_mission()
    
    # 运行 30 秒
    time.sleep(30)
    
    # 停止并降落
    controller.stop_mission()
```

## API 快速参考

### LLMAirSimSwarmController
```python
# 创建
controller = LLMAirSimSwarmController(drone_names=[...])

# 1. 形状描述和路点规划
controller.describe_shape("description")           # 生成 SDF 代码
controller.generate_waypoints(num_points=8)        # 生成路点
controller.prepare_mission("description", 8)       # 一步到位

# 2. 任务执行
controller.start_mission()                         # 启动
controller.stop_mission()                          # 停止

# 3. 交互
controller.interactive_mode()                      # 命令行交互
```

### AirSimSwarmController
```python
from airsim_controller import AirSimSwarmController

swarm = AirSimSwarmController(["Drone1", "Drone2", ...])

# 基本操作
swarm.connect_all("127.0.0.1")
swarm.arm_all()
swarm.takeoff_all(duration=5.0)

# 获取状态
positions = swarm.get_positions()  # 返回 (N, 3) 数组

# 控制
swarm.set_velocities(velocities, duration=0.1)
swarm.set_positions(positions, velocity=1.0)

# 收尾
swarm.land_all()
swarm.disarm_all()
```

### APFSwarmController
```python
from swarm_controller import APFSwarmController

apf = APFSwarmController(
    p_cohesion=1.0,        # 内聚力
    p_separation=1.0,      # 分离力
    max_vel=1.0,          # 最大速度
    min_dist=0.5          # 最小距离
)

# 目标分配
goals = apf.distribute_goals(current_poses, goal_poses)

# 计算速度
velocities = apf.get_control(current_poses)
```

### PointDistributor
```python
from swarm_controller import PointDistributor

# 定义 SDF 函数
def my_sdf(points):
    from sdf import sphere
    return sphere(2)(points)

# 生成路点
distributor = PointDistributor(my_sdf)
waypoints = distributor.generate_points(num_points=8)
```

### LLMClient
```python
from llm_client import LLMClient, SDFGenerator

# API 调用
client = LLMClient()
response = client.chat_completion([
    {"role": "user", "content": "Hello"}
])

# SDF 生成
generator = SDFGenerator(client)
code = generator.generate_sdf_code("a cube shape")
```

## 配置参数

### config.py 中的配置
```python
# LLM 配置
LLM_CONFIG = {
    "api_key": "your-key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 1000,
}

# AirSim 配置
AIRSIM_CONFIG = {
    "ip": "127.0.0.1",
    "drones": {
        "Drone1": {"start_pos": [0, 0, 0]},
        "Drone2": {"start_pos": [1, 0, 0]},
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

## 支持的 SDF 形状

基本形状：
- `sphere(radius)` - 球体
- `box(size)` - 立方体
- `rounded_box(size, radius)` - 圆角立方体
- `torus(major, minor)` - 圆环
- `capsule(p1, p2, radius)` - 胶囊形
- `cylinder(radius)` - 圆柱
- `pyramid(size)` - 金字塔

操作：
- 并集: `a | b`
- 差集: `a - b`
- 交集: `a & b`
- 变换: `.translate()`, `.scale()`, `.rotate()`

示例：
```python
from sdf import *

# 组合形状
f = sphere(2) & box(3)

# 去掉圆柱孔
c = cylinder(0.5)
f -= c.orient(X) | c.orient(Y) | c.orient(Z)

# 保存为 STL
f.save('out.stl')
```

## 环境变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `OPENAI_API_KEY` | LLM API 密钥 | `sk-...` |
| `OPENAI_BASE_URL` | API 端点 | `https://api.openai.com/v1` |
| `LLM_MODEL` | 模型名称 | `gpt-3.5-turbo` |
| `AIRSIM_IP` | AirSim 服务器地址 | `127.0.0.1` |

## 故障排除速查表

| 问题 | 解决方案 |
|------|--------|
| 找不到模块 | `pip install -r requirements.txt` |
| 无法连接 AirSim | 确保 AirSim 运行并配置为多无人机模式 |
| LLM API 错误 | 检查 API 密钥和网络连接 |
| 生成缓慢 | 减少采样点数或简化 SDF |
| 内存不足 | 关闭其他程序或使用较小的参数 |

## 性能指标

| 项目 | 性能 |
|------|------|
| LLM 生成延迟 | 5-30 秒（取决于网络和模型） |
| 路点生成（8 个点） | 2-10 秒 |
| 控制循环频率 | 10 Hz（可调） |
| 同时无人机数量 | 4-10（取决于硬件） |

## 常用命令速查

```bash
# 安装和验证
pip install -r requirements.txt
python diagnose.py

# 运行
python quickstart.py -i                 # 交互模式
python quickstart.py -e 1               # 示例 1
python examples.py                      # 所有示例

# 测试
python quickstart.py --test             # 连接测试
python quickstart.py --check            # 依赖检查

# 开发
python -c "from integrated_controller import *; ..."
```

## 文件大小和行数

| 文件 | 行数 | 大小 | 说明 |
|------|------|------|------|
| llm_client.py | ~200 | 6 KB | LLM 集成 |
| airsim_controller.py | ~350 | 11 KB | AirSim 接口 |
| swarm_controller.py | ~350 | 12 KB | 控制算法 |
| sdf_executor.py | ~100 | 4 KB | SDF 执行 |
| integrated_controller.py | ~400 | 14 KB | 主控制器 |
| config.py | ~80 | 3 KB | 配置 |
| examples.py | ~300 | 10 KB | 示例代码 |
| **总计** | **~1,780** | **~60 KB** | |

## 相关资源

- 📖 [完整 README](README.md)
- 📋 [安装指南](INSTALL.md)
- 📊 [项目总结](PROJECT_SUMMARY.md)
- 🔗 [AirSim 文档](https://microsoft.github.io/AirSim/)
- 🔗 [SDF 库](https://github.com/fogleman/sdf)
- 🔗 [OpenAI API](https://openai.com/api/)

## 下一步

1. ✅ 运行 `diagnose.py` 验证安装
2. ✅ 运行 `quickstart.py --interactive` 体验系统
3. ✅ 研究 `examples.py` 中的示例
4. ✅ 自定义 `config.py` 中的参数
5. ✅ 开发你自己的应用！

---

**最后更新**: 2026 年 1 月 11 日  
**版本**: 1.0.0  
**状态**: 生产就绪 ✅
