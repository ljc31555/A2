# -*- coding: utf-8 -*-
"""
日志对话框模块
用于显示系统日志的对话框组件
"""

import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPlainTextEdit, QPushButton
from PyQt5.QtCore import Qt

from utils.logger import logger


class LogDialog(QDialog):
    """日志显示对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统日志")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        layout.addWidget(self.close_btn)
        
        self.setLayout(layout)
        
        # 加载日志内容
        self.load_log()
    
    def load_log(self):
        """加载日志文件内容"""
        try:
            # 获取日志文件路径 - 修正为正确的logs目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            log_file_path = os.path.join(project_root, "logs", "system.log")
            
            if os.path.exists(log_file_path):
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 只显示最后1000行，避免内容过多
                    lines = content.split('\n')
                    if len(lines) > 1000:
                        lines = lines[-1000:]
                        content = '\n'.join(['... (显示最后1000行) ...'] + lines)
                    self.log_text.setPlainText(content)
                    # 滚动到底部
                    self.log_text.moveCursor(self.log_text.textCursor().End)
            else:
                self.log_text.setPlainText("日志文件不存在。")
        except Exception as e:
            self.log_text.setPlainText(f"日志读取失败: {e}")
            logger.error(f"加载日志文件失败: {e}")
    
    def refresh_log(self):
        """刷新日志内容"""
        self.load_log()