import csv
import sys
import os
import json
import time
import shutil
import requests # 用于异常捕获
import logging # 导入 logging 模块

# 确保能找到 utils 和 models 目录
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QListWidget, QLabel, QPushButton, QProgressBar,
                             QTextEdit, QSplitter, QDialog, QPlainTextEdit, QMessageBox,
                             QComboBox, QLineEdit, QFormLayout, QGroupBox, QScrollArea, QGridLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
                             QStyledItemDelegate, QStyleOptionViewItem, QFrame, QSpacerItem, QSizePolicy,
                             QSpinBox, QDoubleSpinBox, QCheckBox, QSlider)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEnginePage
from PyQt5.QtCore import Qt, QTimer, QUrl, QDateTime, QSize, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QFont

# 从项目中导入的模块
from utils.logger import logger
from models.llm_api import LLMApi
from models.text_parser import TextParser # 虽然在改写中不直接用，但文件内可能其他地方引用
from utils.config_manager import ConfigManager # 用于配置管理
from gui.shots_window import ShotsWindow # Import the new shots window class
from models.comfyui_client import ComfyUIClient
from gui.voice_manager import VoiceManager
from models.image_generation_service import ImageGenerationService

# 导入重构后的组件
from gui.ui_components import ImageDelegate, CustomWebEnginePage
from gui.log_dialog import LogDialog
from gui.workflow_panel import WorkflowPanel

# 导入标签页模块
from gui.storyboard_tab import StoryboardTab
from gui.ai_drawing_tab import AIDrawingTab
from gui.settings_tab import SettingsTab
from gui.project_dialog import ProjectDialog
from utils.project_manager import ProjectManager

APP_SETTINGS_FILENAME = "app_settings.json"





class MainWindow(QMainWindow):
    def __init__(self):
        import traceback
        
        super().__init__()
        logger.info("=== MainWindow初始化开始 ===")
        
        try:
            logger.debug("设置窗口标题和图标")
            self.setWindowTitle("AI 视频生成系统")
            
            # 设置窗口图标（如果文件不存在不要崩溃）
            icon_path = os.path.join(os.path.dirname(__file__), '../../assets/app_icon.png')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                logger.debug(f"窗口图标设置成功: {icon_path}")
            else:
                logger.warning(f"窗口图标文件不存在: {icon_path}")
            
            # 设置固定窗口大小
            logger.debug("设置窗口大小")
            self.resize(1400, 900)
            
            # 加载QSS样式
            logger.debug("开始加载QSS样式")
            try:
                self.apply_stylesheet()
                logger.debug("QSS样式加载成功")
            except Exception as e:
                logger.error(f"加载QSS样式失败: {e}")
                logger.error(f"QSS样式加载异常堆栈: {traceback.format_exc()}")
                # 样式加载失败不应该阻止程序继续运行
        
        except Exception as e:
            logger.critical(f"MainWindow基础初始化失败: {e}")
            logger.critical(f"基础初始化异常堆栈: {traceback.format_exc()}")
            raise
        
        # temp_rewrite_file 用于保存改写后的文本文件路径，供生成分镜步骤使用
        self.temp_rewrite_file = "" #
        self.llm_api_instance = None # 用于存储 LLMApi 实例，避免重复创建
        
        self.config_manager = ConfigManager( # 使用相对路径定位config目录
            config_dir=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config")
        )
        logger.debug("MainWindow: config_manager initialized")

        self.SETTINGS_FILE_PATH = os.path.join(self.config_manager.config_dir, APP_SETTINGS_FILENAME)
        self.app_settings = self._load_app_settings()
        self.comfyui_output_dir = self.app_settings.get('comfyui_output_dir', '')

        # 初始化返回按钮
        self.back_to_edit_btn = None
        
        # 初始化分镜数据
        self.shots_data = []
        
        # 初始化项目管理器
        self.project_manager = ProjectManager(self.config_manager.config_dir)
        self.current_project_name = None
        self.current_project_description = None
        
        # 初始化菜单栏
        self.init_menu_bar()
        
        # 初始化进度条
        self.progress = QProgressBar()
        self.progress.setVisible(False)  # 初始时隐藏进度条
        self.progress.setFixedHeight(32)  # 设置固定高度
        self.progress.setMinimumWidth(200)  # 设置最小宽度
        # 设置进度条样式
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #1976d2;
                border-radius: 8px;
                text-align: center;
                background-color: #f8f9fa;
                height: 32px;
                font-size: 14px;
                color: #2c3e50;
                font-weight: bold;
                padding: 2px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, 
                                          stop: 0 #4fc3f7, stop: 1 #1976d2);
                border-radius: 6px;
                margin: 1px;
            }
            QProgressBar:indeterminate {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, 
                                          stop: 0 #e3f2fd, stop: 0.5 #1976d2, stop: 1 #e3f2fd);
                border-radius: 6px;
            }
        """)
        
        # 初始化分镜表格组件
        self.shots_table = None # 实际的QTableWidget
        self.shots_table_widget = None # 包含QTableWidget的容器QWidget
        
        # 初始化批量绘图相关属性
        self.batch_drawing_manager = None
        self.is_batch_drawing = False
        self.batch_current_index = 0
        self.batch_total_count = 0
        self.batch_success_count = 0
        self.batch_failed_count = 0
        self.batch_queue = []
        
        # 初始化图像生成服务
        self.image_generation_service = None
        
        # 初始化Pollinations客户端
        self.pollinations_client = None
        
        self.init_shots_table_ui() # 在主窗口初始化时就创建表格UI
        
        # 在这里初始化 log_output_bottom
        self.log_output_bottom = QPlainTextEdit() # 使用 QPlainTextEdit
        self.log_output_bottom.setReadOnly(True)
        self.log_output_bottom.setFixedHeight(120) # 增加高度确保可见
        self.log_output_bottom.setPlaceholderText("系统状态信息将显示在此处...")
        self.log_output_bottom.setVisible(True) # 确保可见
        # 添加一些初始内容确保组件正常工作
        self.log_output_bottom.appendPlainText("✅ 状态栏已初始化，准备显示操作信息")

        # 初始化顶部栏和底部栏 - 必须在其他UI组件之前初始化
        self.init_top_bottom_bars()

        logger.debug("MainWindow: init_ui called")
        self.init_ui()
        logger.debug("MainWindow: refresh_model_combo called")
        # refresh_model_combo 已迁移到 settings_tab，在那里初始化
        logger.info("refresh_model_combo 已迁移到 settings_tab") #
        self.init_log_refresh()
        logger.info("主界面初始化完成") #
        logger.debug("MainWindow: __init__ finished")
    
    def _init_image_generation_service(self):
        """初始化图像生成服务"""
        try:
            from models.image_generation_service import ImageGenerationService
            
            # 创建图像生成服务实例
            self.image_generation_service = ImageGenerationService()
            
            # 设置输出目录
            output_dir = self.app_settings.get('comfyui_output_dir', '')
            if output_dir and os.path.exists(output_dir):
                self.image_generation_service.set_output_directory(output_dir)
            
            # 如果有ComfyUI客户端，设置为备用引擎
            if hasattr(self, 'comfyui_client') and self.comfyui_client:
                self.image_generation_service.set_comfyui_client(self.comfyui_client)
            
            logger.info(f"图像生成服务初始化成功")
            
        except Exception as e:
            logger.error(f"图像生成服务初始化失败: {e}")
            self.image_generation_service = None
    
    def init_menu_bar(self):
        """初始化菜单栏"""
        menubar = self.menuBar()
        
        # 项目菜单
        project_menu = menubar.addMenu('项目')
        
        # 新建项目
        new_project_action = project_menu.addAction('新建项目')
        new_project_action.triggered.connect(self.new_project)
        
        # 保存项目
        save_project_action = project_menu.addAction('保存项目')
        save_project_action.triggered.connect(self.save_current_project)
        save_project_action.setShortcut('Ctrl+S')
        
        # 另存为项目
        save_as_project_action = project_menu.addAction('另存为...')
        save_as_project_action.triggered.connect(self.save_project_as)
        save_as_project_action.setShortcut('Ctrl+Shift+S')
        
        project_menu.addSeparator()
        
        # 打开项目管理器
        open_project_action = project_menu.addAction('项目管理器')
        open_project_action.triggered.connect(self.open_project_manager)
        open_project_action.setShortcut('Ctrl+O')
        
        project_menu.addSeparator()
        
        # 退出
        exit_action = project_menu.addAction('退出')
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut('Ctrl+Q')
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        # 关于
        about_action = help_menu.addAction('关于')
        about_action.triggered.connect(self.show_about)
    
    def new_project(self):
        """新建项目"""
        try:
            # 如果当前有未保存的项目，询问是否保存
            if self.has_unsaved_changes():
                reply = QMessageBox.question(
                    self, '保存项目', 
                    '当前项目有未保存的更改，是否保存？',
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    if not self.save_current_project():
                        return  # 保存失败，取消新建
                elif reply == QMessageBox.Cancel:
                    return  # 用户取消
            
            # 清空当前项目状态
            self.clear_current_project()
            self.current_project_name = None
            
            # 更新窗口标题
            self.setWindowTitle("AI 视频生成系统 - 新项目")
            
            logger.info("已创建新项目")
            self.log_output_bottom.appendPlainText("✅ 已创建新项目")
            
        except Exception as e:
            logger.error(f"新建项目失败: {e}")
            QMessageBox.critical(self, "错误", f"新建项目失败: {e}")
    
    def save_current_project(self):
        """保存当前项目"""
        try:
            if not self.current_project_name:
                return self.save_project_as()
            
            project_data = self.get_current_project_data()
            
            if self.project_manager.save_project(self.current_project_name, project_data):
                logger.info(f"项目已保存: {self.current_project_name}")
                self.log_output_bottom.appendPlainText(f"✅ 项目已保存: {self.current_project_name}")
                return True
            else:
                QMessageBox.warning(self, "保存失败", "保存项目失败")
                return False
                
        except Exception as e:
            logger.error(f"保存项目失败: {e}")
            QMessageBox.critical(self, "错误", f"保存项目失败: {e}")
            return False
    
    def save_project_as(self):
        """另存为项目"""
        try:
            from PyQt5.QtWidgets import QInputDialog
            
            project_name, ok = QInputDialog.getText(
                self, '另存为', '请输入项目名称:',
                text=self.current_project_name or ''
            )
            
            if ok and project_name.strip():
                project_name = project_name.strip()
                
                # 检查项目是否已存在
                existing_projects = [p['name'] for p in self.project_manager.list_projects()]
                if project_name in existing_projects:
                    reply = QMessageBox.question(
                        self, '项目已存在', 
                        f'项目 "{project_name}" 已存在，是否覆盖？',
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        return False
                
                project_data = self.get_current_project_data()
                
                if self.project_manager.save_project(project_name, project_data):
                    self.current_project_name = project_name
                    self.setWindowTitle(f"AI 视频生成系统 - {project_name}")
                    logger.info(f"项目已另存为: {project_name}")
                    self.log_output_bottom.appendPlainText(f"✅ 项目已另存为: {project_name}")
                    return True
                else:
                    QMessageBox.warning(self, "保存失败", "另存为项目失败")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"另存为项目失败: {e}")
            QMessageBox.critical(self, "错误", f"另存为项目失败: {e}")
            return False
    
    def open_project_manager(self):
        """打开项目管理器"""
        try:
            dialog = ProjectDialog(self, self.config_manager.config_dir)
            dialog.project_loaded.connect(self.load_project_data)
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"打开项目管理器失败: {e}")
            QMessageBox.critical(self, "错误", f"打开项目管理器失败: {e}")
    
    def load_project_data(self, project_data):
        """加载项目数据到界面"""
        try:
            # 清空当前状态
            self.clear_current_project()
            
            # 加载原始文本
            if project_data.get('original_text'):
                self.storyboard_tab.text_input.setPlainText(project_data['original_text'])
            
            # 加载改写文本，优先使用改写后的内容
            rewritten_text = project_data.get('rewritten_text', '').strip()
            original_text = project_data.get('original_text', '').strip()
            
            # 如果存在改写后的文本且不为空，优先使用改写后的文本
            if rewritten_text:
                self.storyboard_tab.output_text.setPlainText(rewritten_text)
            elif original_text:
                # 如果没有改写文本但有原文，则使用原文
                self.storyboard_tab.output_text.setPlainText(original_text)
            else:
                # 都没有则清空
                self.storyboard_tab.output_text.clear()
            
            # 先设置当前项目名称和目录
            project_name = project_data.get('project_name', '未命名项目')
            self.current_project_name = project_name
            self.current_project_description = project_data.get('description', '')
            self.current_project_dir = project_data.get('project_root', self.project_manager.get_project_path(project_name))
            self.setWindowTitle(f"AI 视频生成系统 - {project_name}")
            
            # 加载分镜数据（在设置项目目录之后）
            if project_data.get('shots_data'):
                self.shots_data = project_data['shots_data']
                self.show_shots_in_settings_tab(self.shots_data)
            else:
                self.shots_data = []
            
            # 加载绘图设置
            if project_data.get('drawing_settings'):
                self.ai_drawing_tab.load_settings(project_data['drawing_settings'])
            
            # 加载配音设置
            if project_data.get('voice_settings'):
                self._load_voice_settings(project_data['voice_settings'])
            
            # 加载工作流设置
            if project_data.get('workflow_settings'):
                self._load_workflow_settings(project_data['workflow_settings'])
            
            # 加载文本转镜头标签页设置
            if project_data.get('storyboard_settings'):
                self._load_storyboard_settings(project_data['storyboard_settings'])
            
            # 更新storyboard_tab中的项目信息
            if hasattr(self.storyboard_tab, 'current_project_name'):
                self.storyboard_tab.current_project_name = project_name
                self.storyboard_tab.current_project_root = project_data.get('project_root', self.project_manager.get_project_path(project_name))
            
            # 记录加载的进度状态
            progress_status = project_data.get('progress_status', {})
            logger.info(f"项目已加载: {project_name}")
            logger.info(f"加载的进度状态: {progress_status}")
            
            # 显示加载信息
            original_len = len(project_data.get('original_text', ''))
            rewritten_len = len(project_data.get('rewritten_text', ''))
            shots_count = len(project_data.get('shots_data', []))
            
            self.log_output_bottom.appendPlainText(f"✅ 项目已加载: {project_name}")
            self.log_output_bottom.appendPlainText(f"   原始文本: {original_len} 字符")
            self.log_output_bottom.appendPlainText(f"   改写文本: {rewritten_len} 字符")
            self.log_output_bottom.appendPlainText(f"   分镜数量: {shots_count} 个")
            
            # 重新计算并更新进度状态
            try:
                # 重新计算当前实际的进度状态
                current_project_data = self.get_current_project_data()
                updated_progress_status = current_project_data.get('progress_status', {})
                
                # 如果进度状态有变化，自动保存项目
                if updated_progress_status != progress_status:
                    logger.info(f"进度状态已更新: {progress_status} -> {updated_progress_status}")
                    self.save_current_project()
                    progress_status = updated_progress_status
                    
            except Exception as update_error:
                logger.error(f"更新进度状态失败: {update_error}")
            
            # 显示进度状态
            if progress_status:
                status_text = []
                if progress_status.get('text_rewritten'): status_text.append('文本改写')
                if progress_status.get('shots_generated'): status_text.append('分镜生成')
                if progress_status.get('images_generated'): status_text.append('图片生成')
                if progress_status.get('voices_generated'): status_text.append('语音生成')
                if progress_status.get('video_composed'): status_text.append('视频合成')
                
                if status_text:
                    self.log_output_bottom.appendPlainText(f"   已完成: {', '.join(status_text)}")
                else:
                    self.log_output_bottom.appendPlainText(f"   进度: 项目刚开始")
            
        except Exception as e:
            logger.error(f"加载项目数据失败: {e}")
            QMessageBox.critical(self, "错误", f"加载项目数据失败: {e}")
    
    def get_current_project_data(self):
        """获取当前项目数据"""
        try:
            # 获取文本内容
            original_text = self.storyboard_tab.text_input.toPlainText().strip()
            rewritten_text = self.storyboard_tab.output_text.toPlainText().strip()
            
            # 检查绘图设置中是否有生成的图片
            drawing_settings = self.ai_drawing_tab.get_current_settings()
            has_generated_images_in_drawing = bool(drawing_settings.get('generated_images', []))
            
            # 检查分镜数据中有图片的数量
            shots_with_images = 0
            total_shots = 0
            if self.shots_data:
                total_shots = len(self.shots_data)
                for shot in self.shots_data:
                    # 检查主图是否存在且文件确实存在
                    image_path = shot.get('image', '').strip()
                    if image_path:
                        # 构建完整路径检查文件是否存在
                        if hasattr(self, 'current_project_dir') and self.current_project_dir:
                            if os.path.isabs(image_path):
                                full_image_path = image_path
                            else:
                                full_image_path = os.path.join(self.current_project_dir, image_path)
                            
                            if os.path.exists(full_image_path):
                                shots_with_images += 1
                        elif os.path.exists(image_path):  # 如果是绝对路径且文件存在
                            shots_with_images += 1
            
            # 图片生成状态：绘图设置中有图片 或 所有分镜都有图片
            # 如果有分镜数据，则需要所有分镜都有图片才算完成；如果没有分镜，则检查绘图设置
            if total_shots > 0:
                has_generated_images = shots_with_images >= total_shots
            else:
                has_generated_images = has_generated_images_in_drawing
            
            # 获取进度状态
            progress_status = {
                'text_rewritten': bool(rewritten_text),
                'shots_generated': bool(self.shots_data),
                'images_generated': has_generated_images,
                'voices_generated': self._check_voices_generated(),  # 检查语音生成状态
                'video_composed': False     # TODO: 检查视频合成状态
            }
            
            # 生成项目描述
            description = ""
            if original_text:
                description = original_text[:100] + "..." if len(original_text) > 100 else original_text
            elif rewritten_text:
                description = rewritten_text[:100] + "..." if len(rewritten_text) > 100 else rewritten_text
            else:
                description = "空项目"
            
            # 从分镜表格收集当前数据
            current_shots_data = self._collect_shots_data_from_table()
            
            # 优先使用内存中的shots_data，因为它包含最新的图片更新
            # 只有当内存数据为空时才使用表格数据
            final_shots_data = self.shots_data if self.shots_data else (current_shots_data or [])
            
            # 获取配音设置
            voice_settings = self._get_current_voice_settings()
            
            # 获取工作流设置
            workflow_settings = self._get_current_workflow_settings()
            
            # 获取文本转镜头标签页设置
            storyboard_settings = self._get_current_storyboard_settings()
            
            project_data = {
                'project_name': self.current_project_name or '未命名项目',
                'original_text': original_text,
                'rewritten_text': rewritten_text,
                'shots_data': final_shots_data,
                'drawing_settings': drawing_settings,
                'voice_settings': voice_settings,
                'workflow_settings': workflow_settings,
                'storyboard_settings': storyboard_settings,
                'progress_status': progress_status,
                'description': description
            }
            
            # 添加图片生成进度的详细信息
            if total_shots > 0:
                image_progress_info = f"图片进度: {shots_with_images}/{total_shots}"
            else:
                image_progress_info = f"绘图设置图片: {len(drawing_settings.get('generated_images', []))}张"
            
            logger.info(f"收集项目数据: 原始文本({len(original_text)}字符), 改写文本({len(rewritten_text)}字符), 分镜({len(self.shots_data or [])}个), {image_progress_info}, 进度状态: {progress_status}")
            return project_data
            
        except Exception as e:
            logger.error(f"获取项目数据失败: {e}")
            return {}
    
    def _collect_shots_data_from_table(self):
        """从分镜表格收集当前数据"""
        try:
            if not hasattr(self, 'shots_table') or not self.shots_table:
                return None
                
            shots_data = []
            for row in range(self.shots_table.rowCount()):
                shot = {}
                
                # 收集各列数据
                columns = ['description', 'scene', 'role', 'prompt', 'image', 'video_prompt', 'audio', 'operation', 'alternative_images']
                for col, key in enumerate(columns):
                    if key == 'operation':  # 跳过操作列，它包含按钮而不是文本
                        continue
                    item = self.shots_table.item(row, col)
                    shot[key] = item.text() if item else ''
                
                shots_data.append(shot)
            
            logger.info(f"从分镜表格收集到 {len(shots_data)} 条数据")
            return shots_data
            
        except Exception as e:
            logger.error(f"获取项目数据失败: {e}")
            return None
    
    def _check_voices_generated(self):
        """检查语音生成状态"""
        try:
            # 检查分镜数据中是否有语音文件
            if not self.shots_data:
                return False
            
            voice_count = 0
            total_shots = len(self.shots_data)
            
            for shot in self.shots_data:
                # 检查语音文件路径
                voice_file = shot.get('voice_file', '')
                if voice_file and os.path.exists(voice_file):
                    voice_count += 1
            
            # 如果有超过一半的分镜有语音文件，认为语音已生成
            return voice_count > 0 and voice_count >= total_shots * 0.5
            
        except Exception as e:
            logger.error(f"检查语音生成状态失败: {e}")
            return False
    
    def _get_current_voice_settings(self):
        """获取当前配音设置"""
        try:
            # 从配置管理器获取默认TTS设置
            tts_config = self.config_manager.get_tts_config()
            
            # 获取分镜数据中的配音信息
            shots_voice_data = []
            if self.shots_data:
                for i, shot in enumerate(self.shots_data):
                    voice_info = {
                        'shot_index': i,
                        'text': shot.get('description', ''),
                        'voice_file': shot.get('audio', ''),
                        'voice_config': shot.get('voice_config', {}),
                        'subtitle_data': shot.get('subtitle_data', None)
                    }
                    shots_voice_data.append(voice_info)
            
            voice_settings = {
                'default_tts_config': tts_config,
                'shots_voice_data': shots_voice_data
            }
            
            logger.debug(f"收集配音设置: {len(shots_voice_data)}个分镜配音数据")
            return voice_settings
            
        except Exception as e:
            logger.error(f"获取配音设置失败: {e}")
            return {}
    
    def _get_current_workflow_settings(self):
        """获取当前工作流设置"""
        try:
            workflow_settings = {}
            
            # 从AI绘图标签页获取工作流设置
            if hasattr(self, 'ai_drawing_tab') and self.ai_drawing_tab:
                workflow_panel = self.ai_drawing_tab.get_workflow_panel()
                if workflow_panel:
                    workflow_settings = workflow_panel.get_current_settings()
            
            logger.debug(f"收集工作流设置: {workflow_settings}")
            return workflow_settings
            
        except Exception as e:
            logger.error(f"获取工作流设置失败: {e}")
            return {}
    
    def _get_current_storyboard_settings(self):
        """获取当前文本转镜头标签页设置"""
        try:
            storyboard_settings = {}
            
            # 从文本转镜头标签页获取设置
            if hasattr(self, 'storyboard_tab') and self.storyboard_tab:
                storyboard_settings = self.storyboard_tab.get_current_settings()
            
            logger.debug(f"收集文本转镜头设置: {storyboard_settings}")
            return storyboard_settings
            
        except Exception as e:
            logger.error(f"获取文本转镜头设置失败: {e}")
            return {}
    
    def _load_voice_settings(self, voice_settings):
        """加载配音设置"""
        try:
            if not voice_settings:
                return
            
            # 加载默认TTS配置
            default_tts_config = voice_settings.get('default_tts_config', {})
            if default_tts_config:
                # 更新配置管理器中的TTS设置
                for key, value in default_tts_config.items():
                    self.config_manager.set_tts_setting(key, value)
            
            # 加载分镜配音数据
            shots_voice_data = voice_settings.get('shots_voice_data', [])
            if shots_voice_data and self.shots_data:
                for voice_info in shots_voice_data:
                    shot_index = voice_info.get('shot_index', -1)
                    if 0 <= shot_index < len(self.shots_data):
                        # 更新分镜数据中的配音信息
                         if voice_info.get('voice_file'):
                             self.shots_data[shot_index]['audio'] = voice_info['voice_file']
                         if voice_info.get('voice_config'):
                             self.shots_data[shot_index]['voice_config'] = voice_info['voice_config']
                         if voice_info.get('subtitle_data'):
                             self.shots_data[shot_index]['subtitle_data'] = voice_info['subtitle_data']
            
            logger.info(f"配音设置已加载: {len(shots_voice_data)}个分镜配音数据")
            
        except Exception as e:
            logger.error(f"加载配音设置失败: {e}")
    
    def _load_workflow_settings(self, workflow_settings):
        """加载工作流设置"""
        try:
            if not workflow_settings:
                return
            
            # 加载到AI绘图标签页的工作流面板
            if hasattr(self, 'ai_drawing_tab') and self.ai_drawing_tab:
                workflow_panel = self.ai_drawing_tab.get_workflow_panel()
                if workflow_panel:
                    workflow_panel.load_settings(workflow_settings)
            
            logger.info("工作流设置已加载")
            
        except Exception as e:
            logger.error(f"加载工作流设置失败: {e}")
    
    def _load_storyboard_settings(self, storyboard_settings):
        """加载文本转镜头标签页设置"""
        try:
            if not storyboard_settings:
                return
            
            # 加载到文本转镜头标签页
            if hasattr(self, 'storyboard_tab') and self.storyboard_tab:
                self.storyboard_tab.load_settings(storyboard_settings)
            
            logger.info("文本转镜头设置已加载")
            
        except Exception as e:
            logger.error(f"加载文本转镜头设置失败: {e}")
    
    def set_current_project(self, project_name: str, project_description: str = ""):
        """设置当前项目信息
        
        Args:
            project_name: 项目名称
            project_description: 项目描述
        """
        self.current_project_name = project_name
        self.current_project_description = project_description
        
        # 更新窗口标题
        self.setWindowTitle(f"AI 视频生成系统 - {project_name}")
        
        # 更新storyboard_tab中的项目信息
        if hasattr(self.storyboard_tab, 'current_project_name'):
            self.storyboard_tab.current_project_name = project_name
            self.storyboard_tab.current_project_root = self.project_manager.get_project_path(project_name)
        
        logger.info(f"当前项目已设置: {project_name}")
    
    def clear_current_project(self):
        """清空当前项目状态"""
        try:
            # 清空文本输入
            self.storyboard_tab.text_input.clear()
            self.storyboard_tab.output_text.clear()
            
            # 清空storyboard_tab中的项目信息
            if hasattr(self.storyboard_tab, 'current_project_name'):
                self.storyboard_tab.current_project_name = None
                self.storyboard_tab.current_project_root = None
            
            # 清空分镜数据
            self.shots_data = []
            if hasattr(self, 'shots_table') and self.shots_table:
                self.shots_table.setRowCount(0)
            
            # 清空绘图设置
            if hasattr(self, 'ai_drawing_tab') and self.ai_drawing_tab:
                self.ai_drawing_tab.reset_to_default()
            
            # 清空其他状态
            self.current_project_name = None
            self.current_project_description = ""
            self.current_project_dir = None
            self.temp_rewrite_file = ""
            
            logger.info("当前项目状态已清空")
            
        except Exception as e:
            logger.error(f"清空项目状态失败: {e}")
    
    def has_unsaved_changes(self):
        """检查是否有未保存的更改"""
        try:
            # 简单检查：如果有文本输入或分镜数据，认为有更改
            has_text = bool(self.storyboard_tab.text_input.toPlainText().strip())
            has_rewrite = bool(self.storyboard_tab.output_text.toPlainText().strip())
            has_shots = bool(self.shots_data)
            
            return has_text or has_rewrite or has_shots
            
        except Exception as e:
            logger.error(f"检查未保存更改失败: {e}")
            return False
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, "关于", 
            "AI 视频生成系统\n\n"
            "版本: 1.0.0\n"
            "一个基于AI的视频内容生成工具\n\n"
            "功能包括：\n"
            "• 文本改写和分镜生成\n"
            "• AI绘图和配音\n"
            "• 视频合成和批量处理\n"
            "• 项目管理和工作流自动化"
        )
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            # 检查是否有未保存的更改
            if self.has_unsaved_changes():
                reply = QMessageBox.question(
                    self, '保存项目', 
                    '当前项目有未保存的更改，是否保存后退出？',
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    if not self.save_current_project():
                        event.ignore()  # 保存失败，取消关闭
                        return
                elif reply == QMessageBox.Cancel:
                    event.ignore()  # 用户取消关闭
                    return
            
            # 保存应用设置
            self.config_manager.save_config(self.app_settings)
            
            event.accept()
            
        except Exception as e:
            logger.error(f"关闭窗口时出错: {e}")
            event.accept()  # 即使出错也允许关闭

    def apply_stylesheet(self):
        # 优先加载QSS文件（Qt原生样式表格式）
        qss_path = os.path.join(os.path.dirname(__file__), '../../assets/styles.qss')
        qss_backup_path = os.path.join(os.path.dirname(__file__), '../../assets/style.qss')
        
        if os.path.exists(qss_path):
            with open(qss_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        elif os.path.exists(qss_backup_path):
            with open(qss_backup_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        else:
            # 默认样式
            self.setStyleSheet('''
                QWidget { font-family: "微软雅黑", Arial, sans-serif; font-size: 15px; }
                QMainWindow { background: #f6f8fa; }
                QPushButton { background: #1976d2; color: white; border-radius: 6px; padding: 6px 18px; font-weight: bold; }
                QPushButton:hover { background: #1565c0; }
            ''')

    def init_ui(self):
        # 主操作区（多标签页）
        self.tabs = QTabWidget()
        
        # 创建各个标签页
        self.storyboard_tab = StoryboardTab(self)
        self.ai_drawing_tab = AIDrawingTab(self)
        self.settings_tab = SettingsTab(self)
        
        # 创建分镜设置标签页
        self.shots_settings_tab = self.create_shots_settings_tab()
        
        # 添加标签页到主标签控件
        self.tabs.addTab(self.storyboard_tab, "文本转分镜")
        self.tabs.addTab(self.shots_settings_tab, "分镜设置")
        self.ai_voice_tab = self.create_ai_voice_tab()
        self.tabs.addTab(self.ai_voice_tab, "AI 配音")
        self.tabs.addTab(self.ai_drawing_tab, "绘图设置")
        self.tabs.addTab(QLabel("视频合成功能区 (待开发)"), "视频合成")
        self.tabs.addTab(QLabel("批量处理功能区 (待开发)"), "批量处理")
        self.tabs.addTab(self.settings_tab, "设置")
        
        # 设置标签页为主窗口的中央部件
        self.setCentralWidget(self.tabs)
        
        # 初始化配音管理器（在UI组件创建之后）
        self.voice_manager = VoiceManager(self)
        
        # 连接配音管理器信号
        if hasattr(self, 'voice_progress_bar') and hasattr(self, 'voice_status_label'):
            self.voice_manager.progress_updated.connect(self.voice_progress_bar.setValue)
            self.voice_manager.status_updated.connect(self.voice_status_label.setText)
        
        # 加载语音模型列表
        if hasattr(self, 'voice_model_combo'):
            self.load_voice_models()



    def init_shots_table_ui(self):
        """初始化分镜表格UI"""
        # 确保 self.shots_table_widget 是一个 QWidget 实例
        if not hasattr(self, 'shots_table_widget') or self.shots_table_widget is None:
            self.shots_table_widget = QWidget() # 创建一个容器Widget
            logger.info("MainWindow: shots_table_widget (container) was None, created in init_shots_table_ui.")
        elif not isinstance(self.shots_table_widget, QWidget):
            logger.warning(f"MainWindow: self.shots_table_widget was type {type(self.shots_table_widget)}, expected QWidget. Recreating.")
            self.shots_table_widget = QWidget()

        # 确保 self.shots_table_widget 有一个布局，如果已经有，则使用现有的
        if self.shots_table_widget.layout() is None:
            layout = QVBoxLayout(self.shots_table_widget) # 将布局设置给 self.shots_table_widget
            # self.shots_table_widget.setLayout(layout) # QVBoxLayout构造时已设置
        else:
            layout = self.shots_table_widget.layout()
            # 清理现有布局，以防重复添加内容，但保留布局本身
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    # widget.deleteLater() # 避免过早删除
        
        # 添加标题
        title_label = QLabel("分镜列表")
        title_label.setFont(QFont("微软雅黑", 14, QFont.Bold))
        title_label.setProperty("class", "title-label")
        layout.addWidget(title_label)
        
        # 添加批量操作按钮区域
        batch_widget = QWidget()
        batch_layout = QHBoxLayout(batch_widget)
        batch_layout.setContentsMargins(10, 5, 10, 5)
        batch_layout.setSpacing(10)
        
        # 批量生图按钮
        self.batch_draw_btn = QPushButton("批量生图")
        self.batch_draw_btn.setProperty("class", "draw-button")
        self.batch_draw_btn.setMinimumSize(100, 40)
        self.batch_draw_btn.setMaximumSize(120, 45)
        self.batch_draw_btn.clicked.connect(self.handle_batch_draw)
        batch_layout.addWidget(self.batch_draw_btn)
        
        # 停止批量按钮
        self.stop_batch_btn = QPushButton("停止批量")
        self.stop_batch_btn.setProperty("class", "voice-button")
        self.stop_batch_btn.setMinimumSize(100, 40)
        self.stop_batch_btn.setMaximumSize(120, 45)
        self.stop_batch_btn.setEnabled(False)  # 初始状态禁用
        self.stop_batch_btn.clicked.connect(self.handle_stop_batch)
        batch_layout.addWidget(self.stop_batch_btn)
        
        # 进度显示标签
        self.batch_progress_label = QLabel("进度: 0/0")
        self.batch_progress_label.setFont(QFont("微软雅黑", 12))
        self.batch_progress_label.setProperty("class", "status-label")
        batch_layout.addWidget(self.batch_progress_label)
        
        # 跳过已有图片选项
        self.skip_existing_checkbox = QCheckBox("跳过已有图片")
        self.skip_existing_checkbox.setChecked(True)  # 默认勾选
        self.skip_existing_checkbox.setFont(QFont("微软雅黑", 10))
        batch_layout.addWidget(self.skip_existing_checkbox)
        
        # 添加弹性空间
        batch_layout.addStretch()
        
        layout.addWidget(batch_widget)
        
        # 创建表格
        self.shots_table = QTableWidget()
        self.shots_table.setFont(QFont("微软雅黑", 12))
        # 表格样式已在CSS文件中定义
        self.shots_table.setToolTip("分镜表格，可编辑和复制内容")
        
        # 定义列（删除编号列）
        columns = ('文案', '分镜', '角色', '提示词', '主图', '视频提示词', '音效', '操作', '备选图片')
        self.shots_table.setColumnCount(len(columns))
        self.shots_table.setHorizontalHeaderLabels(columns)
        
        # 设置列宽
        header = self.shots_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # 文案列
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # 分镜列
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # 角色列
        header.setSectionResizeMode(3, QHeaderView.Interactive)  # 提示词列
        header.setSectionResizeMode(4, QHeaderView.Interactive)  # 主图列
        header.setSectionResizeMode(5, QHeaderView.Interactive)  # 视频提示词列
        header.setSectionResizeMode(6, QHeaderView.Interactive)  # 音效列
        header.setSectionResizeMode(7, QHeaderView.Fixed)  # 操作列固定宽度
        header.setSectionResizeMode(8, QHeaderView.Interactive)  # 备选图片列
        header.setStretchLastSection(True)  # 最后一列拉伸
        
        # 设置操作列的固定宽度以容纳三个按钮
        self.shots_table.setColumnWidth(7, 100)
        
        # 设置主图列的宽度，使用较大尺寸
        self.shots_table.setColumnWidth(4, 220)
        
        # 设置备选图片列的宽度，使用较小尺寸但足够显示图片
        self.shots_table.setColumnWidth(8, 280)
        
        # 设置行高，确保能容纳图片显示（包括备选图片的多行布局）
        self.shots_table.verticalHeader().setDefaultSectionSize(260)
        
        # 设置图片代理，传入MainWindow实例以便访问项目信息
        self.shots_table.setItemDelegateForColumn(4, ImageDelegate(self))
        self.shots_table.setItemDelegateForColumn(8, ImageDelegate(self))
        
        # 设置表格大小策略，让它能够扩展填满可用空间
        self.shots_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout.addWidget(self.shots_table)
        
        # 设置容器的大小策略
        self.shots_table_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 初始状态隐藏表格，只有在需要时才显示
        self.shots_table_widget.setVisible(False)
        
        self.shots_table_widget.setLayout(layout)

    def switch_to_shots_table_view(self):
        """切换到分镜表格显示模式 - 占满整个界面"""
        try:
            # 如果已经在分镜列表视图，直接返回
            if self.current_view_state == "shots_list":
                return
                
            # 如果shots_table_widget还没有创建或不可见，确保它被正确设置
            if self.shots_table_widget is None or not self.shots_table_widget.isVisible():
                if self.shots_table_widget is None:
                    # init_shots_table_ui 应该已经创建了 self.shots_table 和 self.shots_table_widget
                    # 但如果因为某些原因没有，这里可以尝试再次调用，或者记录一个更严重的错误
                    logger.warning("switch_to_shots_table_view: shots_table_widget is None, attempting to re-initialize.")
                    self.init_shots_table_ui() # 确保表格UI已初始化
                
                # 确保 self.shots_table_widget 是一个 QWidget 实例
                if not isinstance(self.shots_table_widget, QWidget):
                    logger.error("switch_to_shots_table_view: self.shots_table_widget is not a QWidget after init. Recreating.")
                    # 这是一个异常情况，可能需要更复杂的处理
                    # 简单处理：重新创建一个QWidget作为容器
                    self.shots_table_widget = QWidget()
                    # 重新将 self.shots_table 放入新的容器中
                    if self.shots_table is not None:
                        layout = QVBoxLayout(self.shots_table_widget)
                        layout.addWidget(self.shots_table)
                        self.shots_table_widget.setLayout(layout)
                    else:
                        logger.error("switch_to_shots_table_view: self.shots_table is also None. Cannot proceed.")
                        return # 无法继续，表格未正确创建
            
            # 确保 self.shots_table 存在并且是 QTableWidget
            if self.shots_table is None or not isinstance(self.shots_table, QTableWidget):
                logger.error("switch_to_shots_table_view: self.shots_table is not a QTableWidget. Cannot proceed.")
                return
            
            # 显示分镜表格
            self.shots_table_widget.setVisible(True)
            
            # 如果back_to_edit_btn还没有创建，先创建它
            if self.back_to_edit_btn is None:
                self.back_to_edit_btn = QPushButton("返回编辑")
                self.back_to_edit_btn.clicked.connect(self.handle_back_button_click)
            
            # 获取主布局
            main_widget = self.centralWidget()
            main_layout = main_widget.layout()
            
            # 保存原始的tabs组件以便恢复（删除左侧导航栏后不再有splitter）
            if not hasattr(self, 'original_tabs_widget'):
                # 找到tabs组件（第二个widget，索引为1）
                for i in range(main_layout.count()):
                    item = main_layout.itemAt(i)
                    if item and item.widget() == self.tabs:
                        self.original_tabs_widget = item.widget()
                        break
            
            # 移除tabs组件
            if hasattr(self, 'original_tabs_widget'):
                main_layout.removeWidget(self.original_tabs_widget)
                self.original_tabs_widget.setParent(None)
            
            # 创建或重用全屏分镜显示区域
            if not hasattr(self, 'fullscreen_shots_widget') or self.fullscreen_shots_widget is None:
                self.fullscreen_shots_widget = QWidget()
                fullscreen_layout = QVBoxLayout()
                self.fullscreen_shots_widget.setLayout(fullscreen_layout)
            else:
                fullscreen_layout = self.fullscreen_shots_widget.layout()
                # 清空现有内容
                while fullscreen_layout.count():
                    child = fullscreen_layout.takeAt(0)
                    if child.widget():
                        child.widget().setParent(None)
            
            # 添加顶部功能选择按键（标签页导航栏）
            tabs_header = QWidget()
            tabs_header_layout = QHBoxLayout()
            
            # 创建功能按钮
            def create_tab_callback(index):
                def callback():
                    # 先切换回默认视图，然后切换到指定标签页
                    self.switch_to_default_view()
                    self.tabs.setCurrentIndex(index)
                    # 为所有标签页显示返回按钮
                    self.show_back_button_for_tab(index)
                return callback
            
            tab_buttons = [
                ("文本转分镜", create_tab_callback(0)),
                ("AI 配音", create_tab_callback(1)),
                ("设置", create_tab_callback(2)),
                ("绘图设置", create_tab_callback(3)),
                ("视频合成", create_tab_callback(4)),
                ("批量处理", create_tab_callback(5))
            ]
            
            for text, callback in tab_buttons:
                btn = QPushButton(text)
                btn.setProperty("class", "nav-button")
                btn.clicked.connect(callback)
                tabs_header_layout.addWidget(btn)
            
            # 添加返回按钮到顶部栏右侧
            tabs_header_layout.addStretch()
            # 设置当前状态为分镜列表，显示并设置返回按钮
            self.current_view_state = "shots_list"
            self.back_to_edit_btn.setText("返回编辑")
            self.back_to_edit_btn.setVisible(True)
            self.back_to_edit_btn.setProperty("class", "back-button")
            # 将返回按钮添加到顶部栏而不是tabs_header
            self.top_layout.addWidget(self.back_to_edit_btn)
            tabs_header.setLayout(tabs_header_layout)
            fullscreen_layout.addWidget(tabs_header)
            
            # 创建带滚动条的分镜表格区域
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            # 确保shots_table有足够的大小来触发滚动条
            self.shots_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # 设置表格的最小尺寸，确保内容超出时能显示滚动条
            self.shots_table.setMinimumSize(800, 600)
            
            scroll_area.setWidget(self.shots_table_widget)
            
            # 添加滚动区域（占据主要空间）
            fullscreen_layout.addWidget(scroll_area, 1)
            
            # 将全屏分镜区域添加到主布局
            main_layout.insertWidget(1, self.fullscreen_shots_widget)
            
            # 同步输出文本内容到紧凑显示区域（如果存在）
            if hasattr(self, 'compact_output_text') and self.compact_output_text is not None and self.output_text is not None:
                self.compact_output_text.setPlainText(self.output_text.toPlainText())
            
            logger.info("已切换到全屏分镜表格显示模式")
        except Exception as e:
            logger.error(f"切换到全屏分镜表格显示模式时发生错误: {e}")
    
    def switch_to_default_view(self):
        """切换回默认显示模式"""
        try:
            # 如果已经在默认视图，直接返回
            if self.current_view_state == "default":
                return
                
            # 获取主布局
            main_widget = self.centralWidget()
            main_layout = main_widget.layout()
            
            # 临时保存bottom_bar的引用
            bottom_bar_ref = self.bottom_bar
            
            # 移除全屏分镜显示区域
            widgets_to_remove = []
            for i in range(main_layout.count()):
                item = main_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    # 保留top_bar和bottom_bar，移除其他widget
                    if widget != self.top_bar and widget != self.bottom_bar:
                        # 检查是否是全屏分镜区域（不是原始的tabs组件）
                        if not hasattr(self, 'original_tabs_widget') or widget != self.original_tabs_widget:
                            widgets_to_remove.append(widget)
            
            # 移除标记的widgets
            for widget in widgets_to_remove:
                main_layout.removeWidget(widget)
                # 如果是全屏分镜组件，先保存shots_table_widget
                if hasattr(self, 'fullscreen_shots_widget') and widget == self.fullscreen_shots_widget:
                    # 在删除fullscreen_shots_widget之前，先将shots_table_widget从scroll_area中移除
                    if hasattr(self, 'shots_table_widget') and self.shots_table_widget is not None:
                        # 找到scroll_area并移除shots_table_widget
                        layout = self.fullscreen_shots_widget.layout()
                        if layout:
                            for i in range(layout.count()):
                                item = layout.itemAt(i)
                                if item and item.widget() and isinstance(item.widget(), QScrollArea):
                                    scroll_area = item.widget()
                                    if scroll_area.widget() == self.shots_table_widget:
                                        scroll_area.takeWidget()  # 移除但不删除shots_table_widget
                                        self.shots_table_widget.setParent(None)  # 设置父组件为None
                                    break
                    self.fullscreen_shots_widget = None
                widget.deleteLater()
            
            # 确保布局中只有top_bar、splitter_main和bottom_bar
            # 先移除bottom_bar（如果存在）
            if bottom_bar_ref.parent():
                main_layout.removeWidget(bottom_bar_ref)
            
            # 恢复原始的tabs组件
            if hasattr(self, 'original_tabs_widget'):
                # 检查tabs组件是否已经在布局中
                tabs_in_layout = False
                for i in range(main_layout.count()):
                    item = main_layout.itemAt(i)
                    if item and item.widget() == self.original_tabs_widget:
                        tabs_in_layout = True
                        break
                
                if not tabs_in_layout:
                    main_layout.insertWidget(1, self.original_tabs_widget)
            
            # 重新添加bottom_bar到正确位置
            main_layout.addWidget(bottom_bar_ref)
            
            # 恢复右侧区域的原始状态
            layout = self.right_stack_widget.layout()
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().setParent(None)
            
            # 添加默认右侧区域
            layout.addWidget(self.default_right_widget)
            
            # 从顶部栏移除返回按钮
            if hasattr(self, 'back_to_edit_btn') and self.back_to_edit_btn is not None:
                # 从顶部栏移除返回按钮
                if hasattr(self, 'top_layout') and self.top_layout is not None:
                    for i in range(self.top_layout.count()):
                        item = self.top_layout.itemAt(i)
                        if item and item.widget() == self.back_to_edit_btn:
                            self.top_layout.removeWidget(self.back_to_edit_btn)
                            break
                self.back_to_edit_btn.setVisible(False)
            
            # 设置当前状态为默认视图
            self.current_view_state = "default"
            
            logger.info("已切换回默认显示模式")
        except Exception as e:
            logger.error(f"切换回默认显示模式时发生错误: {e}")
    
    def handle_back_button_click(self):
        """处理返回按钮点击事件"""
        try:
            if self.current_view_state == "shots_list":
                # 当前在分镜列表，点击返回编辑，回到默认视图并显示"返回分镜列表"按钮
                self.switch_to_default_view()
                
                # 确保返回按钮存在并正确显示
                if self.back_to_edit_btn is not None:
                    self.back_to_edit_btn.setText("返回分镜列表")
                    self.back_to_edit_btn.setVisible(True)
                    # 设置按钮样式
                    self.back_to_edit_btn.setProperty("class", "back-button")
                    # 将按钮添加到顶部栏的右侧
                    top_layout = self.top_bar.layout()
                    if top_layout is not None:
                        # 移除之前可能存在的返回按钮
                        for i in range(top_layout.count()):
                            item = top_layout.itemAt(i)
                            if item and item.widget() == self.back_to_edit_btn:
                                top_layout.removeWidget(self.back_to_edit_btn)
                                break
                        # 在stretch之前添加返回按钮
                        top_layout.insertWidget(top_layout.count(), self.back_to_edit_btn)
                
                logger.info("从分镜列表返回到编辑界面")
            elif self.current_view_state == "default":
                # 当前在默认界面，点击返回分镜列表，回到分镜列表
                self.switch_to_shots_table_view()
                # 确保按钮状态正确设置
                if self.back_to_edit_btn is not None:
                    self.back_to_edit_btn.setText("返回编辑")
                    self.back_to_edit_btn.setVisible(True)
                logger.info("从编辑界面返回到分镜列表")
            else:
                # 从其他标签页返回分镜列表
                self.switch_to_shots_table_view()
                # 更新按钮状态
                if self.back_to_edit_btn is not None:
                    self.back_to_edit_btn.setText("返回编辑")
                    self.back_to_edit_btn.setVisible(True)
        except Exception as e:
            logger.error(f"处理返回按钮点击时发生错误: {e}")
    
    def show_back_button_for_tab(self, tab_index):
        """为指定标签页显示返回按钮"""
        try:
            # 如果back_to_edit_btn还没有创建，先创建它
            if self.back_to_edit_btn is None:
                self.back_to_edit_btn = QPushButton("返回分镜列表")
                self.back_to_edit_btn.clicked.connect(self.handle_back_button_click)
            
            # 设置返回按钮文本为返回分镜列表
            self.back_to_edit_btn.setText("返回分镜列表")
            
            # 设置当前视图状态为标签页模式
            self.current_view_state = f"tab_{tab_index}"
            
            self.back_to_edit_btn.setVisible(True)
            self.back_to_edit_btn.setProperty("class", "back-button")
            
            # 确保返回按钮在顶部栏的正确位置
            top_layout = self.top_bar.layout()
            if top_layout is not None:
                # 移除之前可能存在的返回按钮
                for i in range(top_layout.count()):
                    item = top_layout.itemAt(i)
                    if item and item.widget() == self.back_to_edit_btn:
                        top_layout.removeWidget(self.back_to_edit_btn)
                        break
                
                # 在stretch之前添加返回按钮
                top_layout.insertWidget(top_layout.count(), self.back_to_edit_btn)
            
        except Exception as e:
            logger.error(f"显示返回按钮时发生错误: {e}")

    def _load_app_settings(self):
        try:
            if os.path.exists(self.SETTINGS_FILE_PATH):
                with open(self.SETTINGS_FILE_PATH, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    logger.info(f"App settings loaded from {self.SETTINGS_FILE_PATH}")
                    return settings
            logger.info(f"App settings file not found at {self.SETTINGS_FILE_PATH}. Returning empty settings.")
            return {}
        except Exception as e:
            logger.error(f"Error loading app settings from {self.SETTINGS_FILE_PATH}: {e}")
            QMessageBox.warning(self, "设置加载错误", f"无法加载应用设置: {e}")
            return {}

    def _save_app_settings(self):
        try:
            with open(self.SETTINGS_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.app_settings, f, indent=4, ensure_ascii=False)
            logger.info(f"App settings saved to {self.SETTINGS_FILE_PATH}")
            return True
        except Exception as e:
            logger.error(f"Error saving app settings to {self.SETTINGS_FILE_PATH}: {e}")
            QMessageBox.critical(self, "设置保存错误", f"保存应用设置失败: {e}")
            return False

    def _save_general_settings_action(self):
        logger.debug("Attempting to save general settings.")
        new_output_dir = self.comfyui_output_dir_input.text().strip()
        
        if new_output_dir and not os.path.isdir(new_output_dir):
            QMessageBox.warning(self, "无效路径", f"ComfyUI 输出目录 '{new_output_dir}' 不是一个有效的目录。请检查路径或留空。")
            logger.warning(f"Invalid ComfyUI output directory provided: {new_output_dir}")
            return

        self.app_settings['comfyui_output_dir'] = new_output_dir
        self.comfyui_output_dir = new_output_dir # Update the instance variable too
        if self._save_app_settings():
            QMessageBox.information(self, "成功", "通用设置已保存。")

    def handle_generate_image_btn(self):
        prompt = self.image_desc_input.text().strip()
        if not prompt:
            QMessageBox.warning(self, "提示", "请输入图片描述（prompt）！")
            return

        # 初始化图像生成服务（如果尚未初始化）
        if not hasattr(self, 'image_generation_service') or not self.image_generation_service:
            self._init_image_generation_service()
        
        # 检查图像生成服务是否可用
        if not self.image_generation_service:
            QMessageBox.warning(self, "服务不可用", "图像生成服务初始化失败，请检查配置。")
            return
        
        if not self.image_generation_service.is_service_available():
            QMessageBox.warning(self, "服务不可用", "当前没有可用的图像生成引擎。Pollinations AI 服务可能暂时不可用，ComfyUI 也未连接。")
            return

        comfyui_base_output_dir = self.app_settings.get('comfyui_output_dir', '').strip()
        if not comfyui_base_output_dir:
            QMessageBox.warning(self, "配置缺失", "请先在“设置”中配置 ComfyUI 输出目录的绝对路径。")
            self.generated_image_status_label.setText("错误：ComfyUI 输出目录未配置。")
            logger.warning("ComfyUI output directory not configured.")
            self.tabs.setCurrentWidget(self.settings_widget) # Switch to settings tab
            return
        if not os.path.isdir(comfyui_base_output_dir):
            QMessageBox.warning(self, "配置错误", f"配置的 ComfyUI 输出目录 '{comfyui_base_output_dir}' 无效或不存在。请在“设置”中更正。")
            self.generated_image_status_label.setText(f"错误：ComfyUI 输出目录 '{comfyui_base_output_dir}' 无效。")
            logger.error(f"Configured ComfyUI output directory is invalid: {comfyui_base_output_dir}")
            self.tabs.setCurrentWidget(self.settings_widget) # Switch to settings tab
            return

        # 检查是否已连接到 ComfyUI
        if not hasattr(self, 'comfyui_client') or not self.comfyui_client:
            QMessageBox.warning(self, "提示", "请先连接到 ComfyUI！")
            return
        
        # 获取当前选择的工作流
        current_workflow = self.workflow_panel.get_current_workflow_name()
        if current_workflow in ["无可用工作流", "加载失败", "", "无工作流目录"]:
            QMessageBox.warning(self, "警告", "请选择有效的工作流！")
            return
        
        # 获取工作流参数
        workflow_params = self.workflow_panel.get_current_workflow_parameters()
        
        self.generated_image_status_label.setText("正在生成图片，请稍候...")
        self.generate_image_btn.setEnabled(False)
        
        # 在新线程中生成图片
        from gui.image_generation_thread import ImageGenerationThread
        self.image_generation_thread = ImageGenerationThread(
            prompt=prompt,
            workflow_id=current_workflow,
            parameters=workflow_params,
            project_manager=self.project_manager,
            current_project_name=self.current_project_name
        )
        self.image_generation_thread.set_image_service(self.image_generation_service)
        self.image_generation_thread.image_generated.connect(self.on_image_generated)
        self.image_generation_thread.generation_failed.connect(self.on_image_generation_error)
        self.image_generation_thread.start()
        return  # 退出方法，等待线程完成
        
        # 以下代码将被线程处理替代
        try:
            image_paths = []  # 占位符
            if image_paths and image_paths[0] and not image_paths[0].startswith("ERROR"):
                relative_image_path = image_paths[0]
                # Ensure relative_image_path doesn't start with a slash if comfyui_base_output_dir is a drive root
                if os.path.isabs(relative_image_path):
                    absolute_image_path = relative_image_path
                    logger.warning(f"Received absolute path from ComfyUIClient: {relative_image_path}. Using as is.")
                else:
                    cleaned_relative_path = relative_image_path.lstrip('\\/')
                    absolute_image_path = os.path.join(comfyui_base_output_dir, cleaned_relative_path)
                absolute_image_path = os.path.normpath(absolute_image_path)

                logger.info(f"Attempting to load image from: {absolute_image_path}")
                if os.path.exists(absolute_image_path):
                    # 添加图片到图片库
                    self.add_image_to_gallery(absolute_image_path, prompt)
                    self.generated_image_status_label.setText(f"图片已生成并添加到图片库，共 {len(self.generated_images)} 张图片")
                else:
                    self.generated_image_status_label.setText(f"图片已生成，但最终路径无效：{absolute_image_path}")
                    logger.error(f"最终图片路径无效: {absolute_image_path}. Base dir: '{comfyui_base_output_dir}', Relative path: '{relative_image_path}'")
            elif image_paths and image_paths[0]: # This means image_paths[0] starts with "ERROR"
                self.generated_image_status_label.setText(f"生成失败：{image_paths[0]}")
            else:
                self.generated_image_status_label.setText("生成失败：未知错误，未返回图片路径。")
        except Exception as e:
            self.generated_image_status_label.setText(f"生成图片时发生错误：{e}")
            logger.exception("生成图片时发生错误")
    
    def on_image_generated(self, image_paths):
        """图片生成成功的回调"""
        try:
            if image_paths and image_paths[0]:
                absolute_image_path = image_paths[0]
                
                logger.info(f"Attempting to load image from: {absolute_image_path}")
                if os.path.exists(absolute_image_path):
                    # 添加图片到图片库
                    prompt = self.image_desc_input.text().strip()
                    self.add_image_to_gallery(absolute_image_path, prompt)
                    engine_name = self.ai_drawing_tab.get_current_settings().get('selected_engine', '未知')
                    self.generated_image_status_label.setText(f"图片已生成并添加到图片库（引擎：{engine_name}），共 {len(self.generated_images)} 张图片")
                else:
                    self.generated_image_status_label.setText(f"图片已生成，但路径无效：{absolute_image_path}")
                    logger.error(f"图片路径无效: {absolute_image_path}")
            else:
                self.generated_image_status_label.setText("生成失败：未返回图片路径。")
        except Exception as e:
            self.generated_image_status_label.setText(f"处理生成的图片时发生错误：{e}")
            logger.exception("处理生成的图片时发生错误")
        finally:
            self.generate_image_btn.setEnabled(True)
    
    def on_image_generation_error(self, error_message):
        """图片生成错误的回调"""
        self.generated_image_status_label.setText(f"生成失败：{error_message}")
        self.generate_image_btn.setEnabled(True)
        logger.error(f"图片生成失败: {error_message}")

    def add_image_to_gallery(self, image_path, prompt):
        """添加图片到图片库"""
        try:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                logger.error(f"无法加载图片: {image_path}")
                return
            
            # 创建图片信息字典
            image_info = {
                'path': image_path,
                'prompt': prompt,
                'timestamp': QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')
            }
            self.generated_images.append(image_info)
            
            # 创建图片显示控件
            image_widget = QWidget()
            image_layout = QVBoxLayout(image_widget)
            image_layout.setContentsMargins(5, 5, 5, 5)
            
            # 图片标签
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignCenter)
            # 缩放图片到合适大小
            scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
            image_label.setProperty("class", "image-label")
            image_label.setFixedSize(204, 204)
            
            # 设置点击事件
            image_index = len(self.generated_images) - 1
            image_label.mousePressEvent = lambda event, idx=image_index: self.select_image(idx)
            
            # 提示词标签
            prompt_label = QLabel(prompt[:50] + "..." if len(prompt) > 50 else prompt)
            prompt_label.setWordWrap(True)
            prompt_label.setAlignment(Qt.AlignCenter)
            prompt_label.setProperty("class", "prompt-label")
            prompt_label.setMaximumWidth(200)
            
            # 时间标签
            time_label = QLabel(image_info['timestamp'])
            time_label.setAlignment(Qt.AlignCenter)
            time_label.setProperty("class", "time-label")
            
            image_layout.addWidget(image_label)
            image_layout.addWidget(prompt_label)
            image_layout.addWidget(time_label)
            
            # 计算网格位置
            row = len(self.generated_images) // 3
            col = (len(self.generated_images) - 1) % 3
            
            self.image_gallery_layout.addWidget(image_widget, row, col)
            
            # 自动选中最新生成的图片
            self.select_image(image_index)
            
            logger.info(f"图片已添加到图片库: {image_path}")
            
        except Exception as e:
            logger.error(f"添加图片到图片库时发生错误: {e}")
    
    def select_image(self, index):
        """选择图片"""
        if 0 <= index < len(self.generated_images):
            # 取消之前选中的图片的高亮
            if self.selected_image_index >= 0:
                self.update_image_selection_style(self.selected_image_index, False)
            
            # 设置新选中的图片
            self.selected_image_index = index
            self.update_image_selection_style(index, True)
            
            selected_image = self.generated_images[index]
            self.generated_image_status_label.setText(
                f"已选中第 {index + 1} 张图片 | 提示词: {selected_image['prompt'][:30]}... | 生成时间: {selected_image['timestamp']}"
            )
            logger.info(f"选中图片: {selected_image['path']}")
    
    def update_image_selection_style(self, index, selected):
        """更新图片选中状态的样式"""
        try:
            row = index // 3
            col = index % 3
            widget = self.image_gallery_layout.itemAtPosition(row, col)
            if widget and widget.widget():
                image_widget = widget.widget()
                image_label = image_widget.layout().itemAt(0).widget()
                if selected:
                    image_label.setProperty("class", "image-label-selected")
                else:
                    image_label.setProperty("class", "image-label")
        except Exception as e:
            logger.error(f"更新图片选中样式时发生错误: {e}")
    

    
    def get_selected_image_path(self):
        """获取当前选中的图片路径"""
        if 0 <= self.selected_image_index < len(self.generated_images):
            return self.generated_images[self.selected_image_index]['path']
        return None
    def apply_selected_image_to_shot(self):
        """将选中的图片应用到当前分镜"""
        try:
            # 检查是否有选中的图片
            if self.selected_image_index < 0 or self.selected_image_index >= len(self.generated_images):
                QMessageBox.warning(self, "警告", "请先选择一张图片！")
                return
            
            # 检查是否有当前分镜
            if not hasattr(self, 'current_shot_index') or self.current_shot_index < 0:
                QMessageBox.warning(self, "警告", "请先选择一个分镜！")
                return
            
            selected_image = self.generated_images[self.selected_image_index]
            image_path = selected_image['path']
            
            # 转换为相对路径
            if hasattr(self, 'current_project_dir') and self.current_project_dir:
                try:
                    relative_path = os.path.relpath(image_path, self.current_project_dir)
                    # 使用系统正确的路径分隔符，不强制转换
                    relative_path = os.path.normpath(relative_path)
                except ValueError:
                    # 如果无法转换为相对路径，使用绝对路径
                    relative_path = image_path
            else:
                relative_path = image_path
            
            # 更新分镜数据
            if hasattr(self, 'shots_data') and self.shots_data:
                shot_index = self.current_shot_index
                if 0 <= shot_index < len(self.shots_data):
                    shot = self.shots_data[shot_index]
                    
                    # 如果主图为空，设置为主图
                    if not shot.get('image', '').strip():
                        shot['image'] = relative_path
                        QMessageBox.information(self, "成功", f"已将图片设置为第 {shot_index + 1} 个分镜的主图！")
                    else:
                        # 否则添加到备选图片
                        alternative_images = shot.get('alternative_images', '')
                        if alternative_images:
                            # 如果已有备选图片，追加新图片
                            if relative_path not in alternative_images:
                                shot['alternative_images'] = alternative_images + ',' + relative_path
                                QMessageBox.information(self, "成功", f"已将图片添加到第 {shot_index + 1} 个分镜的备选图片！")
                            else:
                                QMessageBox.information(self, "提示", "该图片已存在于备选图片中！")
                        else:
                            # 如果没有备选图片，直接设置
                            shot['alternative_images'] = relative_path
                            QMessageBox.information(self, "成功", f"已将图片添加到第 {shot_index + 1} 个分镜的备选图片！")
                    
                    # 刷新分镜表格显示
                    self.refresh_shots_table()
                    
                    # 保存项目
                    if hasattr(self, 'save_project'):
                        self.save_project()
                    
                    logger.info(f"已将图片应用到分镜 {shot_index + 1}: {relative_path}")
                else:
                    QMessageBox.warning(self, "错误", "分镜索引超出范围！")
            else:
                QMessageBox.warning(self, "错误", "没有加载分镜数据！")
                
        except Exception as e:
            logger.error(f"应用图片到分镜时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"应用图片到分镜时发生错误: {str(e)}")


    def connect_to_comfyui(self):
        comfyui_url = self.comfyui_url_input.text().strip()
        if not comfyui_url:
            QMessageBox.warning(self, "警告", "请输入 ComfyUI 地址！")
            logger.warning("ComfyUI 地址为空，无法连接。")
            return

        # 确保 URL 格式正确
        if not (comfyui_url.startswith("http://") or comfyui_url.startswith("https://")):
            comfyui_url = "http://" + comfyui_url
            self.comfyui_url_input.setText(comfyui_url) # 更新输入框显示

        try:
            url_q = QUrl(comfyui_url)
            if not url_q.isValid():
                QMessageBox.critical(self, "错误", f"无效的 ComfyUI 地址: {comfyui_url}")
                logger.error(f"无效的 ComfyUI 地址: {comfyui_url}")
                return

            logger.info(f"尝试连接到 ComfyUI: {comfyui_url}")
            
            # 初始化ComfyUI客户端
            try:
                from models.comfyui_client import ComfyUIClient
                self.comfyui_client = ComfyUIClient(comfyui_url, workflows_dir=self.workflows_dir)
                logger.info(f"ComfyUI客户端初始化成功: {comfyui_url}")
                QMessageBox.information(self, "连接成功", f"已成功连接到 ComfyUI: {comfyui_url}")
            except Exception as client_error:
                logger.error(f"初始化ComfyUI客户端失败: {client_error}")
                QMessageBox.critical(self, "连接失败", f"无法连接到 ComfyUI: {client_error}")

        except Exception as e:
            QMessageBox.critical(self, "连接错误", f"连接 ComfyUI 时发生错误: {e}")
            logger.error(f"连接 ComfyUI 时发生错误: {e}")

    def on_js_console_message(self, level, message, lineNumber, sourceID):
        # 将 QWebEnginePage 的日志级别映射到 Python logging 模块的级别
        log_level = logging.DEBUG
        if level == 0: # QWebEnginePage.InfoMessageLevel
            log_level = logging.INFO
        elif level == 1: # QWebEnginePage.WarningMessageLevel
            log_level = logging.WARNING
        elif level == 2: # QWebEnginePage.ErrorMessageLevel
            log_level = logging.ERROR
        logger.log(log_level, f"JS Console ({sourceID}:{lineNumber}): {message}")

    def init_settings_ui(self):
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
        self.model_type_combo_settings.addItems(["tongyi", "deepseek", "其他"])

        model_form.addRow("大模型名称：", self.model_name_input)
        model_form.addRow("模型API类型：", self.model_type_combo_settings)
        model_form.addRow("大模型 API 地址：", self.model_url_input)
        model_form.addRow("大模型 API KEY：", self.model_key_input)
        
        self.save_model_btn = QPushButton("保存模型配置")
        self.save_model_btn.clicked.connect(self.save_model_config)
        self.save_model_btn.setToolTip("保存大模型配置")
        model_form.addRow(self.save_model_btn)
        model_settings_group.setLayout(model_form)
        settings_layout.addWidget(model_settings_group)

        # General Settings
        general_settings_group = QGroupBox("通用设置")
        general_form = QFormLayout()
        self.comfyui_output_dir_input = QLineEdit(self.comfyui_output_dir) # Load existing value
        self.comfyui_output_dir_input.setPlaceholderText("例如: D:\\ComfyUI\\output 或 /path/to/ComfyUI/output")
        self.comfyui_output_dir_input.setToolTip("请输入 ComfyUI 的 output 文件夹的绝对路径")
        general_form.addRow("ComfyUI 输出目录:", self.comfyui_output_dir_input)
        
        self.save_general_settings_btn = QPushButton("保存通用设置")
        self.save_general_settings_btn.clicked.connect(self._save_general_settings_action)
        self.save_general_settings_btn.setToolTip("保存通用应用设置")
        general_form.addRow(self.save_general_settings_btn)
        general_settings_group.setLayout(general_form)
        settings_layout.addWidget(general_settings_group) # This line was missing
        
        self.log_btn = QPushButton("查看系统日志")
        self.log_btn.clicked.connect(self.show_log_dialog)
        self.log_btn.setToolTip("查看系统日志")
        settings_layout.addWidget(self.log_btn)
        settings_layout.addStretch()
        self.settings_widget.setLayout(settings_layout)

        # 主体布局 - top_bar和bottom_bar已在init_top_bottom_bars中初始化
        main_widget = QWidget() #
        main_layout = QVBoxLayout() #
        main_layout.addWidget(self.top_bar) #
        # 删除左侧导航栏，直接添加标签页让其占满整个界面
        main_layout.addWidget(self.tabs) #
        main_layout.addWidget(self.bottom_bar) #
        main_widget.setLayout(main_layout) #
        self.setCentralWidget(main_widget) #

    def init_top_bottom_bars(self):
        """初始化顶部栏和底部栏 - 必须在其他UI组件之前调用"""
        # 顶部栏
        self.top_bar = QWidget()
        self.top_layout = QHBoxLayout()
        self.top_layout.addWidget(QLabel("AI 视频生成系统"))
        self.top_layout.addStretch()
        self.top_bar.setLayout(self.top_layout)
        self.top_bar.setFixedHeight(40)
        self.top_bar.setObjectName("top_bar")

        # 底部栏
        self.bottom_bar = QWidget()
        bottom_layout = QHBoxLayout()
        # 不再重新创建进度条，使用已在__init__中创建并设置样式的进度条
        # 移除这里的 self.log_output_bottom = QTextEdit()，因为它已经在 __init__ 中初始化
        # 不再重复设置高度，使用__init__中的设置
        bottom_layout.addWidget(self.progress)
        bottom_layout.addWidget(self.log_output_bottom)
        self.bottom_bar.setLayout(bottom_layout)
        self.bottom_bar.setFixedHeight(140) # 增加底部栏高度以容纳更高的状态栏
        self.bottom_bar.setObjectName("bottom_bar")
        self.bottom_bar.setVisible(True) # 确保底部栏可见

    def show_log_dialog(self): #
        logger.info("用户打开系统日志弹窗") #
        dlg = LogDialog(self) #
        dlg.exec_() #

    def init_log_refresh(self): #
        self.log_timer = QTimer(self) #
        self.log_timer.timeout.connect(self.refresh_bottom_log) #
        self.log_timer.start(2000) # 每2秒刷新一次 #
        self.refresh_bottom_log() #

    def refresh_bottom_log(self): #
        # 暂时禁用自动日志刷新，避免覆盖用户操作状态信息
        # 用户操作状态信息（如"正在生图"）优先级更高
        pass


            




    def update_shot_images(self, row_index, new_image_path):
        """更新分镜表格中指定行的图片和备选图片"""
        try:
            logger.info(f"开始更新第{row_index+1}行的分镜图片: {new_image_path}")
            
            # 添加数据状态检查
            if hasattr(self, 'shots_data') and self.shots_data:
                logger.debug(f"当前分镜数据行数: {len(self.shots_data)}")
            else:
                logger.warning("分镜数据不存在或为空")
                return False
            
            # 检查表格状态并同步
            if hasattr(self, 'shots_table') and self.shots_table:
                current_row_count = self.shots_table.rowCount()
                expected_row_count = len(self.shots_data)
                logger.debug(f"当前表格行数: {current_row_count}, 期望行数: {expected_row_count}")
                
                # 如果表格行数与数据不匹配，先同步表格
                if current_row_count != expected_row_count:
                    logger.warning(f"表格行数与数据不匹配，开始同步表格: {current_row_count} -> {expected_row_count}")
                    try:
                        self.populate_shots_table_data(self.shots_data)
                        logger.info(f"表格同步完成，新行数: {self.shots_table.rowCount()}")
                    except Exception as sync_error:
                        logger.error(f"表格同步失败: {sync_error}")
                        return False
            else:
                logger.warning("分镜表格不存在")
                return False
            
            # 首先尝试更新分镜标签页中的表格（如果存在）
            result1 = False
            if hasattr(self.storyboard_tab, 'update_shot_image'):
                logger.debug("更新分镜标签页中的表格")
                result1 = self.storyboard_tab.update_shot_image(row_index, new_image_path)
                if result1:
                    logger.debug("分镜标签页表格更新成功")
                else:
                    logger.warning(f"分镜标签页表格更新失败 - 行索引: {row_index}")
            else:
                logger.warning("分镜标签页不存在update_shot_image方法")
            
            # 查找并更新当前打开的ShotsWindow
            result2 = False
            logger.debug("查找当前打开的ShotsWindow")
            for widget in self.findChildren(QWidget):
                if widget.__class__.__name__ == 'ShotsWindow' and hasattr(widget, 'update_shot_image'):
                    logger.debug(f"找到ShotsWindow，开始更新图片")
                    result2 = widget.update_shot_image(row_index, new_image_path)
                    if result2:
                        logger.debug("ShotsWindow表格更新成功")
                    else:
                        logger.warning("ShotsWindow表格更新失败")
                    break
            
            # 如果都没有找到，尝试通过分镜标签页查找
            if not result2:
                logger.debug("在子控件中未找到ShotsWindow，尝试在顶级窗口中查找")
                # 检查是否有活动的ShotsWindow
                from gui.shots_window import ShotsWindow
                for window in QApplication.topLevelWidgets():
                    if isinstance(window, ShotsWindow) and window.isVisible():
                        logger.debug(f"找到活动的ShotsWindow，开始更新图片")
                        result2 = window.update_shot_image(row_index, new_image_path)
                        if result2:
                            logger.debug("活动ShotsWindow表格更新成功")
                        else:
                            logger.warning("活动ShotsWindow表格更新失败")
                        break
            
            # 如果分镜设置标签页中有表格，也要更新
            result3 = False
            if hasattr(self, 'shots_settings_table') and self.shots_settings_table:
                logger.debug("更新分镜设置标签页中的表格")
                result3 = self.update_shots_settings_image(row_index, new_image_path)
                if result3:
                    logger.debug("分镜设置标签页表格更新成功")
                else:
                    logger.warning("分镜设置标签页表格更新失败")
            
            final_result = result1 or result2 or result3
            if final_result:
                logger.info(f"第{row_index+1}行分镜图片更新完成")
                
                # 更新内存中的shots_data
                if 0 <= row_index < len(self.shots_data):
                    # 获取相对路径
                    if hasattr(self, 'current_project_dir') and self.current_project_dir:
                        try:
                            relative_path = os.path.relpath(new_image_path, self.current_project_dir)
                            relative_path = os.path.normpath(relative_path)
                            
                            # 如果主图为空或主图文件不存在，设置为主图
                            current_image = self.shots_data[row_index].get('image', '').strip()
                            if not current_image or not os.path.exists(os.path.join(self.current_project_dir, current_image)):
                                self.shots_data[row_index]['image'] = relative_path
                                logger.info(f"设置第{row_index+1}行主图: {relative_path} (原主图: {current_image})")
                                # 如果原来有无效的主图，从备选图片中移除（如果存在）
                                if current_image:
                                    current_alt = self.shots_data[row_index].get('alternative_images', '')
                                    if current_alt:
                                        alt_images = [img.strip() for img in current_alt.split(',') if img.strip() and img.strip() != current_image]
                                        self.shots_data[row_index]['alternative_images'] = ','.join(alt_images)
                                # 主图栏和备选图栏使用同一张图片，不重复保存
                                # 将主图也设置为备选图片（这样用户可以在备选图栏中看到同一张图片）
                                current_alt = self.shots_data[row_index].get('alternative_images', '')
                                if current_alt and current_alt.strip():
                                    alt_images = [img.strip() for img in current_alt.split(',') if img.strip()]
                                    if relative_path not in alt_images:
                                        alt_images.insert(0, relative_path)  # 插入到开头，作为首选备选图片
                                        self.shots_data[row_index]['alternative_images'] = ','.join(alt_images)
                                else:
                                    self.shots_data[row_index]['alternative_images'] = relative_path
                                logger.info(f"主图和备选图片都设置为同一张图片: {relative_path}")
                            else:
                                # 如果主图已存在且有效，则添加到备选图片
                                current_alt = self.shots_data[row_index].get('alternative_images', '')
                                if current_alt and current_alt.strip():
                                    alt_images = [img.strip() for img in current_alt.split(',') if img.strip()]
                                    if relative_path not in alt_images:
                                        alt_images.append(relative_path)
                                        self.shots_data[row_index]['alternative_images'] = ','.join(alt_images)
                                        logger.info(f"添加第{row_index+1}行备选图片: {relative_path}")
                                else:
                                    self.shots_data[row_index]['alternative_images'] = relative_path
                                    logger.info(f"设置第{row_index+1}行首个备选图片: {relative_path}")
                        except Exception as path_error:
                            logger.error(f"处理图片路径时出错: {path_error}")
                    
                    # 自动保存项目
                    if hasattr(self, 'current_project_name') and self.current_project_name:
                        try:
                            self.save_current_project()
                            logger.info(f"图片更新后自动保存项目: {self.current_project_name}")
                        except Exception as save_error:
                            logger.error(f"自动保存项目失败: {save_error}")
                else:
                    logger.warning(f"行索引超出shots_data范围: {row_index}, 数据行数: {len(self.shots_data)}")
            else:
                logger.warning(f"第{row_index+1}行分镜图片更新失败，所有表格更新都失败")
            
            return final_result
            
        except Exception as e:
            logger.error(f"更新分镜图片时发生错误: {e}")
            return False


    
    def create_ai_voice_tab(self):
        """创建AI配音标签页"""
        try:
            # 创建主容器
            ai_voice_widget = QWidget()
            layout = QVBoxLayout(ai_voice_widget)
            layout.setSpacing(20)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # 标题
            title_label = QLabel("AI 配音设置")
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }")
            layout.addWidget(title_label)
            
            # 创建滚动区域
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            # 创建滚动内容容器
            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)
            scroll_layout.setSpacing(15)
            
            # 配音引擎设置组
            engine_group = QGroupBox("配音引擎设置")
            engine_layout = QFormLayout(engine_group)
            
            # TTS引擎选择
            self.tts_engine_combo = QComboBox()
            self.tts_engine_combo.addItems(["Edge TTS", "SiliconFlow"])
            self.tts_engine_combo.setCurrentText("Edge TTS")
            self.tts_engine_combo.currentTextChanged.connect(self.on_tts_engine_changed)
            engine_layout.addRow("TTS引擎:", self.tts_engine_combo)
            
            # 语音模型选择
            self.voice_model_combo = QComboBox()
            engine_layout.addRow("语音模型:", self.voice_model_combo)
            
            # 语音列表将在voice_manager初始化后加载
            
            # 语速设置
            self.speech_rate_slider = QSlider(Qt.Horizontal)
            self.speech_rate_slider.setRange(-50, 50)
            self.speech_rate_slider.setValue(0)
            self.speech_rate_label = QLabel("正常")
            rate_layout = QHBoxLayout()
            rate_layout.addWidget(self.speech_rate_slider)
            rate_layout.addWidget(self.speech_rate_label)
            engine_layout.addRow("语速:", rate_layout)
            
            # 音调设置
            self.speech_pitch_slider = QSlider(Qt.Horizontal)
            self.speech_pitch_slider.setRange(-50, 50)
            self.speech_pitch_slider.setValue(0)
            self.speech_pitch_label = QLabel("正常")
            pitch_layout = QHBoxLayout()
            pitch_layout.addWidget(self.speech_pitch_slider)
            pitch_layout.addWidget(self.speech_pitch_label)
            engine_layout.addRow("音调:", pitch_layout)
            
            scroll_layout.addWidget(engine_group)
            
            # 批量配音设置组
            batch_group = QGroupBox("批量配音设置")
            batch_layout = QFormLayout(batch_group)
            
            # 输出格式
            self.audio_format_combo = QComboBox()
            self.audio_format_combo.addItems(["wav", "mp3", "m4a"])
            self.audio_format_combo.setCurrentText("wav")
            batch_layout.addRow("音频格式:", self.audio_format_combo)
            
            # 音频质量
            self.audio_quality_combo = QComboBox()
            self.audio_quality_combo.addItems(["高质量", "标准质量", "压缩质量"])
            self.audio_quality_combo.setCurrentText("标准质量")
            batch_layout.addRow("音频质量:", self.audio_quality_combo)
            
            # 并发数量
            self.concurrent_count_spin = QSpinBox()
            self.concurrent_count_spin.setRange(1, 10)
            self.concurrent_count_spin.setValue(3)
            batch_layout.addRow("并发数量:", self.concurrent_count_spin)
            
            scroll_layout.addWidget(batch_group)
            
            # 操作按钮组
            button_group = QGroupBox("配音操作")
            button_layout = QVBoxLayout(button_group)
            
            # 批量配音按钮
            self.batch_voice_btn = QPushButton("批量生成配音")
            self.batch_voice_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #21618c;
                }
            """)
            self.batch_voice_btn.clicked.connect(self.batch_generate_voice)
            button_layout.addWidget(self.batch_voice_btn)
            
            # 测试配音按钮
            self.test_voice_btn = QPushButton("测试配音")
            self.test_voice_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
            """)
            self.test_voice_btn.clicked.connect(self.test_voice_generation)
            button_layout.addWidget(self.test_voice_btn)
            
            # 清除所有配音按钮
            self.clear_voice_btn = QPushButton("清除所有配音")
            self.clear_voice_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            self.clear_voice_btn.clicked.connect(self.clear_all_voices)
            button_layout.addWidget(self.clear_voice_btn)
            
            scroll_layout.addWidget(button_group)
            
            # 状态信息组
            status_group = QGroupBox("配音状态")
            status_layout = QVBoxLayout(status_group)
            
            self.voice_status_label = QLabel("等待开始配音...")
            self.voice_status_label.setStyleSheet("QLabel { color: #7f8c8d; font-size: 12px; }")
            status_layout.addWidget(self.voice_status_label)
            
            self.voice_progress_bar = QProgressBar()
            self.voice_progress_bar.setVisible(False)
            status_layout.addWidget(self.voice_progress_bar)
            
            scroll_layout.addWidget(status_group)
            
            # 连接滑块信号
            self.speech_rate_slider.valueChanged.connect(self.update_rate_label)
            self.speech_pitch_slider.valueChanged.connect(self.update_pitch_label)
            
            # 设置滚动内容
            scroll_area.setWidget(scroll_content)
            layout.addWidget(scroll_area)
            
            return ai_voice_widget
            
        except Exception as e:
            logger.error(f"创建AI配音标签页时发生错误: {e}")
            # 返回一个简单的错误提示标签
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(f"创建AI配音标签页失败: {str(e)}")
            error_label.setAlignment(Qt.AlignCenter)
            error_layout.addWidget(error_label)
            return error_widget
    
    def update_rate_label(self, value):
        """更新语速标签"""
        if value == 0:
            self.speech_rate_label.setText("正常")
        elif value > 0:
            self.speech_rate_label.setText(f"+{value}%")
        else:
            self.speech_rate_label.setText(f"{value}%")
    
    def update_pitch_label(self, value):
        """更新音调标签"""
        if value == 0:
            self.speech_pitch_label.setText("正常")
        elif value > 0:
            self.speech_pitch_label.setText(f"+{value}%")
        else:
            self.speech_pitch_label.setText(f"{value}%")
    
    def batch_generate_voice(self):
        """批量生成配音"""
        try:
            if not hasattr(self, 'shots_data') or not self.shots_data:
                QMessageBox.warning(self, "警告", "请先生成分镜数据！")
                return
            
            # 获取当前设置
            voice_model = self.voice_model_combo.currentData()
            if not voice_model:
                QMessageBox.warning(self, "警告", "请先选择语音模型")
                return
            
            rate = self.speech_rate_slider.value()
            pitch = self.speech_pitch_slider.value()
            
            # 调用配音管理器进行批量生成
            result = self.voice_manager.batch_generate_voices(
                shots_data=self.shots_data,
                voice_model=voice_model,
                rate=rate,
                pitch=pitch
            )
            
            if result:
                self.save_current_project()
                QMessageBox.information(self, "成功", "批量配音生成完成！")
            else:
                QMessageBox.warning(self, "警告", "批量配音生成失败，请检查日志")
            
        except Exception as e:
            logger.error(f"批量配音失败: {e}")
            QMessageBox.critical(self, "错误", f"批量配音失败: {e}")
    
    def test_voice_generation(self):
        """测试配音生成"""
        try:
            test_text = "这是一个配音测试，用于验证当前配音设置是否正常工作。"
            
            # 获取当前设置
            engine = self.tts_engine_combo.currentText()
            model_display = self.voice_model_combo.currentText()
            model = self.voice_model_combo.currentData()  # 获取实际的语音名称
            rate = self.speech_rate_slider.value()
            pitch = self.speech_pitch_slider.value()
            
            if not model:
                QMessageBox.warning(self, "警告", "请先选择语音模型")
                return
            
            # 调用配音管理器进行测试
            result = self.voice_manager.test_voice_generation(
                engine=engine,
                voice_model=model,
                voice_display=model_display,
                rate=rate,
                pitch=pitch,
                test_text=test_text
            )
            
            if result.get('success'):
                QMessageBox.information(self, "测试配音成功", 
                    f"配音测试成功！\n\n当前设置:\n引擎: {result['engine']}\n模型: {result['voice_display']}\n语速: {result['rate']}%\n音调: {result['pitch']}%\n\n生成文件: {result['output_file']}\n文件大小: {result['file_size']} 字节\n\n测试文本: {result['test_text']}")
            else:
                QMessageBox.critical(self, "配音测试失败", f"配音测试失败:\n{result.get('error', '未知错误')}")
            
        except Exception as e:
            logger.error(f"配音测试失败: {e}")
            QMessageBox.critical(self, "错误", f"配音测试失败: {e}")
            self.voice_status_label.setText("配音测试失败")
    
    def load_voice_models(self):
        """加载语音模型列表"""
        try:
            # 调用配音管理器加载语音模型
            success = self.voice_manager.load_voice_models()
            if success:
                self.update_voice_model_list()
            else:
                logger.warning("语音模型加载失败，使用默认配置")
                self.update_voice_model_list()
        except Exception as e:
            logger.error(f"加载语音模型列表失败: {e}")
            self.update_voice_model_list()
    
    def update_voice_model_list(self):
        """更新语音模型列表"""
        self.voice_model_combo.clear()
        
        current_engine = self.tts_engine_combo.currentText()
        voices = self.voice_manager.get_voice_list(current_engine)
        
        for voice in voices:
            # 提取实际的语音名称（去掉描述部分）
            voice_name = voice.split(' (')[0] if ' (' in voice else voice
            self.voice_model_combo.addItem(voice, voice_name)
    
    def on_tts_engine_changed(self):
        """TTS引擎切换事件"""
        self.update_voice_model_list()
        
        # 如果切换到SiliconFlow，检查API Key配置
        if self.tts_engine_combo.currentText() == "SiliconFlow":
            api_key = self.config_manager.get_tts_setting('siliconflow.api_key', '')
            if not api_key:
                QMessageBox.warning(
                    self, "配置提醒", 
                    "使用SiliconFlow需要配置API Key\n请在设置中配置SiliconFlow API Key"
                )
    
    def clear_all_voices(self):
        """清除所有配音"""
        try:
            if not hasattr(self, 'shots_data') or not self.shots_data:
                QMessageBox.warning(self, "警告", "没有分镜数据！")
                return
            
            reply = QMessageBox.question(self, "确认清除", 
                "确定要清除所有分镜的配音文件吗？\n此操作不可撤销！",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # 调用配音管理器清除配音
                success = self.voice_manager.clear_all_voices(self.shots_data)
                
                if success:
                    # 保存项目
                    self.save_current_project()
                    self.voice_status_label.setText("已清除所有配音")
                    QMessageBox.information(self, "成功", "已清除所有配音文件路径")
                else:
                    QMessageBox.warning(self, "警告", "清除配音失败")
                
        except Exception as e:
            logger.error(f"清除配音失败: {e}")
            QMessageBox.critical(self, "错误", f"清除配音失败: {e}")

    def create_shots_settings_tab(self):
        """创建分镜设置标签页"""
        try:
            # 创建主容器
            shots_settings_widget = QWidget()
            layout = QVBoxLayout(shots_settings_widget)
            
            # 添加提示标签
            self.shots_settings_info_label = QLabel("请先在'文本转分镜'标签页生成分镜，然后在此处查看和编辑分镜设置")
            self.shots_settings_info_label.setAlignment(Qt.AlignCenter)
            self.shots_settings_info_label.setStyleSheet("QLabel { color: #666; font-size: 14px; padding: 20px; }")
            layout.addWidget(self.shots_settings_info_label)
            
            # 创建分镜表格容器
            self.shots_settings_table_widget = QWidget()
            self.shots_settings_table_layout = QVBoxLayout(self.shots_settings_table_widget)
            layout.addWidget(self.shots_settings_table_widget)
            
            # 初始状态下隐藏表格容器
            self.shots_settings_table_widget.hide()
            
            return shots_settings_widget
            
        except Exception as e:
            logger.error(f"创建分镜设置标签页时发生错误: {e}")
            # 返回一个简单的错误提示标签
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(f"创建分镜设置标签页失败: {str(e)}")
            error_label.setAlignment(Qt.AlignCenter)
            error_layout.addWidget(error_label)
            return error_widget
    
    def show_shots_in_settings_tab(self, shots_data):
        """在分镜设置标签页中显示分镜表格"""
        try:
            # 隐藏提示标签
            if hasattr(self, 'shots_settings_info_label'):
                self.shots_settings_info_label.hide()
            
            # 清除之前的内容
            for i in reversed(range(self.shots_settings_table_layout.count())):
                child = self.shots_settings_table_layout.takeAt(i)
                if child.widget():
                    child.widget().deleteLater()
            
            # 创建分镜表格
            from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QVBoxLayout
            from gui.shots_window import ImageDelegate
            
            table_widget = QTableWidget()
            table_widget.setFont(QFont("微软雅黑", 13))
            table_widget.setToolTip("分镜表格，可编辑和复制内容")
            
            # 定义列
            columns = ('文案', '分镜', '角色', '提示词', '主图', '视频提示词', '音效', '操作', '备选图片')
            table_widget.setColumnCount(len(columns))
            table_widget.setHorizontalHeaderLabels(columns)
            
            # 设置列宽
            header = table_widget.horizontalHeader()
            for i in range(len(columns)):
                header.setSectionResizeMode(i, QHeaderView.Interactive)
            header.setStretchLastSection(True)
            
            # 设置主图列的委托，传入MainWindow实例
            image_delegate = ImageDelegate(self)
            # 为委托添加on_alternative_image_selected方法
            image_delegate.on_alternative_image_selected = lambda row, path: self.on_shots_alternative_image_selected(row, path)
            table_widget.setItemDelegateForColumn(4, image_delegate)
            table_widget.setItemDelegateForColumn(8, image_delegate)
            
            # 添加数据
            table_widget.setRowCount(len(shots_data))
            for i, shot in enumerate(shots_data):
                # 创建表格项
                item_description = QTableWidgetItem(shot.get('description', ''))
                item_scene = QTableWidgetItem(shot.get('scene', ''))
                item_role = QTableWidgetItem(shot.get('role', ''))
                item_prompt = QTableWidgetItem(shot.get('prompt', ''))
                item_video_prompt = QTableWidgetItem(shot.get('video_prompt', ''))
                item_audio = QTableWidgetItem(shot.get('audio', ''))
                
                # 设置文本对齐和换行
                for item in [item_description, item_scene, item_role, item_prompt]:
                    item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                    item.setFlags(item.flags() | Qt.TextWordWrap)
                
                # 设置表格项
                table_widget.setItem(i, 0, item_description)
                table_widget.setItem(i, 1, item_scene)
                table_widget.setItem(i, 2, item_role)
                table_widget.setItem(i, 3, item_prompt)
                # 主图栏：只有当图片文件确实存在时才显示路径，否则保持空白
                image_path = shot.get('image', '').strip()
                if image_path and hasattr(self, 'current_project_dir') and self.current_project_dir:
                    # 检查图片文件是否存在
                    if os.path.isabs(image_path):
                        full_image_path = image_path
                    else:
                        full_image_path = os.path.join(self.current_project_dir, image_path)
                    
                    if os.path.exists(full_image_path):
                        table_widget.setItem(i, 4, QTableWidgetItem(image_path))
                    else:
                        table_widget.setItem(i, 4, QTableWidgetItem(''))  # 文件不存在时显示空白
                else:
                    table_widget.setItem(i, 4, QTableWidgetItem(''))  # 没有路径时显示空白
                table_widget.setItem(i, 5, item_video_prompt)
                table_widget.setItem(i, 6, item_audio)
                
                # 创建操作按钮
                operation_widget = self.create_shots_operation_buttons(i)
                table_widget.setCellWidget(i, 7, operation_widget)
                
                # 备选图片栏：处理多个用逗号分隔的图片路径
                alternative_images = shot.get('alternative_images', '').strip()
                if alternative_images and hasattr(self, 'current_project_dir') and self.current_project_dir:
                    # 检查备选图片文件是否存在（支持多个路径）
                    valid_paths = []
                    for path in alternative_images.split(','):
                        path = path.strip()
                        if path:
                            if os.path.isabs(path):
                                full_path = path
                            else:
                                full_path = os.path.join(self.current_project_dir, path)
                            
                            if os.path.exists(full_path):
                                valid_paths.append(path)
                    
                    if valid_paths:
                        # 只显示存在的图片路径
                        table_widget.setItem(i, 8, QTableWidgetItem(','.join(valid_paths)))
                    else:
                        table_widget.setItem(i, 8, QTableWidgetItem(''))  # 没有有效文件时显示空白
                else:
                    table_widget.setItem(i, 8, QTableWidgetItem(''))  # 没有路径时显示空白
            
            # 设置行高
            for i in range(table_widget.rowCount()):
                table_widget.setRowHeight(i, max(table_widget.rowHeight(i), 100))
            table_widget.resizeRowsToContents()
            
            # 添加批量操作按钮区域
            batch_widget = QWidget()
            batch_layout = QHBoxLayout(batch_widget)
            batch_layout.setContentsMargins(10, 5, 10, 5)
            batch_layout.setSpacing(10)
            
            # 批量生图按钮
            self.batch_draw_btn = QPushButton("批量生图")
            self.batch_draw_btn.setProperty("class", "draw-button")
            self.batch_draw_btn.setMinimumSize(100, 40)
            self.batch_draw_btn.setMaximumSize(120, 45)
            self.batch_draw_btn.clicked.connect(self.handle_batch_draw)
            batch_layout.addWidget(self.batch_draw_btn)
            
            # 停止批量按钮
            self.stop_batch_btn = QPushButton("停止批量")
            self.stop_batch_btn.setProperty("class", "voice-button")
            self.stop_batch_btn.setMinimumSize(100, 40)
            self.stop_batch_btn.setMaximumSize(120, 45)
            self.stop_batch_btn.setEnabled(False)  # 初始状态禁用
            self.stop_batch_btn.clicked.connect(self.handle_stop_batch)
            batch_layout.addWidget(self.stop_batch_btn)
            
            # 进度显示标签
            self.batch_progress_label = QLabel("进度: 0/0")
            self.batch_progress_label.setFont(QFont("微软雅黑", 12))
            self.batch_progress_label.setProperty("class", "status-label")
            batch_layout.addWidget(self.batch_progress_label)
            
            # 跳过已有图片选项
            self.skip_existing_checkbox = QCheckBox("跳过已有图片")
            self.skip_existing_checkbox.setChecked(True)  # 默认勾选
            self.skip_existing_checkbox.setFont(QFont("微软雅黑", 10))
            batch_layout.addWidget(self.skip_existing_checkbox)
            
            # 添加弹性空间
            batch_layout.addStretch()
            
            # 将批量操作区域添加到布局中
            self.shots_settings_table_layout.addWidget(batch_widget)
            
            # 将表格添加到布局中
            self.shots_settings_table_layout.addWidget(table_widget)
            
            # 显示表格容器并隐藏提示标签
            self.shots_settings_table_widget.show()
            
            # 保存表格引用和数据
            self.shots_settings_table = table_widget
            self.shots_settings_data = shots_data
            
            # 同时更新主表格引用，确保批量绘图功能能正确操作
            self.shots_table = table_widget
            
            # 连接选择事件
            table_widget.itemSelectionChanged.connect(self.on_shot_selection_changed)
            
            logger.info(f"分镜表格已显示在分镜设置标签页中，共{len(shots_data)}行数据")
            
        except Exception as e:
            logger.error(f"在分镜设置标签页中显示分镜表格时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"显示分镜表格失败: {str(e)}")
    
    def create_shots_operation_buttons(self, row_index):
        """为分镜设置标签页创建操作按钮组件"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # 绘图按钮
        draw_btn = QPushButton("绘图")
        draw_btn.setProperty("class", "draw-button")
        draw_btn.clicked.connect(lambda: self.handle_shots_draw_btn(row_index))
        layout.addWidget(draw_btn)
        
        # 配音按钮
        voice_btn = QPushButton("配音")
        voice_btn.setProperty("class", "voice-button")
        voice_btn.clicked.connect(lambda: self.handle_shots_voice_btn(row_index))
        layout.addWidget(voice_btn)
        
        # 试听按钮（初始隐藏）
        preview_btn = QPushButton("试听")
        preview_btn.setProperty("class", "preview-button")
        preview_btn.clicked.connect(lambda: self.handle_shots_preview_btn(row_index))
        preview_btn.setVisible(False)  # 初始隐藏
        layout.addWidget(preview_btn)
        
        # 存储试听按钮引用，用于后续显示/隐藏
        if not hasattr(self, 'shots_preview_buttons'):
            self.shots_preview_buttons = {}
        self.shots_preview_buttons[row_index] = preview_btn
        
        # 检查是否已有配音文件，如果有则显示试听按钮
        self._check_and_show_shots_preview_button(row_index, preview_btn)
        
        # 分镜设置按钮
        setting_btn = QPushButton("设置")
        setting_btn.setProperty("class", "setting-button")
        setting_btn.clicked.connect(lambda: self.handle_shot_setting_btn(row_index))
        layout.addWidget(setting_btn)
        
        widget.setLayout(layout)
        return widget
    
    def handle_shots_draw_btn(self, row_index):
        """处理分镜设置标签页中的绘图按钮点击事件"""
        try:
            # 获取提示词
            if hasattr(self, 'shots_settings_table') and self.shots_settings_table:
                item = self.shots_settings_table.item(row_index, 3)  # 提示词列
                prompt = item.text() if item else ""
                
                if not prompt:
                    QMessageBox.warning(self, "警告", f"第{row_index+1}行没有提示词内容")
                    return
                
                # 调用绘图处理方法
                self.process_draw_request(row_index, prompt)
            else:
                QMessageBox.warning(self, "错误", "分镜表格未初始化")
                
        except Exception as e:
            logger.error(f"处理分镜设置标签页绘图按钮点击时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"绘图功能出错: {str(e)}")
    
    def handle_shots_voice_btn(self, row_index):
        """处理分镜设置标签页中的配音按钮点击事件"""
        try:
            # 获取当前行的文案内容
            text_item = self.shots_table.item(row_index, 0)  # 文案列
            if not text_item or not text_item.text().strip():
                QMessageBox.warning(self, "警告", "当前分镜没有文案内容，无法进行配音")
                return
            
            text_content = text_item.text().strip()
            
            # 导入AI配音对话框
            from gui.ai_voice_dialog import AIVoiceDialog
            
            # 创建并显示AI配音对话框
            dialog = AIVoiceDialog(self, text_content, row_index)
            if dialog.exec_() == QDialog.Accepted:
                # 用户确认生成，获取生成结果
                result = dialog.get_generation_result()
                if result and result.get('success'):
                    # 更新表格中的语音列信息
                    voice_item = self.shots_table.item(row_index, 6)  # 语音列
                    if voice_item:
                        voice_item.setText(f"已生成: {os.path.basename(result['audio_file'])}")
                    else:
                        voice_item = QTableWidgetItem(f"已生成: {os.path.basename(result['audio_file'])}")
                        self.shots_table.setItem(row_index, 6, voice_item)
                    
                    # 更新分镜数据中的语音文件路径
                    if self.shots_data and row_index < len(self.shots_data):
                        self.shots_data[row_index]['voice_file'] = result['audio_file']
                        # 自动保存项目
                        self.save_current_project()
                        logger.info(f"已更新第{row_index+1}行分镜的语音文件: {result['audio_file']}")
                    
                    # 显示试听按钮
                    if hasattr(self, 'shots_preview_buttons') and row_index in self.shots_preview_buttons:
                        self.shots_preview_buttons[row_index].setVisible(True)
                        logger.info(f"第{row_index+1}行试听按钮已显示")
                    
                    QMessageBox.information(self, "成功", "语音生成完成！")
                elif result:
                    QMessageBox.warning(self, "错误", f"语音生成失败: {result.get('error', '未知错误')}")
                    
        except ImportError as e:
            QMessageBox.critical(self, "错误", f"无法加载AI配音模块: {str(e)}")
        except Exception as e:
            logger.error(f"处理分镜设置标签页配音按钮点击时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"配音功能出错: {str(e)}")
    
    def handle_shots_preview_btn(self, row_index):
        """处理分镜设置标签页中的试听按钮点击事件"""
        try:
            # 获取配音文件路径
            voice_file = None
            
            # 从分镜数据中获取语音文件路径
            if self.shots_data and row_index < len(self.shots_data):
                voice_file = self.shots_data[row_index].get('voice_file')
            
            if not voice_file or not os.path.exists(voice_file):
                QMessageBox.warning(self, "警告", "未找到配音文件，请先生成配音")
                return
            
            # 播放音频文件
            self._play_audio_file(voice_file)
            logger.info(f"开始播放第{row_index+1}行的配音文件: {voice_file}")
            
        except Exception as e:
            logger.error(f"处理试听按钮点击时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"试听功能出错: {str(e)}")
    
    def _play_audio_file(self, file_path: str):
        """播放音频文件
        
        Args:
            file_path: 音频文件路径
        """
        try:
            import platform
            import subprocess
            
            system = platform.system()
            logger.debug(f"尝试播放音频文件: {file_path}, 系统: {system}")
            
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":  # macOS
                subprocess.call(["open", file_path])
            else:  # Linux
                subprocess.call(["xdg-open", file_path])
                
        except Exception as e:
            logger.warning(f"播放音频文件失败: {e}")
            QMessageBox.warning(self, "警告", f"无法播放音频文件: {str(e)}")
    
    def _check_and_show_shots_preview_button(self, row_index, preview_btn):
        """检查是否已有配音文件，如果有则显示试听按钮
        
        Args:
            row_index: 行索引
            preview_btn: 试听按钮对象
        """
        try:
            # 从分镜数据中获取语音文件路径
            if self.shots_data and row_index < len(self.shots_data):
                voice_file = self.shots_data[row_index].get('voice_file')
                if voice_file and os.path.exists(voice_file):
                    preview_btn.setVisible(True)
                    logger.debug(f"第{row_index+1}行已有配音文件，显示试听按钮: {voice_file}")
                else:
                    preview_btn.setVisible(False)
            else:
                preview_btn.setVisible(False)
        except Exception as e:
            logger.warning(f"检查配音文件时发生错误: {e}")
            preview_btn.setVisible(False)
    
    def update_shots_settings_image(self, row_index, image_path):
        """更新分镜设置标签页中指定行的图片"""
        try:
            if not hasattr(self, 'shots_settings_table') or not self.shots_settings_table:
                logger.warning("分镜设置表格不存在")
                return False
            
            if not (0 <= row_index < self.shots_settings_table.rowCount()):
                logger.warning(f"行索引超出范围: {row_index}, 表格行数: {self.shots_settings_table.rowCount()}")
                return False
            
            # 获取当前备选图片列的内容
            alt_image_item = self.shots_settings_table.item(row_index, 8)
            current_alt_images = alt_image_item.text() if alt_image_item else ""
            
            # 将新图片追加到备选图片列表中（而不是替换）
            if current_alt_images and current_alt_images.strip():
                # 如果已有备选图片，检查是否已存在，避免重复
                existing_images = [img.strip() for img in current_alt_images.split(',') if img.strip()]
                if image_path not in existing_images:
                    new_alt_images = current_alt_images + ',' + image_path
                    logger.info(f"将新图片追加到备选图片列表: {image_path}")
                else:
                    new_alt_images = current_alt_images
                    logger.info(f"图片已存在于备选图片列表中: {image_path}")
            else:
                # 如果没有备选图片，直接设置
                new_alt_images = image_path
                logger.info(f"设置第一个备选图片: {image_path}")
            
            # 更新备选图片列
            if not alt_image_item:
                alt_image_item = QTableWidgetItem(new_alt_images)
                self.shots_settings_table.setItem(row_index, 8, alt_image_item)
            else:
                alt_image_item.setText(new_alt_images)
            
            # 如果主图列为空，将新图片设置为主图
            main_image_item = self.shots_settings_table.item(row_index, 4)
            if not main_image_item or not main_image_item.text().strip():
                if not main_image_item:
                    main_image_item = QTableWidgetItem(image_path)
                    self.shots_settings_table.setItem(row_index, 4, main_image_item)
                else:
                    main_image_item.setText(image_path)
                main_image_item.setToolTip(f"图片路径: {image_path}")
            
            # 强制刷新表格显示
            self.shots_settings_table.viewport().update()
            
            logger.info(f"分镜设置标签页第{row_index+1}行图片更新成功: {image_path}")
            return True
            
        except Exception as e:
            logger.error(f"更新分镜设置标签页图片时发生错误: {e}")
            return False
    
    def on_shots_alternative_image_selected(self, row_index, selected_image_path):
        """处理分镜设置标签页中备选图片被选中的事件"""
        try:
            if not hasattr(self, 'shots_settings_table') or not self.shots_settings_table:
                logger.warning("分镜设置表格不存在")
                return
            
            if not (0 <= row_index < self.shots_settings_table.rowCount()):
                logger.warning(f"行索引超出范围: {row_index}, 表格行数: {self.shots_settings_table.rowCount()}")
                return
            
            # 更新底层数据 - shots_data
            if hasattr(self, 'shots_data') and self.shots_data and row_index < len(self.shots_data):
                self.shots_data[row_index]['image'] = selected_image_path
                logger.info(f"已更新第{row_index+1}行shots_data主图路径: {selected_image_path}")
                
                # 自动保存项目
                if hasattr(self, 'current_project_name') and self.current_project_name:
                    try:
                        self.save_current_project()
                        logger.info(f"选择主图后自动保存项目: {self.current_project_name}")
                    except Exception as save_error:
                        logger.error(f"自动保存项目失败: {save_error}")
            
            # 将选中的图片设置为主图（第4列）
            main_image_item = QTableWidgetItem(selected_image_path)
            main_image_item.setToolTip(f"图片路径: {selected_image_path}")
            self.shots_settings_table.setItem(row_index, 4, main_image_item)
            
            # 强制刷新表格显示
            self.shots_settings_table.viewport().update()
            # 强制重绘指定行的图片列
            model_index = self.shots_settings_table.model().index(row_index, 4)
            self.shots_settings_table.update(model_index)
            
            logger.info(f"分镜设置标签页第{row_index+1}行已选择图片: {selected_image_path}")
            
            # 同步更新到分镜标签页
            if hasattr(self, 'storyboard_tab') and hasattr(self.storyboard_tab, 'update_shot_image'):
                self.storyboard_tab.update_shot_image(row_index, selected_image_path)
                
        except Exception as e:
            logger.error(f"选择分镜设置备选图片时发生错误: {e}")
            print(f"选择备选图片时发生错误: {e}")
    
    def show_progress(self, message="⏳ 处理中，请稍候..."):
        """显示进度条 - 委托给storyboard_tab处理"""
        if hasattr(self, 'storyboard_tab') and self.storyboard_tab:
            self.storyboard_tab.show_progress(message)
        else:
            logger.warning("storyboard_tab不存在，无法显示进度条")
    
    def hide_progress(self):
        """隐藏进度条 - 委托给storyboard_tab处理"""
        if hasattr(self, 'storyboard_tab') and self.storyboard_tab:
            self.storyboard_tab.hide_progress()
        else:
            logger.warning("storyboard_tab不存在，无法隐藏进度条")
    
    def handle_generate_video_btn(self):
        logger.info("点击了生成视频按钮")
        # TODO: Implement video generation logic
        QMessageBox.information(self, "提示", "生成视频功能待实现。")

    def handle_settings_btn(self):
        logger.info("点击了设置按钮")
        # TODO: Implement settings logic
        QMessageBox.information(self, "提示", "设置功能待实现。")
    
    def process_draw_request(self, row_index, prompt):
        """处理绘图请求：根据绘图设置中的引擎选择，使用相应的生图服务"""
        try:
            logger.info(f"开始处理第{row_index+1}行的绘图请求")
            logger.debug(f"使用提示词栏中的提示词: {prompt}")
            
            # 获取绘图设置中的引擎选择
            drawing_settings = self.ai_drawing_tab.get_current_settings()
            selected_engine = drawing_settings.get('selected_engine', 'pollinations')  # 默认使用Pollinations AI
            logger.info(f"绘图设置中选择的引擎: {selected_engine}")
            
            # 直接使用提示词栏中的内容，不再根据风格选择重新生成
            # 这样可以确保用户在提示词栏中输入的内容得到尊重
            logger.info(f"直接使用用户在提示词栏中输入的内容进行生图: {prompt}")
            
            from PyQt5.QtCore import QThread, pyqtSignal
            
            # 创建绘图线程
            class DrawingThread(QThread):
                finished = pyqtSignal(bool, str, str)  # success, message, image_path
                
                def __init__(self, main_window, prompt, row_index, selected_engine):
                    super().__init__()
                    self.main_window = main_window
                    self.prompt = prompt
                    self.row_index = row_index
                    self.selected_engine = selected_engine
                
                def run(self):
                    try:
                        logger.info(f"绘图线程开始运行，行索引: {self.row_index}，使用引擎: {self.selected_engine}")
                        
                        # 根据选择的引擎使用不同的生图服务
                        if self.selected_engine == "pollinations":
                            self._generate_with_pollinations()
                        elif self.selected_engine == "comfyui":
                            self._generate_with_comfyui()
                        else:
                            logger.error(f"未知的生成引擎: {self.selected_engine}")
                            self.finished.emit(False, f"未知的生成引擎: {self.selected_engine}", "")
                            
                    except Exception as e:
                        logger.error(f"绘图过程中发生错误: {str(e)}")
                        self.finished.emit(False, f"绘图过程中发生错误: {str(e)}", "")
                
                def _generate_with_pollinations(self):
                    """使用 Pollinations AI 生成图片"""
                    try:
                        logger.info("使用 Pollinations AI 生成图片")
                        
                        # 在状态栏显示生成信息
                        if hasattr(self.main_window, 'log_output_bottom'):
                            self.main_window.log_output_bottom.appendPlainText(f"🎨 正在使用 Pollinations AI 生成图片...")
                            self.main_window.log_output_bottom.verticalScrollBar().setValue(
                                self.main_window.log_output_bottom.verticalScrollBar().maximum()
                            )
                        
                        # 初始化 Pollinations 客户端
                        from models.pollinations_client import PollinationsClient
                        pollinations_client = PollinationsClient()
                        
                        # 获取项目管理器和当前项目名称
                        project_manager = getattr(self.main_window, 'project_manager', None)
                        current_project_name = getattr(self.main_window, 'current_project_name', None)
                        
                        # 获取AI绘图标签页的当前Pollinations设置
                        pollinations_settings = {}
                        if hasattr(self.main_window, 'ai_drawing_tab') and self.main_window.ai_drawing_tab:
                            if hasattr(self.main_window.ai_drawing_tab, 'get_current_pollinations_settings'):
                                pollinations_settings = self.main_window.ai_drawing_tab.get_current_pollinations_settings()
                                logger.info(f"从UI获取的Pollinations设置: {pollinations_settings}")
                            else:
                                logger.warning("ai_drawing_tab 中未找到 get_current_pollinations_settings 方法")
                        else:
                            logger.warning("无法访问 ai_drawing_tab 以获取 Pollinations 设置")
                        
                        # 将 project_manager 和 current_project_name 添加到参数字典中
                        # generate_image 方法内部会处理这些特殊参数
                        if project_manager:
                            pollinations_settings['project_manager'] = project_manager
                        if current_project_name:
                            pollinations_settings['current_project_name'] = current_project_name

                        # 生成图片，将收集到的设置作为关键字参数传递
                        result = pollinations_client.generate_image(self.prompt, **pollinations_settings)
                        
                        # pollinations_client.generate_image 返回的是图片路径列表
                        if result and len(result) > 0 and not result[0].startswith("ERROR:"):
                            image_path = result[0]
                            logger.info(f"Pollinations AI 图片生成成功: {image_path}")
                            self.finished.emit(True, "图片生成成功", image_path)
                        else:
                            error_msg = result[0] if result and len(result) > 0 else "未知错误"
                            logger.error(f"Pollinations AI 图片生成失败: {error_msg}")
                            self.finished.emit(False, f"图片生成失败: {error_msg}", "")
                            
                    except Exception as e:
                        logger.error(f"Pollinations AI 生成过程中发生错误: {str(e)}")
                        self.finished.emit(False, f"Pollinations AI 生成过程中发生错误: {str(e)}", "")
                
                def _generate_with_comfyui(self):
                    """使用 ComfyUI 生成图片"""
                    try:
                        logger.info("使用 ComfyUI 生成图片")
                        
                        # 1. 获取LLM API实例用于翻译
                        if not self.main_window.llm_api_instance:
                            logger.debug("LLM API实例不存在，开始初始化")
                            # 在状态栏显示初始化信息
                            if hasattr(self.main_window, 'log_output_bottom'):
                                self.main_window.log_output_bottom.appendPlainText(f"🔧 正在初始化LLM API...")
                                self.main_window.log_output_bottom.verticalScrollBar().setValue(
                                    self.main_window.log_output_bottom.verticalScrollBar().maximum()
                                )
                            
                            # 从设置中获取LLM配置
                            config_manager = self.main_window.config_manager
                            models = config_manager.config.get("models", [])
                            logger.debug(f"配置中的模型数量: {len(models)}")
                            
                            if not models:
                                logger.error("未配置大模型，无法翻译提示词")
                                self.finished.emit(False, "未配置大模型，无法翻译提示词", "")
                                return
                            
                            # 使用第一个可用的模型
                            model_config = models[0]
                            logger.debug(f"使用模型配置: {model_config.get('type', 'deepseek')}")
                            from models.llm_api import LLMApi
                            self.main_window.llm_api_instance = LLMApi(
                                api_type=model_config.get("type", "deepseek"),
                                api_key=model_config.get("key", ""),
                                api_url=model_config.get("url", "")
                            )
                            logger.info("LLM API实例初始化完成")
                            
                            # 百度翻译API会自动从配置文件加载
                            logger.info("百度翻译API将从配置文件自动加载")
 
                        
                        # 2. 获取ComfyUI客户端，确保使用正确的LLM API实例
                        if hasattr(self.main_window, 'log_output_bottom'):
                            self.main_window.log_output_bottom.appendPlainText(f"🔗 正在连接ComfyUI服务...")
                            self.main_window.log_output_bottom.verticalScrollBar().setValue(
                                self.main_window.log_output_bottom.verticalScrollBar().maximum()
                            )
                        
                        comfyui_client = None
                        if hasattr(self.main_window, 'ai_drawing_tab') and self.main_window.ai_drawing_tab.comfyui_client:
                            comfyui_client = self.main_window.ai_drawing_tab.comfyui_client
                            # 更新ComfyUI客户端的LLM API实例，确保能够翻译提示词
                            comfyui_client.llm_api = self.main_window.llm_api_instance
                            logger.info("已更新ComfyUI客户端的LLM API实例")
                        else:
                            # 从设置中获取ComfyUI地址
                            comfyui_url = self.main_window.app_settings.get('comfyui_url', 'http://127.0.0.1:8188')
                            logger.debug(f"使用ComfyUI地址: {comfyui_url}")
                            from models.comfyui_client import ComfyUIClient
                            comfyui_client = ComfyUIClient(comfyui_url, self.main_window.llm_api_instance)
                            logger.info("创建了新的ComfyUI客户端实例")
                        
                        # 3. 获取当前选择的工作流
                        workflow_name = None
                        workflow_params = {}
                        if hasattr(self.main_window, 'ai_drawing_tab') and self.main_window.ai_drawing_tab.workflow_panel:
                            workflow_name = self.main_window.ai_drawing_tab.workflow_panel.get_current_workflow_name()
                            workflow_params = self.main_window.ai_drawing_tab.workflow_panel.get_current_workflow_parameters()
                            logger.info(f"使用AI绘图界面的工作流: {workflow_name}")
                            logger.debug(f"工作流参数: {workflow_params}")
                        
                        if not workflow_name or workflow_name == "请选择工作流":
                            # 使用默认工作流
                            logger.debug("未选择工作流，获取默认工作流")
                            workflow_list = comfyui_client.get_workflow_list()
                            if workflow_list:
                                workflow_name = workflow_list[0]
                                logger.info(f"使用默认工作流: {workflow_name}")
                        
                        # 4. 生成图片
                        logger.info(f"开始生成图片，工作流: {workflow_name}，提示词: {self.prompt}")
                        if hasattr(self.main_window, 'log_output_bottom'):
                            self.main_window.log_output_bottom.appendPlainText(f"⚡ 正在使用工作流 '{workflow_name}' 生成图片...")
                            self.main_window.log_output_bottom.verticalScrollBar().setValue(
                                self.main_window.log_output_bottom.verticalScrollBar().maximum()
                            )
                        
                        # 获取项目管理器和当前项目名称
                        project_manager = None
                        current_project_name = None
                        if hasattr(self.main_window, 'project_manager'):
                            project_manager = self.main_window.project_manager
                        if hasattr(self.main_window, 'current_project_name'):
                            current_project_name = self.main_window.current_project_name
                        
                        image_paths = comfyui_client.generate_image_with_workflow(self.prompt, workflow_name, workflow_params, project_manager, current_project_name)
                        
                        if image_paths and not image_paths[0].startswith("ERROR:"):
                            # 成功生成图片，返回第一张图片的路径
                            logger.info(f"图片生成成功: {image_paths[0]}")
                            self.finished.emit(True, f"成功生成图片", image_paths[0])
                        else:
                            error_msg = image_paths[0] if image_paths else "未知错误"
                            logger.error(f"图片生成失败: {error_msg}")
                            self.finished.emit(False, f"图片生成失败: {error_msg}", "")
                            
                    except Exception as e:
                        logger.error(f"ComfyUI 生成过程中发生错误: {str(e)}")
                        self.finished.emit(False, f"ComfyUI 生成过程中发生错误: {str(e)}", "")
            
            # 创建并启动绘图线程
            self.drawing_thread = DrawingThread(self, prompt, row_index, selected_engine)
            self.drawing_thread.finished.connect(lambda success, message, image_path: self._on_drawing_finished(row_index, success, message, image_path))
            self.drawing_thread.start()
            
        except Exception as e:
            logger.error(f"处理绘图请求时发生错误: {e}")
            self.storyboard_tab.hide_progress()
            QMessageBox.critical(self, "错误", f"绘图请求处理失败: {str(e)}")
    
    def _copy_image_to_project(self, source_image_path):
        """将图片复制到当前项目的images文件夹中"""
        try:
            # 检查是否有当前项目
            if not hasattr(self, 'project_manager') or not self.project_manager:
                logger.warning("项目管理器不可用，无法自动保存图片")
                return None
            
            current_project_name = self.current_project_name
            if not current_project_name:
                logger.warning("当前没有打开的项目，无法自动保存图片")
                return None
            
            # 获取项目路径
            project_root = self.project_manager.get_project_path(current_project_name)
            
            # 根据图片来源确定保存目录
            if 'comfyui' in source_image_path.lower() or 'ComfyUI' in source_image_path:
                project_images_dir = os.path.join(project_root, 'images', 'comfyui')
            elif 'pollinations' in source_image_path.lower():
                project_images_dir = os.path.join(project_root, 'images', 'pollinations')
            else:
                # 根据当前选择的引擎确定默认目录
                if hasattr(self, 'ai_drawing_tab') and hasattr(self.ai_drawing_tab, 'engine_combo'):
                    selected_engine = self.ai_drawing_tab.engine_combo.currentText()
                    if selected_engine == 'pollinations':
                        project_images_dir = os.path.join(project_root, 'images', 'pollinations')
                    else:
                        project_images_dir = os.path.join(project_root, 'images', 'comfyui')
                else:
                    # 默认使用comfyui目录
                    project_images_dir = os.path.join(project_root, 'images', 'comfyui')
            
            # 确保目标目录存在
            os.makedirs(project_images_dir, exist_ok=True)
            
            # 生成新的文件名（避免重复）
            timestamp = int(time.time() * 1000)  # 毫秒级时间戳
            original_filename = os.path.basename(source_image_path)
            name, ext = os.path.splitext(original_filename)
            new_filename = f"{name}_{timestamp}{ext}"
            
            # 目标路径
            target_path = os.path.join(project_images_dir, new_filename)
            
            # 复制文件
            shutil.copy2(source_image_path, target_path)
            
            logger.info(f"图片已复制到项目文件夹: {source_image_path} -> {target_path}")
            return target_path
            
        except Exception as e:
            logger.error(f"复制图片到项目文件夹时发生错误: {e}")
            return None
    
    def _on_drawing_finished(self, row_index, success, message, image_path):
        """绘图完成回调"""
        try:
            logger.info(f"绘图完成回调 - 行索引: {row_index}, 成功: {success}, 图片路径: {image_path}")
            self.storyboard_tab.hide_progress()
            
            # 在底部状态栏显示绘图完成信息
            if success:
                status_message = f"✅ 第{row_index+1}行图片生成成功 | 文件: {os.path.basename(image_path) if image_path else '未知'}"
            else:
                status_message = f"❌ 第{row_index+1}行图片生成失败 | 错误: {message}"
            
            if hasattr(self, 'log_output_bottom'):
                self.log_output_bottom.appendPlainText(status_message)
                # 滚动到底部显示最新信息
                self.log_output_bottom.verticalScrollBar().setValue(
                    self.log_output_bottom.verticalScrollBar().maximum()
                )
            
            # 在处理图片前，记录当前数据状态
            if hasattr(self, 'shots_data') and self.shots_data:
                logger.debug(f"绘图完成时分镜数据行数: {len(self.shots_data)}")
            else:
                logger.warning("绘图完成时分镜数据不存在或为空")
            
            if success and image_path:
                # 将相对路径转换为绝对路径
                comfyui_base_output_dir = self.app_settings.get('comfyui_output_dir', '').strip()
                if comfyui_base_output_dir and not os.path.isabs(image_path):
                    cleaned_relative_path = image_path.lstrip('\\/')
                    absolute_image_path = os.path.join(comfyui_base_output_dir, cleaned_relative_path)
                    absolute_image_path = os.path.normpath(absolute_image_path)
                    logger.info(f"转换图片路径: {image_path} -> {absolute_image_path}")
                else:
                    absolute_image_path = image_path
                
                # 检查图片文件是否存在
                if os.path.exists(absolute_image_path):
                    logger.info(f"图片文件存在，开始更新表格 - 文件大小: {os.path.getsize(absolute_image_path)} bytes")
                    
                    # 检查图片是否已经在项目目录中（避免重复复制）
                    project_image_path = None
                    if hasattr(self, 'current_project_name') and self.current_project_name:
                        if hasattr(self, 'project_manager'):
                            project_root = self.project_manager.get_project_path(self.current_project_name)
                            
                            # 检查图片是否已经在项目目录中
                            try:
                                if os.path.commonpath([absolute_image_path, project_root]) == project_root:
                                    # 图片已经在项目目录中，直接使用
                                    project_image_path = absolute_image_path
                                    logger.info(f"图片已在项目目录中，无需复制: {absolute_image_path}")
                                else:
                                    # 图片不在项目目录中，需要复制
                                    project_image_path = self._copy_image_to_project(absolute_image_path)
                            except ValueError:
                                # 路径不在同一个根目录下，需要复制
                                project_image_path = self._copy_image_to_project(absolute_image_path)
                    
                    # 更新分镜表格中的图片（优先使用项目中的图片路径）
                    final_image_path = project_image_path if project_image_path else absolute_image_path
                    if self.update_shot_images(row_index, final_image_path):
                        # 使用状态栏显示成功信息，避免模态对话框影响分镜窗口
                        if hasattr(self, 'statusBar'):
                            self.statusBar().showMessage(f"第{row_index+1}行图片生成成功！路径: {os.path.basename(absolute_image_path)}", 5000)
                        logger.info(f"第{row_index+1}行图片生成成功: {absolute_image_path}")
                        
                        # 刷新分镜设置界面的进度显示
                        try:
                            if hasattr(self, 'shots_data') and self.shots_data:
                                self.show_shots_in_settings_tab(self.shots_data)
                                logger.info("已刷新分镜设置界面的进度显示")
                        except Exception as refresh_error:
                            logger.error(f"刷新分镜设置界面进度显示失败: {refresh_error}")
                    else:
                        logger.warning(f"图片生成成功但更新表格失败，图片路径: {absolute_image_path}")
                        if hasattr(self, 'statusBar'):
                            self.statusBar().showMessage(f"第{row_index+1}行图片生成成功但更新表格失败", 5000)
                else:
                    logger.error(f"生成的图片文件不存在: {absolute_image_path}")
                    if hasattr(self, 'statusBar'):
                        self.statusBar().showMessage(f"第{row_index+1}行图片生成成功但文件不存在", 5000)
            else:
                logger.warning(f"第{row_index+1}行图片生成失败: {message}")
                if hasattr(self, 'statusBar'):
                    self.statusBar().showMessage(f"第{row_index+1}行图片生成失败", 5000)
                
        except Exception as e:
            logger.error(f"绘图完成回调处理错误: {e}")
            QMessageBox.critical(self, "错误", f"绘图结果处理失败: {str(e)}")
    
    def populate_shots_table_data(self, shots_data):
        print(f"[DEBUG] main_window.populate_shots_table_data - shots_data: {shots_data}")
        print(f"[DEBUG] main_window.populate_shots_table_data - len(shots_data): {len(shots_data) if shots_data else 0}")
        """填充分镜表格数据"""
        try:
            if not self.shots_table or not shots_data:
                return
            
            # 设置表格行数
            self.shots_table.setRowCount(len(shots_data))
            
            # 填充数据
            for row, shot in enumerate(shots_data):
                # 文案列（索引0）- 使用正确的字段名 'description'
                if 'description' in shot:
                    self.shots_table.setItem(row, 0, QTableWidgetItem(str(shot['description'])))
                
                # 分镜列（索引1）
                if 'scene' in shot:
                    self.shots_table.setItem(row, 1, QTableWidgetItem(str(shot['scene'])))
                
                # 角色列（索引2）- 使用正确的字段名 'role'
                if 'role' in shot:
                    self.shots_table.setItem(row, 2, QTableWidgetItem(str(shot['role'])))
                
                # 提示词列（索引3）- 使用正确的字段名 'prompt'
                if 'prompt' in shot:
                    self.shots_table.setItem(row, 3, QTableWidgetItem(str(shot['prompt'])))
                
                # 主图列（索引4）
                if 'image' in shot and shot['image']:
                    self.shots_table.setItem(row, 4, QTableWidgetItem(str(shot['image'])))
                else:
                    self.shots_table.setItem(row, 4, QTableWidgetItem(""))
                
                # 视频提示词列（索引5）
                if 'video_prompt' in shot:
                    self.shots_table.setItem(row, 5, QTableWidgetItem(str(shot['video_prompt'])))
                
                # 音效列（索引6）- 使用正确的字段名 'audio'
                if 'audio' in shot and shot['audio']:
                    self.shots_table.setItem(row, 6, QTableWidgetItem(str(shot['audio'])))
                else:
                    self.shots_table.setItem(row, 6, QTableWidgetItem(""))
                
                # 操作列（索引7）
                operation_widget = self.create_operation_buttons(row)
                self.shots_table.setCellWidget(row, 7, operation_widget)
                
                # 备选图片列（索引8）- 使用正确的字段名 'alternative_images'
                if 'alternative_images' in shot and shot['alternative_images']:
                    self.shots_table.setItem(row, 8, QTableWidgetItem(str(shot['alternative_images'])))
                else:
                    self.shots_table.setItem(row, 8, QTableWidgetItem(""))
            
            logger.info(f"成功填充{len(shots_data)}行分镜数据")
            
        except Exception as e:
            logger.error(f"填充分镜表格数据时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"填充分镜表格数据失败: {str(e)}")
    
    def on_alternative_image_selected(self, row, image_path):
        """当备选图片被选择时的回调函数"""
        return self.on_shots_alternative_image_selected(row, image_path)
    
    def create_operation_buttons(self, row_index):
        """为指定行创建操作按钮组件"""
        from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
        from PyQt5.QtCore import Qt
        
        # 创建按钮容器
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(10, 5, 10, 5)  # 增加边距
        button_layout.setSpacing(8)  # 增加按钮间距
        button_layout.setAlignment(Qt.AlignCenter)  # 居中对齐
        
        # 绘图按钮
        draw_btn = QPushButton("绘图")
        draw_btn.setProperty("class", "draw-button")
        draw_btn.setMinimumSize(80, 40)  # 增大按钮尺寸
        draw_btn.setMaximumSize(100, 45)  # 增大按钮尺寸
        draw_btn.clicked.connect(lambda: self.handle_draw_btn(row_index))
        button_layout.addWidget(draw_btn)
        
        # 配音按钮
        voice_btn = QPushButton("配音")
        voice_btn.setProperty("class", "voice-button")
        voice_btn.setMinimumSize(80, 40)  # 增大按钮尺寸
        voice_btn.setMaximumSize(100, 45)  # 增大按钮尺寸
        voice_btn.clicked.connect(lambda: self.handle_voice_btn(row_index))
        button_layout.addWidget(voice_btn)
        
        # 分镜设置按钮
        setting_btn = QPushButton("分镜设置")
        setting_btn.setProperty("class", "setting-button")
        setting_btn.setMinimumSize(100, 40)  # 增大按钮尺寸（分镜设置文字较长）
        setting_btn.setMaximumSize(120, 45)  # 增大按钮尺寸
        setting_btn.clicked.connect(lambda: self.handle_shot_setting_btn(row_index))
        button_layout.addWidget(setting_btn)
        
        return button_widget
    
    def handle_draw_btn(self, row_index):
        """处理绘图按钮点击事件"""
        try:
            logger.info(f"开始处理第{row_index + 1}行的绘图请求")
            
            # 在状态栏显示绘图操作开始信息
            start_message = f"🎨 用户点击第{row_index + 1}行绘图按钮，开始处理绘图请求..."
            self.log_output_bottom.appendPlainText(start_message)
            
            # 获取当前项目数据
            current_project_data = self.get_current_project_data()
            if not current_project_data:
                warning_message = f"⚠️ 第{row_index + 1}行绘图失败：请先加载项目数据"
                self.log_output_bottom.appendPlainText(warning_message)
                QMessageBox.warning(self, "警告", "请先加载项目数据")
                return
            
            shots_data = current_project_data.get('shots_data', [])
            if row_index >= len(shots_data):
                warning_message = f"⚠️ 第{row_index + 1}行绘图失败：无效的分镜索引"
                self.log_output_bottom.appendPlainText(warning_message)
                QMessageBox.warning(self, "警告", "无效的分镜索引")
                return
            
            shot_data = shots_data[row_index]
            
            # 从shot_data中提取提示词
            prompt = shot_data.get('prompt', '') or shot_data.get('description', '')
            if not prompt:
                warning_message = f"⚠️ 第{row_index + 1}行绘图失败：没有提示词内容"
                self.log_output_bottom.appendPlainText(warning_message)
                QMessageBox.warning(self, "警告", f"第{row_index + 1}行没有提示词内容")
                return
            
            # 调用绘图处理方法，参数顺序：row_index, prompt
            self.process_draw_request(row_index, prompt)
            
        except Exception as e:
            logger.error(f"处理绘图按钮点击事件时发生错误: {e}")
            error_message = f"❌ 第{row_index + 1}行绘图处理失败: {str(e)}"
            self.log_output_bottom.appendPlainText(error_message)
            QMessageBox.critical(self, "错误", f"绘图处理失败: {str(e)}")
    
    def handle_voice_btn(self, row_index):
        """处理配音按钮点击事件"""
        try:
            logger.info(f"开始处理第{row_index + 1}行的配音请求")            # 在状态栏显示配音操作信息
            status_message = f"🎵 正在处理第{row_index + 1}行的配音请求..."
            self.log_output_bottom.appendPlainText(status_message)
            
            QMessageBox.information(self, "提示", "配音功能正在开发中")
            
            # 在状态栏显示配音操作完成信息
            completion_message = f"ℹ️ 第{row_index + 1}行配音功能提示已显示（功能开发中）"
            self.log_output_bottom.appendPlainText(completion_message)
        except Exception as e:
            logger.error(f"处理配音按钮点击事件时发生错误: {e}")
            error_message = f"❌ 第{row_index + 1}行配音处理失败: {str(e)}"
            self.log_output_bottom.appendPlainText(error_message)
            QMessageBox.critical(self, "错误", f"配音处理失败: {str(e)}")
    
    def handle_shot_setting_btn(self, row_index):
        """处理分镜设置按钮点击事件"""
        try:
            logger.info(f"开始处理第{row_index + 1}行的分镜设置请求")
            # 在状态栏显示分镜设置操作信息
            status_message = f"⚙️ 正在处理第{row_index + 1}行的分镜设置请求..."
            self.log_output_bottom.appendPlainText(status_message)
            
            QMessageBox.information(self, "提示", "分镜设置功能正在开发中")
            
            # 在状态栏显示分镜设置操作完成信息
            completion_message = f"ℹ️ 第{row_index + 1}行分镜设置功能提示已显示（功能开发中）"
            self.log_output_bottom.appendPlainText(completion_message)
        except Exception as e:
            logger.error(f"处理分镜设置按钮点击事件时发生错误: {e}")
            error_message = f"❌ 第{row_index + 1}行分镜设置处理失败: {str(e)}"
            self.log_output_bottom.appendPlainText(error_message)
            QMessageBox.critical(self, "错误", f"分镜设置处理失败: {str(e)}")

    


    def closeEvent(self, event):
        logger.info("主窗口关闭事件触发")
        # Clean up temporary files if they exist
        if self.temp_rewrite_file and os.path.exists(self.temp_rewrite_file):
            try:
                os.remove(self.temp_rewrite_file)
                logger.info(f"临时文件 {self.temp_rewrite_file} 已删除。")
            except Exception as e:
                logger.error(f"删除临时文件 {self.temp_rewrite_file} 失败: {e}")

        if hasattr(self, 'comfyui_webview') and self.comfyui_webview:
            # 显式销毁 QWebEnginePage，因为它可能持有对 profile 的引用
            if self.comfyui_webview.page():
                self.comfyui_webview.page().deleteLater()
                logger.info("ComfyUI Webview Page 已标记为删除。")
            self.comfyui_webview.deleteLater()
            logger.info("ComfyUI Webview 已标记为删除。")
        event.accept() # Accept the close event
    
    def on_shot_selection_changed(self):
        """分镜选择改变时的处理"""
        try:
            if hasattr(self, 'shots_settings_table') and self.shots_settings_table:
                current_row = self.shots_settings_table.currentRow()
                self.current_shot_index = current_row
                logger.info(f"当前选中分镜: {current_row + 1 if current_row >= 0 else '无'}")
        except Exception as e:
            logger.error(f"处理分镜选择改变时发生错误: {e}")
    
    def refresh_model_list(self):
        """刷新所有组件的模型列表"""
        try:
            # 重新加载配置管理器
            self.config_manager = ConfigManager(
                config_dir=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config")
            )
            
            # 刷新故事板标签页的模型列表
            if hasattr(self, 'storyboard_tab') and hasattr(self.storyboard_tab, 'refresh_model_combo'):
                self.storyboard_tab.refresh_model_combo()
                logger.info("已刷新故事板标签页的模型列表")
            
            # 刷新设置标签页的模型配置
            if hasattr(self, 'settings_tab') and hasattr(self.settings_tab, 'load_settings'):
                self.settings_tab.config_manager = self.config_manager
                self.settings_tab.load_settings()
                logger.info("已刷新设置标签页的模型配置")
                
            logger.info("模型列表刷新完成")
            
        except Exception as e:
            logger.error(f"刷新模型列表时发生错误: {e}")
    
    def handle_batch_draw(self):
        """处理批量绘图按钮点击事件"""
        try:
            logger.info("开始批量绘图操作")
            
            # 获取当前项目数据
            current_project_data = self.get_current_project_data()
            if not current_project_data:
                QMessageBox.warning(self, "警告", "请先加载项目数据")
                return
            
            shots_data = current_project_data.get('shots_data', [])
            if not shots_data:
                QMessageBox.warning(self, "警告", "没有分镜数据可供绘图")
                return
            
            # 构建绘图队列
            self.batch_queue = []
            skip_existing = self.skip_existing_checkbox.isChecked()
            
            for i, shot in enumerate(shots_data):
                # 如果选择跳过已有图片，检查是否已有图片
                if skip_existing and shot.get('image') and shot['image'].strip():
                    logger.info(f"跳过第{i+1}行，已有图片: {shot['image']}")
                    continue
                
                # 检查是否有有效的提示词
                prompt = shot.get('prompt', '').strip()
                if not prompt:
                    logger.warning(f"第{i+1}行没有提示词，跳过")
                    continue
                
                self.batch_queue.append({
                    'index': i,
                    'shot_data': shot,
                    'prompt': prompt
                })
            
            if not self.batch_queue:
                if skip_existing:
                    QMessageBox.information(self, "提示", "所有分镜都已有图片，无需重新生成")
                else:
                    QMessageBox.warning(self, "警告", "没有有效的分镜数据可供绘图")
                return
            
            # 初始化批量绘图状态
            self.is_batch_drawing = True
            self.batch_current_index = 0
            self.batch_total_count = len(self.batch_queue)
            self.batch_success_count = 0
            self.batch_failed_count = 0
            
            # 更新UI状态
            self.batch_draw_btn.setEnabled(False)
            self.stop_batch_btn.setEnabled(True)
            self.update_batch_progress()
            
            # 在状态栏显示开始信息
            start_message = f"🎨 开始批量绘图，共 {self.batch_total_count} 个分镜待处理..."
            self.log_output_bottom.appendPlainText(start_message)
            self.log_output_bottom.verticalScrollBar().setValue(
                self.log_output_bottom.verticalScrollBar().maximum()
            )
            
            # 开始处理第一个任务
            self.process_next_batch_item()
            
        except Exception as e:
            logger.error(f"处理批量绘图时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"批量绘图失败: {str(e)}")
            self.reset_batch_state()
    
    def handle_stop_batch(self):
        """处理停止批量绘图按钮点击事件"""
        try:
            logger.info("用户请求停止批量绘图")
            
            # 停止当前绘图线程
            if hasattr(self, 'drawing_thread') and self.drawing_thread and self.drawing_thread.isRunning():
                self.drawing_thread.terminate()
                self.drawing_thread.wait(1000)  # 等待最多1秒
                logger.info("已终止当前绘图线程")
            
            # 重置批量状态
            self.reset_batch_state()
            
            # 在状态栏显示停止信息
            stop_message = f"⏹️ 批量绘图已停止 - 成功: {self.batch_success_count}, 失败: {self.batch_failed_count}"
            self.log_output_bottom.appendPlainText(stop_message)
            self.log_output_bottom.verticalScrollBar().setValue(
                self.log_output_bottom.verticalScrollBar().maximum()
            )
            
            QMessageBox.information(self, "提示", "批量绘图已停止")
            
        except Exception as e:
            logger.error(f"停止批量绘图时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"停止批量绘图失败: {str(e)}")
    
    def process_next_batch_item(self):
        """处理下一个批量绘图项目"""
        try:
            # 检查是否还有待处理的项目
            if not self.is_batch_drawing or self.batch_current_index >= len(self.batch_queue):
                self.finish_batch_drawing()
                return
            
            # 获取当前项目
            current_item = self.batch_queue[self.batch_current_index]
            row_index = current_item['index']
            shot_data = current_item['shot_data']
            prompt = current_item['prompt']
            
            logger.info(f"开始处理批量绘图第 {self.batch_current_index + 1}/{self.batch_total_count} 项，分镜行 {row_index + 1}")
            
            # 在状态栏显示当前处理信息
            current_message = f"🎨 正在处理第 {self.batch_current_index + 1}/{self.batch_total_count} 项 (分镜 {row_index + 1})..."
            self.log_output_bottom.appendPlainText(current_message)
            self.log_output_bottom.verticalScrollBar().setValue(
                self.log_output_bottom.verticalScrollBar().maximum()
            )
            
            # 更新进度显示
            self.update_batch_progress()
            
            # 调用现有的绘图处理方法，但需要修改回调
            self.process_batch_draw_request(shot_data, row_index)
            
        except Exception as e:
            logger.error(f"处理批量绘图项目时发生错误: {e}")
            self.batch_failed_count += 1
            self.batch_current_index += 1
            self.process_next_batch_item()  # 继续处理下一个
    
    def process_batch_draw_request(self, shot_data, row_index):
        """处理批量绘图请求（基于现有的process_draw_request方法）"""
        try:
            prompt = shot_data.get('prompt', '')
            logger.info(f"开始处理批量绘图第{row_index+1}行的绘图请求")
            logger.debug(f"使用提示词栏中的内容: {prompt}")
            
            # 直接使用提示词栏中的内容，不再根据风格重新生成
            # 这样可以确保用户在提示词栏中的修改得到尊重
            
            from PyQt5.QtCore import QThread, pyqtSignal
            
            # 创建批量绘图线程（基于现有的DrawingThread）
            class BatchDrawingThread(QThread):
                finished = pyqtSignal(bool, str, str)  # success, message, image_path
                
                def __init__(self, main_window, prompt, row_index):
                    super().__init__()
                    self.main_window = main_window
                    self.prompt = prompt
                    self.row_index = row_index
                
                def run(self):
                    try:
                        logger.info(f"批量绘图线程开始运行，行索引: {self.row_index}")
                        
                        # 复用现有的绘图逻辑
                        # 1. 获取LLM API实例用于翻译
                        if not self.main_window.llm_api_instance:
                            logger.debug("LLM API实例不存在，开始初始化")
                            
                            # 从设置中获取LLM配置
                            config_manager = self.main_window.config_manager
                            models = config_manager.config.get("models", [])
                            logger.debug(f"配置中的模型数量: {len(models)}")
                            
                            if not models:
                                logger.error("未配置大模型，无法翻译提示词")
                                self.finished.emit(False, "未配置大模型，无法翻译提示词", "")
                                return
                            
                            # 使用第一个可用的模型
                            model_config = models[0]
                            logger.debug(f"使用模型配置: {model_config.get('type', 'deepseek')}")
                            from models.llm_api import LLMApi
                            self.main_window.llm_api_instance = LLMApi(
                                api_type=model_config.get("type", "deepseek"),
                                api_key=model_config.get("key", ""),
                                api_url=model_config.get("url", "")
                            )
                            logger.info("LLM API实例初始化完成")
                            
                            # 百度翻译API会自动从配置文件加载
                            logger.info("百度翻译API将从配置文件自动加载")
 
                        
                        # 2. 初始化图像生成服务
                        if not hasattr(self.main_window, 'image_generation_service') or not self.main_window.image_generation_service:
                            self.main_window._init_image_generation_service()
                        
                        if not self.main_window.image_generation_service:
                            raise Exception("图像生成服务初始化失败")
                        
                        # 3. 生成图片
                        ai_drawing_tab = self.main_window.ai_drawing_tab
                        if not ai_drawing_tab:
                            logger.error("无法获取AI绘图标签页的引用")
                            self.finished.emit(False, "无法获取AI绘图设置", "")
                            return

                        current_engine = ai_drawing_tab.get_current_engine_name() # 使用新的方法获取引擎名称
                        logger.info(f"批量绘图线程开始生成图片，引擎: {current_engine}，提示词: {self.prompt[:50]}...")

                        # 获取项目管理器和当前项目名称 (如果需要传递给生成服务)
                        project_manager = getattr(self.main_window, 'project_manager', None)
                        current_project_name = getattr(self.main_window, 'current_project_name', None)

                        image_paths = [] # 用于接收生成结果，期望是路径列表或单个路径字符串
                        error_message_detail = ""

                        if current_engine == "comfyui":
                            if not self.main_window.image_generation_service:
                                self.main_window._init_image_generation_service() # 确保服务已初始化
                            if not self.main_window.image_generation_service:
                                error_message_detail = "ComfyUI 图像生成服务初始化失败"
                                logger.error(error_message_detail)
                                self.finished.emit(False, error_message_detail, "")
                                return
                            
                            # 为 ComfyUI 获取特定设置
                            comfyui_settings = self.main_window.ai_drawing_tab.get_current_comfyui_settings()
                            workflow_name = comfyui_settings.get('workflow_name')
                            workflow_params = comfyui_settings.get('workflow_parameters', {})

                            if not workflow_name:
                                error_message_detail = "无法获取 ComfyUI 工作流名称，跳过生成"
                                logger.error(error_message_detail)
                                self.finished.emit(False, error_message_detail, "")
                                return

                            logger.info(f"使用 ComfyUI 生成图像，工作流: {workflow_name}, 提示词: {self.prompt[:50]}, 参数: {workflow_params}")
                            # 将故事板的提示词优先放入参数中，如果工作流参数中已有prompt，则会被覆盖
                            workflow_params['prompt'] = self.prompt

                            image_paths = self.main_window.image_generation_service.generate_image(
                                prompt=self.prompt, # 主提示词，部分工作流可能直接使用
                                workflow_id=workflow_name,
                                parameters=workflow_params, # 包含具体节点参数和可能覆盖的prompt
                                project_manager=project_manager, 
                                current_project_name=current_project_name
                            )
                        elif current_engine == "pollinations":
                            if not self.main_window.pollinations_client:
                                # 确保 PollinationsClient 已初始化
                                from models.pollinations_client import PollinationsClient
                                self.main_window.pollinations_client = PollinationsClient()
                                logger.info("Pollinations AI 客户端已在批量绘图线程中按需初始化")
                            
                            if not self.main_window.pollinations_client:
                                error_message_detail = "Pollinations AI 客户端初始化失败"
                                logger.error(error_message_detail)
                                self.finished.emit(False, error_message_detail, "")
                                return
                            
                            pollinations_settings = ai_drawing_tab.get_current_pollinations_settings()
                            pollinations_settings['prompt'] = self.prompt # 将主提示词添加到设置中
                            logger.debug(f"Pollinations AI settings for batch: {pollinations_settings}")

                            image_paths = self.main_window.pollinations_client.generate_image(
                                project_manager=project_manager,
                                current_project_name=current_project_name,
                                **pollinations_settings # Pass settings as kwargs
                            )
                        else:
                            error_message_detail = f"未知的图像生成引擎: {current_engine}"
                            logger.error(error_message_detail)
                            self.finished.emit(False, error_message_detail, "")
                            return

                        # 处理生成结果
                        if image_paths: # 检查是否有结果
                            # 统一处理 image_paths，确保其为列表
                            if isinstance(image_paths, str):
                                image_paths = [image_paths]
                            
                            if isinstance(image_paths, list) and len(image_paths) > 0:
                                first_image_path = image_paths[0]
                                if not str(first_image_path).startswith("ERROR:"):
                                    logger.info(f"图片生成成功: {first_image_path}")
                                    self.finished.emit(True, f"成功生成图片", first_image_path)
                                    return
                                else:
                                    error_msg = first_image_path
                                    logger.error(f"图片生成失败: {error_msg}")
                                    self.finished.emit(False, f"图片生成失败: {error_msg}", "")
                                    return
                        
                        # 如果 image_paths 为空或不符合预期格式
                        error_msg = "未知错误或无图片返回"
                        logger.error(f"图片生成失败: {error_msg}")
                        self.finished.emit(False, f"图片生成失败: {error_msg}", "")
                            
                    except Exception as e:
                        logger.error(f"批量绘图过程中发生错误: {str(e)}")
                        self.finished.emit(False, f"绘图过程中发生错误: {str(e)}", "")
            
            # 创建并启动批量绘图线程
            self.drawing_thread = BatchDrawingThread(self, prompt, row_index)
            self.drawing_thread.finished.connect(lambda success, message, image_path: self._on_batch_drawing_finished(row_index, success, message, image_path))
            self.drawing_thread.start()
            
        except Exception as e:
            logger.error(f"处理批量绘图请求时发生错误: {e}")
            self.batch_failed_count += 1
            self.batch_current_index += 1
            self.process_next_batch_item()  # 继续处理下一个
    
    def apply_style_to_prompt(self, prompt, style_template):
        """将风格应用到提示词（复用现有逻辑）"""
        try:
            # 定义需要替换的冲突风格关键词
            conflicting_keywords = {
                '电影感', '戏剧性光影', '超写实', '胶片颗粒', '景深',  # 电影风格
                '动漫风', '鲜艳色彩', '干净线条', '赛璐璐渲染', '日本动画',  # 动漫风格
                '吉卜力风', '柔和色彩', '奇幻', '梦幻', '丰富背景',  # 吉卜力风格
                '赛博朋克', '霓虹灯', '未来都市', '雨夜', '暗色氛围',  # 赛博朋克风格
                '水彩画风', '柔和笔触', '粉彩色', '插画', '温柔',  # 水彩插画风格
                '像素风', '8位', '复古', '低分辨率', '游戏风',  # 像素风格
                '真实光线', '高细节', '写实摄影'  # 写实摄影风格
            }
            
            # 移除原始提示词中的冲突风格关键词
            cleaned_prompt = prompt
            for keyword in conflicting_keywords:
                # 移除关键词及其前后的标点符号
                cleaned_prompt = cleaned_prompt.replace(f"，{keyword}", "")
                cleaned_prompt = cleaned_prompt.replace(f"{keyword}，", "")
                cleaned_prompt = cleaned_prompt.replace(f"。{keyword}", "")
                cleaned_prompt = cleaned_prompt.replace(f"{keyword}。", "")
                cleaned_prompt = cleaned_prompt.replace(keyword, "")
            
            # 清理多余的标点符号
            cleaned_prompt = cleaned_prompt.replace("，，", "，").replace("。。", "。")
            cleaned_prompt = cleaned_prompt.strip("，。 ")
            
            # 提取风格关键词（去掉模板占位符）
            style_keywords = style_template.replace('{scene}，', '').replace('{role}，', '').replace('{scene}', '').replace('{role}', '')
            
            # 应用新风格
            if cleaned_prompt:
                new_prompt = f"{cleaned_prompt}，{style_keywords}"
            else:
                new_prompt = style_keywords
            
            return new_prompt
            
        except Exception as e:
            logger.error(f"应用风格到提示词时发生错误: {e}")
            return prompt  # 出错时返回原始提示词
    
    def _on_batch_drawing_finished(self, row_index, success, message, image_path):
        """批量绘图完成回调"""
        try:
            if success:
                self.batch_success_count += 1
                logger.info(f"批量绘图第 {self.batch_current_index + 1} 项成功完成，分镜行 {row_index + 1}")
                
                # 更新分镜数据和表格显示（使用与单个绘图相同的逻辑）
                if image_path:
                    # 将相对路径转换为绝对路径
                    comfyui_base_output_dir = self.app_settings.get('comfyui_output_dir', '').strip()
                    if comfyui_base_output_dir and not os.path.isabs(image_path):
                        cleaned_relative_path = image_path.lstrip('\\/')
                        absolute_image_path = os.path.join(comfyui_base_output_dir, cleaned_relative_path)
                        absolute_image_path = os.path.normpath(absolute_image_path)
                        logger.info(f"转换图片路径: {image_path} -> {absolute_image_path}")
                    else:
                        absolute_image_path = image_path
                    
                    # 检查图片文件是否存在
                    if os.path.exists(absolute_image_path):
                        logger.info(f"图片文件存在，开始更新表格 - 文件大小: {os.path.getsize(absolute_image_path)} bytes")
                        
                        # 自动复制图片到项目文件夹
                        project_image_path = self._copy_image_to_project(absolute_image_path)
                        
                        # 更新分镜表格中的图片（优先使用项目中的图片路径）
                        final_image_path = project_image_path if project_image_path else absolute_image_path
                        if self.update_shot_images(row_index, final_image_path):
                            logger.info(f"批量绘图第{row_index+1}行图片生成成功: {absolute_image_path}")
                        else:
                            logger.warning(f"批量绘图图片生成成功但更新表格失败，图片路径: {absolute_image_path}")
                    else:
                        logger.error(f"批量绘图生成的图片文件不存在: {absolute_image_path}")
                
                # 在状态栏显示成功信息
                success_message = f"✅ 第 {self.batch_current_index + 1}/{self.batch_total_count} 项完成 (分镜 {row_index + 1})"
                self.log_output_bottom.appendPlainText(success_message)
                
            else:
                self.batch_failed_count += 1
                logger.error(f"批量绘图第 {self.batch_current_index + 1} 项失败，分镜行 {row_index + 1}: {message}")
                
                # 在状态栏显示失败信息
                error_message = f"❌ 第 {self.batch_current_index + 1}/{self.batch_total_count} 项失败 (分镜 {row_index + 1}): {message}"
                self.log_output_bottom.appendPlainText(error_message)
            
            # 滚动到底部
            self.log_output_bottom.verticalScrollBar().setValue(
                self.log_output_bottom.verticalScrollBar().maximum()
            )
            
            # 移动到下一个项目
            self.batch_current_index += 1
            
            # 继续处理下一个项目
            self.process_next_batch_item()
            
        except Exception as e:
            logger.error(f"处理批量绘图完成回调时发生错误: {e}")
            self.batch_failed_count += 1
            self.batch_current_index += 1
            self.process_next_batch_item()
    
    def update_batch_progress(self):
        """更新批量绘图进度显示"""
        try:
            if self.is_batch_drawing:
                progress_text = f"进度: {self.batch_current_index}/{self.batch_total_count}"
                if self.batch_success_count > 0 or self.batch_failed_count > 0:
                    progress_text += f" (成功: {self.batch_success_count}, 失败: {self.batch_failed_count})"
            else:
                progress_text = "进度: 0/0"
            
            self.batch_progress_label.setText(progress_text)
            
        except Exception as e:
            logger.error(f"更新批量绘图进度时发生错误: {e}")
    
    def finish_batch_drawing(self):
        """完成批量绘图"""
        try:
            logger.info(f"批量绘图完成 - 总计: {self.batch_total_count}, 成功: {self.batch_success_count}, 失败: {self.batch_failed_count}")
            
            # 重置状态
            self.reset_batch_state()
            
            # 在状态栏显示完成信息
            if self.batch_failed_count == 0:
                completion_message = f"🎉 批量绘图全部完成！成功生成 {self.batch_success_count} 张图片"
                QMessageBox.information(self, "完成", f"批量绘图全部完成！\n成功生成 {self.batch_success_count} 张图片")
            else:
                completion_message = f"⚠️ 批量绘图完成 - 成功: {self.batch_success_count}, 失败: {self.batch_failed_count}"
                QMessageBox.warning(self, "完成", f"批量绘图完成\n成功: {self.batch_success_count}\n失败: {self.batch_failed_count}")
            
            self.log_output_bottom.appendPlainText(completion_message)
            self.log_output_bottom.verticalScrollBar().setValue(
                self.log_output_bottom.verticalScrollBar().maximum()
            )
            
        except Exception as e:
            logger.error(f"完成批量绘图时发生错误: {e}")
    
    def reset_batch_state(self):
        """重置批量绘图状态"""
        try:
            self.is_batch_drawing = False
            self.batch_current_index = 0
            self.batch_queue = []
            
            # 更新UI状态
            self.batch_draw_btn.setEnabled(True)
            self.stop_batch_btn.setEnabled(False)
            self.update_batch_progress()
            
        except Exception as e:
            logger.error(f"重置批量绘图状态时发生错误: {e}")
    
    def update_shot_image_in_table(self, row_index, image_path):
        """更新表格中指定行的图片"""
        try:
            if hasattr(self, 'shots_table') and self.shots_table and row_index < self.shots_table.rowCount():
                # 更新主图列（索引4）
                image_item = QTableWidgetItem(image_path)
                image_item.setToolTip(f"图片路径: {image_path}")
                self.shots_table.setItem(row_index, 4, image_item)
                
                # 强制刷新表格显示
                self.shots_table.viewport().update()
                model_index = self.shots_table.model().index(row_index, 4)
                self.shots_table.update(model_index)
                
                logger.info(f"已更新表格第{row_index+1}行的图片显示")
                
        except Exception as e:
            logger.error(f"更新表格图片时发生错误: {e}")
            QMessageBox.warning(self, "警告", f"刷新模型列表失败: {str(e)}")


# 注释掉独立启动代码，避免与main.py冲突
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     window.show()
#     sys.exit(app.exec_())
