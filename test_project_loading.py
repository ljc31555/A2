#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试项目加载后五阶段分镜数据的加载情况
"""

import sys
import logging
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.project_manager import ProjectManager
from src.gui.five_stage_storyboard_tab import FiveStageStoryboardTab

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_project_loading():
    """测试项目加载功能"""
    try:
        print("开始测试项目加载功能...")
        sys.stdout.flush()
        
        # 创建QApplication实例
        app = QApplication(sys.argv)
        print("QApplication创建成功")
        sys.stdout.flush()
        
        # 初始化项目管理器
        print("初始化项目管理器...")
        sys.stdout.flush()
        project_manager = ProjectManager()
        print("项目管理器初始化成功")
        sys.stdout.flush()
        
        # 查找项目文件
        projects_dir = project_root / 'output'
        print(f"查找项目目录: {projects_dir}")
        sys.stdout.flush()
        if not projects_dir.exists():
            print(f"项目目录不存在: {projects_dir}")
            sys.stdout.flush()
            return
        
        # 查找"four"项目
        four_project_dir = projects_dir / 'four'
        project_json_path = four_project_dir / 'project.json'
        print(f"查找项目文件: {project_json_path}")
        
        if not project_json_path.exists():
            print(f"项目文件不存在: {project_json_path}")
            return
        
        print(f"找到项目文件: {project_json_path}")
        
        # 加载项目
        print("开始加载项目...")
        project_data = project_manager.load_project(str(four_project_dir))
        print(f"项目加载完成，结果: {project_data is not None}")
        
        if not project_data:
            print("项目加载失败")
            return
        
        print(f"项目加载成功: {project_data.get('name', 'Unknown')}")
        
        # 检查五阶段分镜数据
        five_stage_data = project_data.get('five_stage_storyboard', {})
        print(f"五阶段分镜数据存在: {bool(five_stage_data)}")
        
        if five_stage_data:
            print(f"五阶段分镜数据键: {list(five_stage_data.keys())}")
            
            # 检查第四阶段数据
            stage4_data = five_stage_data.get('storyboard_results', [])
            print(f"第四阶段数据存在: {bool(stage4_data)}")
            print(f"第四阶段数据类型: {type(stage4_data)}")
            print(f"第四阶段数据长度: {len(stage4_data) if isinstance(stage4_data, (list, dict)) else 'N/A'}")
            
            if stage4_data:
                print(f"第四阶段数据前两项: {stage4_data[:2] if isinstance(stage4_data, list) else 'Not a list'}")
        else:
            print("没有找到五阶段分镜数据")
        
        # 创建模拟的父窗口类
        class MockParent:
            def __init__(self):
                self.project_manager = project_manager
        
        # 创建五阶段分镜标签页实例
        print("创建五阶段分镜标签页实例...")
        parent = MockParent()
        five_stage_tab = FiveStageStoryboardTab(parent)
        print("五阶段分镜标签页创建成功")
        
        # 使用QTimer延迟调用load_from_project
        def delayed_load():
            print("开始调用load_from_project...")
            five_stage_tab.load_from_project()
            
            # 检查加载后的状态
            stage_data = getattr(five_stage_tab, 'stage_data', {})
            print(f"标签页中的stage_data: {bool(stage_data)}")
            
            if stage_data:
                print(f"标签页stage_data键: {list(stage_data.keys())}")
                
                # 检查第四阶段数据
                if 4 in stage_data:
                    stage4_data = stage_data[4]
                    print(f"标签页第四阶段数据: {bool(stage4_data)}")
                    
                    storyboard_results = stage4_data.get('storyboard_results', [])
                    print(f"标签页storyboard_results数量: {len(storyboard_results)}")
            
            # 检查storyboard_output组件
            storyboard_output = getattr(five_stage_tab, 'storyboard_output', None)
            print(f"storyboard_output组件存在: {storyboard_output is not None}")
            
            if storyboard_output:
                print(f"storyboard_output类型: {type(storyboard_output)}")
                
                # 检查文本内容
                if hasattr(storyboard_output, 'toPlainText'):
                    text_content = storyboard_output.toPlainText()
                    print(f"storyboard_output文本长度: {len(text_content)}")
                    
                    if text_content:
                        print(f"storyboard_output文本预览: {text_content[:200]}...")
                    else:
                        print("storyboard_output文本为空")
                else:
                    print("storyboard_output没有toPlainText方法")
            else:
                print("storyboard_output组件不存在")
            
            # 退出应用
            app.quit()
        
        # 设置定时器
        timer = QTimer()
        timer.timeout.connect(delayed_load)
        timer.setSingleShot(True)
        timer.start(1000)  # 1秒后执行
        
        # 运行应用
        app.exec_()
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == '__main__':
    test_project_loading()