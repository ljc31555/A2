#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import json
from core.project_manager import ProjectManager
from gui.five_stage_storyboard_tab import FiveStageStoryboardTab
from PyQt5.QtWidgets import QApplication

def test_stage_data_loading():
    """测试五阶段数据加载逻辑"""
    print("=== 测试五阶段数据加载逻辑 ===")
    
    # 创建QApplication实例
    app = QApplication(sys.argv)
    
    try:
        # 初始化项目管理器
        project_manager = ProjectManager()
        
        # 加载项目
        project_path = 'd:/AI_Video_Generator/output/four'
        print(f"加载项目: {project_path}")
        
        success = project_manager.load_project(project_path)
        if not success:
            print("项目加载失败")
            return
        
        print(f"项目加载成功: {project_manager.current_project.get('project_name', 'Unknown')}")
        
        # 检查项目数据结构
        project_data = project_manager.current_project
        if 'five_stage_storyboard' in project_data:
            five_stage_data = project_data['five_stage_storyboard']
            print(f"五阶段数据键: {list(five_stage_data.keys())}")
            
            if 'stage_data' in five_stage_data:
                stage_data = five_stage_data['stage_data']
                print(f"阶段数据键: {list(stage_data.keys())}")
                
                # 检查第4阶段数据
                if '4' in stage_data:
                    stage4 = stage_data['4']
                    print(f"第4阶段数据键: {list(stage4.keys())}")
                    
                    if 'storyboard_results' in stage4:
                        storyboard_results = stage4['storyboard_results']
                        print(f"分镜结果数量: {len(storyboard_results)}")
                        
                        if storyboard_results:
                            first_result = storyboard_results[0]
                            print(f"第一个分镜结果键: {list(first_result.keys())}")
                            print(f"场景信息: {first_result.get('scene_info', 'N/A')}")
                            
                            # 测试数据加载逻辑
                            print("\n=== 测试数据加载逻辑 ===")
                            loaded_stage_data = five_stage_data.get('stage_data', {})
                            test_stage_data = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}}
                            test_stage_data.update(loaded_stage_data)
                            
                            print(f"加载后的stage_data键: {list(test_stage_data.keys())}")
                            print(f"第4阶段数据存在: {bool(test_stage_data.get(4))}")
                            
                            if test_stage_data.get(4):
                                stage4_test = test_stage_data[4]
                                print(f"第4阶段包含键: {list(stage4_test.keys())}")
                                print(f"storyboard_results存在: {'storyboard_results' in stage4_test}")
                                
                                if 'storyboard_results' in stage4_test:
                                    results = stage4_test['storyboard_results']
                                    print(f"storyboard_results长度: {len(results)}")
                                    print(f"数据类型: {type(results)}")
                                    print(f"是否为空: {not results}")
                                    
                                    # 测试条件检查
                                    condition1 = not test_stage_data.get(4)
                                    condition2 = not results
                                    print(f"\n条件检查:")
                                    print(f"  not stage_data.get(4): {condition1}")
                                    print(f"  not storyboard_results: {condition2}")
                                    print(f"  总条件 (应该为False): {condition1 or condition2}")
                        else:
                            print("storyboard_results为空")
                    else:
                        print("第4阶段没有storyboard_results")
                else:
                    print("没有第4阶段数据")
            else:
                print("没有stage_data")
        else:
            print("项目中没有五阶段数据")
            
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        app.quit()

if __name__ == '__main__':
    test_stage_data_loading()