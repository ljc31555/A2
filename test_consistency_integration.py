#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一致性控制系统集成测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from PyQt5.QtWidgets import QApplication
from src.gui.new_main_window import NewMainWindow

def test_consistency_integration():
    """
    测试一致性控制系统的集成
    """
    print("开始测试一致性控制系统集成...")
    
    try:
        # 创建应用
        app = QApplication(sys.argv)
        
        # 创建主窗口
        window = NewMainWindow()
        
        # 检查一致性控制面板是否正确创建
        if hasattr(window, 'consistency_panel'):
            print("✅ 一致性控制面板创建成功")
            
            # 检查一致性增强图像处理器
            if hasattr(window, 'consistency_image_processor'):
                print("✅ 一致性增强图像处理器初始化成功")
            else:
                print("❌ 一致性增强图像处理器未找到")
                
            # 检查标签页是否添加
            tab_count = window.tab_widget.count()
            consistency_tab_found = False
            for i in range(tab_count):
                tab_text = window.tab_widget.tabText(i)
                if "一致性控制" in tab_text:
                    consistency_tab_found = True
                    print(f"✅ 一致性控制标签页已添加: {tab_text}")
                    break
                    
            if not consistency_tab_found:
                print("❌ 一致性控制标签页未找到")
                
        else:
            print("❌ 一致性控制面板创建失败")
            
        # 显示窗口进行手动测试
        window.show()
        print("\n🎉 集成测试完成！窗口已显示，可以进行手动测试。")
        print("请检查以下功能:")
        print("1. 一致性控制标签页是否正常显示")
        print("2. 角色管理功能是否可用")
        print("3. 场景管理功能是否可用")
        print("4. 一致性配置是否可以设置")
        print("5. 预览功能是否正常")
        
        # 运行应用
        return app.exec_()
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保所有依赖文件都已正确创建")
        return 1
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = test_consistency_integration()
    sys.exit(exit_code)