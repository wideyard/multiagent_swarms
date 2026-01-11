#!/usr/bin/env python3
"""
知识库内容查看工具
显示RAG系统中包含的所有领域知识
"""

def show_knowledge_base_content():
    """显示知识库的所有内容"""
    
    print("="*70)
    print("RAG系统知识库内容一览")
    print("="*70)
    
    # 内置知识库内容
    knowledge_contents = {
        "1. AirSim 无人机控制": {
            "概述": "AirSim API和多旋翼无人机控制方法",
            "包含内容": [
                "armDisarm(arm, vehicle_name): 电机上电/下电",
                "takeoff(vehicle_name): 起飞",
                "land(vehicle_name): 着陆",
                "moveToPosition(x, y, z, velocity, vehicle_name): 移动到目标位置",
                "getMultirotorState(vehicle_name): 获取无人机状态",
                "enableApiControl(is_enabled, vehicle_name): 启用/禁用API控制",
                "setSimulationMode(mode): 改变仿真模式"
            ]
        },
        
        "2. 无人机编队": {
            "概述": "多无人机编队技术和空间要求",
            "包含内容": [
                "栅格编队：规则网格排列，均匀间距",
                "圆形编队：围绕中心点排列",
                "V字编队：鸟类V字形，能量高效",
                "直线编队：直线排列",
                "安全最小距离：1-2米",
                "推荐间距：10+无人机时为2-3米",
                "编队直径：应该适应仿真空间"
            ]
        },
        
        "3. 路径点生成": {
            "概述": "无人机位置分布和点生成方法",
            "包含内容": [
                "均匀分布：规则网格间距",
                "随机分布：随机放置",
                "簇聚分布：多个簇群",
                "基于SDF分布：形状表面上的点",
                "L-BFGS-B优化：找到最优点位置",
                "K-means聚类：均匀分布簇",
                "采样：直接从形状采样点"
            ]
        },
        
        "4. SDF和3D形状": {
            "概述": "有符号距离函数和3D形状表示",
            "包含内容": [
                "SDF值：到最近表面的距离（外部为正，内部为负）",
                "常见形状：sphere, box, cylinder, torus, pyramid",
                "组合形状：并集、交集、差集",
                "表面上的点：SDF值 ≈ 0",
                "球体：半径（1-10个单位典型）",
                "立方体：宽、高、深",
                "圆柱体：半径、高度",
                "金字塔：底部大小、高度"
            ]
        },
        
        "5. 碰撞避免": {
            "概述": "多无人机碰撞避免策略",
            "包含内容": [
                "最小分离距离：0.5-1.0米",
                "避免半径：每个无人机2-3米",
                "速度限制：安全运行1-5 m/s",
                "安全边际：加20%缓冲到最小距离",
                "人工势场法：无人机间的排斥力",
                "速度障碍法：预测并避免碰撞",
                "分布式控制：每个无人机做本地决策"
            ]
        },
        
        "6. 任务描述指南": {
            "概述": "如何描述无人机群体任务",
            "包含内容": [
                "形状描述：清晰说明目标3D形状",
                "编队类型：指定编队排列方式",
                "执行时间：任务应该持续多长时间",
                "约束条件：高度限制、速度限制、空间限制",
                "示例1：Form a sphere with 10 drones, 5m diameter",
                "示例2：Create a cube formation with 2m spacing",
                "示例3：Arrange in circular pattern, 3m radius"
            ]
        },
        
        "7. 基础无人机知识": {
            "概述": "无人机的基本特性和操作",
            "包含内容": [
                "位置：(x, y, z)坐标",
                "速度：移动速度和方向",
                "电池电量：剩余电池百分比",
                "IMU传感器：惯性测量单元",
                "起飞：从地面上升",
                "着陆：降落到地面",
                "电机上电：准备飞行",
                "电机下电：停止电机"
            ]
        },
        
        "8. 群体控制": {
            "概述": "多无人机协调控制",
            "包含内容": [
                "编队飞行：无人机保持编队",
                "分布式控制：每个无人机做本地决策",
                "共识算法：无人机同意目标",
                "碰撞避免：保持安全距离"
            ]
        },
        
        "9. 路径规划": {
            "概述": "无人机的路径规划算法",
            "包含内容": [
                "A*：基于网格的路径查找",
                "RRT：快速探索随机树",
                "人工势场法(APF)：物理启发的方法",
                "轨迹优化：平滑路径"
            ]
        },
        
        "10. 仿真环境": {
            "概述": "AirSim模拟器的功能",
            "包含内容": [
                "基于API的控制",
                "多无人机支持",
                "物理仿真",
                "传感器仿真（相机、激光雷达、GPS）"
            ]
        }
    }
    
    # 打印知识库内容
    total_docs = 0
    total_items = 0
    
    for category, content in knowledge_contents.items():
        print(f"\n{category}")
        print("-" * 70)
        print(f"  概述: {content['概述']}")
        print(f"  包含内容:")
        
        for item in content['包含内容']:
            print(f"    • {item}")
            total_items += 1
        
        total_docs += 1
    
    # 统计信息
    print("\n" + "="*70)
    print("知识库统计")
    print("="*70)
    print(f"  • 知识类别数: {total_docs}")
    print(f"  • 知识点数: {total_items}")
    print(f"  • 主要语言: 中文 + English")
    print(f"  • 涵盖领域: 无人机控制、编队、路径规划、碰撞避免、SDF形状")
    
    # 使用建议
    print("\n" + "="*70)
    print("知识库查询示例")
    print("="*70)
    print("""
  查询1: "无人机如何保持安全距离？"
    → 返回: 碰撞避免知识
    
  查询2: "如何排列10架无人机成立方体？"
    → 返回: 编队、路径点生成知识
    
  查询3: "SDF形状参数是什么？"
    → 返回: SDF和3D形状知识
    
  查询4: "无人机的基本操作有哪些？"
    → 返回: AirSim控制、基础知识
    
  查询5: "如何描述一个无人机群体任务？"
    → 返回: 任务描述指南知识
    """)
    
    # 扩展建议
    print("\n" + "="*70)
    print("扩展知识库的方法")
    print("="*70)
    print("""
  方法1: 直接添加文档
  ─────────────────────
  from rag_system import QwenEmbedding, KnowledgeBase
  
  embedding = QwenEmbedding()
  kb = KnowledgeBase(embedding, "my_kb")
  kb.add_document("你的知识内容...", {"type": "custom"})
  kb.save_to_cache()
  
  
  方法2: 从文件加载知识
  ─────────────────────
  kb.add_documents_from_file("knowledge.txt", chunk_size=500)
  
  
  方法3: 使用字典批量添加
  ─────────────────────
  docs = {
      "主题1": "内容1",
      "主题2": "内容2"
  }
  kb.add_documents_from_dict(docs)
    """)


if __name__ == "__main__":
    show_knowledge_base_content()
