#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化主题演示脚本
完全独立运行，不依赖项目文件
演示深色/浅色主题切换功能
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QLineEdit, QComboBox, QTabWidget,
    QProgressBar, QGroupBox, QFormLayout, QSpinBox, QSlider, QMessageBox
)
from PyQt5.QtCore import Qt

class SimpleThemeDemo(QMainWindow):
    """简化主题演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.current_theme = "light"  # light 或 dark
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("深色/浅色主题演示（简化版）")
        self.setGeometry(200, 200, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 顶部控制栏
        control_layout = QHBoxLayout()
        
        # 主题信息标签
        self.theme_info_label = QLabel("当前主题: 浅色")
        control_layout.addWidget(self.theme_info_label)
        
        control_layout.addStretch()
        
        # 主题切换按钮组
        self.light_theme_btn = QPushButton("浅色主题")
        self.light_theme_btn.clicked.connect(lambda: self.set_theme("light"))
        control_layout.addWidget(self.light_theme_btn)
        
        self.dark_theme_btn = QPushButton("深色主题")
        self.dark_theme_btn.clicked.connect(lambda: self.set_theme("dark"))
        control_layout.addWidget(self.dark_theme_btn)
        
        self.toggle_btn = QPushButton("🌙")
        self.toggle_btn.setToolTip("切换主题")
        self.toggle_btn.clicked.connect(self.toggle_theme)
        self.toggle_btn.setMaximumWidth(40)
        control_layout.addWidget(self.toggle_btn)
        
        layout.addLayout(control_layout)
        
        # 标签页演示
        self.tab_widget = QTabWidget()
        
        # 基础控件标签页
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # 按钮组
        button_group = QGroupBox("按钮演示")
        button_layout = QHBoxLayout(button_group)
        
        self.primary_btn = QPushButton("主要按钮")
        button_layout.addWidget(self.primary_btn)
        
        self.secondary_btn = QPushButton("次要按钮")
        button_layout.addWidget(self.secondary_btn)
        
        self.success_btn = QPushButton("成功按钮")
        button_layout.addWidget(self.success_btn)
        
        self.danger_btn = QPushButton("危险按钮")
        button_layout.addWidget(self.danger_btn)
        
        self.disabled_btn = QPushButton("禁用按钮")
        self.disabled_btn.setEnabled(False)
        button_layout.addWidget(self.disabled_btn)
        
        basic_layout.addWidget(button_group)
        
        # 输入框组
        input_group = QGroupBox("输入框演示")
        input_layout = QFormLayout(input_group)
        
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("请输入文本...")
        input_layout.addRow("单行输入:", self.line_edit)
        
        self.combo_box = QComboBox()
        self.combo_box.addItems(["选项1", "选项2", "选项3"])
        input_layout.addRow("下拉选择:", self.combo_box)
        
        self.spin_box = QSpinBox()
        self.spin_box.setRange(0, 100)
        self.spin_box.setValue(50)
        input_layout.addRow("数字输入:", self.spin_box)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(30)
        input_layout.addRow("滑块:", self.slider)
        
        basic_layout.addWidget(input_group)
        
        # 文本区域
        text_group = QGroupBox("文本演示")
        text_layout = QVBoxLayout(text_group)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText("""这是一个多行文本编辑器的演示。

您可以在这里输入多行文本内容，体验不同主题下的显示效果。

主题系统包含：
• 浅色主题（默认）
• 深色主题
• 一键切换功能

所有控件都会根据主题自动调整颜色和样式。

这是一个简化版演示，展示了基本的主题切换功能。""")
        text_layout.addWidget(self.text_edit)
        
        basic_layout.addWidget(text_group)
        
        self.tab_widget.addTab(basic_tab, "基础控件")
        
        # 进度演示标签页
        progress_tab = QWidget()
        progress_layout = QVBoxLayout(progress_tab)
        
        progress_group = QGroupBox("进度条演示")
        progress_group_layout = QVBoxLayout(progress_group)
        
        self.progress_bar1 = QProgressBar()
        self.progress_bar1.setValue(30)
        progress_group_layout.addWidget(self.progress_bar1)
        
        self.progress_bar2 = QProgressBar()
        self.progress_bar2.setValue(70)
        progress_group_layout.addWidget(self.progress_bar2)
        
        self.progress_bar3 = QProgressBar()
        self.progress_bar3.setValue(100)
        progress_group_layout.addWidget(self.progress_bar3)
        
        progress_layout.addWidget(progress_group)
        progress_layout.addStretch()
        
        self.tab_widget.addTab(progress_tab, "进度条")
        
        layout.addWidget(self.tab_widget)
        
        # 应用初始主题
        self.apply_theme()
        
    def set_theme(self, theme_name):
        """设置主题"""
        if theme_name != self.current_theme:
            self.current_theme = theme_name
            self.apply_theme()
            self.show_message(f"已切换到{theme_name}主题！")
        
    def toggle_theme(self):
        """切换主题"""
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.set_theme(new_theme)
        
    def show_message(self, message):
        """显示消息"""
        print(f"主题切换: {message}")
        # 可以用QMessageBox显示，但这里用print避免阻塞演示
        
    def apply_theme(self):
        """应用主题样式"""
        if self.current_theme == "light":
            self.apply_light_theme()
        else:
            self.apply_dark_theme()
            
        self.update_ui()
    
    def apply_light_theme(self):
        """应用浅色主题"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
                color: #212121;
            }
            
            QWidget {
                background-color: #ffffff;
                color: #212121;
            }
            
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                min-height: 20px;
            }
            
            QPushButton:hover {
                background-color: #1976D2;
            }
            
            QPushButton:pressed {
                background-color: #1976D2;
                padding-top: 9px;
                padding-left: 17px;
            }
            
            QPushButton:disabled {
                background-color: #F5F5F5;
                color: #9E9E9E;
            }
            
            QTextEdit, QLineEdit {
                background-color: #F5F5F5;
                color: #212121;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                selection-background-color: #E3F2FD;
            }
            
            QTextEdit:focus, QLineEdit:focus {
                border-color: #2196F3;
            }
            
            QComboBox {
                background-color: #F5F5F5;
                color: #212121;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                padding: 6px 12px;
                min-width: 100px;
                font-size: 14px;
            }
            
            QComboBox:focus {
                border-color: #2196F3;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #757575;
                width: 0px;
                height: 0px;
            }
            
            QProgressBar {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: #F5F5F5;
                text-align: center;
                font-weight: 600;
                height: 20px;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                          stop: 0 #BBDEFB,
                                          stop: 1 #2196F3);
                border-radius: 7px;
                margin: 1px;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                margin: 10px 0px;
                padding-top: 10px;
                background-color: #ffffff;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #212121;
            }
            
            QTabWidget::pane {
                border: 1px solid #E0E0E0;
                background-color: #ffffff;
                border-radius: 6px;
                margin-top: -1px;
            }
            
            QTabBar::tab {
                background-color: #F5F5F5;
                color: #757575;
                padding: 10px 20px;
                margin: 0px 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: 1px solid #E0E0E0;
                border-bottom: none;
                min-width: 80px;
            }
            
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #212121;
                border-color: #E0E0E0;
                border-bottom: 1px solid #ffffff;
                font-weight: 600;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #F5F5F5;
            }
            
            QSpinBox {
                background-color: #F5F5F5;
                color: #212121;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 14px;
            }
            
            QSpinBox:focus {
                border-color: #2196F3;
            }
            
            QSlider::groove:horizontal {
                border: 1px solid #E0E0E0;
                height: 8px;
                background: #F5F5F5;
                border-radius: 4px;
            }
            
            QSlider::handle:horizontal {
                background: #2196F3;
                border: 1px solid #1976D2;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            
            QSlider::handle:horizontal:hover {
                background: #1976D2;
            }
        """)
    
    def apply_dark_theme(self):
        """应用深色主题"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
                color: #FFFFFF;
            }
            
            QWidget {
                background-color: #121212;
                color: #FFFFFF;
            }
            
            QPushButton {
                background-color: #64B5F6;
                color: #000000;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                min-height: 20px;
            }
            
            QPushButton:hover {
                background-color: #42A5F5;
            }
            
            QPushButton:pressed {
                background-color: #42A5F5;
                padding-top: 9px;
                padding-left: 17px;
            }
            
            QPushButton:disabled {
                background-color: #2D2D2D;
                color: #616161;
            }
            
            QTextEdit, QLineEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 2px solid #404040;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                selection-background-color: #1565C0;
            }
            
            QTextEdit:focus, QLineEdit:focus {
                border-color: #64B5F6;
            }
            
            QComboBox {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 2px solid #404040;
                border-radius: 6px;
                padding: 6px 12px;
                min-width: 100px;
                font-size: 14px;
            }
            
            QComboBox:focus {
                border-color: #64B5F6;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #B3B3B3;
                width: 0px;
                height: 0px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 6px;
                selection-background-color: #1565C0;
                outline: none;
            }
            
            QProgressBar {
                border: 1px solid #404040;
                border-radius: 8px;
                background-color: #1E1E1E;
                text-align: center;
                font-weight: 600;
                height: 20px;
                color: #FFFFFF;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                          stop: 0 #90CAF9,
                                          stop: 1 #64B5F6);
                border-radius: 7px;
                margin: 1px;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 1px solid #404040;
                border-radius: 6px;
                margin: 10px 0px;
                padding-top: 10px;
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #FFFFFF;
            }
            
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #2D2D2D;
                border-radius: 6px;
                margin-top: -1px;
            }
            
            QTabBar::tab {
                background-color: #1E1E1E;
                color: #B3B3B3;
                padding: 10px 20px;
                margin: 0px 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: 1px solid #404040;
                border-bottom: none;
                min-width: 80px;
            }
            
            QTabBar::tab:selected {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border-color: #404040;
                border-bottom: 1px solid #2D2D2D;
                font-weight: 600;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #404040;
            }
            
            QSpinBox {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 2px solid #404040;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 14px;
            }
            
            QSpinBox:focus {
                border-color: #64B5F6;
            }
            
            QSlider::groove:horizontal {
                border: 1px solid #404040;
                height: 8px;
                background: #1E1E1E;
                border-radius: 4px;
            }
            
            QSlider::handle:horizontal {
                background: #64B5F6;
                border: 1px solid #42A5F5;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            
            QSlider::handle:horizontal:hover {
                background: #42A5F5;
            }
        """)
        
    def update_ui(self):
        """更新界面"""
        # 更新主题信息
        theme_name = "深色" if self.current_theme == "dark" else "浅色"
        self.theme_info_label.setText(f"当前主题: {theme_name}")
        
        # 更新切换按钮
        if self.current_theme == "dark":
            self.toggle_btn.setText("☀️")
            self.toggle_btn.setToolTip("切换到浅色主题")
        else:
            self.toggle_btn.setText("🌙")
            self.toggle_btn.setToolTip("切换到深色主题")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("主题演示（简化版）")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("AI Video Generator")
    
    # 创建演示窗口
    demo = SimpleThemeDemo()
    demo.show()
    
    print("=== 深色/浅色主题演示 ===")
    print("功能说明：")
    print("• 点击'浅色主题'/'深色主题'按钮切换主题")
    print("• 点击右侧的🌙/☀️按钮快速切换")
    print("• 所有控件会实时响应主题变化")
    print("• 这是一个简化版演示，展示基本功能")
    print("========================")
    
    # 运行应用
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 