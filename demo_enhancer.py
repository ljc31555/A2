#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景描述增强器演示脚本
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

from processors.scene_description_enhancer import SceneDescriptionEnhancer

def main():
    print("=== 场景描述增强器演示 ===")
    
    # 初始化增强器
    enhancer = SceneDescriptionEnhancer('output/三体')
    
    # 演示案例
    test_cases = [
        {
            "original": "叶文洁站在控制室中",
            "characters": ["叶文洁"]
        },
        {
            "original": "特写叶文洁的眼神",
            "characters": ["叶文洁"]
        },
        {
            "original": "从上往下拍摄实验室",
            "characters": []
        },
        {
            "original": "阳光照在叶文洁脸上",
            "characters": ["叶文洁"]
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- 演示 {i} ---")
        print(f"原始描述: {case['original']}")
        print(f"涉及角色: {case['characters']}")
        
        enhanced = enhancer.enhance_description(case['original'], case['characters'])
        print(f"增强后: {enhanced}")
    
    print("\n=== 演示完成 ===")

if __name__ == "__main__":
    main()