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

        # LLM Model Settings
        model_settings_group = QGroupBox("大模型配置")
        model_form = QFormLayout()
        
        self.model_name_input = QLineEdit()
        self.model_name_input.setPlaceholderText("请输入大模型名称，如 通义千问")
        self.model_name_input.setToolTip("输入大模型名称")
        
        self.model_url_input = QLineEdit()
        self.model_url_input.setPlaceholderText("请输入大模型 API 地址")
        self.model_url_input.setToolTip("输入大模型API地址")
        
        self.model_key_input = QLineEdit()
        self.model_key_input.setPlaceholderText("请输入大模型 API KEY")
        self.model_key_input.setEchoMode(QLineEdit.Password)
        self.model_key_input.setToolTip("输入大模型API KEY")
        
        self.model_type_combo_settings = QComboBox()
        self.model_type_combo_settings.addItems(["tongyi", "deepseek", "zhipu", "其他"])

        model_form.addRow("大模型名称：", self.model_name_input)
        model_form.addRow("模型API类型：", self.model_type_combo_settings)
        model_form.addRow("大模型 API 地址：", self.model_url_input)
        model_form.addRow("大模型 API KEY：", self.model_key_input)
        
        # 模型配置按钮布局
        model_buttons_layout = QHBoxLayout()
        
        self.save_model_btn = QPushButton("保存模型配置")
        self.save_model_btn.clicked.connect(self.save_model_config)
        self.save_model_btn.setToolTip("保存大模型配置")
        
        self.manage_models_btn = QPushButton("管理所有模型")
        self.manage_models_btn.clicked.connect(self.open_model_manager)
        self.manage_models_btn.setToolTip("打开模型管理界面，可添加、编辑、删除多个大模型")
        
        model_buttons_layout.addWidget(self.save_model_btn)
        model_buttons_layout.addWidget(self.manage_models_btn)
        
        model_form.addRow(model_buttons_layout)
        
        model_settings_group.setLayout(model_form)
        settings_layout.addWidget(model_settings_group)

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
            # 加载LLM配置
            all_model_configs = self.config_manager.config.get("models", [])
            if all_model_configs:
                # 如果有模型配置，加载第一个模型的信息
                first_model = all_model_configs[0]
                
                self.model_name_input.setText(first_model.get('name', ''))
                self.model_url_input.setText(first_model.get('url', ''))
                self.model_key_input.setText(first_model.get('key', ''))
                
                # 设置模型类型
                model_type = first_model.get('type', 'tongyi')
                index = self.model_type_combo_settings.findText(model_type)
                if index >= 0:
                    self.model_type_combo_settings.setCurrentIndex(index)
            
            # 加载应用设置
            app_config = self.config_manager.config.get('app_settings', {})
            if app_config:
                self.comfyui_output_dir = app_config.get('comfyui_output_dir', '')
                self.comfyui_output_dir_input.setText(self.comfyui_output_dir)
                
        except Exception as e:
            logger.error(f"加载设置时发生错误: {e}")
    
    def save_model_config(self):
        """保存模型配置"""
        try:
            model_name = self.model_name_input.text().strip()
            model_url = self.model_url_input.text().strip()
            model_key = self.model_key_input.text().strip()
            model_type = self.model_type_combo_settings.currentText()
            
            if not all([model_name, model_url, model_key]):
                QMessageBox.warning(self, "警告", "请填写完整的模型配置信息")
                return
            
            # 构建模型配置
            model_config = {
                'models': {
                    model_name: {
                        'api_key': model_key,
                        'base_url': model_url,
                        'model_name': model_name,
                        'type': model_type
                    }
                }
            }
            
            # 保存配置
            success = self.config_manager.save_llm_config(model_config)
            
            if success:
                QMessageBox.information(self, "成功", "模型配置已保存")
                logger.info(f"模型配置已保存: {model_name}")
                
                # 通知父窗口更新模型列表
                if hasattr(self.parent_window, 'refresh_model_list'):
                    self.parent_window.refresh_model_list()
            else:
                QMessageBox.warning(self, "错误", "保存模型配置失败")
                
        except Exception as e:
            logger.error(f"保存模型配置时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
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
            dialog = ModelManagerDialog(self)
            # 连接信号，当模型更新时刷新父窗口的模型列表
            dialog.models_updated.connect(self.on_models_updated)
            dialog.exec_()
        except Exception as e:
            logger.error(f"打开模型管理对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"无法打开模型管理界面: {str(e)}")
    
    def on_models_updated(self):
        """模型配置更新后的回调"""
        try:
            # 重新加载配置
            self.config_manager = ConfigManager()
            self.load_settings()
            
            # 通知父窗口更新模型列表
            if hasattr(self.parent_window, 'refresh_model_list'):
                self.parent_window.refresh_model_list()
                
            logger.info("模型配置已更新")
        except Exception as e:
            logger.error(f"更新模型配置失败: {e}")
    
    def get_current_model_config(self):
        """获取当前模型配置"""
        return {
            'name': self.model_name_input.text().strip(),
            'url': self.model_url_input.text().strip(),
            'key': self.model_key_input.text().strip(),
            'type': self.model_type_combo_settings.currentText()
        }