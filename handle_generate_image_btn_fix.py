# 修复后的 handle_generate_image_btn 方法
# 请将此方法替换 main_window.py 中的对应方法

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
    
    self.generated_image_status_label.setText(f"正在使用 {self.image_generation_service.current_engine.value} 生成图片，请稍候...")
    self.generate_image_btn.setEnabled(False)
    
    # 在新线程中生成图片
    from gui.image_generation_thread import ImageGenerationThread
    self.image_generation_thread = ImageGenerationThread(
        self.image_generation_service, prompt
    )
    self.image_generation_thread.image_generated.connect(self.on_image_generated)
    self.image_generation_thread.error_occurred.connect(self.on_image_generation_error)
    self.image_generation_thread.start()
    return  # 退出方法，等待线程完成