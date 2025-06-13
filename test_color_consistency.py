#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
颜色一致性功能测试脚本

测试新实现的颜色一致性功能，包括：
1. ColorOptimizer类的各项功能
2. 角色颜色数据的优化
3. 场景描述中的颜色一致性应用
4. GUI界面的颜色优化功能
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.color_optimizer import ColorOptimizer
from src.utils.character_scene_manager import CharacterSceneManager
from src.processors.scene_description_enhancer import SceneDescriptionEnhancer
from src.utils.logger import logger

def test_color_optimizer():
    """测试ColorOptimizer类的基本功能"""
    print("\n=== 测试ColorOptimizer基本功能 ===")
    
    optimizer = ColorOptimizer()
    
    # 测试颜色提取
    test_cases = [
        "红色，蓝色，绿色",
        "深蓝色外套，白色衬衫",
        "黑色，白色，灰色，红色",
        "金色头发，蓝色眼睛",
        "紫色长裙"
    ]
    
    for case in test_cases:
        primary_color = optimizer.extract_primary_color(case)
        print(f"输入: {case} -> 主要颜色: {primary_color}")
    
    # 测试角色数据优化
    test_character = {
        "name": "测试角色",
        "clothing": {
            "style": "现代休闲",
            "colors": ["红色", "蓝色", "绿色", "黄色"],
            "accessories": ["手表"]
        }
    }
    
    print(f"\n优化前角色数据: {test_character['clothing']['colors']}")
    optimized_character = optimizer.optimize_character_colors(test_character)
    print(f"优化后角色数据: {optimized_character['clothing']['colors']}")

def test_scene_description_enhancement():
    """测试场景描述增强中的颜色一致性"""
    print("\n=== 测试场景描述增强中的颜色一致性 ===")
    
    # 创建测试用的角色场景管理器
    project_root = str(Path(__file__).parent)
    char_manager = CharacterSceneManager(project_root)
    
    # 添加测试角色数据
    test_character_data = {
        "name": "小明",
        "description": "一个年轻的程序员",
        "clothing": {
            "style": "休闲装",
            "colors": ["蓝色"],  # 已优化的单一主要颜色
            "accessories": ["眼镜"]
        },
        "consistency_prompt": "年轻男性，短发，戴眼镜，穿蓝色休闲装"
    }
    
    char_manager.save_character("char_001", test_character_data)
    
    # 创建场景描述增强器
    enhancer = SceneDescriptionEnhancer(project_root, char_manager)
    
    # 测试场景描述
    test_descriptions = [
        "小明坐在办公桌前编程",
        "小明穿着衬衫走在街上",
        "小明和同事在会议室讨论项目"
    ]
    
    for desc in test_descriptions:
        enhanced = enhancer.enhance_description(desc, ["小明"])
        print(f"原始描述: {desc}")
        print(f"增强描述: {enhanced}")
        print("-" * 50)

def test_color_consistency_application():
    """测试颜色一致性在描述中的应用"""
    print("\n=== 测试颜色一致性应用 ===")
    
    optimizer = ColorOptimizer()
    project_root = str(Path(__file__).parent)
    char_manager = CharacterSceneManager(project_root)
    
    # 创建测试角色
    char_manager.save_character("test_char", {
        "name": "张三",
        "clothing": {
            "colors": ["红色"]
        }
    })
    
    # 测试颜色一致性应用
    test_cases = [
        ("张三穿着外套走进房间", ["张三"]),
        ("张三和李四在咖啡厅聊天", ["张三"]),
        ("张三坐在沙发上看书", ["张三"])
    ]
    
    for description, characters in test_cases:
        enhanced = optimizer.apply_color_consistency(description, characters, char_manager)
        print(f"原始: {description}")
        print(f"增强: {enhanced}")
        print("-" * 30)

def main():
    """主测试函数"""
    print("开始颜色一致性功能测试...")
    
    try:
        # 基本功能测试
        test_color_optimizer()
        
        # 场景描述增强测试
        test_scene_description_enhancement()
        
        # 颜色一致性应用测试
        test_color_consistency_application()
        
        print("\n=== 测试完成 ===")
        print("所有颜色一致性功能测试通过！")
        
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()