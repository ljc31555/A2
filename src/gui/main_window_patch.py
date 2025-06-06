# 主窗口修改补丁文件
# 这个文件包含了对主窗口handle_generate_image_btn方法的修改

def handle_generate_image_btn_new(self):
    """修改后的图像生成按钮处理方法"""
    prompt = self.image_desc_input.text().strip()
    if not prompt:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(self, "提示", "请输入图片描述（prompt）！")
        return

    # 初始化图像生成服务（如果还没有）
    if not hasattr(self, 'image_generation_service') or not self.image_generation_service:
        self._init_image_generation_service()
    
    # 检查服务是否可用
    if not self.image_generation_service or not self.image_generation_service.is_service_available():
        from PyQt5.QtWidgets import QMessageBox
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