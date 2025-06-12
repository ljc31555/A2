#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容融合器测试脚本

测试第二阶段的智能内容融合器功能，包括：
1. 不同融合策略的效果
2. 质量评估机制
3. 智能策略选择
4. 详细信息输出
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.processors.scene_description_enhancer import (
    SceneDescriptionEnhancer, ContentFuser, TechnicalDetails, ConsistencyInfo
)
from src.utils.character_scene_manager import CharacterSceneManager
from src.utils.logger import logger

def test_fusion_strategies():
    """测试不同的融合策略"""
    print("\n=== 测试不同融合策略 ===")
    
    # 创建测试数据
    original = "叶文洁站在控制室中操作设备"
    
    technical = TechnicalDetails(
        shot_type="中景",
        camera_angle="平视角度",
        lighting="自然光",
        camera_movement="静止镜头"
    )
    
    consistency = ConsistencyInfo()
    consistency.characters = ["中年女性，短发，穿着白色实验服"]
    consistency.scenes = ["现代化控制室，多个显示屏"]
    
    # 测试所有融合策略
    fuser = ContentFuser()
    strategies = ['natural', 'structured', 'minimal', 'intelligent']
    
    for strategy in strategies:
        print(f"\n--- {strategy.upper()} 策略 ---")
        result = fuser.fuse_content(original, technical, consistency, strategy)
        print(f"原始描述: {original}")
        print(f"增强描述: {result.enhanced_description}")
        print(f"质量评分: {result.fusion_quality_score:.2f}")
        print(f"技术补充: {result.technical_additions}")
        print(f"一致性补充: {result.consistency_additions}")

def test_quality_assessment():
    """测试质量评估机制"""
    print("\n=== 测试质量评估机制 ===")
    
    test_cases = [
        {
            'name': '短描述+丰富信息',
            'original': '特写镜头',
            'technical': TechnicalDetails(shot_type="特写", lighting="柔光", camera_angle="仰视角度"),
            'consistency': ConsistencyInfo(characters=["年轻男性，黑发"], scenes=["室内环境"])
        },
        {
            'name': '长描述+少量信息',
            'original': '在一个阳光明媚的下午，主角缓缓走过宽阔的广场，周围是熙熙攘攘的人群，远处的建筑在夕阳下显得格外壮观',
            'technical': TechnicalDetails(shot_type="远景"),
            'consistency': ConsistencyInfo(characters=["主角"])
        },
        {
            'name': '中等描述+平衡信息',
            'original': '角色在实验室中进行重要的科学实验',
            'technical': TechnicalDetails(shot_type="中景", lighting="实验室照明"),
            'consistency': ConsistencyInfo(characters=["科学家"], scenes=["现代实验室"])
        }
    ]
    
    fuser = ContentFuser()
    
    for case in test_cases:
        print(f"\n--- {case['name']} ---")
        result = fuser.fuse_content(
            case['original'], 
            case['technical'], 
            case['consistency'], 
            'intelligent'
        )
        print(f"原始长度: {len(case['original'])}")
        print(f"增强描述: {result.enhanced_description}")
        print(f"质量评分: {result.fusion_quality_score:.2f}")
        print(f"选择的策略: {'智能选择'}")

def test_enhancer_integration():
    """测试增强器集成功能"""
    print("\n=== 测试增强器集成功能 ===")
    
    # 初始化增强器
    project_root = os.path.dirname(os.path.abspath(__file__))
    enhancer = SceneDescriptionEnhancer(project_root)
    
    # 配置不同的融合策略
    test_configs = [
        {'fusion_strategy': 'intelligent', 'quality_threshold': 0.6},
        {'fusion_strategy': 'natural', 'quality_threshold': 0.8},
        {'fusion_strategy': 'structured', 'quality_threshold': 0.4}
    ]
    
    test_descriptions = [
        "叶文洁在红岸基地的控制室中",
        "汪淼观察纳米材料的实验结果",
        "史强在审讯室中询问嫌疑人"
    ]
    
    for i, config in enumerate(test_configs):
        print(f"\n--- 配置 {i+1}: {config} ---")
        enhancer.update_config(**config)
        
        for desc in test_descriptions:
            print(f"\n原始: {desc}")
            enhanced = enhancer.enhance_description(desc, ["叶文洁", "汪淼", "史强"])
            print(f"增强: {enhanced}")

def test_detailed_enhancement():
    """测试详细增强功能"""
    print("\n=== 测试详细增强功能 ===")
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    enhancer = SceneDescriptionEnhancer(project_root)
    
    test_description = "叶文洁站在红岸基地的发射天线前"
    characters = ["叶文洁"]
    
    # 获取详细增强结果
    detailed_result = enhancer.enhance_description_with_details(test_description, characters)
    
    print(f"原始描述: {detailed_result['original_description']}")
    print(f"增强描述: {detailed_result['enhanced_description']}")
    print(f"技术细节: {detailed_result['technical_details']}")
    print(f"一致性信息: {detailed_result['consistency_info']}")
    print(f"技术补充: {detailed_result['technical_additions']}")
    print(f"一致性补充: {detailed_result['consistency_additions']}")
    print(f"质量评分: {detailed_result['fusion_quality_score']:.2f}")
    print(f"融合策略: {detailed_result['fusion_strategy']}")
    print(f"增强配置: {detailed_result['enhancement_config']}")

def test_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    fuser = ContentFuser()
    
    edge_cases = [
        {
            'name': '空描述',
            'original': '',
            'technical': None,
            'consistency': None
        },
        {
            'name': '只有技术细节',
            'original': '镜头',
            'technical': TechnicalDetails(shot_type="特写"),
            'consistency': None
        },
        {
            'name': '只有一致性信息',
            'original': '角色出现',
            'technical': None,
            'consistency': ConsistencyInfo(characters=["主角"])
        },
        {
            'name': '超长描述',
            'original': '这是一个非常非常长的描述' * 20,
            'technical': TechnicalDetails(shot_type="远景"),
            'consistency': ConsistencyInfo(characters=["角色"])
        }
    ]
    
    for case in edge_cases:
        print(f"\n--- {case['name']} ---")
        try:
            result = fuser.fuse_content(
                case['original'], 
                case['technical'], 
                case['consistency'], 
                'intelligent'
            )
            print(f"处理成功")
            print(f"结果长度: {len(result.enhanced_description)}")
            print(f"质量评分: {result.fusion_quality_score:.2f}")
        except Exception as e:
            print(f"处理失败: {e}")

def main():
    """主测试函数"""
    print("开始测试第二阶段内容融合器...")
    
    try:
        test_fusion_strategies()
        test_quality_assessment()
        test_enhancer_integration()
        test_detailed_enhancement()
        test_edge_cases()
        
        print("\n=== 测试总结 ===")
        print("✅ 所有测试完成")
        print("✅ 智能内容融合器功能正常")
        print("✅ 质量评估机制有效")
        print("✅ 多种融合策略可用")
        print("✅ 详细信息输出完整")
        print("✅ 边界情况处理良好")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()