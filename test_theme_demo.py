#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主题切换演示脚本
演示深色/浅色主题切换功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QLineEdit, QComboBox, QTabWidget,
    QProgressBar, QGroupBox, QFormLayout, QSpinBox, QSlider
)
from PyQt5.QtCore import Qt

# 导入主题系统
try:
    from src.gui.modern_styles import (
        apply_modern_style, set_theme, toggle_theme, 
        ThemeType, style_manager
    )
    from src.gui.notification_system import show_success, show_info
    THEME_AVAILABLE = True
except ImportError as e:
    print(f"主题系统导入失败: {e}")
    print("将使用基础样式演示")
    THEME_AVAILABLE = False

class ThemeDemo(QMainWindow):
    """主题演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("深色/浅色主题演示")
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
        if THEME_AVAILABLE:
            self.light_theme_btn.clicked.connect(lambda: self.set_theme(ThemeType.LIGHT))
        else:
            self.light_theme_btn.clicked.connect(lambda: self.set_theme("LIGHT"))
        control_layout.addWidget(self.light_theme_btn)
        
        self.dark_theme_btn = QPushButton("深色主题")
        if THEME_AVAILABLE:
            self.dark_theme_btn.clicked.connect(lambda: self.set_theme(ThemeType.DARK))
        else:
            self.dark_theme_btn.clicked.connect(lambda: self.set_theme("DARK"))
        control_layout.addWidget(self.dark_theme_btn)
        
        self.toggle_btn = QPushButton("🌙")
        self.toggle_btn.setToolTip("切换主题")
        self.toggle_btn.clicked.connect(self.toggle_theme)
        self.toggle_btn.setMaximumWidth(40)
        control_layout.addWidget(self.toggle_btn)
        
        layout.addLayout(control_layout)
        
        # 标签页演示
        tab_widget = QTabWidget()
        
        # 基础控件标签页
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # 按钮组
        button_group = QGroupBox("按钮演示")
        button_layout = QHBoxLayout(button_group)
        
        primary_btn = QPushButton("主要按钮")
        button_layout.addWidget(primary_btn)
        
        secondary_btn = QPushButton("次要按钮")
        secondary_btn.setProperty("flat", True)
        button_layout.addWidget(secondary_btn)
        
        success_btn = QPushButton("成功按钮")
        success_btn.setProperty("success", True)
        button_layout.addWidget(success_btn)
        
        danger_btn = QPushButton("危险按钮")
        danger_btn.setProperty("danger", True)
        button_layout.addWidget(danger_btn)
        
        disabled_btn = QPushButton("禁用按钮")
        disabled_btn.setEnabled(False)
        button_layout.addWidget(disabled_btn)
        
        basic_layout.addWidget(button_group)
        
        # 输入框组
        input_group = QGroupBox("输入框演示")
        input_layout = QFormLayout(input_group)
        
        line_edit = QLineEdit()
        line_edit.setPlaceholderText("请输入文本...")
        input_layout.addRow("单行输入:", line_edit)
        
        combo_box = QComboBox()
        combo_box.addItems(["选项1", "选项2", "选项3"])
        input_layout.addRow("下拉选择:", combo_box)
        
        spin_box = QSpinBox()
        spin_box.setRange(0, 100)
        spin_box.setValue(50)
        input_layout.addRow("数字输入:", spin_box)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(30)
        input_layout.addRow("滑块:", slider)
        
        basic_layout.addWidget(input_group)
        
        # 文本区域
        text_group = QGroupBox("文本演示")
        text_layout = QVBoxLayout(text_group)
        
        text_edit = QTextEdit()
        text_edit.setPlainText("""这是一个多行文本编辑器的演示。
        
您可以在这里输入多行文本内容，体验不同主题下的显示效果。

主题系统包含：
• 浅色主题（默认）
• 深色主题
• 自动切换（跟随系统）

所有控件都会根据主题自动调整颜色和样式。""")
        text_layout.addWidget(text_edit)
        
        basic_layout.addWidget(text_group)
        
        tab_widget.addTab(basic_tab, "基础控件")
        
        # 进度演示标签页
        progress_tab = QWidget()
        progress_layout = QVBoxLayout(progress_tab)
        
        progress_group = QGroupBox("进度条演示")
        progress_group_layout = QVBoxLayout(progress_group)
        
        progress_bar1 = QProgressBar()
        progress_bar1.setValue(30)
        progress_group_layout.addWidget(progress_bar1)
        
        progress_bar2 = QProgressBar()
        progress_bar2.setValue(70)
        progress_group_layout.addWidget(progress_bar2)
        
        progress_bar3 = QProgressBar()
        progress_bar3.setValue(100)
        progress_group_layout.addWidget(progress_bar3)
        
        progress_layout.addWidget(progress_group)
        progress_layout.addStretch()
        
        tab_widget.addTab(progress_tab, "进度条")
        
        layout.addWidget(tab_widget)
        
        # 应用主题
        self.init_theme()
        
    def init_theme(self):
        """初始化主题"""
        if THEME_AVAILABLE:
            # 应用现代化样式
            apply_modern_style()
            
            # 连接主题变化信号
            style_manager.theme_changed.connect(self.on_theme_changed)
            
            # 更新界面
            self.update_ui()
        else:
            # 使用基础样式
            self.apply_basic_style()
        
    def apply_basic_style(self):
        """应用基础样式（当主题系统不可用时）"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
                color: #333333;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QTextEdit, QLineEdit {
                background-color: white;
                border: 1px solid #cccccc;
                padding: 4px;
                border-radius: 3px;
            }
            QComboBox {
                background-color: white;
                border: 1px solid #cccccc;
                padding: 4px;
                border-radius: 3px;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 3px;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 4px;
                margin: 10px 0px;
                padding-top: 10px;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
        """)
        
    def set_theme(self, theme_type):
        """设置主题"""
        if THEME_AVAILABLE:
            set_theme(theme_type)
            theme_name = theme_type.value if hasattr(theme_type, 'value') else str(theme_type)
            self.show_message(f"已切换到{theme_name}主题！")
        else:
            theme_name = str(theme_type).lower()
            self.show_message(f"主题系统不可用，但您选择了{theme_name}主题")
        
    def toggle_theme(self):
        """切换主题"""
        if THEME_AVAILABLE:
            toggle_theme()
            self.show_message("主题切换成功！")
        else:
            self.show_message("主题系统不可用，请检查导入")
        
    def show_message(self, message):
        """显示消息"""
        if THEME_AVAILABLE:
            show_success(message)
        else:
            print(f"消息: {message}")
        
    def on_theme_changed(self, theme_name: str):
        """主题变化响应"""
        self.update_ui()
        self.show_message(f"当前主题: {theme_name}")
        
    def update_ui(self):
        """更新界面"""
        if THEME_AVAILABLE:
            # 更新主题信息
            theme_name = "深色" if style_manager.current_theme_type.name == "DARK" else "浅色"
            self.theme_info_label.setText(f"当前主题: {theme_name}")
            
            # 更新切换按钮
            if style_manager.current_theme_type.name == "DARK":
                self.toggle_btn.setText("☀️")
                self.toggle_btn.setToolTip("切换到浅色主题")
            else:
                self.toggle_btn.setText("🌙")
                self.toggle_btn.setToolTip("切换到深色主题")
        else:
            self.theme_info_label.setText("当前主题: 基础样式")
            self.toggle_btn.setText("🌙")
            self.toggle_btn.setToolTip("主题系统不可用")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("主题演示")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("AI Video Generator")
    
    # 创建演示窗口
    demo = ThemeDemo()
    demo.show()
    
    # 运行应用
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 