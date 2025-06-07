import sys
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QTextEdit, QLineEdit, QComboBox, QGroupBox, QFormLayout,
    QMessageBox, QHeaderView, QSplitter, QFrame, QScrollArea,
    QCheckBox, QSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from utils.logger import logger

class CharacterSceneDialog(QDialog):
    """角色场景设置对话框"""
    
    # 信号定义
    character_updated = pyqtSignal(str, dict)  # 角色更新信号
    scene_updated = pyqtSignal(str, dict)      # 场景更新信号
    consistency_applied = pyqtSignal(list, list)  # 一致性应用信号
    
    def __init__(self, character_scene_manager, parent=None):
        super().__init__(parent)
        self.character_scene_manager = character_scene_manager
        self.current_character_id = None
        self.current_scene_id = None
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("角色场景设置")
        self.setModal(True)
        self.resize(1000, 700)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 角色管理标签页
        self.character_tab = self.create_character_tab()
        self.tab_widget.addTab(self.character_tab, "角色管理")
        
        # 场景管理标签页
        self.scene_tab = self.create_scene_tab()
        self.tab_widget.addTab(self.scene_tab, "场景管理")
        
        # 一致性设置标签页
        self.consistency_tab = self.create_consistency_tab()
        self.tab_widget.addTab(self.consistency_tab, "一致性设置")
        
        # 自动提取标签页
        self.extract_tab = self.create_extract_tab()
        self.tab_widget.addTab(self.extract_tab, "自动提取")
        
        main_layout.addWidget(self.tab_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("应用到分镜")
        self.apply_btn.clicked.connect(self.apply_consistency)
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_all_data)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        
        button_layout.addStretch()
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(button_layout)
    
    def create_character_tab(self):
        """创建角色管理标签页"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # 左侧：角色列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 角色列表标题和按钮
        char_header_layout = QHBoxLayout()
        char_header_layout.addWidget(QLabel("角色列表"))
        
        self.add_character_btn = QPushButton("添加角色")
        self.add_character_btn.clicked.connect(self.add_character)
        char_header_layout.addWidget(self.add_character_btn)
        
        self.delete_character_btn = QPushButton("删除角色")
        self.delete_character_btn.clicked.connect(self.delete_character)
        char_header_layout.addWidget(self.delete_character_btn)
        
        left_layout.addLayout(char_header_layout)
        
        # 角色列表表格
        self.character_table = QTableWidget()
        self.character_table.setColumnCount(3)
        self.character_table.setHorizontalHeaderLabels(["角色名称", "描述", "来源"])
        self.character_table.horizontalHeader().setStretchLastSection(True)
        self.character_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.character_table.itemSelectionChanged.connect(self.on_character_selected)
        
        left_layout.addWidget(self.character_table)
        left_widget.setMaximumWidth(400)
        
        # 右侧：角色详细信息编辑
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 角色基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)
        
        self.char_name_edit = QLineEdit()
        self.char_description_edit = QTextEdit()
        self.char_description_edit.setMaximumHeight(80)
        
        basic_layout.addRow("角色名称:", self.char_name_edit)
        basic_layout.addRow("角色描述:", self.char_description_edit)
        
        right_layout.addWidget(basic_group)
        
        # 外貌信息
        appearance_group = QGroupBox("外貌特征")
        appearance_layout = QFormLayout(appearance_group)
        
        self.char_gender_combo = QComboBox()
        self.char_gender_combo.addItems(["", "男性", "女性", "其他"])
        
        self.char_age_edit = QLineEdit()
        self.char_hair_edit = QLineEdit()
        self.char_eyes_edit = QLineEdit()
        self.char_skin_edit = QLineEdit()
        self.char_build_edit = QLineEdit()
        
        appearance_layout.addRow("性别:", self.char_gender_combo)
        appearance_layout.addRow("年龄范围:", self.char_age_edit)
        appearance_layout.addRow("发型发色:", self.char_hair_edit)
        appearance_layout.addRow("眼睛:", self.char_eyes_edit)
        appearance_layout.addRow("肤色:", self.char_skin_edit)
        appearance_layout.addRow("体型:", self.char_build_edit)
        
        right_layout.addWidget(appearance_group)
        
        # 服装信息
        clothing_group = QGroupBox("服装打扮")
        clothing_layout = QFormLayout(clothing_group)
        
        self.char_clothing_style_edit = QLineEdit()
        self.char_clothing_colors_edit = QLineEdit()
        self.char_accessories_edit = QLineEdit()
        
        clothing_layout.addRow("服装风格:", self.char_clothing_style_edit)
        clothing_layout.addRow("主要颜色:", self.char_clothing_colors_edit)
        clothing_layout.addRow("配饰:", self.char_accessories_edit)
        
        right_layout.addWidget(clothing_group)
        
        # 一致性提示词
        consistency_group = QGroupBox("一致性提示词")
        consistency_layout = QVBoxLayout(consistency_group)
        
        self.char_consistency_edit = QTextEdit()
        self.char_consistency_edit.setMaximumHeight(100)
        self.char_consistency_edit.setPlaceholderText("输入用于保持角色一致性的提示词...")
        
        consistency_layout.addWidget(self.char_consistency_edit)
        
        # 生成提示词按钮
        generate_char_prompt_btn = QPushButton("自动生成提示词")
        generate_char_prompt_btn.clicked.connect(self.generate_character_prompt)
        consistency_layout.addWidget(generate_char_prompt_btn)
        
        right_layout.addWidget(consistency_group)
        
        # 保存角色按钮
        save_char_btn = QPushButton("保存角色")
        save_char_btn.clicked.connect(self.save_current_character)
        right_layout.addWidget(save_char_btn)
        
        right_layout.addStretch()
        
        # 添加到分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        return tab
    
    def create_scene_tab(self):
        """创建场景管理标签页"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # 左侧：场景列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 场景列表标题和按钮
        scene_header_layout = QHBoxLayout()
        scene_header_layout.addWidget(QLabel("场景列表"))
        
        self.add_scene_btn = QPushButton("添加场景")
        self.add_scene_btn.clicked.connect(self.add_scene)
        scene_header_layout.addWidget(self.add_scene_btn)
        
        self.delete_scene_btn = QPushButton("删除场景")
        self.delete_scene_btn.clicked.connect(self.delete_scene)
        scene_header_layout.addWidget(self.delete_scene_btn)
        
        left_layout.addLayout(scene_header_layout)
        
        # 场景列表表格
        self.scene_table = QTableWidget()
        self.scene_table.setColumnCount(3)
        self.scene_table.setHorizontalHeaderLabels(["场景名称", "类型", "来源"])
        self.scene_table.horizontalHeader().setStretchLastSection(True)
        self.scene_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.scene_table.itemSelectionChanged.connect(self.on_scene_selected)
        
        left_layout.addWidget(self.scene_table)
        left_widget.setMaximumWidth(400)
        
        # 右侧：场景详细信息编辑
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 场景基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)
        
        self.scene_name_edit = QLineEdit()
        self.scene_category_combo = QComboBox()
        self.scene_category_combo.addItems(["", "室内", "室外", "特殊"])
        self.scene_description_edit = QTextEdit()
        self.scene_description_edit.setMaximumHeight(80)
        
        basic_layout.addRow("场景名称:", self.scene_name_edit)
        basic_layout.addRow("场景类型:", self.scene_category_combo)
        basic_layout.addRow("场景描述:", self.scene_description_edit)
        
        right_layout.addWidget(basic_group)
        
        # 环境信息
        environment_group = QGroupBox("环境设置")
        environment_layout = QFormLayout(environment_group)
        
        self.scene_location_edit = QLineEdit()
        self.scene_size_edit = QLineEdit()
        self.scene_layout_edit = QLineEdit()
        self.scene_decorations_edit = QLineEdit()
        
        environment_layout.addRow("位置类型:", self.scene_location_edit)
        environment_layout.addRow("空间大小:", self.scene_size_edit)
        environment_layout.addRow("布局结构:", self.scene_layout_edit)
        environment_layout.addRow("装饰元素:", self.scene_decorations_edit)
        
        right_layout.addWidget(environment_group)
        
        # 光线氛围
        lighting_group = QGroupBox("光线氛围")
        lighting_layout = QFormLayout(lighting_group)
        
        self.scene_time_combo = QComboBox()
        self.scene_time_combo.addItems(["", "早晨", "上午", "中午", "下午", "傍晚", "晚上", "深夜"])
        
        self.scene_light_source_edit = QLineEdit()
        self.scene_brightness_edit = QLineEdit()
        self.scene_mood_edit = QLineEdit()
        
        lighting_layout.addRow("时间:", self.scene_time_combo)
        lighting_layout.addRow("光源:", self.scene_light_source_edit)
        lighting_layout.addRow("亮度:", self.scene_brightness_edit)
        lighting_layout.addRow("氛围:", self.scene_mood_edit)
        
        right_layout.addWidget(lighting_group)
        
        # 一致性提示词
        consistency_group = QGroupBox("一致性提示词")
        consistency_layout = QVBoxLayout(consistency_group)
        
        self.scene_consistency_edit = QTextEdit()
        self.scene_consistency_edit.setMaximumHeight(100)
        self.scene_consistency_edit.setPlaceholderText("输入用于保持场景一致性的提示词...")
        
        consistency_layout.addWidget(self.scene_consistency_edit)
        
        # 生成提示词按钮
        generate_scene_prompt_btn = QPushButton("自动生成提示词")
        generate_scene_prompt_btn.clicked.connect(self.generate_scene_prompt)
        consistency_layout.addWidget(generate_scene_prompt_btn)
        
        right_layout.addWidget(consistency_group)
        
        # 保存场景按钮
        save_scene_btn = QPushButton("保存场景")
        save_scene_btn.clicked.connect(self.save_current_scene)
        right_layout.addWidget(save_scene_btn)
        
        right_layout.addStretch()
        
        # 添加到分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        return tab
    
    def create_consistency_tab(self):
        """创建一致性设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 说明标签
        info_label = QLabel("选择要应用到分镜的角色和场景，系统将自动生成一致性提示词")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：角色选择
        char_widget = QWidget()
        char_layout = QVBoxLayout(char_widget)
        char_layout.addWidget(QLabel("选择角色:"))
        
        self.char_selection_table = QTableWidget()
        self.char_selection_table.setColumnCount(3)
        self.char_selection_table.setHorizontalHeaderLabels(["选择", "角色名称", "描述"])
        self.char_selection_table.horizontalHeader().setStretchLastSection(True)
        
        char_layout.addWidget(self.char_selection_table)
        
        # 右侧：场景选择
        scene_widget = QWidget()
        scene_layout = QVBoxLayout(scene_widget)
        scene_layout.addWidget(QLabel("选择场景:"))
        
        self.scene_selection_table = QTableWidget()
        self.scene_selection_table.setColumnCount(3)
        self.scene_selection_table.setHorizontalHeaderLabels(["选择", "场景名称", "类型"])
        self.scene_selection_table.horizontalHeader().setStretchLastSection(True)
        
        scene_layout.addWidget(self.scene_selection_table)
        
        splitter.addWidget(char_widget)
        splitter.addWidget(scene_widget)
        layout.addWidget(splitter)
        
        # 预览区域
        preview_group = QGroupBox("一致性提示词预览")
        preview_layout = QVBoxLayout(preview_group)
        
        self.consistency_preview = QTextEdit()
        self.consistency_preview.setMaximumHeight(150)
        self.consistency_preview.setReadOnly(True)
        
        preview_layout.addWidget(self.consistency_preview)
        
        # 生成预览按钮
        generate_preview_btn = QPushButton("生成预览")
        generate_preview_btn.clicked.connect(self.generate_consistency_preview)
        preview_layout.addWidget(generate_preview_btn)
        
        layout.addWidget(preview_group)
        
        return tab
    
    def create_extract_tab(self):
        """创建自动提取标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 说明
        info_label = QLabel("从文本中自动提取角色和场景信息")
        layout.addWidget(info_label)
        
        # 文本输入区域
        text_group = QGroupBox("输入文本")
        text_layout = QVBoxLayout(text_group)
        
        self.extract_text_edit = QTextEdit()
        self.extract_text_edit.setPlaceholderText("请输入要分析的文本内容...")
        text_layout.addWidget(self.extract_text_edit)
        
        # 提取按钮
        extract_btn = QPushButton("开始提取")
        extract_btn.clicked.connect(self.extract_from_text)
        text_layout.addWidget(extract_btn)
        
        layout.addWidget(text_group)
        
        # 提取结果
        result_group = QGroupBox("提取结果")
        result_layout = QVBoxLayout(result_group)
        
        self.extract_result_text = QTextEdit()
        self.extract_result_text.setReadOnly(True)
        result_layout.addWidget(self.extract_result_text)
        
        layout.addWidget(result_group)
        
        return tab
    
    def load_data(self):
        """加载角色和场景数据"""
        self.load_characters()
        self.load_scenes()
        self.load_consistency_selection()
    
    def load_characters(self):
        """加载角色数据到表格"""
        characters = self.character_scene_manager.get_all_characters()
        
        self.character_table.setRowCount(len(characters))
        
        for row, (char_id, char_data) in enumerate(characters.items()):
            # 角色名称
            name_item = QTableWidgetItem(char_data.get('name', ''))
            name_item.setData(Qt.UserRole, char_id)
            self.character_table.setItem(row, 0, name_item)
            
            # 描述
            desc_item = QTableWidgetItem(char_data.get('description', '')[:50] + '...' if len(char_data.get('description', '')) > 50 else char_data.get('description', ''))
            self.character_table.setItem(row, 1, desc_item)
            
            # 来源
            source = "AI提取" if char_data.get('extracted_from_text') else "手动添加"
            if char_data.get('manual_edited'):
                source += "(已编辑)"
            source_item = QTableWidgetItem(source)
            self.character_table.setItem(row, 2, source_item)
    
    def load_scenes(self):
        """加载场景数据到表格"""
        scenes = self.character_scene_manager.get_all_scenes()
        
        self.scene_table.setRowCount(len(scenes))
        
        for row, (scene_id, scene_data) in enumerate(scenes.items()):
            # 场景名称
            name_item = QTableWidgetItem(scene_data.get('name', ''))
            name_item.setData(Qt.UserRole, scene_id)
            self.scene_table.setItem(row, 0, name_item)
            
            # 类型
            category_item = QTableWidgetItem(scene_data.get('category', ''))
            self.scene_table.setItem(row, 1, category_item)
            
            # 来源
            source = "AI提取" if scene_data.get('extracted_from_text') else "手动添加"
            if scene_data.get('manual_edited'):
                source += "(已编辑)"
            source_item = QTableWidgetItem(source)
            self.scene_table.setItem(row, 2, source_item)
    
    def load_consistency_selection(self):
        """加载一致性选择表格"""
        # 加载角色选择表格
        characters = self.character_scene_manager.get_all_characters()
        self.char_selection_table.setRowCount(len(characters))
        
        for row, (char_id, char_data) in enumerate(characters.items()):
            # 复选框
            checkbox = QCheckBox()
            self.char_selection_table.setCellWidget(row, 0, checkbox)
            
            # 角色名称
            name_item = QTableWidgetItem(char_data.get('name', ''))
            name_item.setData(Qt.UserRole, char_id)
            self.char_selection_table.setItem(row, 1, name_item)
            
            # 描述
            desc_item = QTableWidgetItem(char_data.get('description', '')[:30] + '...' if len(char_data.get('description', '')) > 30 else char_data.get('description', ''))
            self.char_selection_table.setItem(row, 2, desc_item)
        
        # 加载场景选择表格
        scenes = self.character_scene_manager.get_all_scenes()
        self.scene_selection_table.setRowCount(len(scenes))
        
        for row, (scene_id, scene_data) in enumerate(scenes.items()):
            # 复选框
            checkbox = QCheckBox()
            self.scene_selection_table.setCellWidget(row, 0, checkbox)
            
            # 场景名称
            name_item = QTableWidgetItem(scene_data.get('name', ''))
            name_item.setData(Qt.UserRole, scene_id)
            self.scene_selection_table.setItem(row, 1, name_item)
            
            # 类型
            category_item = QTableWidgetItem(scene_data.get('category', ''))
            self.scene_selection_table.setItem(row, 2, category_item)
    
    def on_character_selected(self):
        """角色选择改变时的处理"""
        current_row = self.character_table.currentRow()
        if current_row >= 0:
            name_item = self.character_table.item(current_row, 0)
            if name_item:
                char_id = name_item.data(Qt.UserRole)
                self.load_character_details(char_id)
    
    def on_scene_selected(self):
        """场景选择改变时的处理"""
        current_row = self.scene_table.currentRow()
        if current_row >= 0:
            name_item = self.scene_table.item(current_row, 0)
            if name_item:
                scene_id = name_item.data(Qt.UserRole)
                self.load_scene_details(scene_id)
    
    def load_character_details(self, char_id):
        """加载角色详细信息"""
        self.current_character_id = char_id
        char_data = self.character_scene_manager.get_character(char_id)
        
        if char_data:
            self.char_name_edit.setText(char_data.get('name', ''))
            self.char_description_edit.setText(char_data.get('description', ''))
            
            # 外貌信息
            appearance = char_data.get('appearance', {})
            self.char_gender_combo.setCurrentText(appearance.get('gender', ''))
            self.char_age_edit.setText(appearance.get('age_range', ''))
            self.char_hair_edit.setText(appearance.get('hair', ''))
            self.char_eyes_edit.setText(appearance.get('eyes', ''))
            self.char_skin_edit.setText(appearance.get('skin', ''))
            self.char_build_edit.setText(appearance.get('build', ''))
            
            # 服装信息
            clothing = char_data.get('clothing', {})
            self.char_clothing_style_edit.setText(clothing.get('style', ''))
            self.char_clothing_colors_edit.setText(', '.join(clothing.get('colors', [])))
            self.char_accessories_edit.setText(', '.join(clothing.get('accessories', [])))
            
            # 一致性提示词
            self.char_consistency_edit.setText(char_data.get('consistency_prompt', ''))
    
    def load_scene_details(self, scene_id):
        """加载场景详细信息"""
        self.current_scene_id = scene_id
        scene_data = self.character_scene_manager.get_scene(scene_id)
        
        if scene_data:
            self.scene_name_edit.setText(scene_data.get('name', ''))
            self.scene_category_combo.setCurrentText(scene_data.get('category', ''))
            self.scene_description_edit.setText(scene_data.get('description', ''))
            
            # 环境信息
            environment = scene_data.get('environment', {})
            self.scene_location_edit.setText(environment.get('location_type', ''))
            self.scene_size_edit.setText(environment.get('size', ''))
            self.scene_layout_edit.setText(environment.get('layout', ''))
            self.scene_decorations_edit.setText(', '.join(environment.get('decorations', [])))
            
            # 光线信息
            lighting = scene_data.get('lighting', {})
            self.scene_time_combo.setCurrentText(lighting.get('time_of_day', ''))
            self.scene_light_source_edit.setText(lighting.get('light_source', ''))
            self.scene_brightness_edit.setText(lighting.get('brightness', ''))
            self.scene_mood_edit.setText(lighting.get('mood', ''))
            
            # 一致性提示词
            self.scene_consistency_edit.setText(scene_data.get('consistency_prompt', ''))
    
    def add_character(self):
        """添加新角色"""
        char_id = f"manual_{self.character_scene_manager._get_current_time().replace(':', '_')}"
        char_data = {
            "name": "新角色",
            "description": "",
            "appearance": {
                "gender": "",
                "age_range": "",
                "hair": "",
                "eyes": "",
                "skin": "",
                "build": ""
            },
            "clothing": {
                "style": "",
                "colors": [],
                "accessories": []
            },
            "personality": {
                "traits": [],
                "expressions": [],
                "mannerisms": []
            },
            "consistency_prompt": "",
            "extracted_from_text": False,
            "manual_edited": False
        }
        
        self.character_scene_manager.save_character(char_id, char_data)
        self.load_characters()
        self.load_consistency_selection()
        
        # 选中新添加的角色
        for row in range(self.character_table.rowCount()):
            item = self.character_table.item(row, 0)
            if item and item.data(Qt.UserRole) == char_id:
                self.character_table.selectRow(row)
                break
    
    def add_scene(self):
        """添加新场景"""
        scene_id = f"manual_{self.character_scene_manager._get_current_time().replace(':', '_')}"
        scene_data = {
            "name": "新场景",
            "category": "",
            "description": "",
            "environment": {
                "location_type": "",
                "size": "",
                "layout": "",
                "decorations": [],
                "furniture": []
            },
            "lighting": {
                "time_of_day": "",
                "light_source": "",
                "brightness": "",
                "mood": ""
            },
            "atmosphere": {
                "style": "",
                "colors": [],
                "mood": "",
                "weather": ""
            },
            "consistency_prompt": "",
            "extracted_from_text": False,
            "manual_edited": False
        }
        
        self.character_scene_manager.save_scene(scene_id, scene_data)
        self.load_scenes()
        self.load_consistency_selection()
        
        # 选中新添加的场景
        for row in range(self.scene_table.rowCount()):
            item = self.scene_table.item(row, 0)
            if item and item.data(Qt.UserRole) == scene_id:
                self.scene_table.selectRow(row)
                break
    
    def delete_character(self):
        """删除选中的角色"""
        current_row = self.character_table.currentRow()
        if current_row >= 0:
            name_item = self.character_table.item(current_row, 0)
            if name_item:
                char_id = name_item.data(Qt.UserRole)
                char_name = name_item.text()
                
                reply = QMessageBox.question(self, "确认删除", 
                                            f"确定要删除角色 '{char_name}' 吗？",
                                            QMessageBox.Yes | QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    self.character_scene_manager.delete_character(char_id)
                    self.load_characters()
                    self.load_consistency_selection()
                    self.clear_character_details()
    
    def delete_scene(self):
        """删除选中的场景"""
        current_row = self.scene_table.currentRow()
        if current_row >= 0:
            name_item = self.scene_table.item(current_row, 0)
            if name_item:
                scene_id = name_item.data(Qt.UserRole)
                scene_name = name_item.text()
                
                reply = QMessageBox.question(self, "确认删除", 
                                            f"确定要删除场景 '{scene_name}' 吗？",
                                            QMessageBox.Yes | QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    self.character_scene_manager.delete_scene(scene_id)
                    self.load_scenes()
                    self.load_consistency_selection()
                    self.clear_scene_details()
    
    def save_current_character(self):
        """保存当前编辑的角色"""
        if not self.current_character_id:
            QMessageBox.warning(self, "警告", "请先选择一个角色")
            return
        
        try:
            char_data = {
                "name": self.char_name_edit.text(),
                "description": self.char_description_edit.toPlainText(),
                "appearance": {
                    "gender": self.char_gender_combo.currentText(),
                    "age_range": self.char_age_edit.text(),
                    "hair": self.char_hair_edit.text(),
                    "eyes": self.char_eyes_edit.text(),
                    "skin": self.char_skin_edit.text(),
                    "build": self.char_build_edit.text()
                },
                "clothing": {
                    "style": self.char_clothing_style_edit.text(),
                    "colors": [c.strip() for c in self.char_clothing_colors_edit.text().split(',') if c.strip()],
                    "accessories": [a.strip() for a in self.char_accessories_edit.text().split(',') if a.strip()]
                },
                "consistency_prompt": self.char_consistency_edit.toPlainText(),
                "manual_edited": True
            }
            
            # 保留原有的其他字段
            original_data = self.character_scene_manager.get_character(self.current_character_id)
            if original_data:
                char_data.update({
                    "personality": original_data.get("personality", {}),
                    "extracted_from_text": original_data.get("extracted_from_text", False)
                })
            
            self.character_scene_manager.save_character(self.current_character_id, char_data)
            self.load_characters()
            self.load_consistency_selection()
            
            QMessageBox.information(self, "成功", "角色信息已保存")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存角色失败: {str(e)}")
    
    def save_current_scene(self):
        """保存当前编辑的场景"""
        if not self.current_scene_id:
            QMessageBox.warning(self, "警告", "请先选择一个场景")
            return
        
        try:
            scene_data = {
                "name": self.scene_name_edit.text(),
                "category": self.scene_category_combo.currentText(),
                "description": self.scene_description_edit.toPlainText(),
                "environment": {
                    "location_type": self.scene_location_edit.text(),
                    "size": self.scene_size_edit.text(),
                    "layout": self.scene_layout_edit.text(),
                    "decorations": [d.strip() for d in self.scene_decorations_edit.text().split(',') if d.strip()]
                },
                "lighting": {
                    "time_of_day": self.scene_time_combo.currentText(),
                    "light_source": self.scene_light_source_edit.text(),
                    "brightness": self.scene_brightness_edit.text(),
                    "mood": self.scene_mood_edit.text()
                },
                "consistency_prompt": self.scene_consistency_edit.toPlainText(),
                "manual_edited": True
            }
            
            # 保留原有的其他字段
            original_data = self.character_scene_manager.get_scene(self.current_scene_id)
            if original_data:
                scene_data.update({
                    "atmosphere": original_data.get("atmosphere", {}),
                    "extracted_from_text": original_data.get("extracted_from_text", False)
                })
            
            self.character_scene_manager.save_scene(self.current_scene_id, scene_data)
            self.load_scenes()
            self.load_consistency_selection()
            
            QMessageBox.information(self, "成功", "场景信息已保存")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存场景失败: {str(e)}")
    
    def generate_character_prompt(self):
        """自动生成角色一致性提示词"""
        try:
            prompt_parts = []
            
            # 基本信息
            name = self.char_name_edit.text()
            if name:
                prompt_parts.append(f"角色名称: {name}")
            
            # 外貌特征
            appearance_parts = []
            if self.char_gender_combo.currentText():
                appearance_parts.append(self.char_gender_combo.currentText())
            if self.char_age_edit.text():
                appearance_parts.append(f"{self.char_age_edit.text()}岁")
            if self.char_hair_edit.text():
                appearance_parts.append(self.char_hair_edit.text())
            if self.char_eyes_edit.text():
                appearance_parts.append(self.char_eyes_edit.text())
            if self.char_skin_edit.text():
                appearance_parts.append(self.char_skin_edit.text())
            if self.char_build_edit.text():
                appearance_parts.append(self.char_build_edit.text())
            
            if appearance_parts:
                prompt_parts.append(f"外貌: {', '.join(appearance_parts)}")
            
            # 服装
            clothing_parts = []
            if self.char_clothing_style_edit.text():
                clothing_parts.append(self.char_clothing_style_edit.text())
            if self.char_clothing_colors_edit.text():
                clothing_parts.append(f"颜色: {self.char_clothing_colors_edit.text()}")
            if self.char_accessories_edit.text():
                clothing_parts.append(f"配饰: {self.char_accessories_edit.text()}")
            
            if clothing_parts:
                prompt_parts.append(f"服装: {', '.join(clothing_parts)}")
            
            generated_prompt = '; '.join(prompt_parts)
            self.char_consistency_edit.setText(generated_prompt)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成提示词失败: {str(e)}")
    
    def generate_scene_prompt(self):
        """自动生成场景一致性提示词"""
        try:
            prompt_parts = []
            
            # 基本信息
            name = self.scene_name_edit.text()
            if name:
                prompt_parts.append(f"场景: {name}")
            
            category = self.scene_category_combo.currentText()
            if category:
                prompt_parts.append(f"类型: {category}")
            
            # 环境信息
            environment_parts = []
            if self.scene_location_edit.text():
                environment_parts.append(self.scene_location_edit.text())
            if self.scene_size_edit.text():
                environment_parts.append(f"大小: {self.scene_size_edit.text()}")
            if self.scene_layout_edit.text():
                environment_parts.append(f"布局: {self.scene_layout_edit.text()}")
            if self.scene_decorations_edit.text():
                environment_parts.append(f"装饰: {self.scene_decorations_edit.text()}")
            
            if environment_parts:
                prompt_parts.append(f"环境: {', '.join(environment_parts)}")
            
            # 光线氛围
            lighting_parts = []
            if self.scene_time_combo.currentText():
                lighting_parts.append(self.scene_time_combo.currentText())
            if self.scene_light_source_edit.text():
                lighting_parts.append(f"光源: {self.scene_light_source_edit.text()}")
            if self.scene_brightness_edit.text():
                lighting_parts.append(f"亮度: {self.scene_brightness_edit.text()}")
            if self.scene_mood_edit.text():
                lighting_parts.append(f"氛围: {self.scene_mood_edit.text()}")
            
            if lighting_parts:
                prompt_parts.append(f"光线: {', '.join(lighting_parts)}")
            
            generated_prompt = '; '.join(prompt_parts)
            self.scene_consistency_edit.setText(generated_prompt)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成提示词失败: {str(e)}")
    
    def generate_consistency_preview(self):
        """生成一致性预览"""
        try:
            selected_characters = []
            selected_scenes = []
            
            # 获取选中的角色
            for row in range(self.char_selection_table.rowCount()):
                checkbox = self.char_selection_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    name_item = self.char_selection_table.item(row, 1)
                    if name_item:
                        char_id = name_item.data(Qt.UserRole)
                        selected_characters.append(char_id)
            
            # 获取选中的场景
            for row in range(self.scene_selection_table.rowCount()):
                checkbox = self.scene_selection_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    name_item = self.scene_selection_table.item(row, 1)
                    if name_item:
                        scene_id = name_item.data(Qt.UserRole)
                        selected_scenes.append(scene_id)
            
            # 生成一致性提示词
            consistency_prompt = self.character_scene_manager.generate_consistency_prompt(
                selected_characters, selected_scenes
            )
            
            self.consistency_preview.setText(consistency_prompt)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成预览失败: {str(e)}")
    
    def extract_from_text(self):
        """从文本中提取角色和场景"""
        text = self.extract_text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "请输入要分析的文本")
            return
        
        try:
            result = self.character_scene_manager.auto_extract_and_save(text)
            
            if result['success']:
                self.extract_result_text.setText(f"提取成功！\n{result['message']}")
                self.load_data()  # 重新加载所有数据
                QMessageBox.information(self, "成功", result['message'])
            else:
                self.extract_result_text.setText(f"提取失败：{result['message']}")
                QMessageBox.critical(self, "错误", result['message'])
                
        except Exception as e:
            error_msg = f"提取过程中发生错误: {str(e)}"
            self.extract_result_text.setText(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def apply_consistency(self):
        """应用一致性设置到分镜"""
        try:
            selected_characters = []
            selected_scenes = []
            
            # 获取选中的角色
            for row in range(self.char_selection_table.rowCount()):
                checkbox = self.char_selection_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    name_item = self.char_selection_table.item(row, 1)
                    if name_item:
                        char_id = name_item.data(Qt.UserRole)
                        selected_characters.append(char_id)
            
            # 获取选中的场景
            for row in range(self.scene_selection_table.rowCount()):
                checkbox = self.scene_selection_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    name_item = self.scene_selection_table.item(row, 1)
                    if name_item:
                        scene_id = name_item.data(Qt.UserRole)
                        selected_scenes.append(scene_id)
            
            if not selected_characters and not selected_scenes:
                QMessageBox.warning(self, "警告", "请至少选择一个角色或场景")
                return
            
            # 发射信号
            self.consistency_applied.emit(selected_characters, selected_scenes)
            
            QMessageBox.information(self, "成功", "一致性设置已应用到分镜")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用一致性设置失败: {str(e)}")
    
    def save_all_data(self):
        """保存所有数据"""
        try:
            # 如果当前有编辑的角色，先保存
            if self.current_character_id:
                self.save_current_character()
            
            # 如果当前有编辑的场景，先保存
            if self.current_scene_id:
                self.save_current_scene()
            
            QMessageBox.information(self, "成功", "所有数据已保存")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存数据失败: {str(e)}")
    
    def clear_character_details(self):
        """清空角色详细信息"""
        self.current_character_id = None
        self.char_name_edit.clear()
        self.char_description_edit.clear()
        self.char_gender_combo.setCurrentIndex(0)
        self.char_age_edit.clear()
        self.char_hair_edit.clear()
        self.char_eyes_edit.clear()
        self.char_skin_edit.clear()
        self.char_build_edit.clear()
        self.char_clothing_style_edit.clear()
        self.char_clothing_colors_edit.clear()
        self.char_accessories_edit.clear()
        self.char_consistency_edit.clear()
    
    def clear_scene_details(self):
        """清空场景详细信息"""
        self.current_scene_id = None
        self.scene_name_edit.clear()
        self.scene_category_combo.setCurrentIndex(0)
        self.scene_description_edit.clear()
        self.scene_location_edit.clear()
        self.scene_size_edit.clear()
        self.scene_layout_edit.clear()
        self.scene_decorations_edit.clear()
        self.scene_time_combo.setCurrentIndex(0)
        self.scene_light_source_edit.clear()
        self.scene_brightness_edit.clear()
        self.scene_mood_edit.clear()
        self.scene_consistency_edit.clear()