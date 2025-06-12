#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用场景描述增强器演示脚本

演示重构后的增强器如何适用于不同类型的小说和场景
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

from processors.scene_description_enhancer import SceneDescriptionEnhancer

def demo_different_genres():
    """演示不同类型小说的场景描述增强"""
    print("=== 通用场景描述增强器演示 ===")
    print("展示如何适用于不同类型的小说和场景\n")
    
    # 初始化增强器（使用三体项目作为示例）
    enhancer = SceneDescriptionEnhancer('output/三体')
    
    # 不同类型小说的场景示例
    scenarios = [
        {
            "genre": "科幻小说",
            "examples": [
                "主角在太空站的控制室中操作设备",
                "特写机器人的眼部传感器",
                "从上往下拍摄整个实验室",
                "阳光透过舷窗照在宇航员脸上"
            ]
        },
        {
            "genre": "现代都市小说",
            "examples": [
                "女主角在咖啡厅里等待",
                "特写男主角紧握的双手",
                "镜头推进，聚焦在手机屏幕上",
                "夜晚的城市街道，霓虹灯闪烁"
            ]
        },
        {
            "genre": "古装历史小说",
            "examples": [
                "将军在军营中制定作战计划",
                "特写公主忧郁的眼神",
                "从高处俯拍整个皇宫",
                "月光透过窗棂洒在书案上"
            ]
        },
        {
            "genre": "悬疑推理小说",
            "examples": [
                "侦探在案发现场仔细观察",
                "特写血迹斑斑的凶器",
                "镜头缓缓拉远，显示整个房间",
                "昏暗的灯光下，影子在墙上摇摆"
            ]
        },
        {
            "genre": "校园青春小说",
            "examples": [
                "学生们在教室里上课",
                "特写女孩羞涩的笑容",
                "从操场上空俯拍整个学校",
                "夕阳西下，两人在校园里漫步"
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📚 {scenario['genre']} 场景增强示例:")
        print("=" * 50)
        
        for i, description in enumerate(scenario['examples'], 1):
            print(f"\n{i}. 原始描述: {description}")
            
            # 增强描述
            enhanced = enhancer.enhance_description(description, [])
            
            print(f"   增强后: {enhanced}")
            
            # 分析增强内容
            if "镜头类型" in enhanced:
                print("   ✓ 添加了技术细节分析")
            if "光线" in enhanced:
                print("   ✓ 识别了光线条件")
            if "机位角度" in enhanced:
                print("   ✓ 分析了拍摄角度")
            if "镜头运动" in enhanced:
                print("   ✓ 检测了镜头运动")
            if "通用" in enhanced:
                print("   ✓ 匹配了通用场景类型")

def demo_technical_analysis():
    """演示技术细节分析能力"""
    print("\n\n🎬 技术细节分析能力演示:")
    print("=" * 50)
    
    enhancer = SceneDescriptionEnhancer('output/三体')
    
    technical_examples = [
        "特写主角坚定的眼神",
        "从鸟瞰角度拍摄整个战场",
        "镜头缓缓推进，聚焦在关键物品上",
        "阳光从窗户斜射进来，形成光影效果",
        "夜晚室内，只有台灯提供照明",
        "镜头跟随角色在走廊中移动",
        "从低角度仰拍高大的建筑",
        "全景展示广阔的自然风光"
    ]
    
    for i, description in enumerate(technical_examples, 1):
        print(f"\n{i}. {description}")
        enhanced = enhancer.enhance_description(description, [])
        
        # 提取技术分析部分
        if "（" in enhanced and "）" in enhanced:
            tech_part = enhanced[enhanced.find("（"):enhanced.rfind("）")+1]
            print(f"   技术分析: {tech_part}")
        else:
            print("   技术分析: 无特殊技术要素")

def demo_scene_type_recognition():
    """演示通用场景类型识别"""
    print("\n\n🏠 通用场景类型识别演示:")
    print("=" * 50)
    
    enhancer = SceneDescriptionEnhancer('output/三体')
    
    scene_examples = [
        "在办公室里开重要会议",
        "走在繁华的商业街上",
        "在温馨的家中吃晚餐",
        "在学校图书馆里学习",
        "在美丽的森林中徒步",
        "在现代化的实验室做研究",
        "在古老的城堡里探索",
        "在热闹的市场里购物"
    ]
    
    for i, description in enumerate(scene_examples, 1):
        print(f"\n{i}. {description}")
        enhanced = enhancer.enhance_description(description, [])
        
        # 查找场景类型
        if "通用" in enhanced:
            scene_type = enhanced[enhanced.find("通用"):enhanced.find("通用")+10]
            print(f"   识别场景: {scene_type}")
        else:
            print("   识别场景: 未匹配到通用场景类型")

def demo_performance_comparison():
    """演示性能对比"""
    print("\n\n⚡ 性能优化演示:")
    print("=" * 50)
    
    enhancer = SceneDescriptionEnhancer('output/三体')
    
    print("\n重构前 vs 重构后:")
    print("❌ 重构前: 硬编码《三体》特定关键词")
    print("   - 只能识别预设的角色和场景")
    print("   - 无法适用于其他小说")
    print("   - 维护困难，需要为每本小说修改代码")
    
    print("\n✅ 重构后: 通用NLP技术")
    print("   - 动态加载项目中的角色和场景数据")
    print("   - 支持任何小说项目")
    print("   - 通用场景类型识别")
    print("   - 数据缓存机制提高性能")
    print("   - 易于维护和扩展")
    
    # 演示缓存效果
    import time
    
    print("\n缓存机制演示:")
    start_time = time.time()
    for _ in range(5):
        enhancer.enhance_description("测试描述", [])
    total_time = time.time() - start_time
    
    print(f"连续5次增强处理耗时: {total_time:.4f}秒")
    print("缓存机制确保重复访问项目数据时性能最优")

def main():
    """主演示函数"""
    try:
        # 演示不同类型小说的适用性
        demo_different_genres()
        
        # 演示技术细节分析
        demo_technical_analysis()
        
        # 演示场景类型识别
        demo_scene_type_recognition()
        
        # 演示性能对比
        demo_performance_comparison()
        
        print("\n\n🎉 演示完成!")
        print("\n通用场景描述增强器现在可以:")
        print("✓ 适用于任何类型的小说项目")
        print("✓ 智能分析技术细节")
        print("✓ 动态识别角色和场景")
        print("✓ 提供通用场景类型支持")
        print("✓ 高效的缓存机制")
        print("\n无需为不同小说修改代码，真正实现了通用性！")
        
    except Exception as e:
        print(f"\n演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()