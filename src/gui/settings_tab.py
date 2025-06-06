import sys
import os
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QFormLayout, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from utils.logger import logger
from utils.config_manager import ConfigManager
from gui.log_dialog import LogDialog
from gui.model_manager_dialog import ModelManagerDialog


class SettingsTab(QWidget):
    """设置标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 默认ComfyUI输出目录
        self.comfyui_output_dir = ""
        
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """初始化UI界面"""
        settings_layout = QVBoxLayout()
        settings_layout.addWidget(QLabel("设置区"))

        # 大模型配置区域
        llm_group = QGroupBox("大模型配置")
        llm_group.setObjectName("settings-group")
        llm_layout = QVBoxLayout(llm_group)
        
        # 标题
        models_label = QLabel("当前已配置模型")
        models_label.setObjectName("settings-title")
        
        # 当前已配置模型显示
        self.models_display = QLabel("正在加载模型配置...")
        self.models_display.setWordWrap(True)
        self.models_display.setObjectName("models-display")
        self.models_display.setMinimumHeight(100)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        self.manage_models_btn = QPushButton("管理模型")
        self.manage_models_btn.setObjectName("primary-button")
        self.manage_models_btn.clicked.connect(self.open_model_manager)
        self.manage_models_btn.setToolTip("打开模型管理界面，可添加、编辑、删除多个大模型")
        self.refresh_models_btn = QPushButton("刷新显示")
        self.refresh_models_btn.setObjectName("secondary-button")
        self.refresh_models_btn.clicked.connect(self.refresh_models_display)
        self.refresh_models_btn.setToolTip("刷新模型显示")
        
        button_layout.addWidget(self.manage_models_btn)
        button_layout.addWidget(self.refresh_models_btn)
        button_layout.addStretch()
        
        llm_layout.addWidget(models_label)
        llm_layout.addWidget(self.models_display)
        llm_layout.addLayout(button_layout)
        llm_layout.setSpacing(12)
        
        settings_layout.addWidget(llm_group)

        # General Settings
        general_settings_group = QGroupBox("通用设置")
        general_form = QFormLayout()
        
        self.comfyui_output_dir_input = QLineEdit(self.comfyui_output_dir)
        self.comfyui_output_dir_input.setPlaceholderText("例如: D:\\ComfyUI\\output 或 /path/to/ComfyUI/output")
        self.comfyui_output_dir_input.setToolTip("请输入 ComfyUI 的 output 文件夹的绝对路径")
        general_form.addRow("ComfyUI 输出目录:", self.comfyui_output_dir_input)
        
        self.save_general_settings_btn = QPushButton("保存通用设置")
        self.save_general_settings_btn.clicked.connect(self.save_general_settings)
        self.save_general_settings_btn.setToolTip("保存通用应用设置")
        general_form.addRow(self.save_general_settings_btn)
        
        general_settings_group.setLayout(general_form)
        settings_layout.addWidget(general_settings_group)
        
        # 系统日志按钮
        self.log_btn = QPushButton("查看系统日志")
        self.log_btn.clicked.connect(self.show_log_dialog)
        self.log_btn.setToolTip("查看系统日志")
        settings_layout.addWidget(self.log_btn)
        
        settings_layout.addStretch()
        self.setLayout(settings_layout)
        
    def load_settings(self):
        """加载设置"""
        try:
            # 刷新模型显示
            self.refresh_models_display()
            
            # 加载应用设置
            app_config = self.config_manager.config.get('app_settings', {})
            if app_config:
                self.comfyui_output_dir = app_config.get('comfyui_output_dir', '')
                self.comfyui_output_dir_input.setText(self.comfyui_output_dir)
                
        except Exception as e:
            logger.error(f"加载设置时发生错误: {e}")
    
    def refresh_models_display(self):
        """刷新模型显示"""
        try:
            models = self.config_manager.config.get("models", [])
            if models:
                model_info_list = []
                for i, model in enumerate(models, 1):
                    name = model.get("name", "未知模型")
                    model_type = model.get("type", "未知类型")
                    url = model.get("url", "")
                    key = model.get("key", "")
                    
                    # 隐藏API密钥，只显示前几位和后几位
                    if key:
                        if len(key) > 10:
                            masked_key = key[:6] + "***" + key[-4:]
                        else:
                            masked_key = "***"
                    else:
                        masked_key = "未配置"
                    
                    model_info = f"{i}. {name} ({model_type})\n   API地址: {url}\n   API密钥: {masked_key}"
                    model_info_list.append(model_info)
                
                display_text = "\n\n".join(model_info_list)
                self.models_display.setText(display_text)
            else:
                self.models_display.setText("暂无已配置的模型\n\n点击'管理模型'按钮添加新的大模型配置")
        except Exception as e:
            logger.error(f"刷新模型显示失败: {e}")
            self.models_display.setText(f"加载模型信息失败: {e}")
    

    
    def save_general_settings(self):
        """保存通用设置"""
        try:
            comfyui_output_dir = self.comfyui_output_dir_input.text().strip()
            
            # 验证目录路径
            if comfyui_output_dir and not os.path.exists(comfyui_output_dir):
                reply = QMessageBox.question(
                    self, "确认", 
                    f"目录 {comfyui_output_dir} 不存在，是否仍要保存？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # 构建应用配置
            app_config = {
                'comfyui_output_dir': comfyui_output_dir
            }
            
            # 保存配置
            success = self.config_manager.save_app_settings(app_config)
            
            if success:
                self.comfyui_output_dir = comfyui_output_dir
                QMessageBox.information(self, "成功", "通用设置已保存")
                logger.info("通用设置已保存")
            else:
                QMessageBox.warning(self, "错误", "保存通用设置失败")
                
        except Exception as e:
            logger.error(f"保存通用设置时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def show_log_dialog(self):
        """显示系统日志对话框"""
        try:
            logger.info("用户打开系统日志弹窗")
            dlg = LogDialog(self)
            dlg.exec_()
        except Exception as e:
            logger.error(f"显示日志对话框时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"无法打开日志对话框: {str(e)}")
    
    def get_comfyui_output_dir(self):
        """获取ComfyUI输出目录"""
        return self.comfyui_output_dir
    
    def open_model_manager(self):
        """打开模型管理对话框"""
        try:
            dialog = ModelManagerDialog(self.config_manager, self)
            # 连接模型更新信号
            dialog.models_updated.connect(self.refresh_models_display)
            dialog.exec_()
        except Exception as e:
            logger.error(f"打开模型管理对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"打开模型管理对话框失败: {e}")
    

    
    def get_current_model_config(self):
        """获取当前模型配置（已废弃，现在通过模型管理对话框管理）"""
        # 返回第一个配置的模型，如果有的话
        models = self.config_manager.config.get("models", [])
        if models:
            return models[0]
        return None