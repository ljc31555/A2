# 这是一个修改说明文件，展示如何更新main_window.py中的handle_generate_image_btn方法

# 原方法需要替换为以下内容：

def handle_generate_image_btn(self):
    prompt = self.image_desc_input.text().strip()
    if not prompt:
        QMessageBox.warning(self, "提示", "请输入图片描述（prompt）！")
        return

    # 初始化图像生成服务（如果还没有）
    if not hasattr(self, 'image_generation_service') or not self.image_generation_service:
        self._init_image_generation_service()
    
    # 检查服务是否可用
    if not self.image_generation_service or not self.image_generation_service.is_service_available():
        QMessageBox.warning(self, "服务不可用", "图像生成服务当前不可用，请检查网络连接或配置。")
        return
    
    self.generated_image_status_label.setText("正在生成图片，请稍候...")
    self.generate_image_btn.setEnabled(False)
    
    # 在新线程中生成图片
    from gui.image_generation_thread import ImageGenerationThread
    self.image_generation_thread = ImageGenerationThread(
        prompt=prompt
    )
    self.image_generation_thread.set_image_service(self.image_generation_service)
    self.image_generation_thread.image_generated.connect(self.on_image_generated)
    self.image_generation_thread.generation_failed.connect(self.on_image_generation_error)
    self.image_generation_thread.start()
    return  # 退出方法，等待线程完成

# 还需要添加以下方法到MainWindow类中：

def _init_image_generation_service(self):
    """初始化图像生成服务"""
    try:
        from models.image_generation_service import ImageGenerationService
        
        # 设置输出目录（仅使用配置的ComfyUI输出目录）
        output_dir = self.app_settings.get('comfyui_output_dir', '')
        
        # 初始化服务
        self.image_generation_service = ImageGenerationService(
            app_settings=self.app_settings,
            llm_api=getattr(self, 'llm_api', None)
        )
        
        # 设置输出目录
        if hasattr(self.image_generation_service, 'set_output_directory'):
            self.image_generation_service.set_output_directory(output_dir)
        
        # 如果有ComfyUI客户端，将其设置为备用引擎
        if hasattr(self, 'comfyui_client') and self.comfyui_client:
            if hasattr(self.image_generation_service, 'set_comfyui_client'):
                self.image_generation_service.set_comfyui_client(self.comfyui_client)
        
        logger.info("图像生成服务初始化成功")
        
    except Exception as e:
        logger.error(f"初始化图像生成服务失败: {str(e)}")
        self.image_generation_service = None