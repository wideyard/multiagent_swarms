# 无人机形状显示问题修复 - 坐标系统转换

## 问题描述

从图片可以看到，10架无人机都分布在地面的一个平面上，没有形成3D立方体形状。

![无人机分布在地面](../attachments/drones_on_ground.jpg)

## 根本原因

### 1. **坐标系统不匹配**

**SDF生成的坐标**：
- 单位立方体，边长为1
- 中心在原点 (0, 0, 0)
- Z值范围：[-0.5, 0.5]

```python
Waypoints:
 [[ 0.256, -0.300, -0.500]   # Z = -0.5米
  [ 0.279,  0.500,  0.352]   # Z =  0.35米
  [-0.500, -0.316, -0.367]   # Z = -0.37米
  ...]
  
Z values: [-0.5, 0.35, -0.37, 0.5, -0.26, ...]  # 范围只有1米！
```

**AirSim NED坐标系**：
- NED = North-East-Down
- **Z轴负值向上**：
  - `z = 0` → 地面
  - `z = -5` → 海拔5米
  - `z = -10` → 海拔10米
- 起飞后无人机通常在 `z = -2` 到 `z = -5`

### 2. **直接使用相对坐标导致的问题**

```python
# 修复前的代码
self.goal_positions = self.point_distributor.generate_points(num_points)
# 生成的坐标：z ∈ [-0.5, 0.5]

# 在 AirSim 中
swarm.set_positions(goal_positions)  
# 无人机飞向 z=0.5 和 z=-0.5，都接近地面！
```

**视觉效果**：
- 立方体高度只有1米（从-0.5到0.5）
- 在 AirSim 中接近地面
- 看起来像所有无人机都在地面的一个平面上

---

## 解决方案

### 修复策略

1. **缩放形状**：将单位形状放大到合适的尺寸
2. **平移高度**：将形状中心移到安全的飞行高度
3. **坐标转换**：从相对坐标转换到 AirSim NED 坐标

### 代码修复

```python
# 生成相对坐标
waypoints_relative = self.point_distributor.generate_points(num_points)
# Z值范围：[-0.5, 0.5]

# 缩放：放大10倍
self.goal_positions = waypoints_relative * self.shape_scale  # scale=10
# Z值范围变为：[-5.0, 5.0]

# 平移：将中心移到海拔10米（AirSim中z=-10）
self.goal_positions[:, 2] = self.goal_positions[:, 2] - self.flight_altitude  # altitude=10
# Z值范围变为：[-15.0, -5.0]，即海拔5米到15米
```

### 转换示例

| 阶段 | X坐标 | Y坐标 | Z坐标 | 说明 |
|------|-------|-------|-------|------|
| SDF生成 | 0.5 | 0.5 | 0.5 | 立方体顶角，单位：米 |
| 缩放×10 | 5.0 | 5.0 | 5.0 | 放大10倍 |
| 平移-10 | 5.0 | 5.0 | -5.0 | 在AirSim中表示海拔5米 |

```
原始立方体（1m×1m×1m）       缩放后（10m×10m×10m）
       ┌─────┐                       ┌──────────┐
       │     │ z=0.5                 │          │ z=-5 (海拔5m)
   ────┼─────┼────              ─────┼──────────┼───── z=-10 (海拔10m)
       │     │ z=-0.5                │          │ z=-15 (海拔15m)
       └─────┘                       └──────────┘
```

---

## 配置参数

现在可以调整两个关键参数：

### `shape_scale` (形状缩放)
- **默认值**：10.0
- **含义**：SDF单位长度对应的实际米数
- **示例**：
  - `scale=10`：1单位立方体 → 10米立方体
  - `scale=5`：1单位立方体 → 5米立方体
  - `scale=20`：1单位立方体 → 20米立方体

### `flight_altitude` (飞行高度)
- **默认值**：10.0米
- **含义**：形状中心的海拔高度
- **示例**：
  - `altitude=10`：形状中心在海拔10米
  - `altitude=15`：形状中心在海拔15米
  - `altitude=5`：形状中心在海拔5米

---

## 使用方法

### 方法1：交互式设置

```bash
python quickstart.py -i
```

```
> set scale 10
> set altitude 10
> shape A cube with 1 unit side length
> start
```

### 方法2：代码中设置

```python
from src.integrated_controller import LLMAirSimSwarmController

controller = LLMAirSimSwarmController(drone_names, verbose=True)

# 设置参数
controller.set_shape_parameters(scale=10, altitude=10)

# 准备任务
controller.prepare_mission("A cube with 1 unit side length")

# 启动
controller.start_mission()
```

---

## 预期效果

修复后，运行：

```bash
python quickstart.py -i
```

```
> shape A cube with 1 unit side length
> start
```

**现在应该看到**：
1. ✅ 10架无人机同时起飞到约5米高度
2. ✅ 无人机飞向各自的目标位置
3. ✅ 形成一个**10米×10米×10米**的立方体
4. ✅ 立方体中心在**海拔10米**
5. ✅ 无人机悬停在空中，保持立方体形状

**立方体的位置**：
- X范围：[-5, 5] 米
- Y范围：[-5, 5] 米
- Z范围：[-15, -5]（AirSim NED）= 海拔 [5, 15] 米

---

## 调试信息

修复后的日志会显示详细的转换信息：

```
[LLMAirSimSwarm] Generating 10 waypoints from SDF...
[PointDistributor] Estimated bounds: min=[-1. -1. -1.], max=[1. 1. 1.]

[LLMAirSimSwarm] Generated waypoints shape: (10, 3)
[LLMAirSimSwarm] Original SDF waypoints (relative, unit scale):
[[ 0.256 -0.300 -0.500]
 [ 0.279  0.500  0.352]
 ...]

[LLMAirSimSwarm] Transformed waypoints (AirSim NED coordinates):
[[  2.56  -3.00 -15.00]   ← 缩放10x，平移-10
 [  2.79   5.00  -6.48]
 ...]

[LLMAirSimSwarm]   Scale: 10.0x, Center altitude: 10.0m
```

---

## 常见问题

### Q1: 为什么无人机还是太低？
**A**: 增加 `flight_altitude`：
```
> set altitude 15
> shape A cube
> start
```

### Q2: 为什么立方体太小/太大？
**A**: 调整 `shape_scale`：
```
> set scale 20    # 更大的形状
> set scale 5     # 更小的形状
```

### Q3: 无人机飞出视野怎么办？
**A**: 减小缩放或检查 AirSim 摄像机位置：
```
> set scale 5
> set altitude 8
```

---

## 修改的文件

1. **src/integrated_controller.py**
   - 添加 `shape_scale` 和 `flight_altitude` 参数
   - 在 `generate_waypoints()` 中添加坐标转换
   - 添加 `set_shape_parameters()` 方法
   - 在交互模式添加 `set scale` 和 `set altitude` 命令

---

## 技术细节

### AirSim 坐标系（NED）

```
     North (+X)
        ↑
        |
        |
        └──────→ East (+Y)
       /
      /
     ↓
   Down (+Z)  ← 注意：Z正向是向下！

高度关系：
- 地面：z = 0
- 空中：z < 0（负值）
- 海拔h米：z = -h
```

### 坐标转换公式

```python
# 步骤1：生成SDF相对坐标
waypoints_sdf = generate_points(n)  # 范围约 [-0.5, 0.5]

# 步骤2：缩放
waypoints_scaled = waypoints_sdf * scale

# 步骤3：Z轴平移到飞行高度
waypoints_airsim = waypoints_scaled.copy()
waypoints_airsim[:, 2] -= altitude  # NED: 减去altitude得到负的z值

# 示例：
# SDF:    (0.5, 0.5, 0.5)
# 缩放:   (5.0, 5.0, 5.0)  [scale=10]
# AirSim: (5.0, 5.0, -5.0) [altitude=10, 所以5-10=-5]
#         表示：东5米，北5米，海拔5米
```
