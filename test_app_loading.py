#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow
from core.project_manager import ProjectManager
import time

def test_app_loading():
    """测试应用程序加载项目的完整流程"""
    print("=== 测试应用程序加载项目流程 ===")
    
    # 创建QApplication实例
    app = QApplication(sys.argv)
    
    try:
        # 创建主窗口
        main_window = MainWindow()
        
        # 等待界面初始化完成
        app.processEvents()
        time.sleep(1)
        
        # 获取五阶段分镜标签页
        five_stage_tab = main_window.five_stage_tab
        
        # 加载项目
        project_path = 'd:/AI_Video_Generator/output/four'
        print(f"加载项目: {project_path}")
        
        success = five_stage_tab.project_manager.load_project(project_path)
        if not success:
            print("项目加载失败")
            return
        
        print("项目加载成功")
        
        # 调用load_from_project方法
        five_stage_tab.load_from_project()
        
        # 检查stage_data
        print(f"stage_data键: {list(five_stage_tab.stage_data.keys())}")
        print(f"第4阶段数据存在: {bool(five_stage_tab.stage_data.get(4))}")
        
        if five_stage_tab.stage_data.get(4):
            stage4 = five_stage_tab.stage_data[4]
            print(f"第4阶段包含键: {list(stage4.keys())}")
            print(f"storyboard_results存在: {'storyboard_results' in stage4}")
            
            if 'storyboard_results' in stage4:
                results = stage4['storyboard_results']
                print(f"storyboard_results长度: {len(results)}")
                print(f"条件检查结果: {not five_stage_tab.stage_data.get(4) or not results}")
                
                # 检查一致性控制面板是否接收到数据
                if hasattr(main_window, 'consistency_panel'):
                    panel = main_window.consistency_panel
                    if hasattr(panel, 'storyboard_result') and panel.storyboard_result:
                        print(f"一致性控制面板已接收到数据，包含 {len(panel.storyboard_result.shots)} 个分镜")
                    else:
                        print("一致性控制面板未接收到数据")
                else:
                    print("主窗口没有一致性控制面板")
        
        print("测试完成")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        app.quit()

if __name__ == '__main__':
    test_app_loading()