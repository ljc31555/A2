import sys
import os
import json
import shutil
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QScrollArea, QGridLayout, QMessageBox, QSizePolicy, QSpinBox, QComboBox, QCheckBox, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont

from utils.logger import logger
from models.comfyui_client import ComfyUIClient
from gui.workflow_panel import WorkflowPanel


class AIDrawingTab(QWidget):
    """绘图设置标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        
        # 初始化组件
        self.comfyui_client = None
        self.generated_images = []  # 存储图片路径和相关信息
        self.selected_image_index = -1  # 当前选中的图片索引
        
        # 设置工作流目录
        self.workflows_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'config', 'workflows'
        )
        
        self.init_ui()
        
        # 初始化图像生成服务
        self.image_generation_service = None
        self._init_image_generation_service()
        
    def init_ui(self):
        """初始化UI界面"""
        # 创建主要的水平布局
        main_layout = QHBoxLayout()
        
        # 左侧区域 - 主要内容区域
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 引擎选择
        engine_layout = QHBoxLayout()
        engine_label = QLabel("生成引擎:")
        engine_layout.addWidget(engine_label)
        
        from PyQt5.QtWidgets import QComboBox, QGroupBox
        self.engine_combo = QComboBox()
        self.engine_combo.addItem("Pollinations AI (免费)", "pollinations")
        self.engine_combo.addItem("ComfyUI (本地)", "comfyui")
        self.engine_combo.setCurrentIndex(0)  # 默认选择Pollinations AI
        self.engine_combo.setToolTip("选择图像生成引擎")
        self.engine_combo.currentTextChanged.connect(self.on_engine_changed)
        engine_layout.addWidget(self.engine_combo)
        engine_layout.addStretch()
        left_layout.addLayout(engine_layout)

        # ComfyUI 设置区域
        self.comfyui_group = QGroupBox("ComfyUI 设置")
        comfyui_group_layout = QVBoxLayout()
        
        # ComfyUI 地址输入和连接按钮
        comfyui_url_layout = QHBoxLayout()
        self.comfyui_url_input = QLineEdit()
        self.comfyui_url_input.setPlaceholderText("请输入 ComfyUI 地址 (例如: http://127.0.0.1:8188)")
        self.comfyui_url_input.setText("http://127.0.0.1:8188")  # 默认地址
        self.comfyui_url_input.setToolTip("输入 ComfyUI Web UI 的地址")
        comfyui_url_layout.addWidget(self.comfyui_url_input)

        self.connect_comfyui_btn = QPushButton("连接 ComfyUI")
        self.connect_comfyui_btn.clicked.connect(self.connect_to_comfyui)
        self.connect_comfyui_btn.setToolTip("点击连接到 ComfyUI Web UI")
        comfyui_url_layout.addWidget(self.connect_comfyui_btn)
        
        comfyui_group_layout.addLayout(comfyui_url_layout)
        
        # 工作流配置面板（移到ComfyUI设置内）
        self.workflow_panel = WorkflowPanel()
        comfyui_group_layout.addWidget(self.workflow_panel)
        
        self.comfyui_group.setLayout(comfyui_group_layout)
        left_layout.addWidget(self.comfyui_group)
        
        # Pollinations AI 设置区域
        self.pollinations_group = QGroupBox("Pollinations AI 设置")
        pollinations_group_layout = QVBoxLayout()
        
        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型:"))
        self.pollinations_model_combo = QComboBox()
        self.pollinations_model_combo.addItems(["flux", "flux-turbo", "gptimage"])
        self.pollinations_model_combo.setCurrentText("flux")  # 默认选择flux
        model_layout.addWidget(self.pollinations_model_combo)
        pollinations_group_layout.addLayout(model_layout)
        
        # 尺寸设置（宽度和高度）
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("宽度:"))
        self.pollinations_width_spin = QSpinBox()
        self.pollinations_width_spin.setRange(256, 2048)
        self.pollinations_width_spin.setValue(1024)
        self.pollinations_width_spin.setSingleStep(64)
        size_layout.addWidget(self.pollinations_width_spin)
        
        size_layout.addWidget(QLabel("高度:"))
        self.pollinations_height_spin = QSpinBox()
        self.pollinations_height_spin.setRange(256, 2048)
        self.pollinations_height_spin.setValue(1024)
        self.pollinations_height_spin.setSingleStep(64)
        size_layout.addWidget(self.pollinations_height_spin)
        pollinations_group_layout.addLayout(size_layout)
        
        # 种子设置
        seed_layout = QHBoxLayout()
        seed_layout.addWidget(QLabel("种子:"))
        
        # 种子类型下拉菜单
        self.pollinations_seed_type_combo = QComboBox()
        self.pollinations_seed_type_combo.addItems(["随机", "固定"])
        self.pollinations_seed_type_combo.currentTextChanged.connect(self.on_pollinations_seed_type_changed)
        seed_layout.addWidget(self.pollinations_seed_type_combo)
        
        # 种子值输入框
        self.pollinations_seed_edit = QLineEdit()
        self.pollinations_seed_edit.setPlaceholderText("自动生成随机值")
        self.pollinations_seed_edit.setEnabled(False)  # 默认禁用
        seed_layout.addWidget(self.pollinations_seed_edit)
        
        pollinations_group_layout.addLayout(seed_layout)
        
        # 复选框选项
        self.pollinations_enhance_check = QCheckBox("启用增强 (Enhance)")
        self.pollinations_logo_check = QCheckBox("添加Logo水印")
        pollinations_group_layout.addWidget(self.pollinations_enhance_check)
        pollinations_group_layout.addWidget(self.pollinations_logo_check)
        
        self.pollinations_group.setLayout(pollinations_group_layout)
        left_layout.addWidget(self.pollinations_group)

        # 图片描述输入框和生成图片按钮
        desc_layout = QHBoxLayout()
        self.image_desc_input = QLineEdit()
        self.image_desc_input.setPlaceholderText("请输入图片描述（prompt）")
        desc_layout.addWidget(self.image_desc_input)
        
        self.generate_image_btn = QPushButton("生成图片")
        self.generate_image_btn.clicked.connect(self.handle_generate_image_btn)
        desc_layout.addWidget(self.generate_image_btn)
        left_layout.addLayout(desc_layout)

        # 用于显示生成状态或错误信息
        self.generated_image_status_label = QLabel("图片状态将在此显示")
        left_layout.addWidget(self.generated_image_status_label)

        # 用于显示多张生成的图片
        self.image_gallery_scroll = QScrollArea()
        self.image_gallery_widget = QWidget()
        self.image_gallery_layout = QGridLayout(self.image_gallery_widget)
        self.image_gallery_layout.setSpacing(10)
        self.image_gallery_scroll.setWidget(self.image_gallery_widget)
        self.image_gallery_scroll.setWidgetResizable(True)
        self.image_gallery_scroll.setMinimumHeight(300)
        self.image_gallery_scroll.setProperty("class", "image-gallery-scroll")
        left_layout.addWidget(self.image_gallery_scroll)
        
        # 添加清空图片库按钮
        clear_gallery_btn = QPushButton("清空图片库")
        clear_gallery_btn.clicked.connect(self.clear_image_gallery)
        left_layout.addWidget(clear_gallery_btn)
        
        # 将左侧区域添加到主布局（现在只有左侧区域）
        main_layout.addWidget(left_widget)
        
        self.setLayout(main_layout)
        
        # 初始化工作流面板
        self.workflow_panel.set_workflows_directory(self.workflows_dir)
        self.workflow_panel.refresh_workflows()
        
        # 初始化界面显示状态
        self.on_engine_changed()
        
    def on_engine_changed(self):
        """当引擎选择改变时调用"""
        selected_engine = self.engine_combo.currentData()
        
        # 根据选择的引擎显示/隐藏对应的设置区域
        if selected_engine == "comfyui":
            self.comfyui_group.setVisible(True)
            self.pollinations_group.setVisible(False)
            # 工作流面板只在ComfyUI模式下可见
            if hasattr(self, 'workflow_panel'):
                self.workflow_panel.setVisible(True)
        else:  # pollinations
            self.comfyui_group.setVisible(False)
            self.pollinations_group.setVisible(True)
            # 隐藏工作流面板
            if hasattr(self, 'workflow_panel'):
                self.workflow_panel.setVisible(False)
        
    def connect_to_comfyui(self):
        """连接到ComfyUI"""
        try:
            comfyui_url = self.comfyui_url_input.text().strip()
            if not comfyui_url:
                QMessageBox.warning(self, "警告", "请输入ComfyUI地址")
                return
            
            # 验证URL格式
            if not (comfyui_url.startswith('http://') or comfyui_url.startswith('https://')):
                QMessageBox.warning(self, "警告", "请输入有效的URL地址（以http://或https://开头）")
                return
            
            self.connect_comfyui_btn.setEnabled(False)
            self.connect_comfyui_btn.setText("连接中...")
            
            # 初始化ComfyUI客户端
            self.comfyui_client = ComfyUIClient(comfyui_url)
            
            # 尝试获取工作流列表来测试连接
            try:
                self.comfyui_client.get_workflow_list()

                self.generated_image_status_label.setText("✅ ComfyUI连接成功")
                self.generated_image_status_label.setProperty("class", "status-label-success")
                logger.info(f"成功连接到ComfyUI: {comfyui_url}")
            except Exception as e:
                logger.error(f"连接ComfyUI时发生错误: {e}")
                self.generated_image_status_label.setText("❌ ComfyUI连接失败")
                self.generated_image_status_label.setProperty("class", "status-label-error")
                self.comfyui_client = None
                QMessageBox.warning(self, "连接失败", "无法连接到ComfyUI，请检查地址和服务状态")
        finally:
            self.connect_comfyui_btn.setEnabled(True)
            self.connect_comfyui_btn.setText("连接 ComfyUI")
    
    def handle_generate_image_btn(self):
        """处理生成图片按钮点击"""
        import traceback
        
        logger.info("=== 开始图片生成流程 ===")
        try:
            # 检查图片描述
            prompt = self.image_desc_input.text().strip()
            logger.debug(f"用户输入的提示词: '{prompt}'")
            if not prompt:
                logger.warning("用户未输入图片描述")
                QMessageBox.warning(self, "警告", "请输入图片描述")
                return
            
            # 获取选择的引擎
            selected_engine = self.engine_combo.currentData()
            logger.info(f"用户选择的生成引擎: {selected_engine}")
            
            if selected_engine == "pollinations":
                # 使用 Pollinations AI
                self._generate_with_pollinations(prompt)
            elif selected_engine == "comfyui":
                # 使用 ComfyUI
                self._generate_with_comfyui(prompt)
            else:
                logger.error(f"未知的生成引擎: {selected_engine}")
                QMessageBox.warning(self, "错误", "未知的生成引擎")
                return
                
        except Exception as e:
            logger.error(f"图片生成过程中发生错误: {e}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"图片生成失败: {str(e)}")
            self._reset_ui_state()
    
    def _generate_with_pollinations(self, prompt):
        """使用 Pollinations AI 生成图片"""
        logger.info("使用 Pollinations AI 生成图片")
        
        # 初始化图像生成服务
        if not hasattr(self, 'image_generation_service') or not self.image_generation_service:
            self._init_image_generation_service()
        
        if not self.image_generation_service:
            QMessageBox.warning(self, "服务不可用", "图像生成服务初始化失败")
            return
        
        # 更新UI状态
        self.generate_image_btn.setEnabled(False)
        self.generate_image_btn.setText("生成中...")
        self.generated_image_status_label.setText("正在使用 Pollinations AI 生成图片...")
        self.generated_image_status_label.setProperty("class", "status-label-info")
        
        # 在新线程中生成图片
        from gui.image_generation_thread import ImageGenerationThread
        
        # 获取项目管理器和当前项目名称
        project_manager = getattr(self.parent(), 'project_manager', None)
        current_project_name = getattr(self.parent(), 'current_project_name', None)
        
        self.image_generation_thread = ImageGenerationThread(
            self.image_generation_service, prompt, project_manager=project_manager, current_project_name=current_project_name
        )
        self.image_generation_thread.image_generated.connect(self.on_image_generated)
        self.image_generation_thread.error_occurred.connect(self.on_image_generation_error)
        self.image_generation_thread.start()
    
    def _generate_with_comfyui(self, prompt):
        """使用 ComfyUI 生成图片"""
        logger.info("使用 ComfyUI 生成图片")
        
        # 检查ComfyUI连接
        logger.debug(f"检查ComfyUI连接状态: {self.comfyui_client is not None}")
        if not self.comfyui_client:
            logger.warning("ComfyUI未连接，无法生成图片")
            QMessageBox.warning(self, "警告", "请先连接到ComfyUI")
            return
        
        # 检查工作流选择
        workflow_name = self.workflow_panel.get_current_workflow_name()
        logger.debug(f"当前选择的工作流: '{workflow_name}'")
        if not workflow_name or workflow_name == "请选择工作流":
            logger.warning("用户未选择工作流")
            QMessageBox.warning(self, "警告", "请选择一个工作流")
            return
        
        # 获取工作流参数
        try:
            workflow_params = self.workflow_panel.get_current_workflow_parameters()
            logger.debug(f"工作流参数: {workflow_params}")
        except Exception as e:
            logger.error(f"获取工作流参数失败: {e}")
            logger.error(f"工作流参数获取异常堆栈: {traceback.format_exc()}")
            QMessageBox.warning(self, "错误", f"获取工作流参数失败: {str(e)}")
            return
        
        # 更新UI状态
        logger.info("更新UI状态为生成中")
        self.generate_image_btn.setEnabled(False)
        self.generate_image_btn.setText("生成中...")
        self.generated_image_status_label.setText("正在使用 ComfyUI 生成图片...")
        self.generated_image_status_label.setProperty("class", "status-label-info")
        
        # 在底部状态栏显示绘图信息
        if hasattr(self.parent(), 'log_output_bottom'):
            status_message = f"🎨 AI绘图标签页正在生成图片 | 工作流: {workflow_name} | 提示词: {prompt[:30]}{'...' if len(prompt) > 30 else ''}"
            self.parent().log_output_bottom.appendPlainText(status_message)
            self.parent().log_output_bottom.verticalScrollBar().setValue(
                self.parent().log_output_bottom.verticalScrollBar().maximum()
            )
            
        # 强制刷新日志
        logger.flush()
        
        # 调用ComfyUI生成图片
        logger.info(f"开始调用ComfyUI生成图片 - 工作流: {workflow_name}, 提示词: {prompt}")
        try:
            # 获取项目管理器和当前项目名称
            project_manager = None
            current_project_name = None
            if hasattr(self.parent_window, 'project_manager'):
                project_manager = self.parent_window.project_manager
            if hasattr(self.parent_window, 'current_project_name'):
                current_project_name = self.parent_window.current_project_name
            
            image_paths = self.comfyui_client.generate_image_with_workflow(prompt, workflow_name, workflow_params, project_manager, current_project_name)
            logger.info(f"ComfyUI返回结果: {image_paths}")
            
            # 处理生成结果
            if image_paths and not image_paths[0].startswith("ERROR:"):
                logger.info(f"图片生成成功，共 {len(image_paths)} 张图片")
                try:
                    self.add_images_to_gallery(image_paths)
                    logger.info("图片已成功添加到图片库")
                except Exception as e:
                    logger.error(f"添加图片到图片库时发生异常: {e}")
                    logger.error(f"添加图片异常堆栈: {traceback.format_exc()}")
                    raise
                
                self.generated_image_status_label.setText(f"✅ 成功生成 {len(image_paths)} 张图片")
                self.generated_image_status_label.setProperty("class", "status-label-success")
                
                # 在底部状态栏显示成功信息
                if hasattr(self.parent(), 'log_output_bottom'):
                    success_message = f"✅ AI绘图标签页成功生成 {len(image_paths)} 张图片"
                    self.parent().log_output_bottom.appendPlainText(success_message)
                    self.parent().log_output_bottom.verticalScrollBar().setValue(
                        self.parent().log_output_bottom.verticalScrollBar().maximum()
                    )
            else:
                error_message = image_paths[0] if image_paths else "未知错误"
                logger.error(f"图片生成失败: {error_message}")
                self.generated_image_status_label.setText(f"❌ 图片生成失败: {error_message}")
                self.generated_image_status_label.setProperty("class", "status-label-error")
                
                # 在底部状态栏显示失败信息
                if hasattr(self.parent(), 'log_output_bottom'):
                    fail_message = f"❌ AI绘图标签页图片生成失败: {error_message}"
                    self.parent().log_output_bottom.appendPlainText(fail_message)
                    self.parent().log_output_bottom.verticalScrollBar().setValue(
                        self.parent().log_output_bottom.verticalScrollBar().maximum()
                    )
                
                QMessageBox.warning(self, "生成失败", f"图片生成失败，请检查工作流配置或ComfyUI服务状态: {error_message}")
                
        except Exception as e:
            logger.critical(f"图片生成过程中发生严重错误: {e}")
            logger.critical(f"错误类型: {type(e).__name__}")
            logger.critical(f"错误堆栈: {traceback.format_exc()}")
            
            # 强制刷新日志确保错误信息被写入
            logger.flush()
            
            self.generated_image_status_label.setText("❌ 生成错误")
            self.generated_image_status_label.setProperty("class", "status-label-error")
            QMessageBox.critical(self, "严重错误", f"图片生成过程中发生严重错误: {str(e)}\n\n请查看日志文件获取详细信息。")
        finally:
            logger.info("恢复UI状态")
            self.generate_image_btn.setEnabled(True)
            self.generate_image_btn.setText("生成图片")
            logger.info("=== 图片生成流程结束 ===")
            # 强制刷新日志
            logger.flush()
    
    def add_images_to_gallery(self, image_paths):
        """将图片添加到图片库"""
        try:
            # 获取ComfyUI输出目录
            comfyui_output_dir = ""
            if hasattr(self.parent_window, 'app_settings'):
                comfyui_output_dir = self.parent_window.app_settings.get('comfyui_output_dir', '').strip()
            
            for image_path in image_paths:
                # 构建完整的图片路径
                full_image_path = image_path
                if comfyui_output_dir and not os.path.isabs(image_path):
                    # 如果是相对路径，则与ComfyUI输出目录组合
                    cleaned_relative_path = image_path.lstrip('\\/')
                    full_image_path = os.path.join(comfyui_output_dir, cleaned_relative_path)
                    full_image_path = os.path.normpath(full_image_path)
                    logger.info(f"构建完整图片路径: {image_path} -> {full_image_path}")
                
                if os.path.exists(full_image_path):
                    # 自动复制图片到当前项目文件夹
                    project_image_path = self._copy_image_to_project(full_image_path)
                    
                    # 创建图片标签
                    image_label = QLabel()
                    pixmap = QPixmap(full_image_path)
                    if not pixmap.isNull():
                        # 缩放图片到合适大小
                        scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        image_label.setPixmap(scaled_pixmap)
                        image_label.setAlignment(Qt.AlignCenter)
                        image_label.setProperty("class", "image-label")
                        
                        # 添加到网格布局
                        row = len(self.generated_images) // 3
                        col = len(self.generated_images) % 3
                        self.image_gallery_layout.addWidget(image_label, row, col)
                        
                        # 保存图片信息（使用项目中的路径）
                        final_image_path = project_image_path if project_image_path else full_image_path
                        self.generated_images.append({
                            'path': final_image_path,
                            'label': image_label,
                            'prompt': self.image_desc_input.text()
                        })
                        
                        # 同时添加到主窗口的图片库
                        if hasattr(self.parent_window, 'add_image_to_gallery'):
                            try:
                                self.parent_window.add_image_to_gallery(final_image_path, self.image_desc_input.text())
                                logger.info(f"图片已同步到主窗口图片库: {final_image_path}")
                            except Exception as e:
                                logger.error(f"同步图片到主窗口图片库失败: {e}")
                        
                        logger.info(f"添加图片到图片库: {full_image_path}")
                        if project_image_path:
                            logger.info(f"图片已复制到项目文件夹: {project_image_path}")
                    else:
                        logger.warning(f"无法加载图片: {full_image_path}")
                else:
                    logger.warning(f"图片文件不存在: {full_image_path} (原始路径: {image_path})")
                    
        except Exception as e:
            logger.error(f"添加图片到图片库时发生错误: {e}")
    
    def _copy_image_to_project(self, source_image_path):
        """将图片复制到当前项目的images文件夹中
        
        Args:
            source_image_path: 源图片路径
            
        Returns:
            str: 项目中的图片路径，如果复制失败则返回None
        """
        try:
            # 获取当前项目名称
            if not hasattr(self.parent(), 'current_project_name') or not self.parent().current_project_name:
                logger.warning("当前没有打开的项目，无法自动保存图片")
                return None
            
            current_project_name = self.parent().current_project_name
            
            # 获取项目管理器
            if not hasattr(self.parent(), 'project_manager'):
                logger.warning("项目管理器不可用，无法自动保存图片")
                return None
            
            project_manager = self.parent().project_manager
            
            # 获取项目路径
            project_root = project_manager.get_project_path(current_project_name)
            
            # 根据图片来源确定保存目录
            if 'comfyui' in source_image_path.lower() or 'ComfyUI' in source_image_path:
                project_images_dir = os.path.join(project_root, 'images', 'comfyui')
            elif 'pollinations' in source_image_path.lower():
                project_images_dir = os.path.join(project_root, 'images', 'pollinations')
            else:
                # 默认使用comfyui目录（因为AI绘图标签页主要用于ComfyUI）
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
    
    def clear_image_gallery(self):
        """清空图片库"""
        try:
            # 清除所有图片标签
            while self.image_gallery_layout.count():
                child = self.image_gallery_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # 清空图片列表
            self.generated_images.clear()
            self.selected_image_index = -1
            
            self.generated_image_status_label.setText("图片库已清空")
            self.generated_image_status_label.setProperty("class", "status-label-default")
            logger.info("图片库已清空")
            
        except Exception as e:
            logger.error(f"清空图片库时发生错误: {e}")
    
    def get_selected_image_paths(self):
        """获取选中的图片路径列表"""
        # 这里简化实现，返回所有图片路径
        return [img['path'] for img in self.generated_images if os.path.exists(img['path'])]
    
    def get_comfyui_client(self):
        """获取ComfyUI客户端实例"""
        return self.comfyui_client
    
    def get_workflow_panel(self):
        """获取工作流面板实例"""
        return self.workflow_panel
    
    def get_current_settings(self):
        """获取当前绘图设置"""
        try:
            settings = {
                'comfyui_url': self.comfyui_url_input.text(),
                'selected_engine': self.engine_combo.currentData(),  # 添加引擎选择
                'selected_workflow': getattr(self, 'current_workflow_file', ''),
                'workflow_settings': {},
                'generated_images': self.generated_images.copy(),
                'selected_image_index': self.selected_image_index
            }
            
            # 获取工作流面板的设置
            if hasattr(self, 'workflow_panel') and self.workflow_panel:
                settings['workflow_settings'] = self.workflow_panel.get_current_settings()
            
            return settings
            
        except Exception as e:
            logger.error(f"获取绘图设置失败: {e}")
            return {}
    
    def load_settings(self, settings):
        """加载绘图设置"""
        try:
            if not settings:
                return
            
            # 加载ComfyUI地址
            if 'comfyui_url' in settings:
                self.comfyui_url_input.setText(settings['comfyui_url'])
            
            # 加载引擎选择
            if 'selected_engine' in settings:
                engine = settings['selected_engine']
                for i in range(self.engine_combo.count()):
                    if self.engine_combo.itemData(i) == engine:
                        self.engine_combo.setCurrentIndex(i)
                        break
            
            # 加载选中的工作流
            if 'selected_workflow' in settings and settings['selected_workflow']:
                self.current_workflow_file = settings['selected_workflow']
                # TODO: 重新加载工作流文件
            
            # 先清空现有的图片数据
            self.generated_images.clear()
            self.selected_image_index = -1
            
            # 加载生成的图片
            if 'generated_images' in settings and settings['generated_images']:
                # 复制图片数据并验证路径
                for img_info in settings['generated_images']:
                    if isinstance(img_info, dict) and 'path' in img_info:
                        img_path = img_info['path']
                        # 如果是相对路径，转换为绝对路径
                        if not os.path.isabs(img_path) and hasattr(self.parent_window, 'current_project_dir') and self.parent_window.current_project_dir:
                            img_path = os.path.join(self.parent_window.current_project_dir, img_path)
                        
                        # 更新图片信息中的路径
                        updated_img_info = img_info.copy()
                        updated_img_info['path'] = img_path
                        self.generated_images.append(updated_img_info)
                        
                        logger.debug(f"加载图片: {img_info['path']} -> {img_path}")
                
                self.refresh_image_display()
            
            # 加载选中的图片索引
            if 'selected_image_index' in settings:
                self.selected_image_index = settings['selected_image_index']
            
            # 加载工作流设置
            if 'workflow_settings' in settings and hasattr(self, 'workflow_panel') and self.workflow_panel:
                self.workflow_panel.load_settings(settings['workflow_settings'])
            
            logger.info("绘图设置已加载")
            
        except Exception as e:
            logger.error(f"加载绘图设置失败: {e}")
    
    def reset_to_default(self):
        """重置到默认设置"""
        try:
            # 重置ComfyUI地址
            self.comfyui_url_input.setText("http://127.0.0.1:8188")
            
            # 清空生成的图片
            self.generated_images = []
            self.selected_image_index = -1
            self.refresh_image_display()
            
            # 重置工作流设置
            if hasattr(self, 'workflow_panel') and self.workflow_panel:
                self.workflow_panel.reset_to_default()
            
            # 重置其他状态
            self.current_workflow_file = ''
            
            logger.info("绘图设置已重置为默认值")
            
        except Exception as e:
            logger.error(f"重置绘图设置失败: {e}")
    
    def refresh_image_display(self):
        """刷新图片显示"""
        try:
            # 清除所有图片标签
            while self.image_gallery_layout.count():
                child = self.image_gallery_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            logger.info(f"开始刷新图片显示，共有 {len(self.generated_images)} 张图片")
            
            # 重新添加图片
            for i, img_info in enumerate(self.generated_images):
                image_path = img_info['path']
                logger.debug(f"检查图片 {i+1}: {image_path}")
                
                if os.path.exists(image_path):
                    logger.debug(f"图片文件存在: {image_path}")
                    image_label = QLabel()
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        image_label.setPixmap(scaled_pixmap)
                        image_label.setAlignment(Qt.AlignCenter)
                        image_label.setProperty("class", "image-label")
                        
                        row = i // 3
                        col = i % 3
                        self.image_gallery_layout.addWidget(image_label, row, col)
                        
                        # 更新标签引用
                        img_info['label'] = image_label
                        logger.debug(f"图片 {i+1} 显示成功")
                    else:
                        logger.warning(f"无法加载图片像素数据: {image_path}")
                else:
                    logger.warning(f"图片文件不存在: {image_path}")
                    # 检查是否是相对路径问题
                    if hasattr(self.parent_window, 'current_project_name') and self.parent_window.current_project_name:
                        project_manager = getattr(self.parent_window, 'project_manager', None)
                        if project_manager:
                            project_root = project_manager.get_project_path(self.parent_window.current_project_name)
                            # 尝试构建绝对路径
                            if not os.path.isabs(image_path):
                                absolute_path = os.path.join(project_root, image_path)
                                logger.debug(f"尝试绝对路径: {absolute_path}")
                                if os.path.exists(absolute_path):
                                    logger.info(f"找到图片文件，更新路径: {image_path} -> {absolute_path}")
                                    img_info['path'] = absolute_path
                                    # 重新尝试加载
                                    image_label = QLabel()
                                    pixmap = QPixmap(absolute_path)
                                    if not pixmap.isNull():
                                        scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                                        image_label.setPixmap(scaled_pixmap)
                                        image_label.setAlignment(Qt.AlignCenter)
                                        image_label.setProperty("class", "image-label")
                                        
                                        row = i // 3
                                        col = i % 3
                                        self.image_gallery_layout.addWidget(image_label, row, col)
                                        
                                        # 更新标签引用
                                        img_info['label'] = image_label
                                        logger.debug(f"图片 {i+1} 路径修复后显示成功")
            
            logger.info(f"图片显示刷新完成")
            
        except Exception as e:
            logger.error(f"刷新图片显示失败: {e}")
            if hasattr(self, 'parent_window') and hasattr(self.parent_window, 'log_output_bottom'):
                self.parent_window.log_output_bottom.appendPlainText(f"❌ 刷新图片显示失败: {e}")
    
    def _init_image_generation_service(self):
        """初始化图像生成服务"""
        try:
            from src.models.image_generation_service import ImageGenerationService
            self.image_generation_service = ImageGenerationService()
            logger.info("图像生成服务初始化成功")
        except Exception as e:
            logger.error(f"图像生成服务初始化失败: {e}")
            self.image_generation_service = None
    
    def on_image_generated(self, image_paths):
        """图片生成成功的回调"""
        try:
            # 重置UI状态
            self._reset_ui_state()
            
            # 添加到图片库
            self.add_images_to_gallery(image_paths)
            
            # 更新状态
            self.generated_image_status_label.setText("✅ 图片生成成功")
            self.generated_image_status_label.setStyleSheet("color: green;")
            
            logger.info(f"图片生成成功: {image_paths}")
            
        except Exception as e:
            logger.error(f"处理生成的图片失败: {e}")
            self.generated_image_status_label.setText(f"❌ 处理图片失败: {e}")
            self.generated_image_status_label.setStyleSheet("color: red;")
    
    def on_image_generation_error(self, error_message):
        """图片生成失败的回调"""
        # 重置UI状态
        self._reset_ui_state()
        
        # 更新状态
        self.generated_image_status_label.setText(f"❌ 图片生成失败: {error_message}")
        self.generated_image_status_label.setStyleSheet("color: red;")
        
        logger.error(f"图片生成失败: {error_message}")
    
    def _reset_ui_state(self):
        """重置UI状态"""
        self.generate_image_btn.setEnabled(True)
        self.generate_image_btn.setText("生成图片")
    
    def on_pollinations_seed_type_changed(self, seed_type):
        """处理Pollinations种子类型改变"""
        try:
            if seed_type == "随机":
                # 随机模式：禁用输入框，生成随机值
                self.pollinations_seed_edit.setEnabled(False)
                self.pollinations_seed_edit.setPlaceholderText("自动生成随机值")
                # 生成随机种子值并显示
                import random
                random_seed = random.randint(0, 2147483647)
                self.pollinations_seed_edit.setText(str(random_seed))
            else:
                # 固定模式：启用输入框
                self.pollinations_seed_edit.setEnabled(True)
                self.pollinations_seed_edit.setPlaceholderText("输入固定种子值")
                if not self.pollinations_seed_edit.text() or self.pollinations_seed_edit.text().isdigit():
                    self.pollinations_seed_edit.setText("42")  # 默认固定值
        except Exception as e:
            logger.error(f"处理种子类型改变失败: {e}")
    
    def get_current_pollinations_settings(self):
        """获取当前Pollinations AI设置"""
        try:
            settings = {
                'model': self.pollinations_model_combo.currentText(),
                'width': self.pollinations_width_spin.value(),
                'height': self.pollinations_height_spin.value(),
                'enhance': self.pollinations_enhance_check.isChecked(),
                'nologo': not self.pollinations_logo_check.isChecked(),
            }
            
            # 处理种子值
            seed_type = self.pollinations_seed_type_combo.currentText()
            if seed_type == "随机":
                # 随机模式：每次生成新的随机值
                import random
                settings['seed'] = random.randint(0, 2147483647)
            else:
                # 固定模式：使用输入框的值
                try:
                    seed_value = self.pollinations_seed_edit.text().strip()
                    if seed_value and seed_value.isdigit():
                        settings['seed'] = int(seed_value)
                    else:
                        settings['seed'] = 42  # 默认固定值
                except (ValueError, AttributeError):
                    settings['seed'] = 42
            
            logger.debug(f"Pollinations设置: {settings}")
            return settings
            
        except Exception as e:
            logger.error(f"获取Pollinations设置失败: {e}")
            # 返回默认设置
            return {
                'model': 'flux',
                'width': 1024,
                'height': 1024,
                'seed': 42,
                'enhance': False,
                'nologo': True
            }
    
    def get_current_engine_name(self):
        """获取当前选择的引擎名称"""
        try:
            return self.engine_combo.currentData()
        except Exception as e:
            logger.error(f"获取当前引擎名称失败: {e}")
            return "pollinations"  # 默认返回pollinations