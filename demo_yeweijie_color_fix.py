#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
叶文洁角色颜色一致性问题解决演示
展示如何解决角色描述中出现多个颜色的问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.color_optimizer import ColorOptimizer
from src.utils.logger import logger

def demo_yeweijie_color_issue():
    """演示叶文洁角色颜色问题及解决方案"""
    print("\n👩‍🔬 叶文洁角色颜色一致性问题演示")
    print("=" * 60)
    
    optimizer = ColorOptimizer()
    
    # 模拟用户描述的问题场景
    print("\n📝 问题描述:")
    print("用户反馈：叶文洁（中年女性，黑色短发，深邃的眼睛，穿着灰色或深蓝色简约服装）")
    print("在生成的描述中还是同时出现了两个颜色")
    
    # 模拟原始角色数据（包含多个颜色）
    original_character = {
        "name": "叶文洁",
        "description": "中年女性，黑色短发，深邃的眼睛",
        "clothing": {
            "style": "简约服装",
            "colors": ["灰色", "深蓝色"]  # 问题：多个颜色
        }
    }
    
    print(f"\n🔍 原始角色数据:")
    print(f"姓名: {original_character['name']}")
    print(f"服装颜色: {original_character['clothing']['colors']}")
    
    # 解决方案1：自动优化角色颜色数据
    print("\n🔧 解决方案1: 自动优化角色颜色数据")
    optimized_character = optimizer.optimize_character_colors(original_character.copy())
    print(f"优化后颜色: {optimized_character['clothing']['colors']}")
    
    # 解决方案2：场景描述中的颜色一致性处理
    print("\n🔧 解决方案2: 场景描述颜色一致性处理")
    
    # 模拟生成的场景描述（包含多个颜色）
    problematic_descriptions = [
        "叶文洁穿着灰色或深蓝色简约服装，站在实验室中进行研究",
        "叶文洁身着灰色和深蓝色的职业装，神情专注地查看数据",
        "实验室里，叶文洁穿着灰色、深蓝色相间的服装工作",
        "叶文洁穿着简约服装，在房间里思考问题"  # 无颜色描述
    ]
    
    primary_color = optimizer.get_character_primary_color(optimized_character)
    print(f"主要颜色: {primary_color}")
    
    print("\n场景描述优化对比:")
    for i, desc in enumerate(problematic_descriptions, 1):
        enhanced = optimizer.apply_color_consistency_to_description(
            desc, "叶文洁", primary_color
        )
        print(f"\n示例 {i}:")
        print(f"问题描述: {desc}")
        print(f"优化描述: {enhanced}")
        
        # 检查是否还有多个颜色
        color_count = sum(1 for color in optimizer.color_priority.keys() if color in enhanced)
        if color_count <= 1:
            print(f"✅ 颜色一致性: 通过 (颜色数量: {color_count})")
        else:
            print(f"❌ 颜色一致性: 失败 (颜色数量: {color_count})")

def demo_gui_auto_optimization():
    """演示GUI自动优化功能"""
    print("\n🖥️ GUI自动优化功能演示")
    print("=" * 60)
    
    optimizer = ColorOptimizer()
    
    print("\n📋 用户操作流程:")
    print("1. 用户在角色编辑界面输入: '灰色, 深蓝色'")
    print("2. 输入框失去焦点时自动触发优化")
    print("3. 系统自动选择主要颜色")
    
    # 模拟用户输入
    user_input = "灰色, 深蓝色"
    print(f"\n用户输入: '{user_input}'")
    
    # 模拟auto_optimize_colors方法
    if ',' in user_input or len([c for c in user_input.split() if any(color in c for color in optimizer.color_priority.keys())]) > 1:
        primary_color = optimizer.extract_primary_color(user_input)
        if primary_color and primary_color != user_input:
            print(f"✅ 自动优化为: '{primary_color}'")
            print("💡 用户无需手动操作，系统自动完成优化")
        else:
            print("⚠️ 优化失败，保持原输入")
    else:
        print("ℹ️ 单一颜色，无需优化")
    
    print("\n📱 用户体验特点:")
    print("✅ 傻瓜式操作 - 用户只需输入，系统自动处理")
    print("✅ 静默优化 - 不弹出干扰性提示框")
    print("✅ 保留手动按钮 - 高级用户仍可手动优化")
    print("✅ 加载时自动处理 - 历史数据自动优化")

def demo_complete_workflow():
    """演示完整的工作流程"""
    print("\n🔄 完整工作流程演示")
    print("=" * 60)
    
    optimizer = ColorOptimizer()
    
    print("\n步骤1: 用户创建/编辑角色")
    print("- 用户在GUI中输入角色信息")
    print("- 在'主要颜色'字段输入: '灰色, 深蓝色'")
    print("- 输入框失去焦点时自动优化为: '灰色'")
    
    print("\n步骤2: 保存角色数据")
    print("- 系统再次确保颜色数据一致性")
    print("- 角色数据中只保存单一主要颜色")
    
    print("\n步骤3: 生成场景描述")
    print("- 场景描述生成时应用颜色一致性")
    print("- 确保描述中只出现主要颜色")
    
    # 模拟完整流程
    test_description = "叶文洁穿着灰色或深蓝色简约服装，在实验室中工作"
    primary_color = "灰色"
    
    enhanced_description = optimizer.apply_color_consistency_to_description(
        test_description, "叶文洁", primary_color
    )
    
    print(f"\n🎯 最终结果:")
    print(f"原始描述: {test_description}")
    print(f"优化描述: {enhanced_description}")
    
    # 验证结果
    color_mentions = [color for color in optimizer.color_priority.keys() if color in enhanced_description]
    print(f"\n✅ 验证结果: 描述中的颜色 = {color_mentions}")
    print(f"✅ 颜色一致性: {'通过' if len(set(color_mentions)) <= 1 else '失败'}")

def main():
    """主演示函数"""
    print("🎨 叶文洁角色颜色一致性问题解决方案")
    print("=" * 70)
    
    try:
        # 1. 问题演示和解决方案
        demo_yeweijie_color_issue()
        
        # 2. GUI自动优化功能
        demo_gui_auto_optimization()
        
        # 3. 完整工作流程
        demo_complete_workflow()
        
        print("\n🎉 演示完成!")
        print("\n💡 解决方案总结:")
        print("1. ✅ GUI输入框自动优化 - 失去焦点时自动选择主要颜色")
        print("2. ✅ 加载时自动处理 - 历史角色数据自动优化")
        print("3. ✅ 场景描述一致性 - 生成时替换多颜色为主要颜色")
        print("4. ✅ 保存时确保一致性 - 角色数据只保存单一颜色")
        print("5. ✅ 用户友好界面 - 傻瓜式操作，无需手动设置")
        
        print("\n🚀 用户体验改进:")
        print("- 用户只需输入颜色，系统自动处理")
        print("- 不再出现多颜色描述问题")
        print("- 保持界面简洁，减少用户操作")
        print("- 兼容历史数据，自动升级")
        
    except Exception as e:
        logger.error(f"演示失败: {e}")
        print(f"❌ 演示失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)