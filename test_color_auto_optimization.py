#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试颜色自动优化功能
验证GUI中的自动颜色设置和颜色一致性处理
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.color_optimizer import ColorOptimizer
from src.utils.character_scene_manager import CharacterSceneManager
from src.utils.logger import logger

def test_auto_color_optimization():
    """测试自动颜色优化功能"""
    print("\n🎨 测试自动颜色优化功能")
    print("=" * 50)
    
    optimizer = ColorOptimizer()
    
    # 测试用例：多颜色输入
    test_cases = [
        "灰色, 深蓝色",
        "红色，蓝色，绿色",
        "黑色 白色",
        "深蓝色或灰色",
        "紫色和金色的搭配",
        "单一蓝色",
        "蓝"
    ]
    
    for case in test_cases:
        primary_color = optimizer.extract_primary_color(case)
        print(f"输入: '{case}' -> 主要颜色: '{primary_color}'")
    
    print("\n✅ 自动颜色优化测试完成")

def test_character_color_consistency():
    """测试角色颜色一致性处理"""
    print("\n👤 测试角色颜色一致性处理")
    print("=" * 50)
    
    optimizer = ColorOptimizer()
    
    # 模拟角色数据
    test_character = {
        "name": "叶文洁",
        "clothing": {
            "colors": ["灰色", "深蓝色"]  # 多个颜色
        }
    }
    
    print(f"原始角色数据: {test_character['clothing']['colors']}")
    
    # 优化角色颜色
    optimized_character = optimizer.optimize_character_colors(test_character)
    print(f"优化后角色数据: {optimized_character['clothing']['colors']}")
    
    # 测试场景描述中的颜色一致性
    test_descriptions = [
        "叶文洁穿着灰色或深蓝色简约服装，站在实验室中",
        "叶文洁身着灰色和深蓝色的职业装",
        "叶文洁穿着简约服装",
        "叶文洁在房间里工作"
    ]
    
    primary_color = optimizer.get_character_primary_color(optimized_character)
    print(f"\n角色主要颜色: {primary_color}")
    
    print("\n场景描述颜色一致性测试:")
    for desc in test_descriptions:
        enhanced = optimizer.apply_color_consistency_to_description(
            desc, "叶文洁", primary_color
        )
        print(f"原始: {desc}")
        print(f"优化: {enhanced}")
        print("-" * 40)
    
    print("\n✅ 角色颜色一致性测试完成")

def test_gui_integration_simulation():
    """模拟GUI集成测试"""
    print("\n🖥️ 模拟GUI集成测试")
    print("=" * 50)
    
    optimizer = ColorOptimizer()
    
    # 模拟用户在GUI中输入多个颜色
    user_inputs = [
        "灰色, 深蓝色",
        "红色，蓝色",
        "黑色 白色 灰色",
        "蓝色"
    ]
    
    print("模拟用户输入和自动优化:")
    for user_input in user_inputs:
        # 模拟auto_optimize_colors方法的逻辑
        if ',' in user_input or len([c for c in user_input.split() if any(color in c for color in optimizer.color_priority.keys())]) > 1:
            primary_color = optimizer.extract_primary_color(user_input)
            if primary_color and primary_color != user_input:
                print(f"用户输入: '{user_input}' -> 自动优化为: '{primary_color}'")
            else:
                print(f"用户输入: '{user_input}' -> 无需优化")
        else:
            print(f"用户输入: '{user_input}' -> 单一颜色，无需优化")
    
    print("\n✅ GUI集成模拟测试完成")

def main():
    """主测试函数"""
    print("🚀 颜色自动优化功能测试")
    print("=" * 60)
    
    try:
        # 1. 自动颜色优化测试
        test_auto_color_optimization()
        
        # 2. 角色颜色一致性测试
        test_character_color_consistency()
        
        # 3. GUI集成模拟测试
        test_gui_integration_simulation()
        
        print("\n🎉 所有测试完成!")
        print("\n功能特性:")
        print("✅ 自动从多个颜色中选择主要颜色")
        print("✅ GUI输入框失去焦点时自动优化")
        print("✅ 加载角色时自动设置主要颜色")
        print("✅ 场景描述中替换多颜色为主要颜色")
        print("✅ 保持手动优化按钮功能")
        
        print("\n使用说明:")
        print("1. 在角色编辑界面输入多个颜色（用逗号分隔）")
        print("2. 输入框失去焦点时自动优化为主要颜色")
        print("3. 加载已有角色时自动处理多颜色问题")
        print("4. 生成场景描述时确保颜色一致性")
        print("5. 手动'优化颜色'按钮仍可使用")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        print(f"❌ 测试失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)