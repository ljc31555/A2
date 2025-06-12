#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景描述增强器测试脚本

测试场景描述智能增强器的各项功能：
1. 技术细节分析
2. 一致性描述注入
3. 内容融合
"""

import os
import sys
import json

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

from processors.scene_description_enhancer import (
    SceneDescriptionEnhancer, 
    TechnicalDetailsAnalyzer, 
    ConsistencyInjector,
    TechnicalDetails,
    ConsistencyInfo
)
from utils.character_scene_manager import CharacterSceneManager
from utils.logger import logger


def test_technical_analyzer():
    """测试技术细节分析器"""
    print("\n=== 测试技术细节分析器 ===")
    
    analyzer = TechnicalDetailsAnalyzer()
    
    test_descriptions = [
        "叶文洁站在红岸基地的控制室中，特写她深邃的眼神",
        "从上往下俯拍整个实验室，科学家们忙碌工作",
        "阳光透过窗户洒在叶文洁的脸上，形成柔和的光影",
        "镜头缓缓推进，聚焦在叶文洁手中的文件上",
        "夜晚的北京城市全景，灯火通明"
    ]
    
    for i, desc in enumerate(test_descriptions, 1):
        print(f"\n测试 {i}: {desc}")
        details = analyzer.analyze_description(desc)
        print(f"分析结果: {details.to_description()}")


def test_consistency_injector():
    """测试一致性描述注入器"""
    print("\n=== 测试一致性描述注入器 ===")
    
    # 创建测试项目目录
    test_project_dir = os.path.join(project_root, 'output', '三体')
    
    if not os.path.exists(test_project_dir):
        print(f"测试项目目录不存在: {test_project_dir}")
        return
    
    # 初始化角色场景管理器
    char_scene_manager = CharacterSceneManager(test_project_dir)
    injector = ConsistencyInjector(char_scene_manager)
    
    test_descriptions = [
        "叶文洁在实验室中进行研究",
        "红岸基地的天线阵列在夜空中",
        "办公室里的会议正在进行",
        "叶文洁和汪淼在清华大学校园里交谈"
    ]
    
    for i, desc in enumerate(test_descriptions, 1):
        print(f"\n测试 {i}: {desc}")
        consistency_info = injector.extract_consistency_info(desc)
        print(f"一致性信息: {consistency_info.to_description()}")


def test_scene_enhancer():
    """测试场景描述增强器"""
    print("\n=== 测试场景描述增强器 ===")
    
    # 创建测试项目目录
    test_project_dir = os.path.join(project_root, 'output', '三体')
    
    if not os.path.exists(test_project_dir):
        print(f"测试项目目录不存在: {test_project_dir}")
        return
    
    # 初始化增强器
    enhancer = SceneDescriptionEnhancer(test_project_dir)
    
    test_cases = [
        {
            "description": "叶文洁站在控制室中",
            "characters": ["叶文洁"]
        },
        {
            "description": "红岸基地的天线在夜空中",
            "characters": []
        },
        {
            "description": "特写叶文洁的眼神，她正在思考",
            "characters": ["叶文洁"]
        },
        {
            "description": "从上往下拍摄整个实验室",
            "characters": []
        },
        {
            "description": "阳光透过窗户照在叶文洁脸上",
            "characters": ["叶文洁"]
        }
    ]
    
    # 测试不同配置
    configs = [
        {"name": "默认配置", "config": {}},
        {"name": "高级增强", "config": {"enhancement_level": "high"}},
        {"name": "结构化融合", "config": {"fusion_strategy": "structured"}},
        {"name": "最小化融合", "config": {"fusion_strategy": "minimal"}}
    ]
    
    for config_info in configs:
        print(f"\n--- {config_info['name']} ---")
        enhancer.update_config(**config_info['config'])
        
        for i, test_case in enumerate(test_cases, 1):
            original = test_case['description']
            characters = test_case['characters']
            
            enhanced = enhancer.enhance_description(original, characters)
            
            print(f"\n测试 {i}:")
            print(f"原始: {original}")
            print(f"增强: {enhanced}")
            print(f"角色: {characters}")


def test_config_options():
    """测试配置选项"""
    print("\n=== 测试配置选项 ===")
    
    test_project_dir = os.path.join(project_root, 'output', '三体')
    
    if not os.path.exists(test_project_dir):
        print(f"测试项目目录不存在: {test_project_dir}")
        return
    
    enhancer = SceneDescriptionEnhancer(test_project_dir)
    
    # 显示默认配置
    print(f"默认配置: {enhancer.get_config()}")
    
    # 测试配置更新
    test_configs = [
        {"enable_technical_details": False},
        {"enable_consistency_injection": False},
        {"enhancement_level": "low"},
        {"fusion_strategy": "structured"},
        {"enable_technical_details": True, "enable_consistency_injection": True}
    ]
    
    test_description = "叶文洁在实验室中进行特写拍摄"
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n配置 {i}: {config}")
        enhancer.update_config(**config)
        enhanced = enhancer.enhance_description(test_description, ["叶文洁"])
        print(f"结果: {enhanced}")


def main():
    """主测试函数"""
    print("场景描述增强器测试开始")
    print(f"项目根目录: {project_root}")
    
    try:
        # 测试技术细节分析器
        test_technical_analyzer()
        
        # 测试一致性描述注入器
        test_consistency_injector()
        
        # 测试场景描述增强器
        test_scene_enhancer()
        
        # 测试配置选项
        test_config_options()
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()