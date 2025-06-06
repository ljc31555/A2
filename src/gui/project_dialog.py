from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox, QTextEdit,
    QSplitter, QWidget, QGroupBox, QProgressBar, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
import os
from utils.logger import logger
from utils.project_manager import ProjectManager

class ProjectDialog(QDialog):
    """项目管理对话框"""
    
    project_loaded = pyqtSignal(dict)  # 项目加载信号
    
    def __init__(self, parent=None, config_dir=None):
        super().__init__(parent)
        self.config_dir = config_dir or 'config'
        self.project_manager = ProjectManager(self.config_dir)
        self.current_project_data = None
        
        self.setWindowTitle("项目管理")
        self.setModal(True)
        self.resize(800, 600)
        
        self.setup_ui()
        self.load_project_list()
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # 左侧：项目列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 项目列表标题
        list_label = QLabel("项目列表")
        list_label.setFont(QFont("Arial", 12, QFont.Bold))
        left_layout.addWidget(list_label)
        
        # 项目列表
        self.project_list = QListWidget()
        self.project_list.itemClicked.connect(self.on_project_selected)
        left_layout.addWidget(self.project_list)
        
        # 项目操作按钮
        button_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("加载项目")
        self.load_btn.clicked.connect(self.load_selected_project)
        self.load_btn.setEnabled(False)
        button_layout.addWidget(self.load_btn)
        
        self.delete_btn = QPushButton("删除项目")
        self.delete_btn.clicked.connect(self.delete_selected_project)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)
        
        left_layout.addLayout(button_layout)
        
        # 导入导出按钮
        io_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("导入项目")
        self.import_btn.clicked.connect(self.import_project)
        io_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("导出项目")
        self.export_btn.clicked.connect(self.export_project)
        self.export_btn.setEnabled(False)
        io_layout.addWidget(self.export_btn)
        
        left_layout.addLayout(io_layout)
        
        splitter.addWidget(left_widget)
        
        # 右侧：项目详情
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 项目详情标题
        detail_label = QLabel("项目详情")
        detail_label.setFont(QFont("Arial", 12, QFont.Bold))
        right_layout.addWidget(detail_label)
        
        # 项目信息组
        info_group = QGroupBox("基本信息")
        info_layout = QVBoxLayout(info_group)
        
        self.project_name_label = QLabel("项目名称: 未选择")
        info_layout.addWidget(self.project_name_label)
        
        self.created_time_label = QLabel("创建时间: 未知")
        info_layout.addWidget(self.created_time_label)
        
        self.modified_time_label = QLabel("修改时间: 未知")
        info_layout.addWidget(self.modified_time_label)
        
        self.shots_count_label = QLabel("分镜数量: 0")
        info_layout.addWidget(self.shots_count_label)
        
        right_layout.addWidget(info_group)
        
        # 进度信息组
        progress_group = QGroupBox("进度状态")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_text = QLabel("完成度: 0%")
        progress_layout.addWidget(self.progress_text)
        
        # 进度详情
        self.text_status = QLabel("✗ 文本改写")
        progress_layout.addWidget(self.text_status)
        
        self.shots_status = QLabel("✗ 分镜生成")
        progress_layout.addWidget(self.shots_status)
        
        self.images_status = QLabel("✗ 图片生成")
        progress_layout.addWidget(self.images_status)
        
        self.voices_status = QLabel("✗ 语音生成")
        progress_layout.addWidget(self.voices_status)
        
        self.video_status = QLabel("✗ 视频合成")
        progress_layout.addWidget(self.video_status)
        
        right_layout.addWidget(progress_group)
        
        # 项目描述
        desc_group = QGroupBox("项目描述")
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_text = QTextEdit()
        self.description_text.setMaximumHeight(100)
        self.description_text.setPlaceholderText("项目描述信息...")
        self.description_text.setReadOnly(True)
        desc_layout.addWidget(self.description_text)
        
        right_layout.addWidget(desc_group)
        
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setSizes([300, 500])
        
        # 底部按钮
        bottom_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.clicked.connect(self.load_project_list)
        bottom_layout.addWidget(self.refresh_btn)
        
        bottom_layout.addStretch()
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        bottom_layout.addWidget(self.close_btn)
        
        layout.addLayout(bottom_layout)
    
    def load_project_list(self):
        """加载项目列表"""
        try:
            self.project_list.clear()
            projects = self.project_manager.list_projects()
            
            for project in projects:
                item = QListWidgetItem()
                item.setText(project['name'])
                item.setData(Qt.UserRole, project)
                
                # 计算项目完成度
                progress_status = project.get('progress_status', {})
                completion = self.project_manager._calculate_completion_percentage(progress_status)
                
                # 设置项目状态颜色
                if completion >= 80:
                    item.setBackground(QColor(144, 238, 144))  # 浅绿色
                elif completion >= 40:
                    item.setBackground(QColor(255, 255, 144))  # 浅黄色
                elif completion > 0:
                    item.setBackground(QColor(255, 255, 255))  # 白色
                else:
                    item.setBackground(QColor(211, 211, 211))  # 浅灰色
                
                # 在项目名称后显示完成度
                item.setText(f"{project['name']} ({completion}%)")
                
                self.project_list.addItem(item)
            
            logger.info(f"已加载 {len(projects)} 个项目")
            
        except Exception as e:
            logger.error(f"加载项目列表失败: {e}")
            QMessageBox.warning(self, "错误", f"加载项目列表失败: {e}")
    
    def on_project_selected(self, item):
        """项目选择事件"""
        try:
            project_data = item.data(Qt.UserRole)
            project_name = project_data['name']
            
            # 加载完整项目数据
            full_project_data = self.project_manager.load_project(project_name)
            if full_project_data:
                self.current_project_data = full_project_data
                self.update_project_details(project_data, full_project_data)
                
                # 启用按钮
                self.load_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)
                self.export_btn.setEnabled(True)
            
        except Exception as e:
            logger.error(f"选择项目失败: {e}")
            QMessageBox.warning(self, "错误", f"选择项目失败: {e}")
    
    def update_project_details(self, project_summary, full_data):
        """更新项目详情显示"""
        try:
            # 基本信息
            self.project_name_label.setText(f"项目名称: {project_summary['name']}")
            self.created_time_label.setText(f"创建时间: {project_summary.get('created_time', '未知')}")
            self.modified_time_label.setText(f"修改时间: {project_summary.get('last_modified', '未知')}")
            
            shots_count = len(full_data.get('shots_data', []))
            self.shots_count_label.setText(f"分镜数量: {shots_count}")
            
            # 进度状态
            progress_status = full_data.get('progress_status', {})
            completion = self.project_manager._calculate_completion_percentage(progress_status)
            
            self.progress_bar.setValue(completion)
            self.progress_text.setText(f"完成度: {completion}%")
            
            # 更新各步骤状态
            self.text_status.setText("✓ 文本改写" if progress_status.get('text_rewritten', False) else "✗ 文本改写")
            self.shots_status.setText("✓ 分镜生成" if progress_status.get('shots_generated', False) else "✗ 分镜生成")
            self.images_status.setText("✓ 图片生成" if progress_status.get('images_generated', False) else "✗ 图片生成")
            self.voices_status.setText("✓ 语音生成" if progress_status.get('voices_generated', False) else "✗ 语音生成")
            self.video_status.setText("✓ 视频合成" if progress_status.get('video_composed', False) else "✗ 视频合成")
            
            # 项目描述
            description = full_data.get('description', '')
            if not description and full_data.get('original_text'):
                # 如果没有描述，显示原始文本的前100个字符
                description = full_data['original_text'][:100] + "..." if len(full_data['original_text']) > 100 else full_data['original_text']
            
            self.description_text.setPlainText(description)
            
        except Exception as e:
            logger.error(f"更新项目详情失败: {e}")
    
    def load_selected_project(self):
        """加载选中的项目"""
        if not self.current_project_data:
            QMessageBox.warning(self, "警告", "请先选择一个项目")
            return
        
        try:
            # 发送项目加载信号
            self.project_loaded.emit(self.current_project_data)
            
            QMessageBox.information(self, "成功", "项目已加载到主界面")
            self.close()
            
        except Exception as e:
            logger.error(f"加载项目失败: {e}")
            QMessageBox.critical(self, "错误", f"加载项目失败: {e}")
    
    def delete_selected_project(self):
        """删除选中的项目"""
        current_item = self.project_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择一个项目")
            return
        
        project_data = current_item.data(Qt.UserRole)
        project_name = project_data['name']
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除项目 '{project_name}' 吗？\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.project_manager.delete_project(project_name):
                    QMessageBox.information(self, "成功", "项目已删除")
                    self.load_project_list()  # 刷新列表
                    self.clear_project_details()
                else:
                    QMessageBox.warning(self, "失败", "删除项目失败")
                    
            except Exception as e:
                logger.error(f"删除项目失败: {e}")
                QMessageBox.critical(self, "错误", f"删除项目失败: {e}")
    
    def import_project(self):
        """导入项目"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择项目文件", "", "JSON文件 (*.json)"
            )
            
            if file_path:
                project_name = os.path.splitext(os.path.basename(file_path))[0]
                
                if self.project_manager.import_project(file_path, project_name):
                    QMessageBox.information(self, "成功", f"项目 '{project_name}' 导入成功")
                    self.load_project_list()  # 刷新列表
                else:
                    QMessageBox.warning(self, "失败", "导入项目失败")
                    
        except Exception as e:
            logger.error(f"导入项目失败: {e}")
            QMessageBox.critical(self, "错误", f"导入项目失败: {e}")
    
    def export_project(self):
        """导出项目"""
        current_item = self.project_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择一个项目")
            return
        
        try:
            project_data = current_item.data(Qt.UserRole)
            project_name = project_data['name']
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存项目文件", f"{project_name}.json", "JSON文件 (*.json)"
            )
            
            if file_path:
                if self.project_manager.export_project(project_name, file_path):
                    QMessageBox.information(self, "成功", f"项目已导出到: {file_path}")
                else:
                    QMessageBox.warning(self, "失败", "导出项目失败")
                    
        except Exception as e:
            logger.error(f"导出项目失败: {e}")
            QMessageBox.critical(self, "错误", f"导出项目失败: {e}")
    
    def clear_project_details(self):
        """清空项目详情显示"""
        self.project_name_label.setText("项目名称: 未选择")
        self.created_time_label.setText("创建时间: 未知")
        self.modified_time_label.setText("修改时间: 未知")
        self.shots_count_label.setText("分镜数量: 0")
        
        self.progress_bar.setValue(0)
        self.progress_text.setText("完成度: 0%")
        
        self.text_status.setText("✗ 文本改写")
        self.shots_status.setText("✗ 分镜生成")
        self.images_status.setText("✗ 图片生成")
        self.voices_status.setText("✗ 语音生成")
        self.video_status.setText("✗ 视频合成")
        
        self.description_text.clear()
        
        # 禁用按钮
        self.load_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        
        self.current_project_data = None