#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二阶段场景描述增强器演示脚本

展示智能内容融合器的实际应用效果，包括：
1. 智能融合策略选择
2. 质量评估和控制
3. 详细信息输出
4. 不同类型内容的处理
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.processors.scene_description_enhancer import SceneDescriptionEnhancer
from src.utils.character_scene_manager import CharacterSceneManager

def demo_intelligent_fusion():
    """演示智能融合功能"""
    print("\n" + "="*60)
    print("第二阶段场景描述增强器 - 智能内容融合演示")
    print("="*60)
    
    # 初始化增强器
    project_root = os.path.dirname(os.path.abspath(__file__))
    enhancer = SceneDescriptionEnhancer(project_root)
    
    # 配置智能融合策略
    enhancer.update_config(
        fusion_strategy='intelligent',
        quality_threshold=0.6,
        enhancement_level='high'
    )
    
    # 测试不同类型的场景描述
    test_scenarios = [
        {
            'category': '科幻场景',
            'descriptions': [
                "叶文洁在红岸基地的控制室中启动发射程序",
                "汪淼通过VR眼镜观察三体世界的模拟",
                "智子在地球轨道上展开二维形态"
            ],
            'characters': ['叶文洁', '汪淼']
        },
        {
            'category': '日常场景',
            'descriptions': [
                "主角在咖啡厅中与朋友交谈",
                "女主角独自走在夜晚的街道上",
                "老教授在图书馆中查阅资料"
            ],
            'characters': ['主角', '女主角', '老教授']
        },
        {
            'category': '动作场景',
            'descriptions': [
                "特工快速穿越屋顶追击目标",
                "战斗机在云层中进行空中格斗",
                "主角在爆炸中紧急逃生"
            ],
            'characters': ['特工', '主角']
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n--- {scenario['category']} ---")
        
        for i, description in enumerate(scenario['descriptions'], 1):
            print(f"\n{i}. 原始描述: {description}")
            
            # 基础增强
            enhanced = enhancer.enhance_description(description, scenario['characters'])
            print(f"   增强结果: {enhanced}")
            
            # 获取详细信息
            details = enhancer.enhance_description_with_details(description, scenario['characters'])
            print(f"   质量评分: {details['fusion_quality_score']:.2f}")
            print(f"   技术补充: {details['technical_additions']}")
            print(f"   一致性补充: {details['consistency_additions']}")

def demo_quality_control():
    """演示质量控制机制"""
    print("\n" + "="*60)
    print("质量控制机制演示")
    print("="*60)
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    enhancer = SceneDescriptionEnhancer(project_root)
    
    # 测试不同质量阈值
    quality_thresholds = [0.3, 0.6, 0.9]
    test_description = "角色出现在场景中"
    
    for threshold in quality_thresholds:
        print(f"\n--- 质量阈值: {threshold} ---")
        enhancer.update_config(quality_threshold=threshold)
        
        details = enhancer.enhance_description_with_details(test_description, ['角色'])
        print(f"原始描述: {details['original_description']}")
        print(f"增强描述: {details['enhanced_description']}")
        print(f"质量评分: {details['fusion_quality_score']:.2f}")
        print(f"是否达标: {'✅' if details['fusion_quality_score'] >= threshold else '❌'}")

def demo_fusion_strategies():
    """演示不同融合策略"""
    print("\n" + "="*60)
    print("融合策略对比演示")
    print("="*60)
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    enhancer = SceneDescriptionEnhancer(project_root)
    
    test_description = "叶文洁站在红岸基地的巨大天线前思考人类的命运"
    characters = ['叶文洁']
    
    strategies = {
        'natural': '自然融合 - 流畅自然的描述',
        'structured': '结构化融合 - 清晰分层的信息',
        'minimal': '最小化融合 - 简洁紧凑的表达',
        'intelligent': '智能融合 - 自适应最佳策略'
    }
    
    for strategy, description in strategies.items():
        print(f"\n--- {strategy.upper()} 策略 ({description}) ---")
        enhancer.update_config(fusion_strategy=strategy)
        
        details = enhancer.enhance_description_with_details(test_description, characters)
        print(f"增强结果: {details['enhanced_description']}")
        print(f"质量评分: {details['fusion_quality_score']:.2f}")
        print(f"结果长度: {len(details['enhanced_description'])} 字符")

def demo_performance_comparison():
    """演示性能对比"""
    print("\n" + "="*60)
    print("第一阶段 vs 第二阶段 对比演示")
    print("="*60)
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    enhancer = SceneDescriptionEnhancer(project_root)
    
    test_cases = [
        {
            'description': "短描述",
            'text': "特写镜头"
        },
        {
            'description': "中等描述",
            'text': "叶文洁在控制室中操作复杂的设备"
        },
        {
            'description': "长描述",
            'text': "在一个阳光明媚的下午，叶文洁缓缓走向红岸基地的主控制室，她的脸上带着坚定而复杂的表情，准备执行这个将改变人类命运的重要任务"
        }
    ]
    
    for case in test_cases:
        print(f"\n--- {case['description']} ---")
        print(f"原始: {case['text']}")
        
        # 第一阶段效果（简单融合）
        enhancer.update_config(fusion_strategy='natural')
        simple_result = enhancer.enhance_description(case['text'], ['叶文洁'])
        
        # 第二阶段效果（智能融合）
        enhancer.update_config(fusion_strategy='intelligent')
        details = enhancer.enhance_description_with_details(case['text'], ['叶文洁'])
        
        print(f"第一阶段: {simple_result}")
        print(f"第二阶段: {details['enhanced_description']}")
        print(f"质量提升: {details['fusion_quality_score']:.2f}")
        print(f"信息密度: {len(details['technical_additions']) + len(details['consistency_additions'])} 项补充")

def demo_real_world_application():
    """演示实际应用场景"""
    print("\n" + "="*60)
    print("实际应用场景演示")
    print("="*60)
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    enhancer = SceneDescriptionEnhancer(project_root)
    
    # 模拟五阶段分镜脚本的画面描述
    storyboard_scenes = [
        {
            'stage': '开场',
            'description': '叶文洁年轻时在清华大学的物理实验室',
            'characters': ['叶文洁']
        },
        {
            'stage': '发展',
            'description': '汪淼在纳米中心观察实验数据的异常',
            'characters': ['汪淼']
        },
        {
            'stage': '高潮',
            'description': '三体舰队在太空中排列成巨大的阵型',
            'characters': []
        },
        {
            'stage': '转折',
            'description': '史强带领作战小组突袭三体组织据点',
            'characters': ['史强']
        },
        {
            'stage': '结局',
            'description': '地球防务理事会召开紧急会议讨论对策',
            'characters': []
        }
    ]
    
    enhancer.update_config(
        fusion_strategy='intelligent',
        quality_threshold=0.7,
        enhancement_level='high'
    )
    
    for scene in storyboard_scenes:
        print(f"\n--- {scene['stage']}阶段 ---")
        details = enhancer.enhance_description_with_details(
            scene['description'], 
            scene['characters']
        )
        
        print(f"原始描述: {details['original_description']}")
        print(f"增强描述: {details['enhanced_description']}")
        print(f"技术规格: {details['technical_details']}")
        print(f"一致性要求: {details['consistency_info']}")
        print(f"质量评分: {details['fusion_quality_score']:.2f}")
        print(f"融合策略: {details['fusion_strategy']}")

def main():
    """主演示函数"""
    print("🎬 第二阶段场景描述增强器演示")
    print("📈 智能内容融合 + 质量控制 + 策略优化")
    
    try:
        demo_intelligent_fusion()
        demo_quality_control()
        demo_fusion_strategies()
        demo_performance_comparison()
        demo_real_world_application()
        
        print("\n" + "="*60)
        print("演示总结")
        print("="*60)
        print("✅ 智能内容融合器：根据内容特点自动选择最佳融合策略")
        print("✅ 质量评估机制：实时评估融合质量，确保输出标准")
        print("✅ 多策略支持：自然、结构化、最小化、智能四种策略")
        print("✅ 详细信息输出：提供完整的增强过程和质量指标")
        print("✅ 实际应用就绪：可直接集成到五阶段分镜系统")
        print("\n🎯 第二阶段开发完成！内容融合器已就绪。")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()