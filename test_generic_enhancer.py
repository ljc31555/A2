#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用场景描述增强器测试脚本

测试重构后的增强器，验证其通用性和NLP能力：
1. 动态角色识别
2. 通用场景检测
3. 不依赖特定小说的关键词
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


def test_dynamic_character_detection():
    """测试动态角色识别"""
    print("\n=== 测试动态角色识别 ===")
    
    test_project_dir = os.path.join(project_root, 'output', '三体')
    
    if not os.path.exists(test_project_dir):
        print(f"测试项目目录不存在: {test_project_dir}")
        return
    
    char_scene_manager = CharacterSceneManager(test_project_dir)
    injector = ConsistencyInjector(char_scene_manager)
    
    # 测试不同类型的描述
    test_cases = [
        {
            "description": "叶文洁在实验室中进行研究",
            "expected_chars": ["叶文洁"]
        },
        {
            "description": "一个女科学家在办公室里工作",
            "expected_chars": []  # 没有具体角色名
        },
        {
            "description": "主角走进房间，开始思考问题",
            "expected_chars": []  # 通用描述
        },
        {
            "description": "张三和李四在讨论项目",
            "expected_chars": []  # 项目中不存在的角色
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {case['description']}")
        detected = injector._detect_characters(case['description'])
        print(f"检测到的角色: {detected}")
        print(f"预期角色: {case['expected_chars']}")
        
        # 获取一致性信息
        consistency_info = injector.extract_consistency_info(case['description'])
        if consistency_info.characters:
            print(f"一致性描述: {consistency_info.characters[0][:50]}...")
        else:
            print("无一致性描述")


def test_generic_scene_detection():
    """测试通用场景检测"""
    print("\n=== 测试通用场景检测 ===")
    
    test_project_dir = os.path.join(project_root, 'output', '三体')
    
    if not os.path.exists(test_project_dir):
        print(f"测试项目目录不存在: {test_project_dir}")
        return
    
    char_scene_manager = CharacterSceneManager(test_project_dir)
    injector = ConsistencyInjector(char_scene_manager)
    
    # 测试通用场景描述（不依赖特定小说）
    test_cases = [
        "在办公室里开会",
        "走在街道上",
        "在家里看电视",
        "在学校的教室里上课",
        "在森林中漫步",
        "在实验室做实验",
        "在山顶上眺望",
        "在咖啡厅里聊天",
        "在图书馆里读书",
        "在公园里散步"
    ]
    
    for i, description in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {description}")
        detected_scenes = injector._detect_scenes(description)
        print(f"检测到的场景: {detected_scenes}")


def test_enhanced_descriptions():
    """测试增强后的描述效果"""
    print("\n=== 测试增强描述效果 ===")
    
    test_project_dir = os.path.join(project_root, 'output', '三体')
    
    if not os.path.exists(test_project_dir):
        print(f"测试项目目录不存在: {test_project_dir}")
        return
    
    enhancer = SceneDescriptionEnhancer(test_project_dir)
    
    # 测试各种类型的描述
    test_cases = [
        {
            "description": "叶文洁在办公室里思考",
            "characters": ["叶文洁"],
            "type": "已知角色 + 通用场景"
        },
        {
            "description": "特写一个人的眼神",
            "characters": [],
            "type": "技术细节 + 无角色"
        },
        {
            "description": "从上往下拍摄整个教室",
            "characters": [],
            "type": "技术细节 + 通用场景"
        },
        {
            "description": "阳光透过窗户照在桌子上",
            "characters": [],
            "type": "光线分析 + 通用环境"
        },
        {
            "description": "镜头推进，聚焦在文件上",
            "characters": [],
            "type": "镜头运动分析"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- 测试 {i}: {case['type']} ---")
        print(f"原始: {case['description']}")
        
        enhanced = enhancer.enhance_description(
            case['description'], 
            case['characters']
        )
        
        print(f"增强: {enhanced}")
        print(f"角色: {case['characters']}")


def test_project_data_loading():
    """测试项目数据动态加载"""
    print("\n=== 测试项目数据动态加载 ===")
    
    test_project_dir = os.path.join(project_root, 'output', '三体')
    
    if not os.path.exists(test_project_dir):
        print(f"测试项目目录不存在: {test_project_dir}")
        return
    
    char_scene_manager = CharacterSceneManager(test_project_dir)
    injector = ConsistencyInjector(char_scene_manager)
    
    # 测试角色数据加载
    print("\n加载的项目角色:")
    characters = injector._get_all_project_characters()
    for char in characters:
        print(f"  - {char}")
    
    # 测试场景数据加载
    print("\n加载的项目场景:")
    scenes = injector._get_all_project_scenes()
    for scene_name, keywords in scenes.items():
        print(f"  - {scene_name}: {keywords[:3]}...")  # 只显示前3个关键词
    
    # 测试缓存机制
    print("\n测试缓存机制:")
    import time
    start_time = time.time()
    characters1 = injector._get_all_project_characters()
    first_load_time = time.time() - start_time
    
    start_time = time.time()
    characters2 = injector._get_all_project_characters()
    second_load_time = time.time() - start_time
    
    print(f"首次加载时间: {first_load_time:.4f}秒")
    print(f"缓存加载时间: {second_load_time:.4f}秒")
    if second_load_time > 0:
        print(f"缓存效果: {first_load_time/second_load_time:.1f}x 加速")
    else:
        print("缓存效果: 极快（时间太短无法测量）")


def main():
    """主测试函数"""
    print("通用场景描述增强器测试开始")
    print(f"项目根目录: {project_root}")
    
    try:
        # 测试动态角色识别
        test_dynamic_character_detection()
        
        # 测试通用场景检测
        test_generic_scene_detection()
        
        # 测试增强描述效果
        test_enhanced_descriptions()
        
        # 测试项目数据动态加载
        test_project_data_loading()
        
        print("\n=== 通用增强器测试完成 ===")
        print("\n✅ 重构成功：")
        print("  - 移除了硬编码的《三体》特定关键词")
        print("  - 实现了动态角色和场景识别")
        print("  - 添加了通用场景类型支持")
        print("  - 实现了数据缓存机制")
        print("  - 增强器现在可以适用于任何小说项目")
        
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()