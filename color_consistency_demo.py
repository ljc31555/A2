#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
颜色一致性功能演示脚本

展示新实现的颜色一致性功能在实际场景中的应用效果
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.color_optimizer import ColorOptimizer
from src.utils.character_scene_manager import CharacterSceneManager
from src.processors.scene_description_enhancer import SceneDescriptionEnhancer

def demo_color_optimization():
    """演示颜色优化功能"""
    print("\n🎨 颜色优化功能演示")
    print("=" * 50)
    
    optimizer = ColorOptimizer()
    
    # 演示多颜色输入的优化
    demo_cases = [
        "红色，蓝色，绿色，黄色，紫色",
        "深蓝色外套，白色衬衫，黑色裤子",
        "金色头发，蓝色眼睛，红色唇膏",
        "紫色长裙，银色高跟鞋"
    ]
    
    for case in demo_cases:
        primary = optimizer.extract_primary_color(case)
        print(f"📝 输入颜色: {case}")
        print(f"✨ 优化结果: {primary}")
        print("-" * 30)

def demo_character_consistency():
    """演示角色一致性功能"""
    print("\n👤 角色一致性功能演示")
    print("=" * 50)
    
    # 创建角色场景管理器
    project_root = str(Path(__file__).parent)
    char_manager = CharacterSceneManager(project_root)
    
    # 创建演示角色
    characters = {
        "小红": {
            "name": "小红",
            "description": "活泼的女学生",
            "clothing": {
                "style": "校服",
                "colors": ["红色"],
                "accessories": ["书包"]
            },
            "consistency_prompt": "年轻女学生，长发，穿红色校服"
        },
        "老王": {
            "name": "老王",
            "description": "经验丰富的工程师",
            "clothing": {
                "style": "商务装",
                "colors": ["蓝色"],
                "accessories": ["眼镜", "公文包"]
            },
            "consistency_prompt": "中年男性，短发，戴眼镜，穿蓝色西装"
        }
    }
    
    # 保存角色数据
    for char_id, char_data in characters.items():
        char_manager.save_character(char_id, char_data)
        print(f"✅ 已创建角色: {char_data['name']} (主要颜色: {char_data['clothing']['colors'][0]})")
    
    return char_manager

def demo_scene_enhancement(char_manager):
    """演示场景描述增强功能"""
    print("\n🎬 场景描述增强演示")
    print("=" * 50)
    
    # 创建场景描述增强器
    project_root = str(Path(__file__).parent)
    enhancer = SceneDescriptionEnhancer(project_root, char_manager)
    
    # 演示场景
    demo_scenes = [
        {
            "description": "小红走进教室",
            "characters": ["小红"],
            "scene_type": "校园场景"
        },
        {
            "description": "老王在办公室开会",
            "characters": ["老王"],
            "scene_type": "办公场景"
        },
        {
            "description": "小红和老王在咖啡厅讨论项目",
            "characters": ["小红", "老王"],
            "scene_type": "社交场景"
        },
        {
            "description": "小红穿着制服参加毕业典礼",
            "characters": ["小红"],
            "scene_type": "正式场景"
        }
    ]
    
    for i, scene in enumerate(demo_scenes, 1):
        print(f"\n📋 场景 {i}: {scene['scene_type']}")
        print(f"📝 原始描述: {scene['description']}")
        
        enhanced = enhancer.enhance_description(
            scene['description'], 
            scene['characters']
        )
        
        print(f"✨ 增强描述: {enhanced}")
        print(f"👥 涉及角色: {', '.join(scene['characters'])}")
        print("-" * 40)

def demo_gui_integration():
    """演示GUI集成功能"""
    print("\n🖥️ GUI集成功能说明")
    print("=" * 50)
    
    features = [
        "✅ 角色编辑界面新增'优化颜色'按钮",
        "✅ 自动从多个颜色中选择主要颜色",
        "✅ 保存时自动应用颜色优化",
        "✅ 实时显示优化后的颜色信息",
        "✅ 场景描述生成时自动应用颜色一致性"
    ]
    
    for feature in features:
        print(feature)
    
    print("\n💡 使用方法:")
    print("1. 打开角色场景管理对话框")
    print("2. 在'主要颜色'字段输入多个颜色（用逗号分隔）")
    print("3. 点击'优化颜色'按钮或直接保存")
    print("4. 系统会自动选择并保留主要颜色")
    print("5. 在生成分镜脚本时，角色服装颜色会自动保持一致")

def main():
    """主演示函数"""
    print("🌟 AI视频生成器 - 颜色一致性功能演示")
    print("=" * 60)
    
    try:
        # 1. 颜色优化演示
        demo_color_optimization()
        
        # 2. 角色一致性演示
        char_manager = demo_character_consistency()
        
        # 3. 场景描述增强演示
        demo_scene_enhancement(char_manager)
        
        # 4. GUI集成说明
        demo_gui_integration()
        
        print("\n🎉 演示完成！")
        print("颜色一致性功能已成功集成到AI视频生成器中。")
        print("现在可以确保角色在不同场景中的服装颜色保持一致。")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()