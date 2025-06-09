#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
现代化样式系统
提供深色/浅色主题、动态样式切换、响应式设计等功能
"""

import os
import json
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel
from PyQt5.QtCore import QObject, pyqtSignal, QSettings
from PyQt5.QtGui import QPalette, QColor, QFont

try:
    from utils.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class ThemeType(Enum):
    """主题类型"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"  # 根据系统设置自动切换

class ColorScheme:
    """颜色方案"""
    
    def __init__(self, name: str, colors: Dict[str, str]):
        self.name = name
        self.colors = colors
    
    def get_color(self, key: str, fallback: str = "#000000") -> str:
        """获取颜色值"""
        return self.colors.get(key, fallback)
    
    def get_qcolor(self, key: str, fallback: str = "#000000") -> QColor:
        """获取QColor对象"""
        color_str = self.get_color(key, fallback)
        return QColor(color_str)

class ModernThemes:
    """现代化主题定义"""
    
    @staticmethod
    def get_light_theme() -> ColorScheme:
        """浅色主题"""
        return ColorScheme("Light", {
            # 基础颜色
            "primary": "#2196F3",           # 主要蓝色
            "primary_dark": "#1976D2",      # 深蓝色
            "primary_light": "#BBDEFB",     # 浅蓝色
            "secondary": "#FF9800",         # 次要橙色
            "accent": "#4CAF50",            # 强调绿色
            "error": "#F44336",             # 错误红色
            "warning": "#FF9800",           # 警告橙色
            "info": "#2196F3",              # 信息蓝色
            "success": "#4CAF50",           # 成功绿色
            
            # 背景颜色
            "background": "#FFFFFF",         # 主背景
            "surface": "#F5F5F5",           # 表面背景
            "card": "#FFFFFF",              # 卡片背景
            "dialog": "#FFFFFF",            # 对话框背景
            "toolbar": "#FAFAFA",           # 工具栏背景
            "menu": "#FFFFFF",              # 菜单背景
            "tooltip": "#616161",           # 工具提示背景
            
            # 文本颜色
            "text_primary": "#212121",       # 主要文本
            "text_secondary": "#757575",     # 次要文本
            "text_hint": "#BDBDBD",         # 提示文本
            "text_disabled": "#9E9E9E",     # 禁用文本
            "text_on_primary": "#FFFFFF",   # 主色上的文本
            "text_on_surface": "#212121",   # 表面上的文本
            
            # 边框颜色
            "border": "#E0E0E0",            # 普通边框
            "border_light": "#F5F5F5",      # 浅色边框
            "border_dark": "#BDBDBD",       # 深色边框
            "divider": "#E0E0E0",           # 分割线
            
            # 状态颜色
            "hover": "#F5F5F5",             # 悬停
            "pressed": "#EEEEEE",           # 按下
            "selected": "#E3F2FD",          # 选中
            "focus": "#2196F3",             # 焦点
            "disabled": "#F5F5F5",          # 禁用
            
            # 阴影颜色
            "shadow": "rgba(0, 0, 0, 0.1)",
            "shadow_light": "rgba(0, 0, 0, 0.05)",
            "shadow_dark": "rgba(0, 0, 0, 0.2)",
        })
    
    @staticmethod
    def get_dark_theme() -> ColorScheme:
        """深色主题"""
        return ColorScheme("Dark", {
            # 基础颜色
            "primary": "#64B5F6",           # 主要蓝色
            "primary_dark": "#42A5F5",      # 深蓝色
            "primary_light": "#90CAF9",     # 浅蓝色
            "secondary": "#FFB74D",         # 次要橙色
            "accent": "#81C784",            # 强调绿色
            "error": "#EF5350",             # 错误红色
            "warning": "#FFB74D",           # 警告橙色
            "info": "#64B5F6",              # 信息蓝色
            "success": "#81C784",           # 成功绿色
            
            # 背景颜色
            "background": "#121212",         # 主背景
            "surface": "#1E1E1E",           # 表面背景
            "card": "#2D2D2D",              # 卡片背景
            "dialog": "#2D2D2D",            # 对话框背景
            "toolbar": "#1E1E1E",           # 工具栏背景
            "menu": "#2D2D2D",              # 菜单背景
            "tooltip": "#616161",           # 工具提示背景
            
            # 文本颜色
            "text_primary": "#FFFFFF",       # 主要文本
            "text_secondary": "#B3B3B3",     # 次要文本
            "text_hint": "#757575",         # 提示文本
            "text_disabled": "#616161",     # 禁用文本
            "text_on_primary": "#000000",   # 主色上的文本
            "text_on_surface": "#FFFFFF",   # 表面上的文本
            
            # 边框颜色
            "border": "#404040",            # 普通边框
            "border_light": "#2D2D2D",      # 浅色边框
            "border_dark": "#616161",       # 深色边框
            "divider": "#404040",           # 分割线
            
            # 状态颜色
            "hover": "#404040",             # 悬停
            "pressed": "#505050",           # 按下
            "selected": "#1565C0",          # 选中
            "focus": "#64B5F6",             # 焦点
            "disabled": "#2D2D2D",          # 禁用
            
            # 阴影颜色
            "shadow": "rgba(0, 0, 0, 0.3)",
            "shadow_light": "rgba(0, 0, 0, 0.15)",
            "shadow_dark": "rgba(0, 0, 0, 0.5)",
        })

class StyleTemplates:
    """样式模板"""
    
    @staticmethod
    def get_button_style(theme: ColorScheme) -> str:
        """按钮样式"""
        return f"""
            QPushButton {{
                background-color: {theme.get_color('primary')};
                color: {theme.get_color('text_on_primary')};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                min-height: 20px;
            }}
            
            QPushButton:hover {{
                background-color: {theme.get_color('primary_dark')};
            }}
            
            QPushButton:pressed {{
                background-color: {theme.get_color('primary_dark')};
                padding-top: 9px;
                padding-left: 17px;
            }}
            
            QPushButton:disabled {{
                background-color: {theme.get_color('disabled')};
                color: {theme.get_color('text_disabled')};
            }}
            
            QPushButton:focus {{
                outline: 2px solid {theme.get_color('focus')};
                outline-offset: 2px;
            }}
            
            /* 扁平按钮 */
            QPushButton[flat="true"] {{
                background-color: transparent;
                color: {theme.get_color('primary')};
                border: 1px solid {theme.get_color('border')};
            }}
            
            QPushButton[flat="true"]:hover {{
                background-color: {theme.get_color('hover')};
            }}
            
            /* 危险按钮 */
            QPushButton[danger="true"] {{
                background-color: {theme.get_color('error')};
                color: {theme.get_color('text_on_primary')};
            }}
            
            QPushButton[danger="true"]:hover {{
                background-color: #D32F2F;
            }}
            
            /* 成功按钮 */
            QPushButton[success="true"] {{
                background-color: {theme.get_color('success')};
                color: {theme.get_color('text_on_primary')};
            }}
            
            QPushButton[success="true"]:hover {{
                background-color: #388E3C;
            }}
        """
    
    @staticmethod
    def get_input_style(theme: ColorScheme) -> str:
        """输入框样式"""
        return f"""
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {theme.get_color('surface')};
                color: {theme.get_color('text_primary')};
                border: 2px solid {theme.get_color('border')};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                selection-background-color: {theme.get_color('selected')};
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border-color: {theme.get_color('primary')};
                outline: none;
            }}
            
            QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
                background-color: {theme.get_color('disabled')};
                color: {theme.get_color('text_disabled')};
                border-color: {theme.get_color('border_light')};
            }}
            
            /* 占位符文本 */
            QLineEdit::placeholder {{
                color: {theme.get_color('text_hint')};
            }}
        """
    
    @staticmethod
    def get_table_style(theme: ColorScheme) -> str:
        """表格样式"""
        return f"""
            QTableWidget {{
                background-color: {theme.get_color('surface')};
                alternate-background-color: {theme.get_color('card')};
                color: {theme.get_color('text_primary')};
                gridline-color: {theme.get_color('border')};
                border: 1px solid {theme.get_color('border')};
                border-radius: 6px;
                selection-background-color: {theme.get_color('selected')};
            }}
            
            QTableWidget::item {{
                padding: 8px;
                border: none;
            }}
            
            QTableWidget::item:selected {{
                background-color: {theme.get_color('selected')};
                color: {theme.get_color('text_primary')};
            }}
            
            QTableWidget::item:hover {{
                background-color: {theme.get_color('hover')};
            }}
            
            QHeaderView::section {{
                background-color: {theme.get_color('toolbar')};
                color: {theme.get_color('text_primary')};
                padding: 8px;
                border: none;
                border-bottom: 1px solid {theme.get_color('border')};
                font-weight: 600;
            }}
            
            QHeaderView::section:hover {{
                background-color: {theme.get_color('hover')};
            }}
        """
    
    @staticmethod
    def get_tab_style(theme: ColorScheme) -> str:
        """标签页样式"""
        return f"""
            QTabWidget::pane {{
                border: 1px solid {theme.get_color('border')};
                background-color: {theme.get_color('card')};
                border-radius: 6px;
                margin-top: -1px;
            }}
            
            QTabBar::tab {{
                background-color: {theme.get_color('surface')};
                color: {theme.get_color('text_secondary')};
                padding: 10px 20px;
                margin: 0px 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: 1px solid {theme.get_color('border')};
                border-bottom: none;
                min-width: 80px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {theme.get_color('card')};
                color: {theme.get_color('text_primary')};
                border-color: {theme.get_color('border')};
                border-bottom: 1px solid {theme.get_color('card')};
                font-weight: 600;
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {theme.get_color('hover')};
            }}
            
            QTabBar::tab:disabled {{
                color: {theme.get_color('text_disabled')};
                background-color: {theme.get_color('disabled')};
            }}
        """
    
    @staticmethod
    def get_progress_style(theme: ColorScheme) -> str:
        """进度条样式"""
        return f"""
            QProgressBar {{
                border: 1px solid {theme.get_color('border')};
                border-radius: 8px;
                background-color: {theme.get_color('surface')};
                text-align: center;
                font-weight: 600;
                height: 20px;
            }}
            
            QProgressBar::chunk {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                          stop: 0 {theme.get_color('primary_light')},
                                          stop: 1 {theme.get_color('primary')});
                border-radius: 7px;
                margin: 1px;
            }}
        """
    
    @staticmethod
    def get_combobox_style(theme: ColorScheme) -> str:
        """下拉框样式"""
        return f"""
            QComboBox {{
                background-color: {theme.get_color('surface')};
                color: {theme.get_color('text_primary')};
                border: 2px solid {theme.get_color('border')};
                border-radius: 6px;
                padding: 6px 12px;
                min-width: 100px;
                font-size: 14px;
            }}
            
            QComboBox:focus {{
                border-color: {theme.get_color('primary')};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {theme.get_color('text_secondary')};
                width: 0px;
                height: 0px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {theme.get_color('card')};
                color: {theme.get_color('text_primary')};
                border: 1px solid {theme.get_color('border')};
                border-radius: 6px;
                selection-background-color: {theme.get_color('selected')};
                outline: none;
            }}
        """
    
    @staticmethod
    def get_scrollbar_style(theme: ColorScheme) -> str:
        """滚动条样式"""
        return f"""
            QScrollBar:vertical {{
                background-color: {theme.get_color('surface')};
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {theme.get_color('text_hint')};
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {theme.get_color('text_secondary')};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background-color: {theme.get_color('surface')};
                height: 12px;
                border-radius: 6px;
                margin: 0px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {theme.get_color('text_hint')};
                border-radius: 6px;
                min-width: 20px;
                margin: 2px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {theme.get_color('text_secondary')};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """

class StyleManager(QObject):
    """样式管理器"""
    
    # 信号
    theme_changed = pyqtSignal(str)  # theme_name
    
    def __init__(self):
        super().__init__()
        
        # 当前主题
        self.current_theme_type = ThemeType.LIGHT
        self.current_theme = ModernThemes.get_light_theme()
        
        # 设置管理
        self.settings = QSettings("AIVideoGenerator", "StyleManager")
        
        # 加载保存的主题设置
        self.load_theme_settings()
        
        # 缓存样式表
        self._style_cache: Dict[str, str] = {}
    
    def load_theme_settings(self):
        """加载主题设置"""
        try:
            theme_name = self.settings.value("theme", ThemeType.LIGHT.value)
            self.set_theme(ThemeType(theme_name))
        except Exception as e:
            logger.warning(f"加载主题设置失败: {e}")
            self.set_theme(ThemeType.LIGHT)
    
    def save_theme_settings(self):
        """保存主题设置"""
        try:
            self.settings.setValue("theme", self.current_theme_type.value)
        except Exception as e:
            logger.error(f"保存主题设置失败: {e}")
    
    def set_theme(self, theme_type: ThemeType):
        """设置主题"""
        if theme_type == self.current_theme_type:
            return
        
        self.current_theme_type = theme_type
        
        if theme_type == ThemeType.LIGHT:
            self.current_theme = ModernThemes.get_light_theme()
        elif theme_type == ThemeType.DARK:
            self.current_theme = ModernThemes.get_dark_theme()
        elif theme_type == ThemeType.AUTO:
            # 根据系统设置决定
            self.current_theme = self._get_system_theme()
        
        # 清空样式缓存
        self._style_cache.clear()
        
        # 保存设置
        self.save_theme_settings()
        
        # 发送信号
        self.theme_changed.emit(self.current_theme.name)
        
        logger.info(f"切换到主题: {self.current_theme.name}")
    
    def _get_system_theme(self) -> ColorScheme:
        """获取系统主题"""
        try:
            # 检查系统是否使用深色模式
            app = QApplication.instance()
            if app:
                palette = app.palette()
                window_color = palette.color(QPalette.Window)
                # 如果窗口背景较暗，使用深色主题
                if window_color.lightness() < 128:
                    return ModernThemes.get_dark_theme()
            
            return ModernThemes.get_light_theme()
        except Exception as e:
            logger.warning(f"检测系统主题失败: {e}")
            return ModernThemes.get_light_theme()
    
    def get_complete_stylesheet(self) -> str:
        """获取完整样式表"""
        cache_key = f"complete_{self.current_theme.name}"
        
        if cache_key in self._style_cache:
            return self._style_cache[cache_key]
        
        # 组合所有样式
        styles = [
            self.get_base_style(),
            StyleTemplates.get_button_style(self.current_theme),
            StyleTemplates.get_input_style(self.current_theme),
            StyleTemplates.get_table_style(self.current_theme),
            StyleTemplates.get_tab_style(self.current_theme),
            StyleTemplates.get_progress_style(self.current_theme),
            StyleTemplates.get_combobox_style(self.current_theme),
            StyleTemplates.get_scrollbar_style(self.current_theme),
        ]
        
        complete_style = "\n".join(styles)
        self._style_cache[cache_key] = complete_style
        
        return complete_style
    
    def get_base_style(self) -> str:
        """获取基础样式"""
        return f"""
            /* 基础样式 */
            QWidget {{
                background-color: {self.current_theme.get_color('background')};
                color: {self.current_theme.get_color('text_primary')};
                font-family: "Segoe UI", "Microsoft YaHei", "Arial", sans-serif;
                font-size: 14px;
            }}
            
            QMainWindow {{
                background-color: {self.current_theme.get_color('background')};
            }}
            
            QFrame {{
                background-color: {self.current_theme.get_color('surface')};
                border: 1px solid {self.current_theme.get_color('border')};
                border-radius: 6px;
            }}
            
            QLabel {{
                background-color: transparent;
                color: {self.current_theme.get_color('text_primary')};
            }}
            
            QGroupBox {{
                font-weight: 600;
                border: 1px solid {self.current_theme.get_color('border')};
                border-radius: 6px;
                margin: 10px 0px;
                padding-top: 10px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0px 5px;
                background-color: {self.current_theme.get_color('background')};
                color: {self.current_theme.get_color('text_primary')};
            }}
            
            QToolTip {{
                background-color: {self.current_theme.get_color('tooltip')};
                color: {self.current_theme.get_color('text_on_primary')};
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
            }}
            
            QStatusBar {{
                background-color: {self.current_theme.get_color('toolbar')};
                color: {self.current_theme.get_color('text_secondary')};
                border-top: 1px solid {self.current_theme.get_color('border')};
            }}
            
            QMenuBar {{
                background-color: {self.current_theme.get_color('toolbar')};
                color: {self.current_theme.get_color('text_primary')};
                border-bottom: 1px solid {self.current_theme.get_color('border')};
            }}
            
            QMenuBar::item {{
                padding: 6px 12px;
                background-color: transparent;
            }}
            
            QMenuBar::item:selected {{
                background-color: {self.current_theme.get_color('hover')};
            }}
            
            QMenu {{
                background-color: {self.current_theme.get_color('menu')};
                color: {self.current_theme.get_color('text_primary')};
                border: 1px solid {self.current_theme.get_color('border')};
                border-radius: 6px;
                padding: 4px;
            }}
            
            QMenu::item {{
                padding: 6px 20px;
                border-radius: 4px;
            }}
            
            QMenu::item:selected {{
                background-color: {self.current_theme.get_color('selected')};
            }}
            
            QMenu::separator {{
                height: 1px;
                background-color: {self.current_theme.get_color('divider')};
                margin: 4px 0px;
            }}
        """
    
    def apply_to_widget(self, widget: QWidget):
        """应用样式到指定组件"""
        try:
            widget.setStyleSheet(self.get_complete_stylesheet())
        except Exception as e:
            logger.error(f"应用样式失败: {e}")
    
    def apply_to_application(self):
        """应用样式到整个应用"""
        try:
            app = QApplication.instance()
            if app:
                app.setStyleSheet(self.get_complete_stylesheet())
                logger.info("已应用样式到整个应用")
        except Exception as e:
            logger.error(f"应用应用样式失败: {e}")
    
    def get_color(self, key: str, fallback: str = "#000000") -> str:
        """获取当前主题的颜色"""
        return self.current_theme.get_color(key, fallback)
    
    def get_qcolor(self, key: str, fallback: str = "#000000") -> QColor:
        """获取当前主题的QColor"""
        return self.current_theme.get_qcolor(key, fallback)
    
    def toggle_theme(self):
        """切换主题（浅色/深色）"""
        if self.current_theme_type == ThemeType.LIGHT:
            self.set_theme(ThemeType.DARK)
        else:
            self.set_theme(ThemeType.LIGHT)

# 全局样式管理器实例（延迟初始化）
_style_manager = None

def get_style_manager():
    """获取样式管理器实例（延迟初始化）"""
    global _style_manager
    if _style_manager is None:
        try:
            # 检查是否有QApplication实例
            app = QApplication.instance()
            if app is None:
                print("警告：没有QApplication实例，样式系统将不可用")
                return None
            _style_manager = StyleManager()
        except Exception as e:
            print(f"创建样式管理器失败: {e}")
            return None
    return _style_manager

# 便捷函数
def apply_modern_style(widget: QWidget = None):
    """应用现代化样式"""
    manager = get_style_manager()
    if manager:
        if widget:
            manager.apply_to_widget(widget)
        else:
            manager.apply_to_application()
    else:
        print("样式系统不可用")

def set_theme(theme_type: ThemeType):
    """设置主题"""
    manager = get_style_manager()
    if manager:
        manager.set_theme(theme_type)
    else:
        print(f"无法设置主题: {theme_type}")

def toggle_theme():
    """切换主题"""
    manager = get_style_manager()
    if manager:
        manager.toggle_theme()
    else:
        print("无法切换主题")

def get_current_color(key: str, fallback: str = "#000000") -> str:
    """获取当前主题颜色"""
    manager = get_style_manager()
    if manager:
        return manager.get_color(key, fallback)
    else:
        return fallback

def get_current_qcolor(key: str, fallback: str = "#000000") -> QColor:
    """获取当前主题QColor"""
    manager = get_style_manager()
    if manager:
        return manager.get_qcolor(key, fallback)
    else:
        return QColor(fallback)

# 为了向后兼容，提供style_manager属性
def __getattr__(name):
    """模块级别的属性访问"""
    if name == 'style_manager':
        return get_style_manager()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# 动态样式应用函数
def apply_button_style(button: QPushButton, button_type: str = "primary"):
    """应用按钮样式"""
    if button_type == "primary":
        button.setProperty("flat", False)
        button.setProperty("danger", False)
        button.setProperty("success", False)
    elif button_type == "flat":
        button.setProperty("flat", True)
        button.setProperty("danger", False)
        button.setProperty("success", False)
    elif button_type == "danger":
        button.setProperty("flat", False)
        button.setProperty("danger", True)
        button.setProperty("success", False)
    elif button_type == "success":
        button.setProperty("flat", False)
        button.setProperty("danger", False)
        button.setProperty("success", True)
    
    # 刷新样式
    button.style().unpolish(button)
    button.style().polish(button) 