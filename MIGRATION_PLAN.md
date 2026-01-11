# 项目重组迁移计划

## 📋 任务概述

将现有的 `airsim_swarm_llm` 项目重组为更清晰的目录结构：
- `src/` - 源代码（Python模块）
- `docs/` - 文档（Markdown文件）
- 根目录 - 主要运行脚本和配置文件

## ✅ 完成清单

### 已完成
- [x] 创建 `src/` 目录
- [x] 创建 `docs/` 目录
- [x] 创建新的综合 README (包含RAG内容)

### 待完成
- [ ] 将 Python 文件移动到 `src/`
- [ ] 将文档文件移动到 `docs/`
- [ ] 在根目录创建 `main.py` (主运行脚本)
- [ ] 更新所有导入路径
- [ ] 创建 `__init__.py` 文件
- [ ] 验证所有脚本可正常运行

## 🔄 文件迁移映射

### Python 源代码 → src/
```
Current → New Location
─────────────────────────────────────
llm_client.py → src/llm_client.py
airsim_controller.py → src/airsim_controller.py
swarm_controller.py → src/swarm_controller.py
sdf_executor.py → src/sdf_executor.py
integrated_controller.py → src/integrated_controller.py
config.py → src/config.py
rag_system.py → src/rag_system.py
rag_integration.py → src/rag_integration.py
rag_examples.py → src/rag_examples.py
```

### 文档文件 → docs/
```
Current → New Location
────────────────────────────────
README.md → docs/README.md (旧版保留)
INSTALL.md → docs/INSTALL.md
PROJECT_SUMMARY.md → docs/PROJECT_SUMMARY.md
QUICKREF.md → docs/QUICKREF.md
RAG_README.md → docs/RAG_README.md
MANIFEST.md → docs/MANIFEST.md
COMPLETION_REPORT.md → docs/COMPLETION_REPORT.md (已在docs)
docs/COMPLETION_REPORT.md → docs/COMPLETION_REPORT.md (保持)
```

### 根目录运行脚本（保留或创建）
```
quickstart.py → 保留 (根目录)
diagnose.py → 保留 (根目录)
examples.py → 保留 (根目录)
show_knowledge_base.py → 保留 (根目录)
rag_quickstart.py → 保留 (根目录)
test_airsim_simple.py → 保留 (根目录)
main.py → 新建 (根目录) ← 主入口脚本
launcher.py → 保留 (根目录)
```

### 配置和其他
```
requirements.txt → 保留 (根目录)
settings.json → 保留 (根目录)
.env.example → 保留 (根目录)
README.md → 新版 (根目录) ← 综合说明书 (包含RAG)
```

## 🔧 导入路径更新

所有导入需要更新以支持新的 `src/` 结构：

```python
# 旧的导入方式
from llm_client import LLMClient
from integrated_controller import LLMAirSimSwarmController

# 新的导入方式
from src.llm_client import LLMClient
from src.integrated_controller import LLMAirSimSwarmController
```

### 需要更新导入的文件
- `quickstart.py`
- `diagnose.py`
- `examples.py`
- `show_knowledge_base.py`
- `rag_quickstart.py`
- `rag_examples.py`
- `integrated_controller.py` (内部导入)
- `rag_integration.py` (内部导入)

## 📝 主要脚本说明

### 根目录脚本用途

| 脚本 | 用途 | 启动方式 |
|------|------|---------|
| **main.py** | 主运行脚本（待创建） | `python main.py` |
| **quickstart.py** | 快速启动和诊断 | `python quickstart.py --interactive` |
| **diagnose.py** | 环境诊断 | `python diagnose.py` |
| **examples.py** | 代码示例 | `python examples.py` |
| **show_knowledge_base.py** | 显示RAG知识库 | `python show_knowledge_base.py` |
| **rag_quickstart.py** | RAG快速启动 | `python rag_quickstart.py` |
| **test_airsim_simple.py** | AirSim连接测试 | `python test_airsim_simple.py` |

## 📁 最终项目结构

```
airsim_swarm_llm/
├── src/                                    ✨ 源代码目录
│   ├── __init__.py                        (空或导出主类)
│   ├── llm_client.py
│   ├── airsim_controller.py
│   ├── swarm_controller.py
│   ├── sdf_executor.py
│   ├── integrated_controller.py
│   ├── config.py
│   ├── rag_system.py
│   ├── rag_integration.py
│   └── rag_examples.py
│
├── docs/                                   ✨ 文档目录
│   ├── README.md                          (详细说明)
│   ├── INSTALL.md
│   ├── API_REFERENCE.md
│   ├── QUICKREF.md
│   ├── RAG_README.md
│   ├── PROJECT_SUMMARY.md
│   ├── COMPLETION_REPORT.md
│   └── MANIFEST.md
│
├── 根目录主脚本                            ✨ 可执行脚本
│   ├── main.py                           (新建)
│   ├── quickstart.py
│   ├── diagnose.py
│   ├── examples.py
│   ├── show_knowledge_base.py
│   ├── rag_quickstart.py
│   ├── test_airsim_simple.py
│   └── launcher.py
│
├── 配置和依赖                              ← 保留在根目录
│   ├── requirements.txt
│   ├── settings.json
│   ├── .env.example
│   └── README.md                         (新版综合说明)
│
└── __pycache__/                           (Python缓存)
```

## 🚀 迁移步骤

### 步骤 1: 创建新的main.py
```python
#!/usr/bin/env python3
"""
主运行脚本 - LLM AirSim Swarm Controller
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from integrated_controller import LLMAirSimSwarmController

def main():
    """主程序入口"""
    print("="*70)
    print("LLM AirSim Drone Swarm Controller - Main Launcher")
    print("="*70)
    print("\nUsage:")
    print("  python main.py --help          Show help")
    print("  python main.py --interactive   Interactive mode")
    print("  python main.py --test          Test connections")
    print("\nOr use other scripts:")
    print("  python quickstart.py --interactive")
    print("  python diagnose.py")
    print("  python show_knowledge_base.py")
    print("\nFor more info, see: docs/README.md")
    print("="*70)

if __name__ == "__main__":
    main()
```

### 步骤 2: 更新所有导入
在所有根目录脚本中，将:
```python
from integrated_controller import ...
```
改为:
```python
from src.integrated_controller import ...
```

### 步骤 3: 创建src/__init__.py
```python
"""
LLM AirSim Swarm Controller - Source Package
"""

from .integrated_controller import LLMAirSimSwarmController
from .llm_client import LLMClient, SDFGenerator
from .airsim_controller import AirSimSwarmController
from .rag_integration import RAGEnhancedLLMClient

__all__ = [
    'LLMAirSimSwarmController',
    'LLMClient',
    'SDFGenerator',
    'AirSimSwarmController',
    'RAGEnhancedLLMClient',
]
```

## ✨ 新增的README内容（RAG部分）

新的根目录 README.md 应包含：

1. **简介** - 项目概述（包含RAG）
2. **快速开始** - 3分钟入门
3. **主要功能** - 列出RAG作为新增功能
4. **项目结构** - 展示新的src/docs结构
5. **配置** - LLM API + RAG配置
6. **RAG知识库** - 新增章节，说明知识库内容
7. **使用示例** - 包含RAG示例
8. **常见问题** - 包含RAG相关问题
9. **系统架构** - 显示RAG组件
10. **文档导航** - 链接到docs/

## 📊 验证清单

迁移完成后，验证：

- [ ] 所有Python文件可正常导入
- [ ] 所有根目录脚本可正常运行
  - [ ] `python main.py`
  - [ ] `python quickstart.py --test`
  - [ ] `python diagnose.py`
  - [ ] `python examples.py`
  - [ ] `python show_knowledge_base.py`
- [ ] 文档可正常访问
  - [ ] docs/README.md 存在
  - [ ] docs/RAG_README.md 存在
  - [ ] 所有链接有效
- [ ] 新的README包含RAG内容
- [ ] 导入路径全部正确

## 🎯 预期效果

迁移完成后：
1. ✅ 代码结构更清晰（src/ + docs/）
2. ✅ 文档更易查找（集中在docs/）
3. ✅ 易于进阶学习（清晰的模块组织）
4. ✅ RAG功能完全集成（新README说明）
5. ✅ 更专业的项目组织

## 📝 后续维护

迁移完成后的维护建议：
- 保持src/和docs/目录的一致性
- 新增功能时同步更新docs/
- 定期更新README中的示例
- 添加新依赖时更新requirements.txt

---

**预计工作量**: 2-3 小时完成全部迁移和验证
**难度等级**: 低（主要是文件移动和导入更新）
**备份建议**: 迁移前备份原目录结构
