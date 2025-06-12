# -*- coding: utf-8 -*-
"""
一致性控制面板
提供可视化的角色场景一致性管理界面
"""

import json
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QGroupBox, QLabel, QLineEdit, QTextEdit, QPushButton, QSlider,
    QCheckBox, QComboBox, QSpinBox, QDoubleSpinBox, QProgressBar,
    QScrollArea, QFrame, QSplitter, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QDialog, QDialogButtonBox, QApplication
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

from utils.logger import logger
from processors.consistency_enhanced_image_processor import ConsistencyConfig, ConsistencyData
from processors.text_processor import StoryboardResult
from utils.character_scene_manager import CharacterSceneManager
from processors.prompt_optimizer import PromptOptimizer

class ConsistencyPreviewWorker(QObject):
    """一致性预览工作线程"""
    preview_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, processor, storyboard, config):
        super().__init__()
        self.processor = processor
        self.storyboard = storyboard
        self.config = config
    
    def run(self):
        try:
            preview_data = self.processor.get_consistency_preview(self.storyboard, self.config)
            self.preview_ready.emit(preview_data)
        except Exception as e:
            self.error_occurred.emit(str(e))

class CharacterEditor(QDialog):
    """角色编辑器对话框"""
    
    def __init__(self, character_data: Dict[str, Any] = None, parent=None):
        super().__init__(parent)
        self.character_data = character_data or {}
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        self.setWindowTitle("角色编辑器")
        self.setModal(True)
        self.resize(500, 600)
        
        layout = QVBoxLayout(self)
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QGridLayout(basic_group)
        
        basic_layout.addWidget(QLabel("角色名称:"), 0, 0)
        self.name_edit = QLineEdit()
        basic_layout.addWidget(self.name_edit, 0, 1)
        
        basic_layout.addWidget(QLabel("角色描述:"), 1, 0)
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        basic_layout.addWidget(self.description_edit, 1, 1)
        
        layout.addWidget(basic_group)
        
        # 外貌特征
        appearance_group = QGroupBox("外貌特征")
        appearance_layout = QGridLayout(appearance_group)
        
        appearance_layout.addWidget(QLabel("外貌描述:"), 0, 0)
        self.appearance_edit = QTextEdit()
        self.appearance_edit.setMaximumHeight(80)
        appearance_layout.addWidget(self.appearance_edit, 0, 1)
        
        appearance_layout.addWidget(QLabel("服装描述:"), 1, 0)
        self.clothing_edit = QTextEdit()
        self.clothing_edit.setMaximumHeight(80)
        appearance_layout.addWidget(self.clothing_edit, 1, 1)
        
        layout.addWidget(appearance_group)
        
        # 一致性提示词
        consistency_group = QGroupBox("一致性提示词")
        consistency_layout = QVBoxLayout(consistency_group)
        
        self.consistency_edit = QTextEdit()
        self.consistency_edit.setMaximumHeight(100)
        self.consistency_edit.setPlaceholderText("输入用于保持角色一致性的提示词...")
        consistency_layout.addWidget(self.consistency_edit)
        
        layout.addWidget(consistency_group)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_data(self):
        """加载角色数据"""
        if self.character_data:
            self.name_edit.setText(self.character_data.get('name', ''))
            self.description_edit.setPlainText(self.character_data.get('description', ''))
            
            # 处理外貌信息（可能是字符串或字典）
            appearance = self.character_data.get('appearance', '')
            if isinstance(appearance, dict):
                # 如果是字典，提取主要信息
                appearance_parts = []
                for key, value in appearance.items():
                    if value and isinstance(value, str):
                        appearance_parts.append(f"{key}: {value}")
                appearance = "; ".join(appearance_parts)
            elif not isinstance(appearance, str):
                appearance = str(appearance)
            self.appearance_edit.setPlainText(appearance)
            
            # 处理服装信息（可能是字符串或字典）
            clothing = self.character_data.get('clothing', '')
            if isinstance(clothing, dict):
                # 如果是字典，提取主要信息
                clothing_parts = []
                for key, value in clothing.items():
                    if value and isinstance(value, str):
                        clothing_parts.append(f"{key}: {value}")
                clothing = "; ".join(clothing_parts)
            elif not isinstance(clothing, str):
                clothing = str(clothing)
            self.clothing_edit.setPlainText(clothing)
            
            self.consistency_edit.setPlainText(self.character_data.get('consistency_prompt', ''))
    
    def get_data(self) -> Dict[str, Any]:
        """获取编辑后的数据"""
        return {
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'appearance': self.appearance_edit.toPlainText().strip(),
            'clothing': self.clothing_edit.toPlainText().strip(),
            'consistency_prompt': self.consistency_edit.toPlainText().strip()
        }

class SceneEditor(QDialog):
    """场景编辑器对话框"""
    
    def __init__(self, scene_data: Dict[str, Any] = None, parent=None):
        super().__init__(parent)
        self.scene_data = scene_data or {}
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        self.setWindowTitle("场景编辑器")
        self.setModal(True)
        self.resize(500, 600)
        
        layout = QVBoxLayout(self)
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QGridLayout(basic_group)
        
        basic_layout.addWidget(QLabel("场景名称:"), 0, 0)
        self.name_edit = QLineEdit()
        basic_layout.addWidget(self.name_edit, 0, 1)
        
        basic_layout.addWidget(QLabel("场景描述:"), 1, 0)
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        basic_layout.addWidget(self.description_edit, 1, 1)
        
        layout.addWidget(basic_group)
        
        # 环境特征
        environment_group = QGroupBox("环境特征")
        environment_layout = QGridLayout(environment_group)
        
        environment_layout.addWidget(QLabel("环境描述:"), 0, 0)
        self.environment_edit = QTextEdit()
        self.environment_edit.setMaximumHeight(80)
        environment_layout.addWidget(self.environment_edit, 0, 1)
        
        environment_layout.addWidget(QLabel("光线描述:"), 1, 0)
        self.lighting_edit = QTextEdit()
        self.lighting_edit.setMaximumHeight(60)
        environment_layout.addWidget(self.lighting_edit, 1, 1)
        
        environment_layout.addWidget(QLabel("氛围描述:"), 2, 0)
        self.atmosphere_edit = QTextEdit()
        self.atmosphere_edit.setMaximumHeight(60)
        environment_layout.addWidget(self.atmosphere_edit, 2, 1)
        
        layout.addWidget(environment_group)
        
        # 一致性提示词
        consistency_group = QGroupBox("一致性提示词")
        consistency_layout = QVBoxLayout(consistency_group)
        
        self.consistency_edit = QTextEdit()
        self.consistency_edit.setMaximumHeight(100)
        self.consistency_edit.setPlaceholderText("输入用于保持场景一致性的提示词...")
        consistency_layout.addWidget(self.consistency_edit)
        
        layout.addWidget(consistency_group)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_data(self):
        """加载场景数据"""
        if self.scene_data:
            self.name_edit.setText(self.scene_data.get('name', ''))
            self.description_edit.setPlainText(self.scene_data.get('description', ''))
            
            # 处理环境信息（可能是字符串或字典）
            environment = self.scene_data.get('environment', '')
            if isinstance(environment, dict):
                # 如果是字典，提取主要信息
                env_parts = []
                for key, value in environment.items():
                    if value and isinstance(value, (str, list)):
                        if isinstance(value, list):
                            value = ", ".join(str(v) for v in value)
                        env_parts.append(f"{key}: {value}")
                environment = "; ".join(env_parts)
            elif not isinstance(environment, str):
                environment = str(environment)
            self.environment_edit.setPlainText(environment)
            
            # 处理光线信息（可能是字符串或字典）
            lighting = self.scene_data.get('lighting', '')
            if isinstance(lighting, dict):
                # 如果是字典，提取主要信息
                lighting_parts = []
                for key, value in lighting.items():
                    if value and isinstance(value, (str, list)):
                        if isinstance(value, list):
                            value = ", ".join(str(v) for v in value)
                        lighting_parts.append(f"{key}: {value}")
                lighting = "; ".join(lighting_parts)
            elif not isinstance(lighting, str):
                lighting = str(lighting)
            self.lighting_edit.setPlainText(lighting)
            
            # 处理氛围信息（可能是字符串或字典）
            atmosphere = self.scene_data.get('atmosphere', '')
            if isinstance(atmosphere, dict):
                # 如果是字典，提取主要信息
                atmosphere_parts = []
                for key, value in atmosphere.items():
                    if value and isinstance(value, (str, list)):
                        if isinstance(value, list):
                            value = ", ".join(str(v) for v in value)
                        atmosphere_parts.append(f"{key}: {value}")
                atmosphere = "; ".join(atmosphere_parts)
            elif not isinstance(atmosphere, str):
                atmosphere = str(atmosphere)
            self.atmosphere_edit.setPlainText(atmosphere)
            
            self.consistency_edit.setPlainText(self.scene_data.get('consistency_prompt', ''))
    
    def get_data(self) -> Dict[str, Any]:
        """获取编辑后的数据"""
        return {
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'environment': self.environment_edit.toPlainText().strip(),
            'lighting': self.lighting_edit.toPlainText().strip(),
            'atmosphere': self.atmosphere_edit.toPlainText().strip(),
            'consistency_prompt': self.consistency_edit.toPlainText().strip()
        }

class ConsistencyControlPanel(QWidget):
    """一致性控制面板"""
    
    # 信号定义
    config_changed = pyqtSignal(object)  # ConsistencyConfig
    preview_requested = pyqtSignal()
    generate_requested = pyqtSignal(object, object)  # storyboard, config
    
    def __init__(self, image_processor, project_manager, parent=None):
        super().__init__(parent)
        self.image_processor = image_processor
        self.project_manager = project_manager
        self.parent_window = parent  # 添加parent_window属性
        self.cs_manager = None  # 将在image_processor可用时初始化
        self.current_storyboard = None
        self.current_config = ConsistencyConfig()
        self.preview_worker = None
        self.preview_thread = None
        self.llm_api = None
        
        # 初始化LLM API
        self._init_llm_api()
        
        # 初始化提示词优化器
        self.prompt_optimizer = PromptOptimizer(self.llm_api, self.cs_manager)
        
        self.init_ui()
        self.setup_connections()
        # 延迟加载数据，确保所有组件都已初始化
        QTimer.singleShot(100, self.load_character_scene_data)
    
    def _init_llm_api(self):
        """初始化LLM API"""
        try:
            from models.llm_api import LLMApi
            from utils.config_manager import ConfigManager
            
            # 获取LLM配置
            config_manager = ConfigManager()
            llm_config = config_manager.get_llm_config()
            
            if llm_config and llm_config.get('api_key') and llm_config.get('api_url'):
                self.llm_api = LLMApi(
                    api_type=llm_config.get('api_type', 'deepseek'),
                    api_key=llm_config['api_key'],
                    api_url=llm_config['api_url']
                )
                logger.info("LLM API初始化成功")
            else:
                logger.warning("LLM配置不完整，跳过LLM API初始化")
                self.llm_api = None
        except Exception as e:
            logger.warning(f"LLM API初始化失败: {e}")
            self.llm_api = None
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 配置选项卡
        self.config_tab = self.create_config_tab()
        self.tab_widget.addTab(self.config_tab, "一致性配置")
        
        # 角色管理选项卡
        self.character_tab = self.create_character_tab()
        self.tab_widget.addTab(self.character_tab, "角色管理")
        
        # 场景管理选项卡
        self.scene_tab = self.create_scene_tab()
        self.tab_widget.addTab(self.scene_tab, "场景管理")
        
        # 高级优化选项卡
        self.advanced_tab = self.create_advanced_tab()
        self.tab_widget.addTab(self.advanced_tab, "高级优化")
        
        # 预览选项卡
        self.preview_tab = self.create_preview_tab()
        self.tab_widget.addTab(self.preview_tab, "一致性预览")
        
        layout.addWidget(self.tab_widget)
        
        # 底部控制按钮
        button_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("生成预览")
        self.preview_btn.setEnabled(False)
        button_layout.addWidget(self.preview_btn)
        
        self.generate_btn = QPushButton("开始生成")
        self.generate_btn.setEnabled(False)
        button_layout.addWidget(self.generate_btn)
        
        button_layout.addStretch()
        
        self.export_config_btn = QPushButton("导出配置")
        button_layout.addWidget(self.export_config_btn)
        
        self.import_config_btn = QPushButton("导入配置")
        button_layout.addWidget(self.import_config_btn)
        
        layout.addLayout(button_layout)
    
    def create_config_tab(self) -> QWidget:
        """创建配置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 基本设置
        basic_group = QGroupBox("基本设置")
        basic_layout = QGridLayout(basic_group)
        
        # 启用角色一致性
        self.enable_char_cb = QCheckBox("启用角色一致性")
        self.enable_char_cb.setChecked(True)
        basic_layout.addWidget(self.enable_char_cb, 0, 0)
        
        # 启用场景一致性
        self.enable_scene_cb = QCheckBox("启用场景一致性")
        self.enable_scene_cb.setChecked(True)
        basic_layout.addWidget(self.enable_scene_cb, 0, 1)
        
        # 自动提取新元素
        self.auto_extract_cb = QCheckBox("自动提取新角色和场景")
        self.auto_extract_cb.setChecked(True)
        basic_layout.addWidget(self.auto_extract_cb, 1, 0)
        
        # 预留位置
        basic_layout.addWidget(QLabel(""), 1, 1)
        
        layout.addWidget(basic_group)
        
        # 权重设置
        weight_group = QGroupBox("权重设置")
        weight_layout = QGridLayout(weight_group)
        
        # 一致性强度
        weight_layout.addWidget(QLabel("一致性强度:"), 0, 0)
        self.consistency_strength_slider = QSlider(Qt.Horizontal)
        self.consistency_strength_slider.setRange(0, 100)
        self.consistency_strength_slider.setValue(70)
        self.consistency_strength_label = QLabel("0.7")
        weight_layout.addWidget(self.consistency_strength_slider, 0, 1)
        weight_layout.addWidget(self.consistency_strength_label, 0, 2)
        
        # 角色权重
        weight_layout.addWidget(QLabel("角色权重:"), 1, 0)
        self.character_weight_slider = QSlider(Qt.Horizontal)
        self.character_weight_slider.setRange(0, 100)
        self.character_weight_slider.setValue(40)
        self.character_weight_label = QLabel("0.4")
        weight_layout.addWidget(self.character_weight_slider, 1, 1)
        weight_layout.addWidget(self.character_weight_label, 1, 2)
        
        # 场景权重
        weight_layout.addWidget(QLabel("场景权重:"), 2, 0)
        self.scene_weight_slider = QSlider(Qt.Horizontal)
        self.scene_weight_slider.setRange(0, 100)
        self.scene_weight_slider.setValue(30)
        self.scene_weight_label = QLabel("0.3")
        weight_layout.addWidget(self.scene_weight_slider, 2, 1)
        weight_layout.addWidget(self.scene_weight_label, 2, 2)
        
        # 风格权重
        weight_layout.addWidget(QLabel("风格权重:"), 3, 0)
        self.style_weight_slider = QSlider(Qt.Horizontal)
        self.style_weight_slider.setRange(0, 100)
        self.style_weight_slider.setValue(30)
        self.style_weight_label = QLabel("0.3")
        weight_layout.addWidget(self.style_weight_slider, 3, 1)
        weight_layout.addWidget(self.style_weight_label, 3, 2)
        
        layout.addWidget(weight_group)
        
        layout.addStretch()
        return widget
    
    def create_character_tab(self) -> QWidget:
        """创建角色管理选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        self.add_character_btn = QPushButton("添加角色")
        toolbar_layout.addWidget(self.add_character_btn)
        
        self.edit_character_btn = QPushButton("编辑角色")
        self.edit_character_btn.setEnabled(False)
        toolbar_layout.addWidget(self.edit_character_btn)
        
        self.delete_character_btn = QPushButton("删除角色")
        self.delete_character_btn.setEnabled(False)
        toolbar_layout.addWidget(self.delete_character_btn)
        
        toolbar_layout.addStretch()
        
        self.refresh_character_btn = QPushButton("刷新角色")
        toolbar_layout.addWidget(self.refresh_character_btn)
        
        layout.addLayout(toolbar_layout)
        
        # 角色列表
        self.character_table = QTableWidget()
        self.character_table.setColumnCount(4)
        self.character_table.setHorizontalHeaderLabels(["角色名称", "描述", "外貌", "一致性提示词"])
        self.character_table.horizontalHeader().setStretchLastSection(True)
        self.character_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.character_table)
        
        return widget
    
    def create_scene_tab(self) -> QWidget:
        """创建场景管理选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        self.add_scene_btn = QPushButton("添加场景")
        toolbar_layout.addWidget(self.add_scene_btn)
        
        self.edit_scene_btn = QPushButton("编辑场景")
        self.edit_scene_btn.setEnabled(False)
        toolbar_layout.addWidget(self.edit_scene_btn)
        
        self.delete_scene_btn = QPushButton("删除场景")
        self.delete_scene_btn.setEnabled(False)
        toolbar_layout.addWidget(self.delete_scene_btn)
        
        toolbar_layout.addStretch()
        
        self.refresh_scene_btn = QPushButton("刷新场景")
        toolbar_layout.addWidget(self.refresh_scene_btn)
        
        layout.addLayout(toolbar_layout)
        
        # 场景列表
        self.scene_table = QTableWidget()
        self.scene_table.setColumnCount(5)
        self.scene_table.setHorizontalHeaderLabels(["场景名称", "描述", "环境", "光线", "一致性提示词"])
        self.scene_table.horizontalHeader().setStretchLastSection(True)
        self.scene_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.scene_table)
        
        return widget
    
    def create_advanced_tab(self) -> QWidget:
        """创建高级优化选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # LLM优化设置
        llm_group = QGroupBox("LLM智能优化")
        llm_layout = QVBoxLayout(llm_group)
        
        # 启用LLM优化
        self.use_llm_cb = QCheckBox("启用LLM提示词优化")
        self.use_llm_cb.setChecked(False)  # 默认关闭
        llm_layout.addWidget(self.use_llm_cb)
        
        # 优化说明
        info_label = QLabel("注意：LLM优化功能需要配置有效的LLM API，\n可能会增加处理时间和API调用成本。")
        info_label.setStyleSheet("color: #666; font-size: 12px; padding: 10px;")
        info_label.setWordWrap(True)
        llm_layout.addWidget(info_label)
        
        # 优化选项
        options_layout = QGridLayout()
        
        # 优化强度
        options_layout.addWidget(QLabel("优化强度:"), 0, 0)
        self.llm_strength_slider = QSlider(Qt.Horizontal)
        self.llm_strength_slider.setRange(1, 10)
        self.llm_strength_slider.setValue(5)
        self.llm_strength_label = QLabel("5")
        options_layout.addWidget(self.llm_strength_slider, 0, 1)
        options_layout.addWidget(self.llm_strength_label, 0, 2)
        
        # 优化模式
        options_layout.addWidget(QLabel("优化模式:"), 1, 0)
        self.llm_mode_combo = QComboBox()
        self.llm_mode_combo.addItems(["快速优化", "标准优化", "深度优化"])
        self.llm_mode_combo.setCurrentIndex(1)
        options_layout.addWidget(self.llm_mode_combo, 1, 1, 1, 2)
        
        llm_layout.addLayout(options_layout)
        
        # 启用状态控制
        self.use_llm_cb.toggled.connect(self.on_llm_toggle)
        self.llm_strength_slider.setEnabled(False)
        self.llm_mode_combo.setEnabled(False)
        
        layout.addWidget(llm_group)
        
        # 翻译设置
        translate_group = QGroupBox("双语翻译")
        translate_layout = QVBoxLayout(translate_group)
        
        self.enable_translation_cb = QCheckBox("启用中英文双语提示词生成")
        self.enable_translation_cb.setChecked(True)  # 默认开启
        translate_layout.addWidget(self.enable_translation_cb)
        
        translate_info = QLabel("将增强后的提示词翻译为中英文对照格式，\n便于不同AI绘图工具使用。")
        translate_info.setStyleSheet("color: #666; font-size: 12px; padding: 10px;")
        translate_info.setWordWrap(True)
        translate_layout.addWidget(translate_info)
        
        layout.addWidget(translate_group)
        
        layout.addStretch()
        
        return widget
    
    def on_llm_toggle(self, enabled):
        """LLM优化开关切换"""
        self.llm_strength_slider.setEnabled(enabled)
        self.llm_mode_combo.setEnabled(enabled)
        self.on_config_changed()
    
    def create_preview_tab(self) -> QWidget:
        """创建预览选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 预览信息
        info_layout = QHBoxLayout()
        
        self.preview_status_label = QLabel("状态: 等待分镜数据")
        info_layout.addWidget(self.preview_status_label)
        
        info_layout.addStretch()
        
        self.update_preview_btn = QPushButton("更新预览")
        self.update_preview_btn.setEnabled(False)
        info_layout.addWidget(self.update_preview_btn)
        
        layout.addLayout(info_layout)
        
        # 预览内容
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("一致性预览信息将在这里显示...")
        
        layout.addWidget(self.preview_text)
        
        return widget
    
    def setup_connections(self):
        """设置信号连接"""
        # 配置变化信号
        self.enable_char_cb.toggled.connect(self.on_config_changed)
        self.enable_scene_cb.toggled.connect(self.on_config_changed)
        self.auto_extract_cb.toggled.connect(self.on_config_changed)
        self.use_llm_cb.toggled.connect(self.on_config_changed)
        self.enable_translation_cb.toggled.connect(self.on_config_changed)
        
        # 高级优化信号
        self.llm_strength_slider.valueChanged.connect(self.on_llm_strength_changed)
        self.llm_mode_combo.currentTextChanged.connect(self.on_config_changed)
        
        # 滑块变化信号
        self.consistency_strength_slider.valueChanged.connect(self.on_strength_changed)
        self.character_weight_slider.valueChanged.connect(self.on_char_weight_changed)
        self.scene_weight_slider.valueChanged.connect(self.on_scene_weight_changed)
        self.style_weight_slider.valueChanged.connect(self.on_style_weight_changed)
        
        # 角色管理信号
        self.add_character_btn.clicked.connect(self.add_character)
        self.edit_character_btn.clicked.connect(self.edit_character)
        self.delete_character_btn.clicked.connect(self.delete_character)
        self.refresh_character_btn.clicked.connect(self.refresh_characters)
        self.character_table.itemSelectionChanged.connect(self.on_character_selection_changed)
        
        # 场景管理信号
        self.add_scene_btn.clicked.connect(self.add_scene)
        self.edit_scene_btn.clicked.connect(self.edit_scene)
        self.delete_scene_btn.clicked.connect(self.delete_scene)
        self.refresh_scene_btn.clicked.connect(self.refresh_scenes)
        self.scene_table.itemSelectionChanged.connect(self.on_scene_selection_changed)
        
        # 按钮信号
        self.preview_btn.clicked.connect(self.request_preview)
        self.generate_btn.clicked.connect(self.request_generation)
        self.update_preview_btn.clicked.connect(self.update_preview)
        self.export_config_btn.clicked.connect(self.export_config)
        self.import_config_btn.clicked.connect(self.import_config)
    
    def on_config_changed(self):
        """配置变化处理"""
        self.update_config()
        self.config_changed.emit(self.current_config)
    
    def on_strength_changed(self, value):
        """一致性强度变化"""
        strength = value / 100.0
        self.consistency_strength_label.setText(f"{strength:.1f}")
        self.on_config_changed()
    
    def on_char_weight_changed(self, value):
        """角色权重变化"""
        weight = value / 100.0
        self.character_weight_label.setText(f"{weight:.1f}")
        self.on_config_changed()
    
    def on_scene_weight_changed(self, value):
        """场景权重变化"""
        weight = value / 100.0
        self.scene_weight_label.setText(f"{weight:.1f}")
        self.on_config_changed()
    
    def on_style_weight_changed(self, value):
        """风格权重变化"""
        weight = value / 100.0
        self.style_weight_label.setText(f"{weight:.1f}")
        self.on_config_changed()
    
    def on_llm_strength_changed(self, value):
        """LLM优化强度变化"""
        self.llm_strength_label.setText(str(value))
        self.on_config_changed()
    
    def update_config(self):
        """更新配置对象"""
        self.current_config = ConsistencyConfig(
            enable_character_consistency=self.enable_char_cb.isChecked(),
            enable_scene_consistency=self.enable_scene_cb.isChecked(),
            consistency_strength=self.consistency_strength_slider.value() / 100.0,
            auto_extract_new_elements=self.auto_extract_cb.isChecked(),
            use_llm_enhancement=False,  # LLM功能已移到高级优化
            character_weight=self.character_weight_slider.value() / 100.0,
            scene_weight=self.scene_weight_slider.value() / 100.0,
            style_weight=self.style_weight_slider.value() / 100.0
        )
    
    def set_storyboard(self, storyboard: StoryboardResult):
        """设置分镜数据"""
        self.current_storyboard = storyboard
        self.preview_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        self.update_preview_btn.setEnabled(True)
        
        self.preview_status_label.setText(f"状态: 已加载 {len(storyboard.shots)} 个分镜，点击'更新预览'按钮查看详细信息")
        
        # 自动提取并保存角色和场景数据到数据库
        self._extract_and_save_storyboard_data(storyboard)
        
        # 移除自动更新预览，改为用户手动点击按钮触发
        # self.update_preview()
    
    def update_button_states(self):
        """更新按钮状态"""
        try:
            # 检查是否有角色或场景数据
            has_character_data = False
            has_scene_data = False
            
            if self.cs_manager:
                characters = self.cs_manager.get_all_characters()
                scenes = self.cs_manager.get_all_scenes()
                has_character_data = len(characters) > 0
                has_scene_data = len(scenes) > 0
            
            # 如果有分镜数据或者有角色/场景数据，则启用按钮
            has_data = self.current_storyboard is not None or has_character_data or has_scene_data
            
            self.preview_btn.setEnabled(has_data)
            self.generate_btn.setEnabled(has_data)
            self.update_preview_btn.setEnabled(has_data)
            
            # 更新状态标签
            if self.current_storyboard:
                self.preview_status_label.setText(f"状态: 已加载 {len(self.current_storyboard.shots)} 个分镜")
            elif has_character_data or has_scene_data:
                char_count = len(self.cs_manager.get_all_characters()) if self.cs_manager else 0
                scene_count = len(self.cs_manager.get_all_scenes()) if self.cs_manager else 0
                self.preview_status_label.setText(f"状态: 已加载 {char_count} 个角色, {scene_count} 个场景")
            else:
                self.preview_status_label.setText("状态: 无数据")
                
        except Exception as e:
            logger.error(f"更新按钮状态失败: {e}")
    
    def load_character_scene_data(self):
        """加载角色场景数据"""
        import re  # 添加re模块导入
        try:
            # 检查cs_manager是否可用，如果不可用尝试重新初始化
            if not self.cs_manager:
                logger.warning("角色场景管理器未初始化，尝试重新初始化")
                self._try_reinit_cs_manager()
                
                # 如果仍然不可用，跳过数据加载
                if not self.cs_manager:
                    logger.warning("角色场景管理器重新初始化失败，跳过数据加载")
                    self.update_button_states()  # 仍然更新按钮状态
                    return
                
            # 加载角色数据
            characters = self.cs_manager.get_all_characters()
            self.character_table.setRowCount(len(characters))
            
            for row, (char_id, char_data) in enumerate(characters.items()):
                # 处理不同的数据格式
                name = char_data.get('name', '')
                description = char_data.get('description', '')
                
                # 处理外貌信息（可能是字符串或字典）
                appearance = char_data.get('appearance', '')
                if isinstance(appearance, dict):
                    # 如果是字典，提取主要信息
                    appearance_parts = []
                    for key, value in appearance.items():
                        if value and isinstance(value, str):
                            appearance_parts.append(f"{key}: {value}")
                    appearance = "; ".join(appearance_parts)
                elif not isinstance(appearance, str):
                    appearance = str(appearance)
                
                consistency_prompt = char_data.get('consistency_prompt', '')
                
                self.character_table.setItem(row, 0, QTableWidgetItem(name))
                self.character_table.setItem(row, 1, QTableWidgetItem(description))
                self.character_table.setItem(row, 2, QTableWidgetItem(appearance))
                self.character_table.setItem(row, 3, QTableWidgetItem(consistency_prompt))
                
                # 存储ID
                self.character_table.item(row, 0).setData(Qt.UserRole, char_id)
            
            # 加载场景数据
            all_scenes = self.cs_manager.get_all_scenes()
            
            # 直接使用所有场景数据（源头已过滤）
            filtered_scenes = all_scenes
            
            self.scene_table.setRowCount(len(filtered_scenes))
            
            # 对过滤后的场景进行自然排序
            def natural_sort_key(item):
                scene_id, scene_data = item
                scene_name = scene_data.get('name', '')
                # 提取场景名称中的数字进行排序
                numbers = re.findall(r'\d+', scene_name)
                if numbers:
                    return (0, int(numbers[0]), scene_name)  # 优先按数字排序
                else:
                    return (1, 0, scene_name)  # 非数字场景排在后面
            
            sorted_scenes = sorted(filtered_scenes.items(), key=natural_sort_key)
            
            for row, (scene_id, scene_data) in enumerate(sorted_scenes):
                name = scene_data.get('name', '')
                description = scene_data.get('description', '')
                
                # 处理环境信息（可能是字符串或字典）
                environment = scene_data.get('environment', '')
                if isinstance(environment, dict):
                    # 如果是字典，提取主要信息
                    env_parts = []
                    for key, value in environment.items():
                        if value and isinstance(value, (str, list)):
                            if isinstance(value, list):
                                value = ", ".join(str(v) for v in value)
                            env_parts.append(f"{key}: {value}")
                    environment = "; ".join(env_parts)
                elif not isinstance(environment, str):
                    environment = str(environment)
                
                # 处理光线信息（可能是字符串或字典）
                lighting = scene_data.get('lighting', '')
                if isinstance(lighting, dict):
                    lighting_parts = []
                    for key, value in lighting.items():
                        if value and isinstance(value, str):
                            lighting_parts.append(f"{key}: {value}")
                    lighting = "; ".join(lighting_parts)
                elif not isinstance(lighting, str):
                    lighting = str(lighting)
                
                consistency_prompt = scene_data.get('consistency_prompt', '')
                
                self.scene_table.setItem(row, 0, QTableWidgetItem(name))
                self.scene_table.setItem(row, 1, QTableWidgetItem(description))
                self.scene_table.setItem(row, 2, QTableWidgetItem(environment))
                self.scene_table.setItem(row, 3, QTableWidgetItem(lighting))
                self.scene_table.setItem(row, 4, QTableWidgetItem(consistency_prompt))
                
                # 存储ID
                self.scene_table.item(row, 0).setData(Qt.UserRole, scene_id)
            
            logger.info(f"加载了 {len(characters)} 个角色和 {len(filtered_scenes)} 个用户创建的场景（已过滤分镜生成的场景）")
            
            # 更新按钮状态
            self.update_button_states()
        except Exception as e:
            logger.error(f"加载角色场景数据失败: {e}")
    
    def _read_generated_text_from_file(self):
        """从项目texts文件夹中读取generate_text文件内容"""
        try:
            if not hasattr(self, 'project_manager') or not self.project_manager:
                return None
                
            project_name = self.project_manager.get_current_project_name()
            if not project_name:
                return None
                
            # 构建generate_text文件路径
            texts_dir = os.path.join("output", project_name, "texts")
            generate_text_file = os.path.join(texts_dir, "generate_text.json")
            
            if not os.path.exists(generate_text_file):
                logger.debug(f"generate_text文件不存在: {generate_text_file}")
                return None
                
            # 读取文件内容
            with open(generate_text_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 获取最新的增强内容
            if 'enhanced_content' in data:
                logger.info(f"成功读取场景增强器生成的内容: {len(data['enhanced_content'])}字符")
                return data['enhanced_content']
            elif 'original' in data:
                logger.info(f"使用原始内容作为备选: {len(data['original'])}字符")
                return data['original']
            else:
                logger.warning("generate_text文件格式不正确")
                return None
                
        except Exception as e:
            logger.error(f"读取generate_text文件失败: {e}")
            return None
    
    def _generate_simple_bilingual_prompt(self, description):
        """生成简单的双语提示词（中文原文 + 英文翻译）"""
        try:
            # 如果有翻译API，使用翻译API
            if hasattr(self, 'llm_api') and self.llm_api and self.llm_api.is_configured():
                try:
                    # 使用LLM进行翻译
                    translation_prompt = f"请将以下中文提示词翻译成英文，保持专业性和准确性：\n{description}"
                    response = self.llm_api.rewrite_text(translation_prompt)
                    if response and len(response.strip()) > 0:
                        return (description, response.strip())
                except Exception as e:
                    logger.warning(f"LLM翻译失败: {e}")
            
            # 简单的关键词翻译映射
            translation_map = {
                '男性': 'male', '女性': 'female', '男人': 'man', '女人': 'woman',
                '室内': 'indoor', '室外': 'outdoor', '白天': 'daytime', '夜晚': 'night',
                '阳光': 'sunlight', '月光': 'moonlight', '灯光': 'lighting',
                '特写': 'close-up', '中景': 'medium shot', '远景': 'long shot',
                '正面': 'front view', '侧面': 'side view', '背面': 'back view',
                '微笑': 'smile', '严肃': 'serious', '愤怒': 'angry', '悲伤': 'sad',
                '现代': 'modern', '古典': 'classical', '科幻': 'sci-fi', '奇幻': 'fantasy'
            }
            
            # 简单替换翻译
            english_desc = description
            for cn, en in translation_map.items():
                english_desc = english_desc.replace(cn, en)
            
            return (description, english_desc)
            
        except Exception as e:
            logger.warning(f"生成简单双语提示词失败: {e}")
            return (description, description)
            
            # 尝试加载保存的预览数据
            self._load_preview_data()
            
        except Exception as e:
            logger.error(f"加载角色场景数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.warning(self, "错误", f"加载数据失败: {e}")
            # 即使出错也要更新按钮状态
            self.update_button_states()
    
    def on_character_selection_changed(self):
        """角色选择变化"""
        has_selection = len(self.character_table.selectedItems()) > 0
        self.edit_character_btn.setEnabled(has_selection)
        self.delete_character_btn.setEnabled(has_selection)
    
    def on_scene_selection_changed(self):
        """场景选择变化"""
        has_selection = len(self.scene_table.selectedItems()) > 0
        self.edit_scene_btn.setEnabled(has_selection)
        self.delete_scene_btn.setEnabled(has_selection)
    
    def add_character(self):
        """添加角色"""
        editor = CharacterEditor(parent=self)
        if editor.exec_() == QDialog.Accepted:
            char_data = editor.get_data()
            if char_data['name']:
                try:
                    char_id = self.cs_manager.save_character(char_data)
                    self.load_character_scene_data()
                    logger.info(f"添加角色成功: {char_data['name']}")
                except Exception as e:
                    logger.error(f"添加角色失败: {e}")
                    QMessageBox.warning(self, "错误", f"添加角色失败: {e}")
    
    def edit_character(self):
        """编辑角色"""
        current_row = self.character_table.currentRow()
        if current_row >= 0:
            char_id = self.character_table.item(current_row, 0).data(Qt.UserRole)
            char_data = self.cs_manager.get_character(char_id)
            
            if char_data:
                editor = CharacterEditor(char_data, parent=self)
                if editor.exec_() == QDialog.Accepted:
                    updated_data = editor.get_data()
                    try:
                        self.cs_manager.save_character(updated_data, char_id)
                        self.load_character_scene_data()
                        logger.info(f"编辑角色成功: {updated_data['name']}")
                    except Exception as e:
                        logger.error(f"编辑角色失败: {e}")
                        QMessageBox.warning(self, "错误", f"编辑角色失败: {e}")
    
    def delete_character(self):
        """删除角色"""
        current_row = self.character_table.currentRow()
        if current_row >= 0:
            char_name = self.character_table.item(current_row, 0).text()
            char_id = self.character_table.item(current_row, 0).data(Qt.UserRole)
            
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除角色 '{char_name}' 吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    self.cs_manager.delete_character(char_id)
                    self.load_character_scene_data()
                    logger.info(f"删除角色成功: {char_name}")
                except Exception as e:
                    logger.error(f"删除角色失败: {e}")
                    QMessageBox.warning(self, "错误", f"删除角色失败: {e}")
    
    def add_scene(self):
        """添加场景"""
        editor = SceneEditor(parent=self)
        if editor.exec_() == QDialog.Accepted:
            scene_data = editor.get_data()
            if scene_data['name']:
                try:
                    scene_id = self.cs_manager.save_scene(scene_data)
                    self.load_character_scene_data()
                    logger.info(f"添加场景成功: {scene_data['name']}")
                except Exception as e:
                    logger.error(f"添加场景失败: {e}")
                    QMessageBox.warning(self, "错误", f"添加场景失败: {e}")
    
    def edit_scene(self):
        """编辑场景"""
        current_row = self.scene_table.currentRow()
        if current_row >= 0:
            scene_id = self.scene_table.item(current_row, 0).data(Qt.UserRole)
            scene_data = self.cs_manager.get_scene(scene_id)
            
            if scene_data:
                editor = SceneEditor(scene_data, parent=self)
                if editor.exec_() == QDialog.Accepted:
                    updated_data = editor.get_data()
                    try:
                        self.cs_manager.save_scene(updated_data, scene_id)
                        self.load_character_scene_data()
                        logger.info(f"编辑场景成功: {updated_data['name']}")
                    except Exception as e:
                        logger.error(f"编辑场景失败: {e}")
                        QMessageBox.warning(self, "错误", f"编辑场景失败: {e}")
    
    def delete_scene(self):
        """删除场景"""
        current_row = self.scene_table.currentRow()
        if current_row >= 0:
            scene_name = self.scene_table.item(current_row, 0).text()
            scene_id = self.scene_table.item(current_row, 0).data(Qt.UserRole)
            
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除场景 '{scene_name}' 吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    self.cs_manager.delete_scene(scene_id)
                    self.load_character_scene_data()
                    logger.info(f"删除场景成功: {scene_name}")
                except Exception as e:
                    logger.error(f"删除场景失败: {e}")
                    QMessageBox.warning(self, "错误", f"删除场景失败: {e}")
    
    def update_preview(self):
        """更新预览"""
        if not self.current_storyboard:
            return
        
        try:
            # 获取数据库中的角色和场景信息
            db_characters = []
            db_scenes = []
            
            if self.cs_manager:
                try:
                    all_characters = self.cs_manager.get_all_characters()
                    db_characters = [char_data.get('name', '') for char_data in all_characters.values() if char_data.get('name')]
                    
                    all_scenes = self.cs_manager.get_all_scenes()
                    db_scenes = [scene_data.get('name', '') for scene_data in all_scenes.values() if scene_data.get('name')]
                except Exception as e:
                    logger.warning(f"获取数据库角色场景信息失败: {e}")
            
            # 合并分镜中的角色和数据库中的角色
            storyboard_characters = list(set(self.current_storyboard.characters))
            all_characters_list = list(set(storyboard_characters + db_characters))
            
            # 合并分镜中的场景和数据库中的场景
            storyboard_scenes = list(set(self.current_storyboard.scenes))
            all_scenes_list = list(set(storyboard_scenes + db_scenes))
            
            # 生成详细的预览信息
            preview_text = "=== 一致性预览 ===\n\n"
            
            preview_text += f"分镜总数: {len(self.current_storyboard.shots)}\n"
            preview_text += f"角色数量: {len(all_characters_list)}\n"
            preview_text += f"场景数量: {len(all_scenes_list)}\n\n"
            
            preview_text += "=== 配置信息 ===\n"
            preview_text += f"角色一致性: {'启用' if self.current_config.enable_character_consistency else '禁用'}\n"
            preview_text += f"场景一致性: {'启用' if self.current_config.enable_scene_consistency else '禁用'}\n"
            preview_text += f"一致性强度: {self.current_config.consistency_strength:.1f}\n"
            preview_text += f"LLM增强: {'启用' if self.current_config.use_llm_enhancement else '禁用'}\n\n"
            
            # 显示角色信息
            if all_characters_list:
                preview_text += "=== 角色信息 ===\n"
                for char_name in sorted(all_characters_list):
                    preview_text += f"• {char_name}\n"
                preview_text += "\n"
            
            # 显示场景信息
            if all_scenes_list:
                preview_text += "=== 场景信息 ===\n"
                for scene_name in sorted(all_scenes_list):
                    preview_text += f"• {scene_name}\n"
                preview_text += "\n"
            
            preview_text += "=== 分镜预览 ===\n"
            
            # 尝试从五阶段分镜获取详细数据
            detailed_storyboard_data = self._get_five_stage_storyboard_data()
            
            if detailed_storyboard_data:
                # 显示详细的五阶段分镜数据
                preview_text += "（以下调用五阶段分镜中的第四阶段分镜生成的信息）\n"
                
                for i, scene_data in enumerate(detailed_storyboard_data):
                    scene_info = scene_data.get("scene_info", "")
                    storyboard_script = scene_data.get("storyboard_script", "")
                    
                    preview_text += f"\n{'='*50}\n"
                    preview_text += f"场景 {i+1}\n"
                    preview_text += f"{'='*50}\n"
                    preview_text += f"场景信息: {scene_info}\n\n"
                    
                    # 解析分镜脚本中的镜头信息
                    if storyboard_script:
                        preview_text += "## 场景分镜脚本\n\n"
                        
                        # 先提取镜头信息用于生成双语提示词
                        shots_with_prompts = self._extract_shots_from_script(storyboard_script, scene_info)
                        shot_bilingual_prompts = {}
                        
                        # 生成双语提示词
                        total_shots = len(shots_with_prompts)
                        for idx, (shot_num, shot_description) in enumerate(shots_with_prompts, 1):
                            try:
                                # 更新进度状态显示
                                self.preview_status_label.setText(f"状态: 正在生成镜头{shot_num}双语提示词... ({idx}/{total_shots})")
                                QApplication.processEvents()  # 允许UI更新
                                
                                # 构建整合后的画面描述
                                enhanced_description = self._build_enhanced_description_for_scene(
                                    shot_description, scene_info, all_characters_list, all_scenes_list
                                )
                                
                                # 检查是否启用翻译功能
                                if hasattr(self, 'enable_translation_cb') and self.enable_translation_cb.isChecked():
                                    # 生成双语提示词
                                    try:
                                        # 首先尝试从generate_text文件读取增强器生成的内容
                                        generated_content = self._read_generated_text_from_file()
                                        
                                        if generated_content:
                                            logger.info(f"镜头{shot_num}使用场景增强器生成的优化提示词")
                                            # 使用生成的内容进行翻译
                                            if hasattr(self, 'llm_enable_cb') and self.llm_enable_cb.isChecked() and self.llm_api and self.llm_api.is_configured():
                                                # 使用LLM翻译生成的内容
                                                translation_prompt = f"请将以下中文提示词翻译成英文，保持专业性和准确性：\n{generated_content}"
                                                english_translation = self.llm_api.rewrite_text(translation_prompt)
                                                if english_translation and len(english_translation.strip()) > 10:
                                                    shot_bilingual_prompts[shot_num] = (generated_content, english_translation.strip())
                                                    logger.info(f"镜头{shot_num}使用场景增强器内容的LLM翻译完成")
                                                else:
                                                    # LLM翻译失败，使用简单翻译
                                                    shot_bilingual_prompts[shot_num] = self._generate_simple_bilingual_prompt(generated_content)
                                            else:
                                                # 使用简单翻译
                                                shot_bilingual_prompts[shot_num] = self._generate_simple_bilingual_prompt(generated_content)
                                        else:
                                            # 没有生成的内容，使用原有逻辑
                                            if hasattr(self, 'llm_enable_cb') and self.llm_enable_cb.isChecked() and self.llm_api and self.llm_api.is_configured():
                                                logger.info(f"开始为镜头{shot_num}生成LLM优化提示词")
                                                optimized_cn, optimized_en = self.prompt_optimizer._generate_ai_optimized_prompt(enhanced_description)
                                                
                                                # 检查生成质量
                                                if optimized_cn and optimized_en and len(optimized_cn.strip()) > 10 and len(optimized_en.strip()) > 10:
                                                    shot_bilingual_prompts[shot_num] = (optimized_cn, optimized_en)
                                                    logger.info(f"镜头{shot_num}LLM优化提示词生成成功")
                                                else:
                                                    # 回退到简单翻译
                                                    shot_bilingual_prompts[shot_num] = self._generate_simple_bilingual_prompt(enhanced_description)
                                            else:
                                                # 使用简单的双语生成
                                                shot_bilingual_prompts[shot_num] = self._generate_simple_bilingual_prompt(enhanced_description)
                                            
                                    except Exception as inner_e:
                                        logger.warning(f"镜头{shot_num}双语提示词生成失败: {inner_e}")
                                        shot_bilingual_prompts[shot_num] = self._generate_simple_bilingual_prompt(enhanced_description)
                                else:
                                    # 不启用翻译，只显示原始描述
                                    shot_bilingual_prompts[shot_num] = (enhanced_description, enhanced_description)
                                
                            except Exception as e:
                                logger.warning(f"生成镜头{shot_num}提示词失败: {e}")
                                shot_bilingual_prompts[shot_num] = (shot_description, shot_description)
                                
                            # 每处理一个镜头后更新UI
                            QApplication.processEvents()
                        
                        # 完成所有双语提示词生成
                        self.preview_status_label.setText(f"状态: 双语提示词生成完成，共处理{total_shots}个镜头")
                        QApplication.processEvents()
                        
                        # 逐行处理分镜脚本，在AI绘图提示词后插入双语提示词
                        enhanced_script = self._insert_bilingual_prompts_into_script(storyboard_script, shot_bilingual_prompts)
                        preview_text += enhanced_script
                        preview_text += "\n"
                    
                    preview_text += "\n"
            else:
                # 回退到原有的简化显示
                for i, shot in enumerate(self.current_storyboard.shots[:5]):  # 只显示前5个
                    preview_text += f"\n分镜 {shot.shot_id}:\n"
                    preview_text += f"场景: {shot.scene}\n"
                    preview_text += f"角色: {', '.join(shot.characters) if shot.characters else '无'}\n"
                    
                    # 显示完整的原始提示词
                    preview_text += f"原始提示词: {shot.image_prompt}\n"
                    
                    # 生成优化后的提示词（中英文对照）
                    try:
                        optimized_prompt_cn, optimized_prompt_en = self._generate_optimized_prompt(shot, all_characters_list, all_scenes_list)
                        preview_text += f"优化后提示词(中文): {optimized_prompt_cn}\n"
                        preview_text += f"优化后提示词(英文): {optimized_prompt_en}\n"
                    except Exception as e:
                        logger.warning(f"生成优化提示词失败: {e}")
                        preview_text += "优化后提示词: 生成失败\n"
                    
                    preview_text += "-" * 50 + "\n"
                
                if len(self.current_storyboard.shots) > 5:
                    preview_text += f"\n... 还有 {len(self.current_storyboard.shots) - 5} 个分镜\n"
            
            self.preview_text.setPlainText(preview_text)
            self.preview_status_label.setText("状态: 预览已更新")
            
            # 保存预览数据到项目
            self._save_preview_data(preview_text)
            
        except Exception as e:
            logger.error(f"更新预览失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.preview_text.setPlainText(f"预览生成失败: {e}")
    
    def _save_preview_data(self, preview_text):
        """保存预览数据到项目"""
        try:
            if hasattr(self.parent_window, 'project_manager') and self.parent_window.project_manager.current_project:
                # 获取项目管理器
                project_manager = self.parent_window.project_manager
                
                # 保存预览数据到项目配置中
                if 'consistency_preview' not in project_manager.current_project:
                    project_manager.current_project['consistency_preview'] = {}
                
                project_manager.current_project['consistency_preview'] = {
                    'preview_text': preview_text,
                    'last_updated': datetime.now().isoformat(),
                    'config': {
                        'enable_character_consistency': self.current_config.enable_character_consistency,
                        'enable_scene_consistency': self.current_config.enable_scene_consistency,
                        'consistency_strength': self.current_config.consistency_strength
                    }
                }
                
                # 保存项目
                project_manager.save_project()
                logger.info("一致性预览数据已保存到项目")
                
        except Exception as e:
            logger.error(f"保存预览数据失败: {e}")
    
    def _load_preview_data(self):
        """从项目加载预览数据"""
        try:
            if hasattr(self.parent_window, 'project_manager') and self.parent_window.project_manager.current_project:
                project_config = self.parent_window.project_manager.current_project
                
                # 检查是否有保存的预览数据
                if 'consistency_preview' in project_config:
                    preview_data = project_config['consistency_preview']
                    preview_text = preview_data.get('preview_text', '')
                    
                    if preview_text:
                        self.preview_text.setPlainText(preview_text)
                        last_updated = preview_data.get('last_updated', '')
                        if last_updated:
                            try:
                                update_time = datetime.fromisoformat(last_updated)
                                time_str = update_time.strftime('%Y-%m-%d %H:%M:%S')
                                self.preview_status_label.setText(f"状态: 已加载上次预览 (更新于 {time_str})")
                            except:
                                self.preview_status_label.setText("状态: 已加载上次预览")
                        else:
                            self.preview_status_label.setText("状态: 已加载上次预览")
                        
                        logger.info("一致性预览数据已从项目加载")
                        return True
                        
        except Exception as e:
            logger.error(f"加载预览数据失败: {e}")
        
        return False
    
    def _get_five_stage_storyboard_data(self):
        """获取五阶段分镜的详细数据"""
        try:
            # 检查主窗口是否有五阶段分镜标签页
            if not hasattr(self.parent_window, 'five_stage_storyboard_tab'):
                logger.debug("主窗口没有五阶段分镜标签页")
                return None
            
            five_stage_tab = self.parent_window.five_stage_storyboard_tab
            
            # 检查是否有第四阶段的数据
            if not hasattr(five_stage_tab, 'stage_data') or not five_stage_tab.stage_data.get(4):
                logger.debug("五阶段分镜没有第四阶段数据")
                return None
            
            # 获取第四阶段的分镜结果
            stage4_data = five_stage_tab.stage_data[4]
            storyboard_results = stage4_data.get('storyboard_results', [])
            
            if not storyboard_results:
                logger.debug("第四阶段没有分镜结果数据")
                return None
            
            logger.info(f"成功获取到 {len(storyboard_results)} 个场景的详细分镜数据")
            return storyboard_results
            
        except Exception as e:
            logger.error(f"获取五阶段分镜数据失败: {e}")
            return None
    
    def _generate_optimized_prompt(self, shot, all_characters, all_scenes):
        """生成优化后的提示词（中英文对照）"""
        try:
            # 使用PromptOptimizer生成优化的提示词
            optimized_cn, optimized_en = self.prompt_optimizer.generate_optimized_prompt(
                shot, all_characters, all_scenes, self.cs_manager
            )
            return optimized_cn, optimized_en
            
        except Exception as e:
            logger.error(f"生成优化提示词失败: {e}")
            return shot.image_prompt, shot.image_prompt
    

    
    def _extract_shots_from_script(self, storyboard_script, scene_info):
        """从分镜脚本中提取镜头信息"""
        try:
            shots_with_prompts = []
            lines = storyboard_script.split('\n')
            current_shot = None
            current_description = ""
            
            for line in lines:
                line = line.strip()
                
                # 检测镜头标题
                if line.startswith('### 镜头') or line.startswith('##镜头') or '镜头' in line and line.endswith('###'):
                    # 保存上一个镜头的信息
                    if current_shot and current_description:
                        shots_with_prompts.append((current_shot, current_description.strip()))
                    
                    # 提取镜头编号
                    import re
                    shot_match = re.search(r'镜头(\d+)', line)
                    if shot_match:
                        current_shot = shot_match.group(1)
                        current_description = ""
                
                # 检测画面描述
                elif line.startswith('- **画面描述**：') or line.startswith('**画面描述**：'):
                    current_description = line.replace('- **画面描述**：', '').replace('**画面描述**：', '').strip()
                elif line.startswith('- **画面描述**:') or line.startswith('**画面描述**:'):
                    current_description = line.replace('- **画面描述**:', '').replace('**画面描述**:', '').strip()
            
            # 保存最后一个镜头的信息
            if current_shot and current_description:
                shots_with_prompts.append((current_shot, current_description.strip()))
            
            logger.info(f"从分镜脚本中提取到 {len(shots_with_prompts)} 个镜头")
            return shots_with_prompts
            
        except Exception as e:
            logger.error(f"提取镜头信息失败: {e}")
            return []
    
    def _build_enhanced_description_for_scene(self, shot_description, scene_info, all_characters, all_scenes):
        """为场景构建增强的画面描述"""
        try:
            # 使用PromptOptimizer构建增强描述
            character_details = self.prompt_optimizer._get_character_details(all_characters)
            
            # 处理scene_info可能是字符串或字典的情况
            if isinstance(scene_info, dict):
                scene_name = scene_info.get('name', '')
            elif isinstance(scene_info, str):
                scene_name = scene_info
            else:
                scene_name = ''
                
            scene_details = self.prompt_optimizer._get_scene_details(all_scenes, scene_name)
            
            enhanced_description = self.prompt_optimizer._build_enhanced_description(
                shot_description, character_details, scene_details
            )
            
            return enhanced_description
            
        except Exception as e:
            logger.error(f"构建场景增强描述失败: {e}")
            return shot_description
    
    def _insert_bilingual_prompts_into_script(self, storyboard_script, shot_bilingual_prompts):
        """在分镜脚本中的AI绘图提示词后插入双语提示词"""
        try:
            lines = storyboard_script.split('\n')
            enhanced_lines = []
            current_shot = None
            
            for line in lines:
                enhanced_lines.append(line)
                
                # 检测镜头标题
                if line.strip().startswith('### 镜头') or line.strip().startswith('##镜头') or ('镜头' in line and line.strip().endswith('###')):
                    import re
                    shot_match = re.search(r'镜头(\d+)', line)
                    if shot_match:
                        current_shot = shot_match.group(1)
                
                # 检测AI绘图提示词行，在其后插入双语提示词
                elif line.strip().startswith('- **AI绘图提示词**：') or line.strip().startswith('**AI绘图提示词**：'):
                    if current_shot and current_shot in shot_bilingual_prompts:
                        prompt_cn, prompt_en = shot_bilingual_prompts[current_shot]
                        # 只有在启用翻译且中英文不同时才显示双语
                        if hasattr(self, 'enable_translation_cb') and self.enable_translation_cb.isChecked() and prompt_cn != prompt_en:
                            enhanced_lines.append(f"- **双语提示词(中文)**：{prompt_cn}")
                            enhanced_lines.append(f"- **双语提示词(英文)**：{prompt_en}")
                        elif prompt_cn != line.split('：', 1)[-1] if '：' in line else True:
                            enhanced_lines.append(f"- **增强提示词**：{prompt_cn}")
                elif line.strip().startswith('- **AI绘图提示词**:') or line.strip().startswith('**AI绘图提示词**:'):
                    if current_shot and current_shot in shot_bilingual_prompts:
                        prompt_cn, prompt_en = shot_bilingual_prompts[current_shot]
                        # 只有在启用翻译且中英文不同时才显示双语
                        if hasattr(self, 'enable_translation_cb') and self.enable_translation_cb.isChecked() and prompt_cn != prompt_en:
                            enhanced_lines.append(f"- **双语提示词(中文)**：{prompt_cn}")
                            enhanced_lines.append(f"- **双语提示词(英文)**：{prompt_en}")
                        elif prompt_cn != line.split(':', 1)[-1] if ':' in line else True:
                            enhanced_lines.append(f"- **增强提示词**：{prompt_cn}")
            
            return '\n'.join(enhanced_lines)
            
        except Exception as e:
            logger.error(f"插入双语提示词失败: {e}")
            return storyboard_script  # 返回原始脚本
    
    def request_preview(self):
        """请求预览"""
        if self.current_storyboard:
            self.preview_requested.emit()
        else:
            # 如果没有分镜数据但有角色/场景数据，也可以生成预览
            if self.cs_manager:
                characters = self.cs_manager.get_all_characters()
                scenes = self.cs_manager.get_all_scenes()
                if len(characters) > 0 or len(scenes) > 0:
                    self.preview_requested.emit()
                else:
                    QMessageBox.information(self, "提示", "请先加载分镜数据或添加角色/场景数据")
            else:
                QMessageBox.information(self, "提示", "请先加载分镜数据或添加角色/场景数据")
    
    def request_generation(self):
        """请求生成"""
        if self.current_storyboard:
            self.generate_requested.emit(self.current_storyboard, self.current_config)
        else:
            # 如果没有分镜数据但有角色/场景数据，提示用户
            if self.cs_manager:
                characters = self.cs_manager.get_all_characters()
                scenes = self.cs_manager.get_all_scenes()
                if len(characters) > 0 or len(scenes) > 0:
                    QMessageBox.information(self, "提示", "当前只有角色/场景数据，没有分镜数据。\n请先在五阶段分镜中生成分镜，或直接使用角色/场景数据进行图像生成。")
                else:
                    QMessageBox.information(self, "提示", "请先加载分镜数据或添加角色/场景数据")
            else:
                QMessageBox.information(self, "提示", "请先加载分镜数据或添加角色/场景数据")
    
    def export_config(self):
        """导出配置"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出一致性配置", "", "JSON文件 (*.json)"
            )
            
            if file_path:
                config_data = {
                    'consistency_config': {
                        'enable_character_consistency': self.current_config.enable_character_consistency,
                        'enable_scene_consistency': self.current_config.enable_scene_consistency,
                        'consistency_strength': self.current_config.consistency_strength,
                        'auto_extract_new_elements': self.current_config.auto_extract_new_elements,
                        'use_llm_enhancement': self.current_config.use_llm_enhancement,
                        'character_weight': self.current_config.character_weight,
                        'scene_weight': self.current_config.scene_weight,
                        'style_weight': self.current_config.style_weight
                    }
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, "成功", "配置导出成功！")
                logger.info(f"配置导出到: {file_path}")
                
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            QMessageBox.warning(self, "错误", f"导出配置失败: {e}")
    
    def import_config(self):
        """导入配置"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "导入一致性配置", "", "JSON文件 (*.json)"
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                if 'consistency_config' in config_data:
                    config = config_data['consistency_config']
                    
                    # 更新UI控件
                    self.enable_char_cb.setChecked(config.get('enable_character_consistency', True))
                    self.enable_scene_cb.setChecked(config.get('enable_scene_consistency', True))
                    self.auto_extract_cb.setChecked(config.get('auto_extract_new_elements', True))
                    # use_llm_enhancement已移到高级优化功能中
                    
                    self.consistency_strength_slider.setValue(int(config.get('consistency_strength', 0.7) * 100))
                    self.character_weight_slider.setValue(int(config.get('character_weight', 0.4) * 100))
                    self.scene_weight_slider.setValue(int(config.get('scene_weight', 0.3) * 100))
                    self.style_weight_slider.setValue(int(config.get('style_weight', 0.3) * 100))
                    
                    # 更新配置对象
                    self.update_config()
                    
                    QMessageBox.information(self, "成功", "配置导入成功！")
                    logger.info(f"配置从 {file_path} 导入成功")
                else:
                    QMessageBox.warning(self, "错误", "配置文件格式不正确")
                
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            QMessageBox.warning(self, "错误", f"导入配置失败: {e}")
    
    def _extract_and_save_storyboard_data(self, storyboard: StoryboardResult):
        """从分镜数据中提取并保存角色和场景信息"""
        try:
            if not self.cs_manager:
                logger.warning("角色场景管理器未初始化，尝试重新初始化")
                self._try_reinit_cs_manager()
                
                if not self.cs_manager:
                    logger.warning("无法初始化角色场景管理器，跳过数据保存")
                    return
            
            # 提取并保存角色数据
            characters_saved = 0
            for character_name in storyboard.characters:
                if character_name and character_name.strip():
                    character_name = character_name.strip()
                    
                    # 检查角色是否已存在
                    existing_characters = self.cs_manager.get_all_characters()
                    char_exists = any(data.get('name') == char_name for data in existing_characters.values())

                    if not char_exists:
                        # 创建角色数据
                        character_data = {
                            'name': char_name,
                            'description': f'从分镜中提取的角色: {char_name}',
                            'appearance': {
                                'gender': '', 'age_range': '', 'hair': '', 'eyes': '', 'skin': '', 'build': ''
                            },
                            'clothing': {
                                'style': '', 'colors': [], 'accessories': []
                            },
                            'personality': {
                                'traits': [], 'expressions': [], 'mannerisms': []
                            },
                            'consistency_prompt': f'{char_name}, 保持角色一致性',
                            'source': 'storyboard_extraction'
                        }
                        
                        # 生成唯一ID
                        char_id = f"分镜角色_{char_name}" # 简化ID，如果需要更强的唯一性，可以考虑其他策略

                        if self.current_config.use_llm_enhancement and self.current_config.auto_extract_new_elements:
                            if self.cs_manager and hasattr(self.cs_manager, '_extract_characters_with_llm'):
                                try:
                                    llm_input_text = f"角色名称: {char_name}. 现有描述: {character_data.get('description', '')}"
                                    enhanced_characters_list = self.cs_manager._extract_characters_with_llm(llm_input_text)
                                    
                                    if enhanced_characters_list and isinstance(enhanced_characters_list, list) and len(enhanced_characters_list) > 0:
                                        enhanced_data_from_llm = enhanced_characters_list[0]
                                        
                                        original_name = character_data['name']
                                        original_source = character_data['source']
                                        
                                        character_data.update(enhanced_data_from_llm)
                                        
                                        character_data['name'] = original_name
                                        character_data['source'] = original_source
                                        if not character_data.get('consistency_prompt') or not character_data['consistency_prompt'].strip():
                                            character_data['consistency_prompt'] = f'{char_name}, 保持角色一致性'
                                            
                                        logger.info(f"LLM增强角色数据: {char_name}")
                                    else:
                                        logger.info(f"LLM未对角色 {char_name} 提供增强信息或返回格式不符.")
                                except Exception as e:
                                    logger.error(f"LLM增强角色 {char_name} 失败: {e}")
                            else:
                                logger.warning(f"LLM增强角色 {char_name} 跳过: cs_manager 或 _extract_characters_with_llm 方法不可用.")
                        
                        # 保存角色
                        self.cs_manager.save_character(char_id, character_data)
                        characters_saved += 1
                        logger.info(f"保存新角色: {char_name}")
            
            # 提取并保存场景数据
            scenes_saved = 0
            for scene_name in storyboard.scenes:
                if scene_name and scene_name.strip():
                    scene_name = scene_name.strip()
                    
                    # 检查场景是否已存在
                    existing_scenes = self.cs_manager.get_all_scenes()
                    scene_exists = any(data.get('name') == scene_name for data in existing_scenes.values())

                    if not scene_exists:
                        # 创建场景数据
                        scene_data = {
                            'name': scene_name,
                            'description': f'从分镜中提取的场景: {scene_name}',
                            'environment': {
                                'location_type': '',
                                'setting': '',
                                'props': [],
                                'atmosphere': ''
                            },
                            'lighting': {
                                'time_of_day': '',
                                'weather': '',
                                'light_source': '',
                                'mood': ''
                            },
                            'consistency_prompt': f'{scene_name}, 保持场景一致性',
                            'source': 'storyboard_extraction'
                        }
                        
                        # 生成唯一ID
                        scene_id = f"分镜场景_{scene_name}" # 简化ID

                        if self.current_config.use_llm_enhancement and self.current_config.auto_extract_new_elements:
                            if self.cs_manager and hasattr(self.cs_manager, '_extract_scenes_with_llm'):
                                # 增强LLM场景解析，添加重试机制
                                max_retries = 2
                                retry_count = 0
                                llm_success = False
                                
                                while retry_count < max_retries and not llm_success:
                                    try:
                                        # 构建更详细的LLM输入文本
                                        llm_input_text = f"""请分析以下场景信息并提供详细描述：
场景名称: {scene_name}
现有描述: {scene_data.get('description', '')}

请提供场景的环境、光线、氛围等详细信息，并生成适合AI绘画的一致性提示词。"""
                                        
                                        enhanced_scenes_list = self.cs_manager._extract_scenes_with_llm(llm_input_text)
                                        
                                        if enhanced_scenes_list and isinstance(enhanced_scenes_list, list) and len(enhanced_scenes_list) > 0:
                                            enhanced_data_from_llm = enhanced_scenes_list[0]
                                            
                                            # 验证LLM返回的数据质量
                                            if isinstance(enhanced_data_from_llm, dict) and enhanced_data_from_llm.get('name'):
                                                original_name = scene_data['name']
                                                original_source = scene_data['source']
                                                
                                                scene_data.update(enhanced_data_from_llm)
                                                
                                                scene_data['name'] = original_name 
                                                scene_data['source'] = original_source
                                                if not scene_data.get('consistency_prompt') or not scene_data['consistency_prompt'].strip():
                                                    scene_data['consistency_prompt'] = f'{scene_name}, 保持场景一致性'
                                                    
                                                logger.info(f"LLM增强场景数据成功: {scene_name}")
                                                llm_success = True
                                            else:
                                                logger.warning(f"LLM返回的场景数据格式不正确: {scene_name}, 重试中...")
                                                retry_count += 1
                                        else:
                                            logger.warning(f"LLM未对场景 {scene_name} 提供有效增强信息, 重试中...")
                                            retry_count += 1
                                    except Exception as e:
                                        logger.error(f"LLM增强场景 {scene_name} 失败 (尝试 {retry_count + 1}/{max_retries}): {e}")
                                        retry_count += 1
                                        import traceback
                                        logger.debug(f"详细错误信息: {traceback.format_exc()}")
                                
                                if not llm_success:
                                    logger.warning(f"场景 {scene_name} 的LLM增强在 {max_retries} 次尝试后仍然失败，将使用基础数据")
                            else:
                                logger.warning(f"LLM增强场景 {scene_name} 跳过: cs_manager 或 _extract_scenes_with_llm 方法不可用.")
                        
                        # 保存场景
                        self.cs_manager.save_scene(scene_id, scene_data)
                        scenes_saved += 1
                        logger.info(f"保存新场景: {scene_name}")
            
            if characters_saved > 0 or scenes_saved > 0:
                logger.info(f"从分镜数据中提取并保存了 {characters_saved} 个角色和 {scenes_saved} 个场景")
                # 重新加载数据到表格
                self.load_character_scene_data()
            else:
                logger.info("分镜数据中的角色和场景都已存在，无需重复保存")
                
        except Exception as e:
            logger.error(f"提取和保存分镜数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _try_reinit_cs_manager(self):
        """尝试重新初始化角色场景管理器"""
        try:
            # 检查是否有项目管理器和当前项目
            if not self.project_manager or not self.project_manager.current_project:
                logger.warning("没有当前项目，无法初始化角色场景管理器")
                return
            
            # 获取项目目录
            project_dir = self.project_manager.current_project.get("project_dir")
            if not project_dir:
                logger.warning("项目目录不存在，无法初始化角色场景管理器")
                return
            
            # 创建角色场景管理器
            from utils.character_scene_manager import CharacterSceneManager
            service_manager = getattr(self.project_manager, 'service_manager', None)
            if hasattr(self.project_manager, 'app_controller'):
                service_manager = self.project_manager.app_controller.service_manager
            
            self.cs_manager = CharacterSceneManager(project_dir, service_manager)
            logger.info(f"角色场景管理器重新初始化成功，项目目录: {project_dir}")
            
        except Exception as e:
            logger.error(f"重新初始化角色场景管理器失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def get_current_config(self) -> ConsistencyConfig:
        """获取当前配置"""
        return self.current_config
    
    def refresh_characters(self):
        """刷新角色数据"""
        try:
            logger.info("开始刷新角色数据...")
            
            # 检查cs_manager是否可用
            if not self.cs_manager:
                logger.warning("角色场景管理器未初始化，尝试重新初始化")
                self._try_reinit_cs_manager()
                
                if not self.cs_manager:
                    QMessageBox.warning(self, "警告", "角色场景管理器未初始化，无法刷新角色数据")
                    return
            
            # 重新加载角色数据
            characters = self.cs_manager.get_all_characters()
            self.character_table.setRowCount(len(characters))
            
            for row, (char_id, char_data) in enumerate(characters.items()):
                # 处理不同的数据格式
                name = char_data.get('name', '')
                description = char_data.get('description', '')
                
                # 处理外貌信息（可能是字符串或字典）
                appearance = char_data.get('appearance', '')
                if isinstance(appearance, dict):
                    # 如果是字典，提取主要信息
                    appearance_parts = []
                    for key, value in appearance.items():
                        if value and isinstance(value, str):
                            appearance_parts.append(f"{key}: {value}")
                    appearance = "; ".join(appearance_parts)
                elif not isinstance(appearance, str):
                    appearance = str(appearance)
                
                consistency_prompt = char_data.get('consistency_prompt', '')
                
                self.character_table.setItem(row, 0, QTableWidgetItem(name))
                self.character_table.setItem(row, 1, QTableWidgetItem(description))
                self.character_table.setItem(row, 2, QTableWidgetItem(appearance))
                self.character_table.setItem(row, 3, QTableWidgetItem(consistency_prompt))
                
                # 存储ID
                self.character_table.item(row, 0).setData(Qt.UserRole, char_id)
            
            # 更新按钮状态
            self.update_button_states()
            
            logger.info(f"角色数据刷新完成，共加载 {len(characters)} 个角色")
            QMessageBox.information(self, "提示", f"角色数据已刷新\n共加载 {len(characters)} 个角色")
            
        except Exception as e:
            logger.error(f"刷新角色数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "错误", f"刷新角色数据失败: {str(e)}")
    
    def refresh_scenes(self):
        """刷新场景数据"""
        try:
            import re
            logger.info("开始刷新场景数据...")
            
            # 检查cs_manager是否可用
            if not self.cs_manager:
                logger.warning("角色场景管理器未初始化，尝试重新初始化")
                self._try_reinit_cs_manager()
                
                if not self.cs_manager:
                    QMessageBox.warning(self, "警告", "角色场景管理器未初始化，无法刷新场景数据")
                    return
            
            # 重新加载场景数据
            all_scenes = self.cs_manager.get_all_scenes()
            
            # 直接使用所有场景数据（源头已过滤）
            filtered_scenes = all_scenes
            
            self.scene_table.setRowCount(len(filtered_scenes))
            
            # 对过滤后的场景进行自然排序
            def natural_sort_key(item):
                scene_id, scene_data = item
                scene_name = scene_data.get('name', '')
                numbers = re.findall(r'\d+', scene_name)
                if numbers:
                    return (0, int(numbers[0]), scene_name)
                else:
                    return (1, 0, scene_name)
            
            sorted_scenes = sorted(filtered_scenes.items(), key=natural_sort_key)
            
            for row, (scene_id, scene_data) in enumerate(sorted_scenes):
                name = scene_data.get('name', '')
                description = scene_data.get('description', '')
                
                # 处理环境信息（可能是字符串或字典）
                environment = scene_data.get('environment', '')
                if isinstance(environment, dict):
                    env_parts = []
                    for key, value in environment.items():
                        if value and isinstance(value, (str, list)):
                            if isinstance(value, list):
                                value = ", ".join(str(v) for v in value)
                            env_parts.append(f"{key}: {value}")
                    environment = "; ".join(env_parts)
                elif not isinstance(environment, str):
                    environment = str(environment)
                
                # 处理光线信息（可能是字符串或字典）
                lighting = scene_data.get('lighting', '')
                if isinstance(lighting, dict):
                    lighting_parts = []
                    for key, value in lighting.items():
                        if value and isinstance(value, str):
                            lighting_parts.append(f"{key}: {value}")
                    lighting = "; ".join(lighting_parts)
                elif not isinstance(lighting, str):
                    lighting = str(lighting)
                
                consistency_prompt = scene_data.get('consistency_prompt', '')
                
                self.scene_table.setItem(row, 0, QTableWidgetItem(name))
                self.scene_table.setItem(row, 1, QTableWidgetItem(description))
                self.scene_table.setItem(row, 2, QTableWidgetItem(environment))
                self.scene_table.setItem(row, 3, QTableWidgetItem(lighting))
                self.scene_table.setItem(row, 4, QTableWidgetItem(consistency_prompt))
                
                # 存储ID
                self.scene_table.item(row, 0).setData(Qt.UserRole, scene_id)
            
            # 更新按钮状态
            self.update_button_states()
            
            logger.info(f"场景数据刷新完成，共加载 {len(filtered_scenes)} 个用户创建的场景（已过滤分镜生成的场景）")
            QMessageBox.information(self, "提示", f"场景数据已刷新\n共加载 {len(filtered_scenes)} 个用户创建的场景")
            
        except Exception as e:
            logger.error(f"刷新场景数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "错误", f"刷新场景数据失败: {str(e)}")