#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频生成器主程序
直接启动主窗口，无需登录验证
"""

import sys
import os
import atexit
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

def exit_handler():
    """
    程序退出处理函数
    """
    print("程序正在退出...")

if __name__ == "__main__":
    # 注册退出处理函数
    atexit.register(exit_handler)
    
    # 设置Qt属性以支持QtWebEngine
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    
    app = QApplication(sys.argv)
    
    try:
        # 导入并创建主窗口
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from gui.new_main_window import NewMainWindow
        
        print("正在启动主程序...")
        main_window = NewMainWindow()
        main_window.show()
        print("主程序窗口已显示")
        
        # 启动事件循环
        sys.exit(app.exec_())
    except ImportError as e:
        print(f"导入主窗口失败: {e}")
        QMessageBox.critical(None, "错误", f"无法启动主程序: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"启动主程序失败: {e}")
        QMessageBox.critical(None, "错误", f"启动主程序时发生错误: {e}")
        sys.exit(1)