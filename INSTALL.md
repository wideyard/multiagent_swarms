# 安装和配置指南

## 目录
1. [系统要求](#系统要求)
2. [AirSim 安装](#airsim-安装)
3. [Python 环境设置](#python-环境设置)
4. [LLM API 配置](#llm-api-配置)
5. [验证安装](#验证安装)
6. [故障排除](#故障排除)

## 系统要求

### 硬件
- CPU: Intel i7 或更高
- GPU: NVIDIA RTX 2080 或更高（推荐用于 AirSim）
- RAM: 16GB 或更多
- 磁盘空间: 20GB+

### 软件
- Windows 10/11 或 Linux
- Python 3.8+
- AirSim 1.8.0+

## AirSim 安装

### Windows

1. **下载 AirSim**
   - 访问 [AirSim Releases](https://github.com/microsoft/AirSim/releases)
   - 下载最新的 Windows 版本

2. **配置多无人机模式**
   
   创建或编辑 `settings.json` 文件（通常在 `Documents\AirSim\` 目录）：

   ```json
   {
       "SettingsVersion": 1.2,
       "SimMode": "Multirotor",
       "Vehicles": {
           "Drone1": {
               "VehicleType": "SimpleFlight",
               "X": 0,
               "Y": 0,
               "Z": 0,
               "Yaw": 0
           },
           "Drone2": {
               "VehicleType": "SimpleFlight",
               "X": 1,
               "Y": 0,
               "Z": 0,
               "Yaw": 0
           },
           "Drone3": {
               "VehicleType": "SimpleFlight",
               "X": 0,
               "Y": 1,
               "Z": 0,
               "Yaw": 0
           },
           "Drone4": {
               "VehicleType": "SimpleFlight",
               "X": -1,
               "Y": 0,
               "Z": 0,
               "Yaw": 0
           }
       },
       "LocalHostIp": "127.0.0.1"
   }
   ```

3. **启动 AirSim**
   - 运行下载的 AirSim 可执行文件
   - 等待仿真环境加载

### Linux

```bash
# 克隆 AirSim 仓库
git clone https://github.com/microsoft/AirSim.git
cd AirSim

# 构建 AirSim
bash build.sh

# 配置设置文件
cp settings.json ~/.bashrc  # 或复制到适当位置

# 运行 AirSim
./build/linux/Binaries/AirSim/AirSim/Binaries/Linux/AirSim-linux
```

## Python 环境设置

### 1. 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv airsim_swarm_env

# 激活虚拟环境
# Windows:
airsim_swarm_env\Scripts\activate

# Linux/Mac:
source airsim_swarm_env/bin/activate
```

### 2. 安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 如果 sdf 包安装失败，尝试：
pip install git+https://github.com/fogleman/sdf.git@main
```

### 3. 验证安装

```bash
python -c "import airsim; import numpy; print('✓ Dependencies OK')"
```

## LLM API 配置

### OpenAI API

1. **获取 API 密钥**
   - 访问 [OpenAI 官网](https://openai.com/api/)
   - 创建账户并生成 API 密钥

2. **设置环境变量**

   Windows (PowerShell):
   ```powershell
   $env:OPENAI_API_KEY = "sk-..."
   $env:OPENAI_BASE_URL = "https://api.openai.com/v1"
   $env:LLM_MODEL = "gpt-3.5-turbo"
   ```

   Windows (CMD):
   ```cmd
   set OPENAI_API_KEY=sk-...
   set OPENAI_BASE_URL=https://api.openai.com/v1
   set LLM_MODEL=gpt-3.5-turbo
   ```

   Linux/Mac (Bash):
   ```bash
   export OPENAI_API_KEY="sk-..."
   export OPENAI_BASE_URL="https://api.openai.com/v1"
   export LLM_MODEL="gpt-3.5-turbo"
   ```

3. **持久化配置**

   创建 `.env` 文件（项目根目录）：
   ```
   OPENAI_API_KEY=sk-...
   OPENAI_BASE_URL=https://api.openai.com/v1
   LLM_MODEL=gpt-3.5-turbo
   ```

   安装 python-dotenv：
   ```bash
   pip install python-dotenv
   ```

   在 Python 代码中加载：
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

### 国内 API 服务（例如 Doubao）

```python
import os

os.environ["OPENAI_API_KEY"] = "your-api-key"
os.environ["OPENAI_BASE_URL"] = "https://ark.cn-beijing.volces.com/api/v3"
os.environ["LLM_MODEL"] = "doubao-seed-1-8-251228"

from llm_client import LLMClient

client = LLMClient()
```

## 验证安装

### 1. 检查依赖

```bash
python quickstart.py --check
```

### 2. 测试连接

```bash
python quickstart.py --test
```

这将测试：
- Python 依赖
- LLM API 连接
- AirSim 连接

### 3. 运行示例

```bash
# 列出所有可用示例
python examples.py

# 运行特定示例
python quickstart.py -e 1  # 基本用法
python quickstart.py -e 5  # 形状描述测试
```

### 4. 交互式测试

```bash
python quickstart.py --interactive
```

## 故障排除

### AirSim 连接错误

**问题**: `ConnectionRefusedError: [WinError 10061]`

**解决方案**:
1. 确保 AirSim 正在运行
2. 检查 `settings.json` 中的 `LocalHostIp` 是否为 `127.0.0.1`
3. 重启 AirSim 和 Python 脚本
4. 尝试增加连接超时：
   ```python
   client = airsim.MultirotorClient(ip="127.0.0.1")
   client.confirmConnection()
   ```

### LLM API 错误

**问题**: `AuthenticationError: Invalid API key`

**解决方案**:
1. 验证 API 密钥是否正确
2. 检查 API 额度是否用尽
3. 确保网络连接正常
4. 测试 API 连接：
   ```bash
   python -c "from llm_client import LLMClient; LLMClient().chat_completion([{'role': 'user', 'content': 'Hi'}])"
   ```

### SDF 库错误

**问题**: `ModuleNotFoundError: No module named 'sdf'`

**解决方案**:
```bash
pip install --upgrade git+https://github.com/fogleman/sdf.git@main
```

### 内存不足

**问题**: `MemoryError` 或点分配生成缓慢

**解决方案**:
1. 减少采样点数：
   ```python
   points = distributor.generate_points(num_points=4, num_samples=500)
   ```
2. 简化 SDF 形状
3. 增加系统 RAM

### 缓慢的 LLM 生成

**问题**: 生成 SDF 代码很慢

**解决方案**:
1. 检查网络延迟
2. 尝试更快的模型：
   ```python
   client = LLMClient(model="gpt-3.5-turbo")
   ```
3. 增加超时时间：
   ```python
   response = client.chat_completion(messages, temperature=0.5)
   ```

## 性能优化

### Python 优化

```python
# 使用 NumPy 向量化操作
import numpy as np

# 好的做法
velocities = np.array([v for v in velocities])

# 避免循环
for i in range(n):
    x[i] = y[i]  # 慢
x = y  # 快
```

### AirSim 优化

在 `settings.json` 中：
```json
{
    "ClockSpeed": 1.0,  # 1.0 = 实时，> 1.0 = 加速
    "EngineMaxFPS": 30,  # 限制 FPS 以节省 GPU
    "LevelName": "Soccer",  // 使用简单场景
}
```

### 并行化

使用多线程处理多架无人机：
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(drone.set_velocity, v) for drone, v in zip(drones, velocities)]
```

## 常见配置

### 4 架无人机配置

```json
{
    "Vehicles": {
        "Drone1": {"X": 0, "Y": 0, "Z": 0},
        "Drone2": {"X": 2, "Y": 0, "Z": 0},
        "Drone3": {"X": 0, "Y": 2, "Z": 0},
        "Drone4": {"X": 2, "Y": 2, "Z": 0}
    }
}
```

### 8 架无人机配置

```json
{
    "Vehicles": {
        "Drone1": {"X": 0, "Y": 0},
        "Drone2": {"X": 2, "Y": 0},
        "Drone3": {"X": 4, "Y": 0},
        "Drone4": {"X": 0, "Y": 2},
        "Drone5": {"X": 2, "Y": 2},
        "Drone6": {"X": 4, "Y": 2},
        "Drone7": {"X": 0, "Y": 4},
        "Drone8": {"X": 2, "Y": 4}
    }
}
```

## 下一步

1. 运行 `quickstart.py --test` 验证安装
2. 查看 [README.md](README.md) 了解基本用法
3. 运行 `examples.py` 中的示例
4. 开始构建自己的应用！

## 获取帮助

- 查看 [常见问题](FAQ.md)
- 访问 [AirSim 文档](https://microsoft.github.io/AirSim/)
- 检查 [sdf 库文档](https://github.com/fogleman/sdf)
- 提交 GitHub issue
