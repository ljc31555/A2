#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新的主窗口
基于重构后的应用控制器的现代化GUI界面
"""

import sys
import os
import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QProgressBar, QTextEdit, 
    QSplitter, QMessageBox, QComboBox, QLineEdit, QFormLayout, 
    QGroupBox, QScrollArea, QGridLayout, QSpacerItem, QSizePolicy,
    QSpinBox, QDoubleSpinBox, QCheckBox, QSlider, QFileDialog,
    QFrame, QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QDialog, QDesktopWidget
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QColor

# 导入重构后的核心组件
from core.app_controller import AppController
from core.project_manager import ProjectManager
from processors.text_processor import StoryboardResult
from processors.image_processor import ImageGenerationConfig, BatchImageResult
from processors.video_processor import VideoConfig
from utils.logger import logger
from gui.storyboard_tab import StoryboardTab
from gui.project_dialog import NewProjectDialog, OpenProjectDialog

# 导入主题系统
try:
    # 当从main.py运行时使用相对导入
    from .modern_styles import (
        apply_modern_style, set_theme, toggle_theme as global_toggle_theme, 
        ThemeType, get_style_manager
    )
    from .notification_system import show_success, show_info
except ImportError:
    # 当直接运行或测试时使用绝对导入
    from modern_styles import (
        apply_modern_style, set_theme, toggle_theme as global_toggle_theme, 
        ThemeType, get_style_manager
    )
    from notification_system import show_success, show_info

class WorkerSignals(QObject):
    """工作线程信号"""
    progress = pyqtSignal(float, str)  # 进度, 消息
    finished = pyqtSignal(object)  # 结果
    error = pyqtSignal(str)  # 错误信息

class AsyncWorker(QThread):
    """异步工作线程"""
    
    def __init__(self, coro, *args, **kwargs):
        super().__init__()
        self.coro = coro
        self.args = args
        self.kwargs = kwargs
        # 确保signals在主线程中创建
        self.signals = WorkerSignals()
        # 将signals移动到主线程，避免跨线程问题
        self.signals.moveToThread(QApplication.instance().thread())
        self.result = None
        
    def run(self):
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # 运行协程
                self.result = loop.run_until_complete(
                    self.coro(*self.args, **self.kwargs)
                )
                
                self.signals.finished.emit(self.result)
                
            except Exception as e:
                logger.error(f"异步任务执行失败: {e}")
                self.signals.error.emit(str(e))
            finally:
                # 确保事件循环正确关闭
                try:
                    # 取消所有未完成的任务
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    
                    # 等待所有任务完成或取消
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        
                except Exception as cleanup_error:
                    logger.warning(f"清理事件循环时出错: {cleanup_error}")
                finally:
                    loop.close()
                    
        except Exception as e:
            logger.error(f"线程执行失败: {e}")
            self.signals.error.emit(str(e))

class NewMainWindow(QMainWindow):
    """新的主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化应用控制器
        self.app_controller = AppController()
        
        # 初始化项目管理器
        self.project_manager = ProjectManager()
        
        # 当前工作线程
        self.current_worker = None
        
        # 初始化UI
        self.init_ui()
        
        # 初始化应用控制器
        self.init_app_controller()
        
        # 应用现代化主题
        self.init_theme_system()
        
        # 初始化项目状态显示
        self.update_project_status()
        
        # 初始化文本占位符
        self.update_text_placeholder()
        
        logger.info("新主窗口初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("AI 视频生成系统 - 重构版")
        
        # 获取屏幕尺寸并设置合适的窗口大小
        screen = QApplication.desktop().screenGeometry()
        
        # 设置窗口为屏幕的90%，但不超过最大尺寸
        max_width = min(1600, int(screen.width() * 0.9))
        max_height = min(1000, int(screen.height() * 0.9))
        
        # 计算居中位置
        x = (screen.width() - max_width) // 2
        y = (screen.height() - max_height) // 2
        
        self.setGeometry(x, y, max_width, max_height)
        
        # 设置最小窗口大小
        self.setMinimumSize(1200, 800)
        
        # 原有的基础样式被现代化主题系统替代
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建工具栏
        self.create_toolbar(main_layout)
        
        # 创建标签页
        self.create_tabs(main_layout)
        
        # 创建状态栏
        self.create_status_bar()
    
    def create_toolbar(self, parent_layout):
        """创建工具栏"""
        toolbar_frame = QFrame()
        toolbar_frame.setFrameStyle(QFrame.StyledPanel)
        toolbar_layout = QHBoxLayout(toolbar_frame)
        
        # 新建项目按钮
        self.new_project_btn = QPushButton("新建项目")
        self.new_project_btn.clicked.connect(self.new_project)
        toolbar_layout.addWidget(self.new_project_btn)
        
        # 打开项目按钮
        self.open_project_btn = QPushButton("打开项目")
        self.open_project_btn.clicked.connect(self.open_project)
        toolbar_layout.addWidget(self.open_project_btn)
        
        # 保存项目按钮
        self.save_project_btn = QPushButton("保存项目")
        self.save_project_btn.clicked.connect(self.save_project)
        toolbar_layout.addWidget(self.save_project_btn)
        
        toolbar_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # 服务状态指示器
        self.service_status_label = QLabel("服务状态: 未知")
        toolbar_layout.addWidget(self.service_status_label)
        
        # 刷新服务按钮
        self.refresh_services_btn = QPushButton("刷新服务")
        self.refresh_services_btn.clicked.connect(self.refresh_services)
        toolbar_layout.addWidget(self.refresh_services_btn)
        
        # 主题切换按钮
        self.theme_toggle_btn = QPushButton("🌙")
        self.theme_toggle_btn.setToolTip("切换深色/浅色主题")
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        self.theme_toggle_btn.setMaximumWidth(40)
        toolbar_layout.addWidget(self.theme_toggle_btn)
        
        parent_layout.addWidget(toolbar_frame)
    
    def create_tabs(self, parent_layout):
        """创建标签页"""
        self.tab_widget = QTabWidget()
        
        # 文本处理标签页
        self.text_tab = self.create_text_tab()
        self.tab_widget.addTab(self.text_tab, "文本处理")
        
        # 分镜生成标签页
        self.storyboard_tab = self.create_storyboard_tab()
        self.tab_widget.addTab(self.storyboard_tab, "分镜生成")
        
        # 图像生成标签页
        self.image_tab = self.create_image_tab()
        self.tab_widget.addTab(self.image_tab, "图像生成")
        
        # 视频生成标签页
        self.video_tab = self.create_video_tab()
        self.tab_widget.addTab(self.video_tab, "视频生成")
        
        # 项目管理标签页
        self.project_tab = self.create_project_tab()
        self.tab_widget.addTab(self.project_tab, "项目管理")
        
        # 设置标签页
        self.settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(self.settings_tab, "设置")
        
        parent_layout.addWidget(self.tab_widget)
    
    def create_text_tab(self):
        """创建文本处理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文本输入区域
        text_group = QGroupBox("文本输入")
        text_layout = QVBoxLayout(text_group)
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("请先创建项目，然后输入要转换为视频的文本内容...")
        self.text_input.setMinimumHeight(200)
        # 连接文本变化信号，自动保存
        self.text_input.textChanged.connect(self.on_text_changed)
        text_layout.addWidget(self.text_input)
        
        # 文本操作按钮
        text_buttons_layout = QHBoxLayout()
        
        self.load_text_btn = QPushButton("加载文本文件")
        self.load_text_btn.clicked.connect(self.load_text_file)
        text_buttons_layout.addWidget(self.load_text_btn)
        
        self.rewrite_text_btn = QPushButton("AI改写文本")
        self.rewrite_text_btn.clicked.connect(self.rewrite_text)
        text_buttons_layout.addWidget(self.rewrite_text_btn)
        
        self.clear_text_btn = QPushButton("清空文本")
        self.clear_text_btn.clicked.connect(self.clear_text)
        text_buttons_layout.addWidget(self.clear_text_btn)
        
        text_buttons_layout.addStretch()
        text_layout.addLayout(text_buttons_layout)
        
        layout.addWidget(text_group)
        
        # 改写后的文本显示区域
        rewritten_group = QGroupBox("改写后的文本")
        rewritten_layout = QVBoxLayout(rewritten_group)
        
        self.rewritten_text = QTextEdit()
        self.rewritten_text.setReadOnly(True)
        self.rewritten_text.setMinimumHeight(150)
        rewritten_layout.addWidget(self.rewritten_text)
        
        layout.addWidget(rewritten_group)
        
        # 快速生成按钮
        quick_generate_layout = QHBoxLayout()
        
        self.quick_generate_btn = QPushButton("一键生成视频")
        self.quick_generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.quick_generate_btn.clicked.connect(self.quick_generate_video)
        quick_generate_layout.addWidget(self.quick_generate_btn)
        
        layout.addLayout(quick_generate_layout)
        
        return tab
    
    def create_storyboard_tab(self):
        """创建分镜生成标签页"""
        # 使用重构后的StoryboardTab类
        return StoryboardTab(self)
    
    def create_image_tab(self):
        """创建图像生成标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 图像配置
        config_group = QGroupBox("图像生成配置")
        config_layout = QFormLayout(config_group)
        
        # 图像提供商选择
        self.image_provider_combo = QComboBox()
        config_layout.addRow("图像提供商:", self.image_provider_combo)
        
        # 图像尺寸
        size_layout = QHBoxLayout()
        self.width_spin = QSpinBox()
        self.width_spin.setRange(256, 2048)
        self.width_spin.setValue(1024)
        self.width_spin.setSingleStep(64)
        size_layout.addWidget(self.width_spin)
        
        size_layout.addWidget(QLabel("×"))
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(256, 2048)
        self.height_spin.setValue(576)
        self.height_spin.setSingleStep(64)
        size_layout.addWidget(self.height_spin)
        
        config_layout.addRow("图像尺寸:", size_layout)
        
        # 生成步数
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(10, 100)
        self.steps_spin.setValue(20)
        config_layout.addRow("生成步数:", self.steps_spin)
        
        # CFG Scale
        self.cfg_scale_spin = QDoubleSpinBox()
        self.cfg_scale_spin.setRange(1.0, 20.0)
        self.cfg_scale_spin.setValue(7.0)
        self.cfg_scale_spin.setSingleStep(0.5)
        config_layout.addRow("CFG Scale:", self.cfg_scale_spin)
        
        # 负面提示词
        self.negative_prompt_edit = QLineEdit()
        self.negative_prompt_edit.setText("low quality, blurry, distorted")
        config_layout.addRow("负面提示词:", self.negative_prompt_edit)
        
        layout.addWidget(config_group)
        
        # 图像操作按钮
        image_buttons_layout = QHBoxLayout()
        
        self.generate_images_btn = QPushButton("生成图像")
        self.generate_images_btn.clicked.connect(self.generate_images)
        image_buttons_layout.addWidget(self.generate_images_btn)
        
        self.view_images_btn = QPushButton("查看图像")
        self.view_images_btn.clicked.connect(self.view_images)
        image_buttons_layout.addWidget(self.view_images_btn)
        
        image_buttons_layout.addStretch()
        layout.addLayout(image_buttons_layout)
        
        # 图像预览区域
        self.image_list = QListWidget()
        self.image_list.setViewMode(QListWidget.IconMode)
        self.image_list.setIconSize(QSize(200, 150))
        self.image_list.setResizeMode(QListWidget.Adjust)
        layout.addWidget(self.image_list)
        
        return tab
    
    def create_video_tab(self):
        """创建视频生成标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 视频配置
        config_group = QGroupBox("视频生成配置")
        config_layout = QFormLayout(config_group)
        
        # 帧率
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(15, 60)
        self.fps_spin.setValue(24)
        config_layout.addRow("帧率 (FPS):", self.fps_spin)
        
        # 每镜头时长
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(1.0, 10.0)
        self.duration_spin.setValue(3.0)
        self.duration_spin.setSingleStep(0.5)
        config_layout.addRow("每镜头时长 (秒):", self.duration_spin)
        
        # 转场效果
        self.transition_combo = QComboBox()
        self.transition_combo.addItems(["fade", "cut", "dissolve", "slide_left", "slide_right", "zoom_in", "zoom_out"])
        config_layout.addRow("转场效果:", self.transition_combo)
        
        # 背景音乐
        music_layout = QHBoxLayout()
        self.music_path_edit = QLineEdit()
        self.music_path_edit.setPlaceholderText("选择背景音乐文件...")
        music_layout.addWidget(self.music_path_edit)
        
        self.browse_music_btn = QPushButton("浏览")
        self.browse_music_btn.clicked.connect(self.browse_music_file)
        music_layout.addWidget(self.browse_music_btn)
        
        config_layout.addRow("背景音乐:", music_layout)
        
        # 音乐音量
        self.music_volume_slider = QSlider(Qt.Horizontal)
        self.music_volume_slider.setRange(0, 100)
        self.music_volume_slider.setValue(30)
        config_layout.addRow("音乐音量:", self.music_volume_slider)
        
        layout.addWidget(config_group)
        
        # 视频操作按钮
        video_buttons_layout = QHBoxLayout()
        
        self.create_video_btn = QPushButton("创建视频")
        self.create_video_btn.clicked.connect(self.create_video)
        video_buttons_layout.addWidget(self.create_video_btn)
        
        self.create_animated_btn = QPushButton("创建动画视频")
        self.create_animated_btn.clicked.connect(self.create_animated_video)
        video_buttons_layout.addWidget(self.create_animated_btn)
        
        self.add_subtitles_btn = QPushButton("添加字幕")
        self.add_subtitles_btn.clicked.connect(self.add_subtitles)
        video_buttons_layout.addWidget(self.add_subtitles_btn)
        
        video_buttons_layout.addStretch()
        layout.addLayout(video_buttons_layout)
        
        # 视频预览区域
        self.video_info_label = QLabel("暂无视频")
        self.video_info_label.setAlignment(Qt.AlignCenter)
        self.video_info_label.setMinimumHeight(200)
        self.video_info_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #555555;
                border-radius: 8px;
                background-color: #404040;
            }
        """)
        layout.addWidget(self.video_info_label)
        
        return tab
    
    def create_project_tab(self):
        """创建项目管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 项目状态
        status_group = QGroupBox("项目状态")
        status_layout = QVBoxLayout(status_group)
        
        self.project_status_label = QLabel("项目状态: 空")
        status_layout.addWidget(self.project_status_label)
        
        layout.addWidget(status_group)
        
        # 项目信息
        info_group = QGroupBox("项目信息")
        info_layout = QVBoxLayout(info_group)
        
        self.project_info_text = QTextEdit()
        self.project_info_text.setReadOnly(True)
        self.project_info_text.setMaximumHeight(200)
        info_layout.addWidget(self.project_info_text)
        
        layout.addWidget(info_group)
        
        # 项目操作
        project_buttons_layout = QHBoxLayout()
        
        self.clear_project_btn = QPushButton("清空项目")
        self.clear_project_btn.clicked.connect(self.clear_project)
        project_buttons_layout.addWidget(self.clear_project_btn)
        
        self.export_project_btn = QPushButton("导出项目")
        self.export_project_btn.clicked.connect(self.export_project)
        project_buttons_layout.addWidget(self.export_project_btn)
        
        project_buttons_layout.addStretch()
        layout.addLayout(project_buttons_layout)
        
        layout.addStretch()
        
        return tab
    
    def create_settings_tab(self):
        """创建设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 服务配置
        service_group = QGroupBox("服务配置")
        service_layout = QFormLayout(service_group)
        
        # API配置按钮
        self.config_apis_btn = QPushButton("配置API")
        self.config_apis_btn.clicked.connect(self.config_apis)
        service_layout.addRow("API设置:", self.config_apis_btn)
        
        layout.addWidget(service_group)
        
        # 输出配置
        output_group = QGroupBox("输出配置")
        output_layout = QFormLayout(output_group)
        
        # 输出目录
        output_dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText("output")
        output_dir_layout.addWidget(self.output_dir_edit)
        
        self.browse_output_btn = QPushButton("浏览")
        self.browse_output_btn.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(self.browse_output_btn)
        
        output_layout.addRow("输出目录:", output_dir_layout)
        
        layout.addWidget(output_group)
        
        layout.addStretch()
        
        return tab
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
    
    def init_app_controller(self):
        """初始化应用控制器"""
        def on_init_finished():
            self.update_service_status()
            self.update_providers()
            self.status_label.setText("应用初始化完成")
        
        def on_init_error(error):
            self.status_label.setText(f"初始化失败: {error}")
            QMessageBox.critical(self, "初始化失败", f"应用初始化失败:\n{error}")
        
        # 创建初始化工作线程
        self.init_worker = AsyncWorker(self.app_controller.initialize)
        self.init_worker.signals.finished.connect(on_init_finished)
        self.init_worker.signals.error.connect(on_init_error)
        self.init_worker.start()
        
        self.status_label.setText("正在初始化应用...")
    
    def update_service_status(self):
        """更新服务状态"""
        # 这里可以添加服务状态检查逻辑
        self.service_status_label.setText("服务状态: 正常")
        self.service_status_label.setStyleSheet("color: #28a745;")
    
    def update_providers(self):
        """更新提供商列表"""
        try:
            providers = self.app_controller.get_available_providers()
            
            # 更新图像提供商
            self.image_provider_combo.clear()
            self.image_provider_combo.addItems(providers.get("image", []))
            
            # 通过storyboard_tab更新LLM提供商
            if hasattr(self, 'storyboard_tab') and hasattr(self.storyboard_tab, 'load_providers'):
                self.storyboard_tab.load_providers()
            
        except Exception as e:
            logger.error(f"更新提供商列表失败: {e}")
    
    def show_progress(self, progress: float, message: str):
        """显示进度"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(int(progress * 100))
        self.status_label.setText(message)
    
    def hide_progress(self):
        """隐藏进度"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("就绪")
    
    # 事件处理方法
    def new_project(self):
        """新建项目"""
        # 检查是否有未保存的内容
        if self.project_manager.current_project:
            reply = QMessageBox.question(
                self, "新建项目", 
                "当前项目尚未保存，确定要新建项目吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # 显示新建项目对话框
        dialog = NewProjectDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                project_info = dialog.get_project_info()
                
                # 创建新项目
                project_config = self.project_manager.create_new_project(
                    project_info["name"], 
                    project_info["description"]
                )
                
                # 清空界面
                self.clear_all_content()
                
                # 立即保存当前内容（如果有的话）
                self.save_current_content()
                
                # 更新项目状态显示
                self.update_project_status()
                
                # 显示成功消息
                show_success(f"项目 '{project_info['name']}' 创建成功！")
                
                # 更新窗口标题
                self.setWindowTitle(f"AI 视频生成系统 - {project_info['name']}")
                
                # 更新文本框占位符
                self.update_text_placeholder()
                
                logger.info(f"新项目创建成功: {project_info['name']}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建项目失败：{e}")
                logger.error(f"创建项目失败: {e}")
    
    def clear_all_content(self):
        """清空所有内容"""
        try:
            # 暂时禁用自动保存
            self._disable_auto_save = True
            
            # 清空文本输入
            self.text_input.clear()
            self.rewritten_text.clear()
            
            # 清空分镜数据
            if hasattr(self, 'storyboard_tab'):
                if hasattr(self.storyboard_tab, 'text_input'):
                    self.storyboard_tab.text_input.clear()
                if hasattr(self.storyboard_tab, 'output_text'):
                    self.storyboard_tab.output_text.clear()
            
            # 清空图像列表
            self.image_list.clear()
            
            # 重置视频信息
            self.video_info_label.setText("暂无视频")
            
            # 清空应用控制器
            self.app_controller.clear_project()
            
            # 更新文本框占位符
            self.update_text_placeholder()
            
            # 重新启用自动保存
            self._disable_auto_save = False
            
        except Exception as e:
            logger.error(f"清空内容失败: {e}")
            self._disable_auto_save = False
    
    def open_project(self):
        """打开项目"""
        try:
            # 获取项目列表
            projects = self.project_manager.list_projects()
            
            # 显示打开项目对话框
            dialog = OpenProjectDialog(projects, self)
            if dialog.exec_() == QDialog.Accepted:
                selected_project = dialog.get_selected_project()
                if selected_project:
                    try:
                        # 加载项目
                        project_config = self.project_manager.load_project(selected_project["path"])
                        
                        # 清空当前内容
                        self.clear_all_content()
                        
                        # 加载项目内容到界面
                        self.load_project_content(project_config)
                        
                        # 更新项目状态
                        self.update_project_status()
                        
                        # 更新窗口标题
                        self.setWindowTitle(f"AI 视频生成系统 - {project_config['name']}")
                        
                        # 更新文本框占位符
                        self.update_text_placeholder()
                        
                        # 显示成功消息
                        show_success(f"项目 '{project_config['name']}' 加载成功！")
                        
                        # 强制刷新界面
                        self.repaint()
                        
                        logger.info(f"项目加载成功: {project_config['name']}")
                        
                    except Exception as e:
                        QMessageBox.critical(self, "错误", f"加载项目失败：{e}")
                        logger.error(f"加载项目失败: {e}")
                        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开项目失败：{e}")
            logger.error(f"打开项目失败: {e}")
    
    def load_project_content(self, project_config):
        """加载项目内容到界面"""
        try:
            # 暂时禁用自动保存
            self._disable_auto_save = True
            
            files = project_config.get("files", {})
            logger.info(f"加载项目文件信息: {files}")
            
            # 加载原始文本
            original_text_path = files.get("original_text")
            if original_text_path:
                original_file = Path(original_text_path)
                logger.info(f"尝试加载原始文本: {original_file}")
                if original_file.exists():
                    try:
                        with open(original_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            self.text_input.setPlainText(content)
                            logger.info(f"原始文本加载成功，长度: {len(content)}")
                    except Exception as e:
                        logger.error(f"读取原始文本文件失败: {e}")
                else:
                    logger.warning(f"原始文本文件不存在: {original_file}")
            else:
                logger.info("项目中没有原始文本文件路径")
            
            # 加载改写后的文本
            rewritten_text_path = files.get("rewritten_text")
            if rewritten_text_path:
                rewritten_file = Path(rewritten_text_path)
                logger.info(f"尝试加载改写文本: {rewritten_file}")
                if rewritten_file.exists():
                    try:
                        with open(rewritten_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            self.rewritten_text.setPlainText(content)
                            logger.info(f"改写文本加载成功，长度: {len(content)}")
                    except Exception as e:
                        logger.error(f"读取改写文本文件失败: {e}")
                else:
                    logger.warning(f"改写文本文件不存在: {rewritten_file}")
            else:
                logger.info("项目中没有改写文本文件路径")
            
            # 加载图像
            if files.get("images"):
                logger.info(f"加载图像列表: {files['images']}")
                for image_path in files["images"]:
                    if Path(image_path).exists():
                        self.add_image_to_list(image_path)
                    else:
                        logger.warning(f"图像文件不存在: {image_path}")
            
            logger.info("项目内容加载完成")
            
            # 重新启用自动保存
            self._disable_auto_save = False
            
        except Exception as e:
            logger.error(f"加载项目内容失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            # 确保重新启用自动保存
            self._disable_auto_save = False
    
    def add_image_to_list(self, image_path):
        """添加图像到列表"""
        try:
            item = QListWidgetItem()
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                item.setIcon(QIcon(scaled_pixmap))
            
            filename = Path(image_path).name
            item.setText(filename)
            item.setToolTip(str(image_path))
            self.image_list.addItem(item)
            
        except Exception as e:
            logger.error(f"添加图像到列表失败: {e}")
    
    def save_project(self):
        """保存项目"""
        try:
            if not self.project_manager.current_project:
                QMessageBox.warning(self, "警告", "没有打开的项目可以保存！")
                return
            
            # 保存当前界面内容到项目
            self.save_current_content()
            
            # 保存项目
            if self.project_manager.save_project():
                show_success("项目保存成功！")
                self.status_label.setText("项目已保存")
                logger.info("项目保存成功")
            else:
                QMessageBox.critical(self, "错误", "项目保存失败！")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存项目失败：{e}")
            logger.error(f"保存项目失败: {e}")
    
    def on_text_changed(self):
        """文本内容变化时自动保存"""
        try:
            # 检查是否禁用自动保存
            if getattr(self, '_disable_auto_save', False):
                return
            
            # 检查是否有当前项目，如果没有且有文本内容，强制创建项目
            if hasattr(self, 'project_manager'):
                text_content = self.text_input.toPlainText().strip()
                
                if not self.project_manager.current_project and text_content:
                    # 用户输入了内容但没有项目，强制创建项目
                    self.force_create_project()
                    return
                
                if self.project_manager.current_project:
                    # 延迟保存，避免频繁保存
                    if hasattr(self, '_save_timer'):
                        self._save_timer.stop()
                    
                    self._save_timer = QTimer()
                    self._save_timer.setSingleShot(True)
                    self._save_timer.timeout.connect(self.auto_save_original_text)
                    self._save_timer.start(2000)  # 2秒后保存
        except Exception as e:
            logger.error(f"文本变化处理失败: {e}")
    
    def force_create_project(self):
        """强制创建项目"""
        try:
            # 暂时禁用自动保存，防止递归
            self._disable_auto_save = True
            
            # 获取当前文本内容
            current_text = self.text_input.toPlainText().strip()
            
            QMessageBox.information(
                self, 
                "需要创建项目", 
                "检测到您输入了文本内容，但还没有创建项目。\n\n请先创建一个项目来保存您的工作内容。"
            )
            
            # 显示新建项目对话框
            dialog = NewProjectDialog(self)
            dialog.setWindowTitle("创建项目 - 必需")
            
            # 循环直到用户创建项目或清空文本
            while True:
                if dialog.exec_() == QDialog.Accepted:
                    try:
                        project_info = dialog.get_project_info()
                        
                        # 创建新项目
                        project_config = self.project_manager.create_new_project(
                            project_info["name"], 
                            project_info["description"]
                        )
                        
                        # 重新启用自动保存
                        self._disable_auto_save = False
                        
                        # 保存当前文本到项目
                        if current_text:
                            self.project_manager.save_text_content(current_text, "original_text")
                        
                        # 更新项目状态显示
                        self.update_project_status()
                        
                        # 显示成功消息
                        show_success(f"项目 '{project_info['name']}' 创建成功！文本内容已保存。")
                        
                        # 更新窗口标题
                        self.setWindowTitle(f"AI 视频生成系统 - {project_info['name']}")
                        
                        # 更新文本框占位符
                        self.update_text_placeholder()
                        
                        logger.info(f"强制新项目创建成功: {project_info['name']}")
                        break
                        
                    except Exception as e:
                        QMessageBox.critical(self, "错误", f"创建项目失败：{e}")
                        logger.error(f"强制创建项目失败: {e}")
                        # 继续循环，让用户重新尝试
                        continue
                
                else:
                    # 用户取消了，询问是否清空文本
                    reply = QMessageBox.question(
                        self, 
                        "确认操作", 
                        "您取消了项目创建。\n\n要继续工作，必须创建一个项目。\n是否清空文本内容？",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        # 清空文本
                        self.text_input.clear()
                        self._disable_auto_save = False
                        logger.info("用户选择清空文本内容")
                        break
                    else:
                        # 继续要求创建项目
                        continue
            
            # 重新启用自动保存
            self._disable_auto_save = False
            
        except Exception as e:
            logger.error(f"强制创建项目过程失败: {e}")
            self._disable_auto_save = False
    
    def update_text_placeholder(self):
        """更新文本框占位符"""
        try:
            if self.project_manager.current_project:
                project_name = self.project_manager.current_project.get("name", "当前项目")
                placeholder = f"项目：{project_name}\n请输入要转换为视频的文本内容..."
            else:
                placeholder = "请先创建项目，然后输入要转换为视频的文本内容..."
            
            self.text_input.setPlaceholderText(placeholder)
            
        except Exception as e:
            logger.error(f"更新文本占位符失败: {e}")
    
    def auto_save_original_text(self):
        """自动保存原始文本"""
        try:
            if self.project_manager.current_project:
                original_text = self.text_input.toPlainText().strip()
                if original_text:
                    self.project_manager.save_text_content(original_text, "original_text")
                    logger.debug("原始文本已自动保存")
        except Exception as e:
            logger.error(f"自动保存原始文本失败: {e}")
    
    def save_current_content(self):
        """保存当前界面内容到项目"""
        try:
            if not self.project_manager.current_project:
                return
            
            # 保存原始文本
            original_text = self.text_input.toPlainText().strip()
            if original_text:
                self.project_manager.save_text_content(original_text, "original_text")
            
            # 保存改写后的文本
            rewritten_text = self.rewritten_text.toPlainText().strip()
            if rewritten_text:
                self.project_manager.save_text_content(rewritten_text, "rewritten_text")
            
            logger.info("当前内容已保存到项目")
            
        except Exception as e:
            logger.error(f"保存当前内容失败: {e}")
    
    def refresh_services(self):
        """刷新服务"""
        self.update_service_status()
        self.update_providers()
        self.status_label.setText("服务状态已刷新")
    
    def load_text_file(self):
        """加载文本文件"""
        # 检查是否有项目，如果没有提示创建
        if not self.project_manager.current_project:
            reply = QMessageBox.question(
                self, "需要创建项目", 
                "加载文本文件需要先创建一个项目。\n是否现在创建项目？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.new_project()
                if not self.project_manager.current_project:
                    return  # 用户取消了项目创建
            else:
                return
        
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文本文件", "", "文本文件 (*.txt *.md)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_input.setPlainText(content)
                
                # 自动保存到项目
                self.project_manager.save_text_content(content, "original_text")
                
                self.status_label.setText(f"文本文件已加载并保存到项目: {file_path}")
                show_success("文本文件加载成功并已保存到项目！")
                
            except Exception as e:
                QMessageBox.critical(self, "加载失败", f"无法加载文本文件:\n{e}")
    
    def rewrite_text(self):
        """AI改写文本"""
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "请先输入文本内容")
            return
        
        # 检查是否有项目，如果没有提示创建
        if not self.project_manager.current_project:
            reply = QMessageBox.question(
                self, "需要创建项目", 
                "AI改写功能需要先创建一个项目来保存结果。\n是否现在创建项目？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.new_project()
                if not self.project_manager.current_project:
                    return  # 用户取消了项目创建
            else:
                return
        
        def on_rewrite_finished(result):
            self.rewritten_text.setPlainText(result)
            
            # 自动保存改写后的文本到项目
            try:
                if self.project_manager.current_project:
                    self.project_manager.save_text_content(result, "rewritten_text")
                    logger.info("改写后的文本已自动保存到项目")
            except Exception as e:
                logger.error(f"保存改写文本失败: {e}")
            
            self.hide_progress()
            # 更新左下角状态显示
            self.status_label.setText("✅ 文本改写完成")
            show_success("文本改写已完成！改写后的内容已显示在下方文本框中。")
            
            # 同步到分镜标签页
            if hasattr(self, 'storyboard_tab') and hasattr(self.storyboard_tab, 'load_rewritten_text_from_main'):
                self.storyboard_tab.load_rewritten_text_from_main()
        
        def on_rewrite_error(error):
            self.hide_progress()
            # 更新左下角状态显示
            self.status_label.setText("❌ 文本改写失败")
            QMessageBox.critical(self, "改写失败", f"文本改写失败:\n{error}")
        
        def on_progress(progress, message):
            # 更新左下角状态显示
            self.status_label.setText(f"🔄 正在改写文章...")
            self.show_progress(progress, message)
        
        # 创建改写工作线程
        provider = self.storyboard_tab.rewrite_provider_combo.currentText() if hasattr(self, 'storyboard_tab') and hasattr(self.storyboard_tab, 'rewrite_provider_combo') and self.storyboard_tab.rewrite_provider_combo.currentText() != "自动选择" else None
        self.current_worker = AsyncWorker(self.app_controller.rewrite_text, text, provider)
        self.current_worker.signals.finished.connect(on_rewrite_finished)
        self.current_worker.signals.error.connect(on_rewrite_error)
        self.current_worker.signals.progress.connect(on_progress)
        self.current_worker.start()
    
    def clear_text(self):
        """清空文本"""
        self.text_input.clear()
        self.rewritten_text.clear()
    
    def quick_generate_video(self):
        """一键生成视频"""
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "请先输入文本内容")
            return
        
        def on_generate_finished(result):
            self.hide_progress()
            self.video_info_label.setText(f"视频已生成: {result}")
            self.update_project_status()
            self.status_label.setText("视频生成完成")
            QMessageBox.information(self, "生成完成", f"视频已生成:\n{result}")
        
        def on_generate_error(error):
            self.hide_progress()
            QMessageBox.critical(self, "生成失败", f"视频生成失败:\n{error}")
        
        def on_progress(progress, message):
            self.show_progress(progress, message)
        
        # 准备配置
        style = self.storyboard_tab.style_combo.currentText() if hasattr(self, 'storyboard_tab') and hasattr(self.storyboard_tab, 'style_combo') else "电影风格"
        providers = {
            "llm": self.storyboard_tab.rewrite_provider_combo.currentText() if hasattr(self, 'storyboard_tab') and hasattr(self.storyboard_tab, 'rewrite_provider_combo') and self.storyboard_tab.rewrite_provider_combo.currentText() != "自动选择" else None,
            "image": self.image_provider_combo.currentText() if self.image_provider_combo.currentText() else None
        }
        
        image_config = ImageGenerationConfig(
            width=self.width_spin.value(),
            height=self.height_spin.value(),
            steps=self.steps_spin.value(),
            cfg_scale=self.cfg_scale_spin.value(),
            negative_prompt=self.negative_prompt_edit.text()
        )
        
        video_config = VideoConfig(
            fps=self.fps_spin.value(),
            duration_per_shot=self.duration_spin.value(),
            transition_type=self.transition_combo.currentText(),
            background_music=self.music_path_edit.text() if self.music_path_edit.text() else None,
            background_music_volume=self.music_volume_slider.value() / 100.0
        )
        
        # 创建生成工作线程
        self.current_worker = AsyncWorker(
            self.app_controller.create_video_from_text,
            text, style, image_config, video_config, providers, on_progress
        )
        self.current_worker.signals.finished.connect(on_generate_finished)
        self.current_worker.signals.error.connect(on_generate_error)
        self.current_worker.start()
    
    def generate_storyboard(self):
        """生成分镜"""
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "请先输入文本内容")
            return
        
        def on_storyboard_finished(result):
            self.display_storyboard(result)
            self.hide_progress()
            self.update_project_status()
            self.status_label.setText("分镜生成完成")
        
        def on_storyboard_error(error):
            self.hide_progress()
            QMessageBox.critical(self, "生成失败", f"分镜生成失败:\n{error}")
        
        def on_progress(progress, message):
            self.show_progress(progress, message)
        
        style = self.storyboard_tab.style_combo.currentText() if hasattr(self, 'storyboard_tab') and hasattr(self.storyboard_tab, 'style_combo') else "电影风格"
        provider = self.storyboard_tab.rewrite_provider_combo.currentText() if hasattr(self, 'storyboard_tab') and hasattr(self.storyboard_tab, 'rewrite_provider_combo') and self.storyboard_tab.rewrite_provider_combo.currentText() != "自动选择" else None
        
        self.current_worker = AsyncWorker(
            self.app_controller.generate_storyboard_only,
            text, style, provider, on_progress
        )
        self.current_worker.signals.finished.connect(on_storyboard_finished)
        self.current_worker.signals.error.connect(on_storyboard_error)
        self.current_worker.start()
    
    def display_storyboard(self, storyboard: StoryboardResult):
        """显示分镜"""
        # 通过storyboard_tab显示分镜数据
        if hasattr(self, 'storyboard_tab') and hasattr(self.storyboard_tab, 'show_shots_table'):
            # 转换数据格式以适配StoryboardTab的show_shots_table方法
            shots_data = []
            for shot in storyboard.shots:
                shots_data.append({
                    'shot_id': shot.shot_id,
                    'scene': shot.scene,
                    'characters': shot.characters,
                    'action': shot.action,
                    'dialogue': shot.dialogue,
                    'image_prompt': shot.image_prompt
                })
            self.storyboard_tab.show_shots_table(shots_data)
        else:
            logger.warning("无法显示分镜：storyboard_tab不可用")
    
    def export_storyboard(self):
        """导出分镜"""
        project_status = self.app_controller.get_project_status()
        if not project_status.get("has_storyboard"):
            QMessageBox.warning(self, "警告", "没有可导出的分镜数据")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(self, "导出分镜", "", "JSON文件 (*.json);;Markdown文件 (*.md)")
        if file_path:
            try:
                if file_path.endswith('.json'):
                    format_type = "json"
                else:
                    format_type = "markdown"
                
                storyboard = self.app_controller.current_project["storyboard"]
                content = self.app_controller.text_processor.export_storyboard(storyboard, format_type)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.status_label.setText(f"分镜已导出: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"无法导出分镜:\n{e}")
    
    def generate_images(self):
        """生成图像"""
        project_status = self.app_controller.get_project_status()
        if not project_status.get("has_storyboard"):
            QMessageBox.warning(self, "警告", "请先生成分镜")
            return
        
        def on_images_finished(result):
            self.display_images(result)
            self.hide_progress()
            self.update_project_status()
            self.status_label.setText(f"图像生成完成，成功 {result.success_count} 张")
        
        def on_images_error(error):
            self.hide_progress()
            QMessageBox.critical(self, "生成失败", f"图像生成失败:\n{error}")
        
        def on_progress(progress, message):
            self.show_progress(progress, message)
        
        config = ImageGenerationConfig(
            provider=self.image_provider_combo.currentText(),
            width=self.width_spin.value(),
            height=self.height_spin.value(),
            steps=self.steps_spin.value(),
            cfg_scale=self.cfg_scale_spin.value(),
            negative_prompt=self.negative_prompt_edit.text()
        )
        
        self.current_worker = AsyncWorker(
            self.app_controller.generate_images_only,
            None, config, on_progress
        )
        self.current_worker.signals.finished.connect(on_images_finished)
        self.current_worker.signals.error.connect(on_images_error)
        self.current_worker.start()
    
    def display_images(self, image_results: BatchImageResult):
        """显示图像"""
        self.image_list.clear()
        
        for result in image_results.results:
            if os.path.exists(result.image_path):
                item = QListWidgetItem()
                pixmap = QPixmap(result.image_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    item.setIcon(QIcon(scaled_pixmap))
                item.setText(f"镜头 {result.shot_id}")
                item.setToolTip(result.prompt)
                self.image_list.addItem(item)
    
    def view_images(self):
        """查看图像"""
        project_status = self.app_controller.get_project_status()
        if not project_status.get("has_images"):
            QMessageBox.warning(self, "警告", "没有可查看的图像")
            return
        
        # 打开图像输出目录
        images_info = project_status.get("images_info", {})
        output_dir = images_info.get("output_directory")
        if output_dir and os.path.exists(output_dir):
            os.startfile(output_dir)
    
    def create_video(self):
        """创建视频"""
        project_status = self.app_controller.get_project_status()
        if not project_status.get("has_storyboard") or not project_status.get("has_images"):
            QMessageBox.warning(self, "警告", "请先生成分镜和图像")
            return
        
        def on_video_finished(result):
            self.video_info_label.setText(f"视频已生成: {result}")
            self.hide_progress()
            self.update_project_status()
            self.status_label.setText("视频创建完成")
            QMessageBox.information(self, "创建完成", f"视频已创建:\n{result}")
        
        def on_video_error(error):
            self.hide_progress()
            QMessageBox.critical(self, "创建失败", f"视频创建失败:\n{error}")
        
        def on_progress(progress, message):
            self.show_progress(progress, message)
        
        config = VideoConfig(
            fps=self.fps_spin.value(),
            duration_per_shot=self.duration_spin.value(),
            transition_type=self.transition_combo.currentText(),
            background_music=self.music_path_edit.text() if self.music_path_edit.text() else None,
            background_music_volume=self.music_volume_slider.value() / 100.0
        )
        
        self.current_worker = AsyncWorker(
            self.app_controller.create_video_only,
            None, None, config, on_progress
        )
        self.current_worker.signals.finished.connect(on_video_finished)
        self.current_worker.signals.error.connect(on_video_error)
        self.current_worker.start()
    
    def create_animated_video(self):
        """创建动画视频"""
        project_status = self.app_controller.get_project_status()
        if not project_status.get("has_images"):
            QMessageBox.warning(self, "警告", "请先生成图像")
            return
        
        def on_animated_finished(result):
            self.video_info_label.setText(f"动画视频已生成: {result}")
            self.hide_progress()
            self.status_label.setText("动画视频创建完成")
            QMessageBox.information(self, "创建完成", f"动画视频已创建:\n{result}")
        
        def on_animated_error(error):
            self.hide_progress()
            QMessageBox.critical(self, "创建失败", f"动画视频创建失败:\n{error}")
        
        def on_progress(progress, message):
            self.show_progress(progress, message)
        
        config = VideoConfig(
            fps=self.fps_spin.value(),
            duration_per_shot=self.duration_spin.value()
        )
        
        self.current_worker = AsyncWorker(
            self.app_controller.create_animated_video,
            None, "ken_burns", config, on_progress
        )
        self.current_worker.signals.finished.connect(on_animated_finished)
        self.current_worker.signals.error.connect(on_animated_error)
        self.current_worker.start()
    
    def add_subtitles(self):
        """添加字幕"""
        project_status = self.app_controller.get_project_status()
        if not project_status.get("has_final_video") or not project_status.get("has_storyboard"):
            QMessageBox.warning(self, "警告", "请先生成视频和分镜")
            return
        
        def on_subtitles_finished(result):
            self.video_info_label.setText(f"带字幕视频已生成: {result}")
            self.hide_progress()
            self.status_label.setText("字幕添加完成")
            QMessageBox.information(self, "添加完成", f"带字幕视频已生成:\n{result}")
        
        def on_subtitles_error(error):
            self.hide_progress()
            QMessageBox.critical(self, "添加失败", f"字幕添加失败:\n{error}")
        
        self.current_worker = AsyncWorker(self.app_controller.add_subtitles)
        self.current_worker.signals.finished.connect(on_subtitles_finished)
        self.current_worker.signals.error.connect(on_subtitles_error)
        self.current_worker.start()
        
        self.show_progress(0.5, "正在添加字幕...")
    
    def browse_music_file(self):
        """浏览音乐文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择音乐文件", "", "音频文件 (*.mp3 *.wav *.m4a *.aac)")
        if file_path:
            self.music_path_edit.setText(file_path)
    
    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir_edit.setText(dir_path)
    
    def clear_project(self):
        """清空项目"""
        reply = QMessageBox.question(self, "清空项目", "确定要清空当前项目吗？")
        if reply == QMessageBox.Yes:
            self.new_project()
    
    def export_project(self):
        """导出项目"""
        file_path, _ = QFileDialog.getSaveFileName(self, "导出项目", "", "JSON文件 (*.json)")
        if file_path:
            try:
                project_data = self.app_controller.export_project()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(project_data)
                
                self.status_label.setText(f"项目已导出: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"无法导出项目:\n{e}")
    
    def config_apis(self):
        """配置API"""
        QMessageBox.information(self, "配置API", "API配置功能正在开发中...")
    
    def update_project_status(self):
        """更新项目状态"""
        try:
            # 获取项目管理器状态
            project_status = self.project_manager.get_project_status()
            
            if project_status["has_project"]:
                # 有项目时显示项目状态
                status_text = f"项目: {project_status['project_name']}\n"
                status_text += f"目录: {project_status['project_dir']}\n\n"
                status_text += "文件状态:\n"
                
                files_status = project_status["files_status"]
                status_names = {
                    "original_text": "原始文本",
                    "rewritten_text": "改写文本",
                    "storyboard": "分镜脚本",
                    "images": "生成图片",
                    "audio": "音频文件",
                    "video": "视频文件",
                    "final_video": "最终视频",
                    "subtitles": "字幕文件"
                }
                
                for file_type, status in files_status.items():
                    name = status_names.get(file_type, file_type)
                    if file_type == "images":
                        exists = status.get("exists", False)
                        count = status.get("count", 0)
                        status_icon = "✅" if exists else "❌"
                        status_text += f"{status_icon} {name}: {count} 张\n"
                    else:
                        exists = status.get("exists", False)
                        status_icon = "✅" if exists else "❌"
                        status_text += f"{status_icon} {name}\n"
                
                self.project_status_label.setText(status_text)
                
                # 更新项目信息
                info_text = f"创建时间: {project_status['created_time'][:19].replace('T', ' ')}\n"
                info_text += f"修改时间: {project_status['last_modified'][:19].replace('T', ' ')}\n\n"
                
                # 添加文件路径信息
                info_text += "文件路径:\n"
                for file_type, status in files_status.items():
                    if file_type != "images" and status.get("path"):
                        name = status_names.get(file_type, file_type)
                        info_text += f"• {name}: {status['path']}\n"
                
                self.project_info_text.setPlainText(info_text)
                
            else:
                # 没有项目时显示默认状态
                self.project_status_label.setText("项目状态: 无项目\n\n请创建或打开一个项目")
                self.project_info_text.setPlainText("暂无项目信息")
            
        except Exception as e:
            logger.error(f"更新项目状态失败: {e}")
            self.project_status_label.setText("项目状态: 获取状态失败")
            self.project_info_text.setPlainText(f"错误: {e}")
    
    def init_theme_system(self):
        """初始化主题系统"""
        try:
            # 应用现代化样式到整个应用
            apply_modern_style()
            
            # 连接主题变化信号
            style_manager = get_style_manager()
            if style_manager:
                style_manager.theme_changed.connect(self.on_theme_changed)
                # 强制刷新样式
                self.refresh_theme_styles()
            
            # 更新主题切换按钮
            self.update_theme_button()
            
            logger.info("主题系统初始化完成")
        except Exception as e:
            logger.error(f"主题系统初始化失败: {e}")
    
    def refresh_theme_styles(self):
        """刷新主题样式"""
        try:
            style_manager = get_style_manager()
            if style_manager:
                # 获取完整样式表
                stylesheet = style_manager.get_complete_stylesheet()
                
                # 应用到主窗口
                self.setStyleSheet(stylesheet)
                
                # 强制更新所有子控件
                self.update()
                
                # 递归更新所有子控件
                for widget in self.findChildren(QWidget):
                    widget.update()
                    
                logger.info("主题样式已刷新")
        except Exception as e:
            logger.error(f"刷新主题样式失败: {e}")
    
    def toggle_theme(self):
        """切换主题"""
        try:
            global_toggle_theme()
            show_success("主题切换成功！")
        except Exception as e:
            logger.error(f"主题切换失败: {e}")
    
    def on_theme_changed(self, theme_name: str):
        """主题变化响应"""
        try:
            # 刷新样式
            self.refresh_theme_styles()
            
            # 更新主题按钮
            self.update_theme_button()
            
            # 显示切换成功通知
            show_success(f"已切换到{theme_name}主题")
            logger.info(f"主题已切换到: {theme_name}")
        except Exception as e:
            logger.error(f"主题变化响应失败: {e}")
    
    def update_theme_button(self):
        """更新主题切换按钮"""
        try:
            style_manager = get_style_manager()
            if style_manager and hasattr(style_manager, 'current_theme_type'):
                if style_manager.current_theme_type == ThemeType.DARK:
                    self.theme_toggle_btn.setText("☀️")
                    self.theme_toggle_btn.setToolTip("切换到浅色主题")
                else:
                    self.theme_toggle_btn.setText("🌙")
                    self.theme_toggle_btn.setToolTip("切换到深色主题")
            else:
                # 默认状态
                self.theme_toggle_btn.setText("🌙")
                self.theme_toggle_btn.setToolTip("切换主题")
        except Exception as e:
            logger.error(f"更新主题按钮失败: {e}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        reply = QMessageBox.question(self, "退出", "确定要退出应用吗？")
        if reply == QMessageBox.Yes:
            # 关闭应用控制器
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.app_controller.shutdown())
                loop.close()
            except Exception as e:
                logger.error(f"关闭应用控制器失败: {e}")
            
            event.accept()
        else:
            event.ignore()

# 移除main函数，避免与主程序冲突
# def main():
#     """主函数"""
#     app = QApplication(sys.argv)
#     
#     # 设置应用信息
#     app.setApplicationName("AI视频生成系统")
#     app.setApplicationVersion("2.0")
#     app.setOrganizationName("AI Video Generator")
#     
#     # 创建主窗口
#     window = NewMainWindow()
#     window.show()
#     
#     # 运行应用
#     sys.exit(app.exec_())

# 移除独立的应用程序入口点，避免与主程序冲突
# if __name__ == "__main__":
#     main()