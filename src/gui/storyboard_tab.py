import sys
import os
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QPushButton,
    QPlainTextEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QScrollArea, QGridLayout, QFrame, QSpacerItem,
    QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from .text_processing_threads import TextRewriteThread, ShotsGenerationThread

from utils.logger import logger
from models.llm_api import LLMApi
from models.text_parser import TextParser
from utils.config_manager import ConfigManager
from gui.shots_window import ShotsWindow
from gui.ui_components import ImageDelegate
from gui.project_name_dialog import ProjectNameDialog
from utils.project_manager import ProjectManager


class StoryboardTab(QWidget):
    """文本转分镜标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        
        # 初始化组件
        self.llm_api = None
        self.text_parser = None
        self.config_manager = ConfigManager()
        self.project_manager = ProjectManager(self.config_manager.config_dir)
        
        # 当前项目信息
        self.current_project_name = None
        self.current_project_root = None
        
        # 界面状态管理
        self.current_view_state = "default"  # "default" 或 "shots_list"
        self.is_generating = False  # 是否正在生成分镜
        self.stop_generation = False  # 停止生成标志
        
        # 线程相关
        self.rewrite_thread = None
        self.shots_thread = None
        
        # 分镜表格相关组件
        self.shots_table_widget = None
        self.shots_display_widget = None
        self.compact_output_text = None
        self.back_to_edit_btn = None
        self.fullscreen_shots_widget = None
        
        self.init_ui()
        self.load_models()
    
    def _auto_save_project(self):
        """自动保存项目状态"""
        if self.current_project_name and self.parent_window:
            try:
                # 获取当前项目数据
                project_data = self.parent_window.get_current_project_data()
                
                # 保存项目
                success = self.project_manager.save_project(self.current_project_name, project_data)
                if success:
                    logger.info(f"项目已自动保存: {self.current_project_name}")
                else:
                    logger.error(f"项目自动保存失败: {self.current_project_name}")
            except Exception as e:
                logger.error(f"自动保存项目时发生错误: {e}")
        
    def init_ui(self):
        """初始化UI界面"""
        # 创建主分割器
        storyboard_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：原文输入
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("请输入小说原文或内容文本（支持 Markdown/TXT）："))
        
        self.text_input = QPlainTextEdit()
        self.text_input.setPlaceholderText("在此输入或粘贴小说原文、分镜脚本等内容...")
        self.text_input.setToolTip("输入原文或脚本，支持Markdown/TXT")
        left_layout.addWidget(self.text_input)

        # 风格选择下拉框
        style_select_layout = QHBoxLayout()
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "电影风格", "动漫风格", "吉卜力风格", "赛博朋克风格", "水彩插画风格", "像素风格", "写实摄影风格"
        ])
        # 连接风格选择变化事件
        self.style_combo.currentTextChanged.connect(self.on_style_changed)
        style_select_layout.addWidget(QLabel("选择风格："))
        style_select_layout.addWidget(self.style_combo)
        style_select_layout.addStretch()
        self.style_combo.setToolTip("选择分镜和生图的风格模板")
        left_layout.addLayout(style_select_layout)
        
        # 恢复上次选择的风格
        self.restore_style_selection()

        # 模型选择下拉框
        model_select_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        model_select_layout.addWidget(QLabel("选择大模型："))
        model_select_layout.addWidget(self.model_combo)
        model_select_layout.addStretch()
        self.model_combo.setToolTip("选择用于改写/分镜的大模型")
        left_layout.addLayout(model_select_layout)
        
        # 改写文章按钮
        self.rewrite_btn = QPushButton("改写文章")
        self.rewrite_btn.clicked.connect(self.handle_rewrite_btn)
        self.rewrite_btn.setToolTip("点击调用大模型对文本进行改写")
        left_layout.addWidget(self.rewrite_btn)
        
        left_widget.setLayout(left_layout)

        # 右侧：分镜/脚本/生图描述展示
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("分镜/脚本/生图描述（大模型输出）："))
        
        self.output_text = QPlainTextEdit()
        self.output_text.setToolTip("显示大模型输出的分镜/脚本/描述")
        right_layout.addWidget(self.output_text)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        self.generate_shots_btn = QPushButton("生成分镜")
        self.generate_shots_btn.clicked.connect(self.handle_generate_shots_btn)
        self.generate_shots_btn.setToolTip("根据大模型输出生成分镜表")
        button_layout.addWidget(self.generate_shots_btn)
        
        self.stop_generate_btn = QPushButton("停止生成")
        self.stop_generate_btn.clicked.connect(self.handle_stop_generate_btn)
        self.stop_generate_btn.setToolTip("停止当前的分镜生成任务")
        self.stop_generate_btn.setEnabled(False)  # 初始状态为禁用
        button_layout.addWidget(self.stop_generate_btn)
        
        right_layout.addLayout(button_layout)
        
        # 添加分镜生成专用进度条
        from PyQt5.QtWidgets import QProgressBar
        self.storyboard_progress = QProgressBar()
        self.storyboard_progress.setVisible(False)  # 初始时隐藏
        self.storyboard_progress.setFixedHeight(32)
        self.storyboard_progress.setMinimumWidth(200)
        # 设置进度条样式
        self.storyboard_progress.setStyleSheet("""
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
        right_layout.addWidget(self.storyboard_progress)
        
        right_widget.setLayout(right_layout)

        # 创建可切换的右侧区域
        self.right_stack_widget = QWidget()
        right_stack_layout = QVBoxLayout()
        
        # 默认显示的右侧区域
        self.default_right_widget = right_widget
        right_stack_layout.addWidget(self.default_right_widget)
        self.right_stack_widget.setLayout(right_stack_layout)
        
        # 设置分割器
        storyboard_splitter.addWidget(left_widget)
        storyboard_splitter.addWidget(self.right_stack_widget)
        storyboard_splitter.setStretchFactor(0, 1)  # 左侧输入区域
        storyboard_splitter.setStretchFactor(1, 3)  # 右侧区域占更大空间
        
        # 主布局
        layout = QVBoxLayout()
        layout.addWidget(storyboard_splitter)
        self.setLayout(layout)
        
    def load_models(self):
        """加载模型列表"""
        try:
            # 使用 ConfigManager 实例获取模型列表
            all_model_configs = self.config_manager.config.get("models", [])
            model_names = [cfg.get("name") for cfg in all_model_configs if cfg.get("name")]
            
            self.model_combo.clear()
            if model_names:
                self.model_combo.addItems(model_names)
                logger.debug(f"加载模型列表成功: {model_names}")
            else:
                self.model_combo.addItem("未配置模型")
                logger.warning("未找到模型配置")
        except Exception as e:
            logger.error(f"加载模型列表失败: {e}")
            self.model_combo.addItem("加载失败")
    
    def refresh_model_combo(self):
        """刷新模型下拉框"""
        logger.info("StoryboardTab: refresh_model_combo 函数开始执行")
        self.load_models()
    
    def handle_rewrite_btn(self):
        """处理改写文章按钮点击"""
        try:
            input_text = self.text_input.toPlainText().strip()
            if not input_text:
                QMessageBox.warning(self, "警告", "请先输入要改写的文本内容")
                return
            
            # 检查是否有当前项目，如果没有则弹出项目命名对话框
            if not self.current_project_name:
                dialog = ProjectNameDialog(self)
                if dialog.exec_() == dialog.Accepted:
                    project_info = dialog.get_project_info()
                    project_name = project_info['name']
                    project_description = project_info['description']
                    
                    # 设置当前项目信息
                    self.current_project_name = project_name
                    self.current_project_root = self.project_manager.create_project_structure(project_name)
                    
                    # 通知主窗口更新项目信息
                    if hasattr(self.parent_window, 'set_current_project'):
                        self.parent_window.set_current_project(project_name, project_description)
                    
                    logger.info(f"新项目已创建: {project_name}")
                else:
                    # 用户取消了项目命名，不继续改写
                    return
            
            selected_model = self.model_combo.currentText()
            if selected_model in ["未配置模型", "加载失败"]:
                QMessageBox.warning(self, "警告", "请先在设置中配置大模型")
                return
            
            # 初始化LLM API（每次都根据当前选择的模型重新创建）
            all_model_configs = self.config_manager.config.get("models", [])
            model_config = None
            for cfg in all_model_configs:
                if cfg.get("name") == selected_model:
                    model_config = cfg
                    break
            
            if model_config:
                self.llm_api = LLMApi(
                    api_type=model_config.get('type', 'deepseek'),
                    api_key=model_config.get('key', ''),
                    api_url=model_config.get('url', '')
                )
                logger.info(f"使用模型: {selected_model}, 类型: {model_config.get('type')}, URL: {model_config.get('url')}")
            else:
                QMessageBox.warning(self, "错误", "模型配置不完整")
                return
            
            # 获取选择的风格
            selected_style = self.style_combo.currentText()
            
            # 显示进度条
            self.show_progress("🔄 正在改写文本，请稍候...")
            
            # 调用大模型进行改写
            self.rewrite_btn.setEnabled(False)
            self.rewrite_btn.setText("🔄 改写中...")
            
            # 检查是否已有线程在运行
            if self.rewrite_thread and self.rewrite_thread.isRunning():
                QMessageBox.warning(self, "警告", "文本改写正在进行中，请稍候...")
                return
            
            # 创建并启动改写线程
            self.rewrite_thread = TextRewriteThread(self.llm_api, input_text)
            self.rewrite_thread.progress_updated.connect(self.show_progress)
            self.rewrite_thread.rewrite_completed.connect(self._on_rewrite_completed)
            self.rewrite_thread.error_occurred.connect(self._on_rewrite_error)
            self.rewrite_thread.finished.connect(self._on_rewrite_finished)
            self.rewrite_thread.start()
                
        except Exception as e:
            logger.error(f"启动改写线程时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"启动改写失败: {str(e)}")
            self._reset_rewrite_ui()
    
    def handle_generate_shots_btn(self):
        """处理生成分镜按钮点击"""
        try:
            output_text = self.output_text.toPlainText().strip()
            if not output_text:
                QMessageBox.warning(self, "警告", "请先改写文本或输入分镜内容")
                return
            
            # 设置生成状态
            self.is_generating = True
            self.stop_generation = False
            
            # 初始化LLM API（每次都根据当前选择的模型重新创建）
            selected_model = self.model_combo.currentText()
            all_model_configs = self.config_manager.config.get("models", [])
            model_config = None
            for cfg in all_model_configs:
                if cfg.get("name") == selected_model:
                    model_config = cfg
                    break
            
            if model_config:
                self.llm_api = LLMApi(
                    api_type=model_config.get('type', 'deepseek'),
                    api_key=model_config.get('key', ''),
                    api_url=model_config.get('url', '')
                )
                logger.info(f"使用模型: {selected_model}, 类型: {model_config.get('type')}, URL: {model_config.get('url')}")
            else:
                QMessageBox.warning(self, "错误", "模型配置不完整")
                self.is_generating = False
                return
            
            # 初始化文本解析器
            if not self.text_parser:
                selected_style = self.style_combo.currentText()
                self.text_parser = TextParser(llm_api=self.llm_api, style=selected_style)
            
            # 显示进度条
            self.show_progress("🎬 正在生成分镜，请稍候...")
            
            # 更新按钮状态
            self.generate_shots_btn.setEnabled(False)
            self.generate_shots_btn.setText("🎬 生成中...")
            self.stop_generate_btn.setEnabled(True)
            
            # 检查是否被停止
            if self.stop_generation:
                logger.info("分镜生成被用户停止")
                return
            
            # 检查是否已有线程在运行
            if self.shots_thread and self.shots_thread.isRunning():
                QMessageBox.warning(self, "警告", "分镜生成正在进行中，请稍候...")
                return
            
            # 创建并启动分镜生成线程
            self.shots_thread = ShotsGenerationThread(self.text_parser, output_text)
            self.shots_thread.progress_updated.connect(self.show_progress)
            self.shots_thread.shots_generated.connect(self._on_shots_generated)
            self.shots_thread.error_occurred.connect(self._on_shots_error)
            self.shots_thread.finished.connect(self._on_shots_finished)
            self.shots_thread.start()
                
        except Exception as e:
            logger.error(f"启动分镜生成线程时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"启动分镜生成失败: {str(e)}")
            self._reset_shots_ui()
    
    def handle_stop_generate_btn(self):
        """处理停止生成按钮点击"""
        if self.is_generating:
            self.stop_generation = True
            logger.info("用户请求停止分镜生成")
            
            # 停止正在运行的线程
            if hasattr(self, 'shots_thread') and self.shots_thread and self.shots_thread.isRunning():
                logger.info("正在停止分镜生成线程")
                self.shots_thread.cancel()  # 调用线程的取消方法
                self.shots_thread.wait(3000)  # 等待最多3秒让线程正常结束
                if self.shots_thread.isRunning():
                    logger.warning("线程未能正常停止，强制终止")
                    self.shots_thread.terminate()
                    self.shots_thread.wait(1000)
            
            # 立即更新按钮状态
            self.stop_generate_btn.setEnabled(False)
            self.stop_generate_btn.setText("正在停止...")
            # 显示停止消息
            self.show_progress("⏹️ 正在停止生成...")
            
            # 重置UI状态
            self._reset_shots_ui()
    
    def show_progress(self, message="⏳ 处理中，请稍候..."):
        """显示进度条"""
        try:
            # 使用分镜界面专用的进度条
            if hasattr(self, 'storyboard_progress'):
                # 设置进度条属性
                self.storyboard_progress.setVisible(True)
                self.storyboard_progress.setRange(0, 0)  # 设置为不确定进度条
                self.storyboard_progress.setFormat(message)  # 设置显示文本
                self.storyboard_progress.setTextVisible(True)  # 确保文本可见
                
                # 强制刷新界面
                self.storyboard_progress.update()
                from PyQt5.QtWidgets import QApplication
                QApplication.instance().processEvents()
                
                # 在日志中显示消息
                if self.parent_window and hasattr(self.parent_window, 'log_output_bottom'):
                    self.parent_window.log_output_bottom.appendPlainText(f"[分镜进度] {message}")
                logger.info(f"分镜进度条已显示: {message}, 可见性: {self.storyboard_progress.isVisible()}")
            else:
                logger.warning("未找到分镜进度条组件")
        except Exception as e:
            logger.error(f"显示分镜进度条时发生错误: {e}")
    
    def hide_progress(self):
        """隐藏进度条"""
        try:
            # 使用分镜界面专用的进度条
            if hasattr(self, 'storyboard_progress'):
                self.storyboard_progress.setVisible(False)
                self.storyboard_progress.setFormat("")  # 清空显示文本
                self.storyboard_progress.setTextVisible(False)  # 隐藏文本
                
                # 强制刷新界面
                self.storyboard_progress.update()
                from PyQt5.QtWidgets import QApplication
                QApplication.instance().processEvents()
                
                # 在日志中显示消息
                if self.parent_window and hasattr(self.parent_window, 'log_output_bottom'):
                    self.parent_window.log_output_bottom.appendPlainText("✅ 分镜操作完成")
                logger.info(f"分镜进度条已隐藏，可见性: {self.storyboard_progress.isVisible()}")
            else:
                logger.warning("未找到分镜进度条组件")
        except Exception as e:
            logger.error(f"隐藏分镜进度条时发生错误: {e}")
    
    def show_shots_table(self, shots_data):
        print(f"[DEBUG] storyboard_tab.show_shots_table - shots_data: {shots_data}")
        print(f"[DEBUG] storyboard_tab.show_shots_table - len(shots_data): {len(shots_data) if shots_data else 0}")
        """显示分镜表格"""
        try:
            # 将分镜表格显示在分镜设置标签页中，而不是弹出新窗口
            if hasattr(self, 'parent_window') and self.parent_window:
                self.parent_window.show_shots_in_settings_tab(shots_data)
                # 切换到分镜设置标签页
                self.parent_window.tabs.setCurrentIndex(1)  # 1是分镜设置标签页的索引
            else:
                # 如果没有父窗口，尝试获取主窗口引用
                main_window = self.parent_window if hasattr(self, 'parent_window') and self.parent_window else self.get_main_window()
                shots_window = ShotsWindow(main_window, shots_data)
                shots_window.show()
            
        except Exception as e:
            logger.error(f"显示分镜表格时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"显示分镜表格失败: {str(e)}")
    
    def get_main_window(self):
        """获取主窗口引用"""
        widget = self
        while widget.parent():
            widget = widget.parent()
            if hasattr(widget, 'on_shots_alternative_image_selected'):
                return widget
        return None
    
    def get_current_model(self):
        """获取当前选择的模型"""
        return self.model_combo.currentText()
    
    def get_current_style(self):
        """获取当前选择的风格"""
        current_style = self.style_combo.currentText()
        logger.debug(f"获取当前选择的风格: {current_style}")
        return current_style
    
    def on_style_changed(self, style_text):
        """风格选择变化时的处理"""
        logger.info(f"用户选择了新风格: {style_text}")
        self.save_style_selection(style_text)
    
    def save_style_selection(self, style_text):
        """保存风格选择到配置文件"""
        try:
            if hasattr(self.parent_window, 'config_manager'):
                config = self.parent_window.config_manager.config
                if 'ui_settings' not in config:
                    config['ui_settings'] = {}
                config['ui_settings']['selected_style'] = style_text
                self.parent_window.config_manager.save_config(config) # 传递config数据
                logger.debug(f"风格选择已保存: {style_text}")
        except Exception as e:
            logger.error(f"保存风格选择失败: {e}")
    
    def restore_style_selection(self):
        """恢复上次选择的风格"""
        try:
            if hasattr(self.parent_window, 'config_manager'):
                config = self.parent_window.config_manager.config
                saved_style = config.get('ui_settings', {}).get('selected_style', '吉卜力风格')
                
                # 查找并设置保存的风格
                for i in range(self.style_combo.count()):
                    if self.style_combo.itemText(i) == saved_style:
                        self.style_combo.setCurrentIndex(i)
                        logger.info(f"恢复风格选择: {saved_style}")
                        break
                else:
                    # 如果没找到保存的风格，默认选择吉卜力风格
                    for i in range(self.style_combo.count()):
                        if self.style_combo.itemText(i) == '吉卜力风格':
                            self.style_combo.setCurrentIndex(i)
                            logger.info("使用默认风格: 吉卜力风格")
                            break
        except Exception as e:
            logger.error(f"恢复风格选择失败: {e}")
            # 出错时默认选择吉卜力风格
            for i in range(self.style_combo.count()):
                if self.style_combo.itemText(i) == '吉卜力风格':
                    self.style_combo.setCurrentIndex(i)
                    break
    
    def get_input_text(self):
        """获取输入文本"""
        return self.text_input.toPlainText()
    
    def get_output_text(self):
        """获取输出文本"""
        return self.output_text.toPlainText()
    
    def set_output_text(self, text):
        """设置输出文本"""
        self.output_text.setPlainText(text)
    
    def create_operation_buttons(self, row_index):
        """为指定行创建操作按钮组件"""
        from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
        
        # 创建按钮容器
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(5, 2, 5, 2)
        button_layout.setSpacing(3)
        
        # 绘图按钮
        draw_btn = QPushButton("绘图")
        draw_btn.setProperty("class", "draw-button")
        draw_btn.clicked.connect(lambda: self.handle_draw_btn(row_index))
        button_layout.addWidget(draw_btn)
        
        # 配音按钮
        voice_btn = QPushButton("配音")
        voice_btn.setProperty("class", "voice-button")
        voice_btn.clicked.connect(lambda: self.handle_voice_btn(row_index))
        button_layout.addWidget(voice_btn)
        
        # 试听按钮（初始隐藏）
        preview_btn = QPushButton("试听")
        preview_btn.setProperty("class", "preview-button")
        preview_btn.clicked.connect(lambda: self.handle_preview_btn(row_index))
        preview_btn.setVisible(False)  # 初始隐藏
        button_layout.addWidget(preview_btn)
        
        # 存储试听按钮引用，用于后续显示/隐藏
        if not hasattr(self, 'preview_buttons'):
            self.preview_buttons = {}
        self.preview_buttons[row_index] = preview_btn
        
        # 检查是否已有配音文件，如果有则显示试听按钮
        self._check_and_show_preview_button(row_index, preview_btn)
        
        # 分镜设置按钮
        setting_btn = QPushButton("分镜设置")
        setting_btn.setProperty("class", "setting-button")
        setting_btn.clicked.connect(lambda: self.handle_shot_setting_btn(row_index))
        button_layout.addWidget(setting_btn)
        
        return button_widget
    
    def handle_draw_btn(self, row_index):
        """处理绘图按钮点击事件"""
        try:
            logger.info(f"用户点击第{row_index+1}行的绘图按钮")
            
            # 获取该行的提示词
            prompt = self.get_prompt_for_row(row_index)
            logger.debug(f"第{row_index+1}行原始提示词: {prompt}")
            
            if not prompt:
                logger.warning(f"第{row_index+1}行没有提示词内容，无法生成图片")
                QMessageBox.warning(self, "警告", f"第{row_index+1}行没有提示词内容")
                return

            # 获取当前选择的风格
            current_style = self.get_current_style()
            logger.info(f"当前选择的风格: {current_style}")

            # 显示进度提示
            logger.debug(f"显示第{row_index+1}行图片生成进度提示")
            self.show_progress(f"正在为第{row_index+1}行生成图片...")
            
            # 在底部状态栏立即显示"正在生图"状态
            if self.parent_window and hasattr(self.parent_window, 'log_output_bottom'):
                status_message = f"🎨 正在生图 | 第{row_index+1}行 | 提示词: {prompt[:50]}{'...' if len(prompt) > 50 else ''}"
                self.parent_window.log_output_bottom.appendPlainText(status_message)
                # 滚动到底部显示最新信息
                self.parent_window.log_output_bottom.verticalScrollBar().setValue(
                    self.parent_window.log_output_bottom.verticalScrollBar().maximum()
                )

            # 调用父窗口的绘图处理方法，传递行索引和提示词
            if self.parent_window and hasattr(self.parent_window, 'process_draw_request'):
                logger.info(f"开始处理第{row_index+1}行的绘图请求，提示词: {prompt}")
                self.parent_window.process_draw_request(row_index, prompt)
            else:
                logger.error("无法找到绘图处理方法，父窗口或process_draw_request方法不存在")
                self.hide_progress()
                QMessageBox.warning(self, "错误", "无法找到绘图处理方法")
                
        except Exception as e:
            self.hide_progress()
            logger.error(f"处理绘图按钮点击时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"绘图功能出错: {str(e)}")
    
    def handle_voice_btn(self, row_index):
        """处理配音按钮点击事件"""
        try:
            # 获取当前行的文案内容
            text_item = self.table_widget.item(row_index, 0)  # 文案列
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
                     voice_item = self.table_widget.item(row_index, 6)  # 语音列
                     if voice_item:
                         voice_item.setText(f"已生成: {os.path.basename(result['audio_file'])}")
                     else:
                         voice_item = QTableWidgetItem(f"已生成: {os.path.basename(result['audio_file'])}")
                         self.table_widget.setItem(row_index, 6, voice_item)
                     
                     # 更新分镜数据中的语音文件路径
                     if hasattr(self.parent_window, 'shots_data') and self.parent_window.shots_data and row_index < len(self.parent_window.shots_data):
                         self.parent_window.shots_data[row_index]['voice_file'] = result['audio_file']
                         # 自动保存项目
                         self.parent_window.save_current_project()
                         logger.info(f"已更新第{row_index+1}行分镜的语音文件: {result['audio_file']}")
                     
                     # 显示试听按钮
                     if hasattr(self, 'preview_buttons') and row_index in self.preview_buttons:
                         self.preview_buttons[row_index].setVisible(True)
                         logger.info(f"第{row_index+1}行试听按钮已显示")
                     
                     QMessageBox.information(self, "成功", "语音生成完成！")
                elif result:
                    QMessageBox.warning(self, "错误", f"语音生成失败: {result.get('error', '未知错误')}")
                    
        except ImportError as e:
            QMessageBox.critical(self, "错误", f"无法加载AI配音模块: {str(e)}")
        except Exception as e:
            logger.error(f"处理配音按钮点击时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"配音功能出错: {str(e)}")
    
    def handle_preview_btn(self, row_index):
        """处理试听按钮点击事件"""
        try:
            # 获取配音文件路径
            voice_file = None
            
            # 从分镜数据中获取语音文件路径
            if hasattr(self.parent_window, 'shots_data') and self.parent_window.shots_data and row_index < len(self.parent_window.shots_data):
                voice_file = self.parent_window.shots_data[row_index].get('voice_file')
            
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
    
    def _check_and_show_preview_button(self, row_index, preview_btn):
        """检查是否已有配音文件，如果有则显示试听按钮
        
        Args:
            row_index: 行索引
            preview_btn: 试听按钮对象
        """
        try:
            # 从分镜数据中获取语音文件路径
            if hasattr(self.parent_window, 'shots_data') and self.parent_window.shots_data and row_index < len(self.parent_window.shots_data):
                voice_file = self.parent_window.shots_data[row_index].get('voice_file')
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
    
    def handle_shot_setting_btn(self, row_index):
        """处理分镜设置按钮点击事件"""
        try:
            # 这里将实现分镜设置功能
            QMessageBox.information(self, "提示", f"分镜设置功能 - 第{row_index+1}行\n\n此功能正在开发中，敬请期待！")
        except Exception as e:
            logger.error(f"处理分镜设置按钮点击时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"分镜设置功能出错: {str(e)}")
    
    def update_shot_image(self, row_index, image_path):
        """更新分镜表格中指定行的图片"""
        try:
            logger.info(f"更新第{row_index+1}行的分镜图片: {image_path}")
            
            # 如果父窗口有分镜表格，更新表格中的图片
            if (self.parent_window and 
                hasattr(self.parent_window, 'shots_table') and 
                self.parent_window.shots_table is not None):
                
                table = self.parent_window.shots_table
                
                # 检查表格行数与数据是否同步
                if (hasattr(self.parent_window, 'shots_data') and 
                    self.parent_window.shots_data and 
                    table.rowCount() != len(self.parent_window.shots_data)):
                    
                    logger.warning(f"表格行数不匹配，开始同步: {table.rowCount()} -> {len(self.parent_window.shots_data)}")
                    try:
                        self.parent_window.populate_shots_table_data(self.parent_window.shots_data)
                        logger.info(f"表格同步完成，新行数: {table.rowCount()}")
                    except Exception as sync_error:
                        logger.error(f"表格同步失败: {sync_error}")
                        return False
                
                if 0 <= row_index < table.rowCount():
                    # 图片列是第4列（索引为4）
                    from PyQt5.QtWidgets import QTableWidgetItem
                    from PyQt5.QtGui import QPixmap
                    from PyQt5.QtCore import Qt
                    
                    # 创建图片项
                    item = QTableWidgetItem(image_path)  # 设置DisplayRole数据为图片路径
                    if os.path.exists(image_path):
                        # 加载图片并设置为缩略图
                        pixmap = QPixmap(image_path)
                        if not pixmap.isNull():
                            # 缩放图片到合适大小
                            scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            item.setData(Qt.DecorationRole, scaled_pixmap)  # 设置DecorationRole数据为图片对象
                            item.setToolTip(f"图片路径: {image_path}")
                            logger.info(f"成功设置第{row_index+1}行的图片")
                        else:
                            logger.warning(f"第{row_index+1}行图片加载失败: {image_path}")
                    else:
                        logger.warning(f"第{row_index+1}行图片文件不存在: {image_path}")
                    
                    # 设置到表格中
                    table.setItem(row_index, 4, item)
                    
                    # 调整行高以适应图片
                    table.setRowHeight(row_index, 120)
                    
                    logger.info(f"第{row_index+1}行分镜图片更新完成")
                    return True
                else:
                    logger.debug(f"行索引超出范围: {row_index}, 表格行数: {table.rowCount()}")
                    return False
            else:
                logger.debug("未找到分镜表格，无法更新图片")
                return False
                
        except Exception as e:
            logger.error(f"更新分镜图片时发生错误: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            return False
    

    
    def get_prompt_for_row(self, row_index):
        """获取指定行的提示词内容"""
        try:
            # 如果当前在分镜表格视图中，从父窗口的分镜表格获取数据
            if (self.parent_window and 
                hasattr(self.parent_window, 'shots_table') and 
                self.parent_window.shots_table is not None):
                
                table = self.parent_window.shots_table
                if 0 <= row_index < table.rowCount():
                    # 提示词列是第3列（索引为3）
                    item = table.item(row_index, 3)
                    if item and item.text().strip():
                        return item.text().strip()
            
            # 如果没有找到提示词，返回空字符串
            return ""
        except Exception as e:
            logger.error(f"获取提示词时发生错误: {e}")
            return ""
    
    def get_current_style(self):
        """获取当前选择的风格"""
        try:
            if hasattr(self, 'style_combo') and self.style_combo:
                return self.style_combo.currentText()
            return "默认"
        except Exception as e:
            logger.error(f"获取当前风格时发生错误: {e}")
            return "默认"
    
    def on_style_changed(self, style_text):
        """风格选择变化时的处理"""
        logger.info(f"用户选择了新风格: {style_text}")
        self.save_style_selection(style_text)
    
    def save_style_selection(self, style_text):
        """保存风格选择到配置文件"""
        try:
            if hasattr(self.parent_window, 'config_manager'):
                config = self.parent_window.config_manager.config
                if 'ui_settings' not in config:
                    config['ui_settings'] = {}
                config['ui_settings']['selected_style'] = style_text
                self.parent_window.config_manager.save_config(config) # 传递config数据
                logger.debug(f"风格选择已保存: {style_text}")
        except Exception as e:
            logger.error(f"保存风格选择失败: {e}")
    
    def restore_style_selection(self):
        """恢复上次选择的风格"""
        try:
            if hasattr(self.parent_window, 'config_manager'):
                config = self.parent_window.config_manager.config
                saved_style = config.get('ui_settings', {}).get('selected_style', '吉卜力风格')
                
                # 查找并设置保存的风格
                for i in range(self.style_combo.count()):
                    if self.style_combo.itemText(i) == saved_style:
                        self.style_combo.setCurrentIndex(i)
                        logger.info(f"恢复风格选择: {saved_style}")
                        break
                else:
                    # 如果没找到保存的风格，默认选择吉卜力风格
                    for i in range(self.style_combo.count()):
                        if self.style_combo.itemText(i) == '吉卜力风格':
                            self.style_combo.setCurrentIndex(i)
                            logger.info("使用默认风格: 吉卜力风格")
                            break
        except Exception as e:
            logger.error(f"恢复风格选择失败: {e}")
            # 出错时默认选择吉卜力风格
            for i in range(self.style_combo.count()):
                if self.style_combo.itemText(i) == '吉卜力风格':
                    self.style_combo.setCurrentIndex(i)
                    break
    
    def get_input_text(self):
        """获取输入文本"""
        return self.text_input.toPlainText()
    
    def get_output_text(self):
        """获取输出文本"""
        return self.output_text.toPlainText()
    
    def set_output_text(self, text):
        """设置输出文本"""
        self.output_text.setPlainText(text)
    
    def create_operation_buttons(self, row_index):
        """为指定行创建操作按钮组件"""
        from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
        
        # 创建按钮容器
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(5, 2, 5, 2)
        button_layout.setSpacing(3)
        
        # 绘图按钮
        draw_btn = QPushButton("绘图")
        draw_btn.setProperty("class", "draw-button")
        draw_btn.clicked.connect(lambda: self.handle_draw_btn(row_index))
        button_layout.addWidget(draw_btn)
        
        # 配音按钮
        voice_btn = QPushButton("配音")
        voice_btn.setProperty("class", "voice-button")
        voice_btn.clicked.connect(lambda: self.handle_voice_btn(row_index))
        button_layout.addWidget(voice_btn)
        
        # 试听按钮（初始隐藏）
        preview_btn = QPushButton("试听")
        preview_btn.setProperty("class", "preview-button")
        preview_btn.clicked.connect(lambda: self.handle_preview_btn(row_index))
        preview_btn.setVisible(False)  # 初始隐藏
        button_layout.addWidget(preview_btn)
        
        # 存储试听按钮引用，用于后续显示/隐藏
        if not hasattr(self, 'preview_buttons'):
            self.preview_buttons = {}
        self.preview_buttons[row_index] = preview_btn
        
        # 检查是否已有配音文件，如果有则显示试听按钮
        self._check_and_show_preview_button(row_index, preview_btn)
        
        # 分镜设置按钮
        setting_btn = QPushButton("分镜设置")
        setting_btn.setProperty("class", "setting-button")
        setting_btn.clicked.connect(lambda: self.handle_shot_setting_btn(row_index))
        button_layout.addWidget(setting_btn)
        
        return button_widget
    
    def handle_draw_btn(self, row_index):
        """处理绘图按钮点击事件"""
        try:
            logger.info(f"用户点击第{row_index+1}行的绘图按钮")
            
            # 获取该行的提示词
            prompt = self.get_prompt_for_row(row_index)
            logger.debug(f"第{row_index+1}行原始提示词: {prompt}")
            
            if not prompt:
                logger.warning(f"第{row_index+1}行没有提示词内容，无法生成图片")
                QMessageBox.warning(self, "警告", f"第{row_index+1}行没有提示词内容")
                return

            # 获取当前选择的风格
            current_style = self.get_current_style()
            logger.info(f"当前选择的风格: {current_style}")

            # 显示进度提示
            logger.debug(f"显示第{row_index+1}行图片生成进度提示")
            self.show_progress(f"正在为第{row_index+1}行生成图片...")
            
            # 在底部状态栏立即显示"正在生图"状态
            if self.parent_window and hasattr(self.parent_window, 'log_output_bottom'):
                status_message = f"🎨 正在生图 | 第{row_index+1}行 | 提示词: {prompt[:50]}{'...' if len(prompt) > 50 else ''}"
                self.parent_window.log_output_bottom.appendPlainText(status_message)
                # 滚动到底部显示最新信息
                self.parent_window.log_output_bottom.verticalScrollBar().setValue(
                    self.parent_window.log_output_bottom.verticalScrollBar().maximum()
                )

            # 调用父窗口的绘图处理方法，传递行索引和提示词
            if self.parent_window and hasattr(self.parent_window, 'process_draw_request'):
                logger.info(f"开始处理第{row_index+1}行的绘图请求，提示词: {prompt}")
                self.parent_window.process_draw_request(row_index, prompt)
            else:
                logger.error("无法找到绘图处理方法，父窗口或process_draw_request方法不存在")
                self.hide_progress()
                QMessageBox.warning(self, "错误", "无法找到绘图处理方法")
                
        except Exception as e:
            self.hide_progress()
            logger.error(f"处理绘图按钮点击时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"绘图功能出错: {str(e)}")
    
    def handle_voice_btn(self, row_index):
        """处理配音按钮点击事件"""
        try:
            # 获取当前行的文案内容
            text_item = self.table_widget.item(row_index, 0)  # 文案列
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
                     voice_item = self.table_widget.item(row_index, 6)  # 语音列
                     if voice_item:
                         voice_item.setText(f"已生成: {os.path.basename(result['audio_file'])}")
                     else:
                         voice_item = QTableWidgetItem(f"已生成: {os.path.basename(result['audio_file'])}")
                         self.table_widget.setItem(row_index, 6, voice_item)
                     
                     # 更新分镜数据中的语音文件路径
                     if hasattr(self.parent_window, 'shots_data') and self.parent_window.shots_data and row_index < len(self.parent_window.shots_data):
                         self.parent_window.shots_data[row_index]['voice_file'] = result['audio_file']
                         # 自动保存项目
                         self.parent_window.save_current_project()
                         logger.info(f"已更新第{row_index+1}行分镜的语音文件: {result['audio_file']}")
                     
                     # 显示试听按钮
                     if hasattr(self, 'preview_buttons') and row_index in self.preview_buttons:
                         self.preview_buttons[row_index].setVisible(True)
                         logger.info(f"第{row_index+1}行试听按钮已显示")
                     
                     QMessageBox.information(self, "成功", "语音生成完成！")
                elif result:
                    QMessageBox.warning(self, "错误", f"语音生成失败: {result.get('error', '未知错误')}")
                    
        except ImportError as e:
            QMessageBox.critical(self, "错误", f"无法加载AI配音模块: {str(e)}")
        except Exception as e:
            logger.error(f"处理配音按钮点击时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"配音功能出错: {str(e)}")
    
    def handle_preview_btn(self, row_index):
        """处理试听按钮点击事件"""
        try:
            # 获取配音文件路径
            voice_file = None
            
            # 从分镜数据中获取语音文件路径
            if hasattr(self.parent_window, 'shots_data') and self.parent_window.shots_data and row_index < len(self.parent_window.shots_data):
                voice_file = self.parent_window.shots_data[row_index].get('voice_file')
            
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
    
    def _check_and_show_preview_button(self, row_index, preview_btn):
        """检查是否已有配音文件，如果有则显示试听按钮
        
        Args:
            row_index: 行索引
            preview_btn: 试听按钮对象
        """
        try:
            # 从分镜数据中获取语音文件路径
            if hasattr(self.parent_window, 'shots_data') and self.parent_window.shots_data and row_index < len(self.parent_window.shots_data):
                voice_file = self.parent_window.shots_data[row_index].get('voice_file')
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
    
    def handle_shot_setting_btn(self, row_index):
        """处理分镜设置按钮点击事件"""
        try:
            # 这里将实现分镜设置功能
            QMessageBox.information(self, "提示", f"分镜设置功能 - 第{row_index+1}行\n\n此功能正在开发中，敬请期待！")
        except Exception as e:
            logger.error(f"处理分镜设置按钮点击时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"分镜设置功能出错: {str(e)}")
    
    def update_shot_image(self, row_index, image_path):
        """更新分镜表格中指定行的图片"""
        try:
            logger.info(f"更新第{row_index+1}行的分镜图片: {image_path}")
            
            # 如果父窗口有分镜表格，更新表格中的图片
            if (self.parent_window and 
                hasattr(self.parent_window, 'shots_table') and 
                self.parent_window.shots_table is not None):
                
                table = self.parent_window.shots_table
                
                # 检查表格行数与数据是否同步
                if (hasattr(self.parent_window, 'shots_data') and 
                    self.parent_window.shots_data and 
                    table.rowCount() != len(self.parent_window.shots_data)):
                    
                    logger.warning(f"表格行数不匹配，开始同步: {table.rowCount()} -> {len(self.parent_window.shots_data)}")
                    try:
                        self.parent_window.populate_shots_table_data(self.parent_window.shots_data)
                        logger.info(f"表格同步完成，新行数: {table.rowCount()}")
                    except Exception as sync_error:
                        logger.error(f"表格同步失败: {sync_error}")
                        return False
                
                if 0 <= row_index < table.rowCount():
                    # 图片列是第4列（索引为4）
                    from PyQt5.QtWidgets import QTableWidgetItem
                    from PyQt5.QtGui import QPixmap
                    from PyQt5.QtCore import Qt
                    
                    # 创建图片项
                    item = QTableWidgetItem(image_path)  # 设置DisplayRole数据为图片路径
                    if os.path.exists(image_path):
                        # 加载图片并设置为缩略图
                        pixmap = QPixmap(image_path)
                        if not pixmap.isNull():
                            # 缩放图片到合适大小
                            scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            item.setData(Qt.DecorationRole, scaled_pixmap)  # 设置DecorationRole数据为图片对象
                            item.setToolTip(f"图片路径: {image_path}")
                            logger.info(f"成功设置第{row_index+1}行的图片")
                        else:
                            logger.warning(f"第{row_index+1}行图片加载失败: {image_path}")
                    else:
                        logger.warning(f"第{row_index+1}行图片文件不存在: {image_path}")
                    
                    # 设置到表格中
                    table.setItem(row_index, 4, item)
                    
                    # 调整行高以适应图片
                    table.setRowHeight(row_index, 120)
                    
                    logger.info(f"第{row_index+1}行分镜图片更新完成")
                    return True
                else:
                    logger.debug(f"行索引超出范围: {row_index}, 表格行数: {table.rowCount()}")
                    return False
            else:
                logger.debug("未找到分镜表格，无法更新图片")
                return False
                
        except Exception as e:
            logger.error(f"更新分镜图片时发生错误: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            return False
    

    
    def get_prompt_for_row(self, row_index):
        """获取指定行的提示词内容"""
        try:
            # 如果当前在分镜表格视图中，从父窗口的分镜表格获取数据
            if (self.parent_window and 
                hasattr(self.parent_window, 'shots_table') and 
                self.parent_window.shots_table is not None):
                
                table = self.parent_window.shots_table
                if 0 <= row_index < table.rowCount():
                    # 提示词列是第3列（索引为3）
                    item = table.item(row_index, 3)
                    if item and item.text().strip():
                        return item.text().strip()
            
            # 如果没有找到提示词，返回空字符串
            return ""
        except Exception as e:
            logger.error(f"获取提示词时发生错误: {e}")
            return ""
    
    def get_current_style(self):
        """获取当前选择的风格"""
        try:
            if hasattr(self, 'style_combo') and self.style_combo:
                return self.style_combo.currentText()
            return "默认"
        except Exception as e:
            logger.error(f"获取当前风格时发生错误: {e}")
            return "默认"
    
    def on_style_changed(self, style_text):
        """风格选择变化时的处理"""
        logger.info(f"用户选择了新风格: {style_text}")
        self.save_style_selection(style_text)
    
    def save_style_selection(self, style_text):
        """保存风格选择到配置文件"""
        try:
            if hasattr(self.parent_window, 'config_manager'):
                config = self.parent_window.config_manager.config
                if 'ui_settings' not in config:
                    config['ui_settings'] = {}
                config['ui_settings']['selected_style'] = style_text
                self.parent_window.config_manager.save_config(config) # 传递config数据
                logger.debug(f"风格选择已保存: {style_text}")
        except Exception as e:
            logger.error(f"保存风格选择失败: {e}")
    
    def restore_style_selection(self):
        """恢复上次选择的风格"""
        try:
            if hasattr(self.parent_window, 'config_manager'):
                config = self.parent_window.config_manager.config
                saved_style = config.get('ui_settings', {}).get('selected_style', '吉卜力风格')
                
                # 查找并设置保存的风格
                for i in range(self.style_combo.count()):
                    if self.style_combo.itemText(i) == saved_style:
                        self.style_combo.setCurrentIndex(i)
                        logger.info(f"恢复风格选择: {saved_style}")
                        break
                else:
                    # 如果没找到保存的风格，默认选择吉卜力风格
                    for i in range(self.style_combo.count()):
                        if self.style_combo.itemText(i) == '吉卜力风格':
                            self.style_combo.setCurrentIndex(i)
                            logger.info("使用默认风格: 吉卜力风格")
                            break
        except Exception as e:
            logger.error(f"恢复风格选择失败: {e}")
            # 出错时默认选择吉卜力风格
            for i in range(self.style_combo.count()):
                if self.style_combo.itemText(i) == '吉卜力风格':
                    self.style_combo.setCurrentIndex(i)
                    break
    
    def get_input_text(self):
        """获取输入文本"""
        return self.text_input.toPlainText()
    
    def get_output_text(self):
        """获取输出文本"""
        return self.output_text.toPlainText()
    
    def set_output_text(self, text):
        """设置输出文本"""
        self.output_text.setPlainText(text)
    
    def create_operation_buttons(self, row_index):
        """为指定行创建操作按钮组件"""
        from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
        
        # 创建按钮容器
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(5, 2, 5, 2)
        button_layout.setSpacing(3)
        
        # 绘图按钮
        draw_btn = QPushButton("绘图")
        draw_btn.setProperty("class", "draw-button")
        draw_btn.clicked.connect(lambda: self.handle_draw_btn(row_index))
        button_layout.addWidget(draw_btn)
        
        # 配音按钮
        voice_btn = QPushButton("配音")
        voice_btn.setProperty("class", "voice-button")
        voice_btn.clicked.connect(lambda: self.handle_voice_btn(row_index))
        button_layout.addWidget(voice_btn)
        
        # 试听按钮（初始隐藏）
        preview_btn = QPushButton("试听")
        preview_btn.setProperty("class", "preview-button")
        preview_btn.clicked.connect(lambda: self.handle_preview_btn(row_index))
        preview_btn.setVisible(False)  # 初始隐藏
        button_layout.addWidget(preview_btn)
        
        # 存储试听按钮引用，用于后续显示/隐藏
        if not hasattr(self, 'preview_buttons'):
            self.preview_buttons = {}
        self.preview_buttons[row_index] = preview_btn
        
        # 检查是否已有配音文件，如果有则显示试听按钮
        self._check_and_show_preview_button(row_index, preview_btn)
        
        # 分镜设置按钮
        setting_btn = QPushButton("分镜设置")
        setting_btn.setProperty("class", "setting-button")
        setting_btn.clicked.connect(lambda: self.handle_shot_setting_btn(row_index))
        button_layout.addWidget(setting_btn)
        
        return button_widget
    
    def handle_draw_btn(self, row_index):
        """处理绘图按钮点击事件"""
        try:
            logger.info(f"用户点击第{row_index+1}行的绘图按钮")
            
            # 获取该行的提示词
            prompt = self.get_prompt_for_row(row_index)
            logger.debug(f"第{row_index+1}行原始提示词: {prompt}")
            
            if not prompt:
                logger.warning(f"第{row_index+1}行没有提示词内容，无法生成图片")
                QMessageBox.warning(self, "警告", f"第{row_index+1}行没有提示词内容")
                return

            # 获取当前选择的风格
            current_style = self.get_current_style()
            logger.info(f"当前选择的风格: {current_style}")

            # 显示进度提示
            logger.debug(f"显示第{row_index+1}行图片生成进度提示")
            self.show_progress(f"正在为第{row_index+1}行生成图片...")
            
            # 在底部状态栏立即显示"正在生图"状态
            if self.parent_window and hasattr(self.parent_window, 'log_output_bottom'):
                status_message = f"🎨 正在生图 | 第{row_index+1}行 | 提示词: {prompt[:50]}{'...' if len(prompt) > 50 else ''}"
                self.parent_window.log_output_bottom.appendPlainText(status_message)
                # 滚动到底部显示最新信息
                self.parent_window.log_output_bottom.verticalScrollBar().setValue(
                    self.parent_window.log_output_bottom.verticalScrollBar().maximum()
                )

            # 调用父窗口的绘图处理方法，传递行索引和提示词
            if self.parent_window and hasattr(self.parent_window, 'process_draw_request'):
                logger.info(f"开始处理第{row_index+1}行的绘图请求，提示词: {prompt}")
                self.parent_window.process_draw_request(row_index, prompt)
            else:
                logger.error("无法找到绘图处理方法，父窗口或process_draw_request方法不存在")
                self.hide_progress()
                QMessageBox.warning(self, "错误", "无法找到绘图处理方法")
                
        except Exception as e:
            self.hide_progress()
            logger.error(f"处理绘图按钮点击时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"绘图功能出错: {str(e)}")
    
    def handle_voice_btn(self, row_index):
        """处理配音按钮点击事件"""
        try:
            # 获取当前行的文案内容
            text_item = self.table_widget.item(row_index, 0)  # 文案列
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
                     voice_item = self.table_widget.item(row_index, 6)  # 语音列
                     if voice_item:
                         voice_item.setText(f"已生成: {os.path.basename(result['audio_file'])}")
                     else:
                         voice_item = QTableWidgetItem(f"已生成: {os.path.basename(result['audio_file'])}")
                         self.table_widget.setItem(row_index, 6, voice_item)
                     
                     # 更新分镜数据中的语音文件路径
                     if hasattr(self.parent_window, 'shots_data') and self.parent_window.shots_data and row_index < len(self.parent_window.shots_data):
                         self.parent_window.shots_data[row_index]['voice_file'] = result['audio_file']
                         # 自动保存项目
                         self.parent_window.save_current_project()
                         logger.info(f"已更新第{row_index+1}行分镜的语音文件: {result['audio_file']}")
                     
                     # 显示试听按钮
                     if hasattr(self, 'preview_buttons') and row_index in self.preview_buttons:
                         self.preview_buttons[row_index].setVisible(True)
                         logger.info(f"第{row_index+1}行试听按钮已显示")
                     
                     QMessageBox.information(self, "成功", "语音生成完成！")
                elif result:
                    QMessageBox.warning(self, "错误", f"语音生成失败: {result.get('error', '未知错误')}")
                    
        except ImportError as e:
            QMessageBox.critical(self, "错误", f"无法加载AI配音模块: {str(e)}")
        except Exception as e:
            logger.error(f"处理配音按钮点击时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"配音功能出错: {str(e)}")
    
    def handle_preview_btn(self, row_index):
        """处理试听按钮点击事件"""
        try:
            # 获取配音文件路径
            voice_file = None
            
            # 从分镜数据中获取语音文件路径
            if hasattr(self.parent_window, 'shots_data') and self.parent_window.shots_data and row_index < len(self.parent_window.shots_data):
                voice_file = self.parent_window.shots_data[row_index].get('voice_file')
            
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
    
    def _check_and_show_preview_button(self, row_index, preview_btn):
        """检查是否已有配音文件，如果有则显示试听按钮
        
        Args:
            row_index: 行索引
            preview_btn: 试听按钮对象
        """
        try:
            # 从分镜数据中获取语音文件路径
            if hasattr(self.parent_window, 'shots_data') and self.parent_window.shots_data and row_index < len(self.parent_window.shots_data):
                voice_file = self.parent_window.shots_data[row_index].get('voice_file')
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
    
    def handle_shot_setting_btn(self, row_index):
        """处理分镜设置按钮点击事件"""
        try:
            # 这里将实现分镜设置功能
            QMessageBox.information(self, "提示", f"分镜设置功能 - 第{row_index+1}行\n\n此功能正在开发中，敬请期待！")
        except Exception as e:
            logger.error(f"处理分镜设置按钮点击时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"分镜设置功能出错: {str(e)}")
    
    def update_shot_image(self, row_index, image_path):
        """更新分镜表格中指定行的图片"""
        try:
            logger.info(f"更新第{row_index+1}行的分镜图片: {image_path}")
            
            # 如果父窗口有分镜表格，更新表格中的图片
            if (self.parent_window and 
                hasattr(self.parent_window, 'shots_table') and 
                self.parent_window.shots_table is not None):
                
                table = self.parent_window.shots_table
                
                # 检查表格行数与数据是否同步
                if (hasattr(self.parent_window, 'shots_data') and 
                    self.parent_window.shots_data and 
                    table.rowCount() != len(self.parent_window.shots_data)):
                    
                    logger.warning(f"表格行数不匹配，开始同步: {table.rowCount()} -> {len(self.parent_window.shots_data)}")
                    try:
                        self.parent_window.populate_shots_table_data(self.parent_window.shots_data)
                        logger.info(f"表格同步完成，新行数: {table.rowCount()}")
                    except Exception as sync_error:
                        logger.error(f"表格同步失败: {sync_error}")
                        return False
                
                if 0 <= row_index < table.rowCount():
                    # 图片列是第4列（索引为4）
                    from PyQt5.QtWidgets import QTableWidgetItem
                    from PyQt5.QtGui import QPixmap
                    from PyQt5.QtCore import Qt
                    
                    # 创建图片项
                    item = QTableWidgetItem(image_path)  # 设置DisplayRole数据为图片路径
                    if os.path.exists(image_path):
                        # 加载图片并设置为缩略图
                        pixmap = QPixmap(image_path)
                        if not pixmap.isNull():
                            # 缩放图片到合适大小
                            scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            item.setData(Qt.DecorationRole, scaled_pixmap)  # 设置DecorationRole数据为图片对象
                            item.setToolTip(f"图片路径: {image_path}")
                            logger.info(f"成功设置第{row_index+1}行的图片")
                        else:
                            logger.warning(f"第{row_index+1}行图片加载失败: {image_path}")
                    else:
                        logger.warning(f"第{row_index+1}行图片文件不存在: {image_path}")
                    
                    # 设置到表格中
                    table.setItem(row_index, 4, item)
                    
                    # 调整行高以适应图片
                    table.setRowHeight(row_index, 120)
                    
                    logger.info(f"第{row_index+1}行分镜图片更新完成")
                    return True
                else:
                    logger.debug(f"行索引超出范围: {row_index}, 表格行数: {table.rowCount()}")
                    return False
            else:
                logger.debug("未找到分镜表格，无法更新图片")
                return False
                
        except Exception as e:
            logger.error(f"更新分镜图片时发生错误: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            return False
    

    
    def get_prompt_for_row(self, row_index):
        """获取指定行的提示词内容"""
        try:
            # 如果当前在分镜表格视图中，从父窗口的分镜表格获取数据
            if (self.parent_window and 
                hasattr(self.parent_window, 'shots_table') and 
                self.parent_window.shots_table is not None):
                
                table = self.parent_window.shots_table
                if 0 <= row_index < table.rowCount():
                    # 提示词列是第3列（索引为3）
                    item = table.item(row_index, 3)
                    if item and item.text().strip():
                        return item.text().strip()
            
            # 如果没有找到提示词，返回空字符串
            return ""
        except Exception as e:
            logger.error(f"获取提示词时发生错误: {e}")
            return ""
    
    def get_current_style(self):
        """获取当前选择的风格"""
        try:
            if hasattr(self, 'style_combo') and self.style_combo:
                return self.style_combo.currentText()
            return "默认"
        except Exception as e:
            logger.error(f"获取当前风格时发生错误: {e}")
            return "默认"
    
    def on_style_changed(self, style_text):
        """风格选择变化时的处理"""
        logger.info(f"用户选择了新风格: {style_text}")
        self.save_style_selection(style_text)
    
    def save_style_selection(self, style_text):
        """保存风格选择到配置文件"""
        try:
            if hasattr(self.parent_window, 'config_manager'):
                config = self.parent_window.config_manager.config
                if 'ui_settings' not in config:
                    config['ui_settings'] = {}
                config['ui_settings']['selected_style'] = style_text
                self.parent_window.config_manager.save_config(config) # 传递config数据
                logger.debug(f"风格选择已保存: {style_text}")
        except Exception as e:
            logger.error(f"保存风格选择失败: {e}")
    
    def restore_style_selection(self):
        """恢复上次选择的风格"""
        try:
            if hasattr(self.parent_window, 'config_manager'):
                config = self.parent_window.config_manager.config
                saved_style = config.get('ui_settings', {}).get('selected_style', '吉卜力风格')
                
                # 查找并设置保存的风格
                for i in range(self.style_combo.count()):
                    if self.style_combo.itemText(i) == saved_style:
                        self.style_combo.setCurrentIndex(i)
                        logger.info(f"恢复风格选择: {saved_style}")
                        break
                else:
                    # 如果没找到保存的风格，默认选择吉卜力风格
                    for i in range(self.style_combo.count()):
                        if self.style_combo.itemText(i) == '吉卜力风格':
                            self.style_combo.setCurrentIndex(i)
                            logger.info("使用默认风格: 吉卜力风格")
                            break
        except Exception as e:
            logger.error(f"恢复风格选择失败: {e}")
            # 出错时默认选择吉卜力风格
            for i in range(self.style_combo.count()):
                if self.style_combo.itemText(i) == '吉卜力风格':
                    self.style_combo.setCurrentIndex(i)
                    break
    
    def get_input_text(self):
        """获取输入文本"""
        return self.text_input.toPlainText()
    
    def get_output_text(self):
        """获取输出文本"""
        return self.output_text.toPlainText()
    
    def set_output_text(self, text):
        """设置输出文本"""
        self.output_text.setPlainText(text)
    
    def create_operation_buttons(self, row_index):
        """为指定行创建操作按钮组件"""
        from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
        
        # 创建按钮容器
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(5, 2, 5, 2)
        button_layout.setSpacing(3)
        
        # 绘图按钮
        draw_btn = QPushButton("绘图")
        draw_btn.setProperty("class", "draw-button")
        draw_btn.clicked.connect(lambda: self.handle_draw_btn(row_index))
        button_layout.addWidget(draw_btn)
        
        # 配音按钮
        voice_btn = QPushButton("配音")
        voice_btn.setProperty("class", "voice-button")
        voice_btn.clicked.connect(lambda: self.handle_voice_btn(row_index))
        button_layout.addWidget(voice_btn)
        
        # 试听按钮（初始隐藏）
        preview_btn = QPushButton("试听")
        preview_btn.setProperty("class", "preview-button")
        preview_btn.clicked.connect(lambda: self.handle_preview_btn(row_index))
        preview_btn.setVisible(False)  # 初始隐藏
        button_layout.addWidget(preview_btn)
        
        # 存储试听按钮引用，用于后续显示/隐藏
        if not hasattr(self, 'preview_buttons'):
            self.preview_buttons = {}
        self.preview_buttons[row_index] = preview_btn
        
        # 检查是否已有配音文件，如果有则显示试听按钮
        self._check_and_show_preview_button(row_index, preview_btn)
        
        # 分镜设置按钮
        setting_btn = QPushButton("分镜设置")
        setting_btn.setProperty("class", "setting-button")
        setting_btn.clicked.connect(lambda: self.handle_shot_setting_btn(row_index))
        button_layout.addWidget(setting_btn)
        
        return button_widget
    
    def handle_draw_btn(self, row_index):
        """处理绘图按钮点击事件"""
        try:
            logger.info(f"用户点击第{row_index+1}行的绘图按钮")
            
            # 获取该行的提示词
            prompt = self.get_prompt_for_row(row_index)
            logger.debug(f"第{row_index+1}行原始提示词: {prompt}")
            
            if not prompt:
                logger.warning(f"第{row_index+1}行没有提示词内容，无法生成图片")
                QMessageBox.warning(self, "警告", f"第{row_index+1}行没有提示词内容")
                return

            # 获取当前选择的风格
            current_style = self.get_current_style()
            logger.info(f"当前选择的风格: {current_style}")

            # 显示进度提示
            logger.debug(f"显示第{row_index+1}行图片生成进度提示")
            self.show_progress(f"正在为第{row_index+1}行生成图片...")
            
            # 在底部状态栏立即显示"正在生图"状态
            if self.parent_window and hasattr(self.parent_window, 'log_output_bottom'):
                status_message = f"🎨 正在生图 | 第{row_index+1}行 | 提示词: {prompt[:50]}{'...' if len(prompt) > 50 else ''}"
                self.parent_window.log_output_bottom.appendPlainText(status_message)
                # 滚动到底部显示最新信息
                self.parent_window.log_output_bottom.verticalScrollBar().setValue(
                    self.parent_window.log_output_bottom.verticalScrollBar().maximum()
                )

            # 调用父窗口的绘图处理方法，传递行索引和提示词
            if self.parent_window and hasattr(self.parent_window, 'process_draw_request'):
                logger.info(f"开始处理第{row_index+1}行的绘图请求，提示词: {prompt}")
                self.parent_window.process_draw_request(row_index, prompt)
            else:
                logger.error("无法找到绘图处理方法，父窗口或process_draw_request方法不存在")
                self.hide_progress()
                QMessageBox.warning(self, "错误", "无法找到绘图处理方法")
                
        except Exception as e:
            self.hide_progress()
            logger.error(f"处理绘图按钮点击时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"绘图功能出错: {str(e)}")
    
    # 线程回调方法
    def _on_rewrite_completed(self, response):
        """文本改写完成回调"""
        try:
            self.output_text.setPlainText(response)
            
            # 保存改写后的文本到项目文件夹
            if self.current_project_root:
                try:
                    rewritten_file = os.path.join(self.current_project_root, 'texts', 'rewritten.txt')
                    with open(rewritten_file, 'w', encoding='utf-8') as f:
                        f.write(response)
                    logger.info(f"改写文本已保存到: {rewritten_file}")
                except Exception as e:
                    logger.error(f"保存改写文本失败: {e}")
            
            # 自动保存项目状态
            self._auto_save_project()
            
            logger.info("文本改写完成")
        except Exception as e:
            logger.error(f"处理改写完成回调时发生错误: {e}")
    
    def _on_rewrite_error(self, error_msg):
        """文本改写错误回调"""
        QMessageBox.warning(self, "错误", error_msg)
    
    def _on_rewrite_finished(self):
        """文本改写线程结束回调"""
        self._reset_rewrite_ui()
    
    def _reset_rewrite_ui(self):
        """重置改写UI状态"""
        self.rewrite_btn.setEnabled(True)
        self.rewrite_btn.setText("改写文章")
        self.hide_progress()
    
    def _on_shots_generated(self, shots_data):
        """分镜生成完成回调"""
        try:
            # 保存分镜数据到主窗口
            if hasattr(self, 'parent_window') and self.parent_window:
                self.parent_window.shots_data = shots_data
                logger.debug(f"分镜数据已保存到主窗口，共 {len(shots_data)} 个分镜")
            self.show_shots_table(shots_data)
            logger.info(f"成功生成 {len(shots_data)} 个分镜")
        except Exception as e:
            logger.error(f"处理分镜生成完成回调时发生错误: {e}")
    
    def _on_shots_error(self, error_msg):
        """分镜生成错误回调"""
        QMessageBox.critical(self, "错误", error_msg)
    
    def _on_shots_finished(self):
        """分镜生成线程结束回调"""
        self._reset_shots_ui()
    
    def _reset_shots_ui(self):
        """重置分镜生成UI状态"""
        self.is_generating = False
        self.stop_generation = False
        self.generate_shots_btn.setEnabled(True)
        self.generate_shots_btn.setText("生成分镜")
        self.stop_generate_btn.setEnabled(False)
        self.hide_progress()