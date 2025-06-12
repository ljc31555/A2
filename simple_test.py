#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    print("开始简单测试...")
    
    # 检查项目目录
    projects_dir = project_root / 'output'
    print(f"项目目录: {projects_dir}")
    print(f"项目目录存在: {projects_dir.exists()}")
    
    if projects_dir.exists():
        # 列出项目目录内容
        print("项目目录内容:")
        for item in projects_dir.iterdir():
            print(f"  - {item.name}")
        
        # 检查four项目
        four_project = projects_dir / 'four'
        print(f"\nfour项目目录: {four_project}")
        print(f"four项目存在: {four_project.exists()}")
        
        if four_project.exists():
            project_json = four_project / 'project.json'
            print(f"project.json存在: {project_json.exists()}")
            
            if project_json.exists():
                try:
                    import json
                    with open(project_json, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    print(f"项目名称: {data.get('name', 'Unknown')}")
                    print(f"项目数据键: {list(data.keys())}")
                    
                    # 检查五阶段数据
                    if 'five_stage_storyboard' in data:
                        five_stage = data['five_stage_storyboard']
                        print(f"五阶段数据键: {list(five_stage.keys())}")
                        
                        if 'storyboard_results' in five_stage:
                            results = five_stage['storyboard_results']
                            print(f"storyboard_results类型: {type(results)}")
                            print(f"storyboard_results长度: {len(results) if isinstance(results, (list, dict)) else 'N/A'}")
                    else:
                        print("没有五阶段数据")
                        
                except Exception as e:
                    print(f"读取项目文件出错: {e}")
    
    print("测试完成")

if __name__ == '__main__':
    main()