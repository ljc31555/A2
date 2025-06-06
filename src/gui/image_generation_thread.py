# -*- coding: utf-8 -*-
"""
图像生成线程 - 重写版本
- 简化异常处理，移除SystemExit相关代码
- 使用直接错误返回机制
- 减少复杂依赖
"""
from PyQt5.QtCore import QThread, pyqtSignal
from utils.logger import logger
from models.image_generation_service import ImageGenerationService
import traceback

class ImageGenerationThread(QThread):
    """图像生成线程类"""
    
    # 信号定义
    image_generated = pyqtSignal(str)  # 图像生成成功信号，传递图像路径
    generation_failed = pyqtSignal(str)  # 图像生成失败信号，传递错误信息
    progress_updated = pyqtSignal(str)  # 进度更新信号，传递状态信息
    error_occurred = pyqtSignal(str)  # 错误信号，传递错误信息
    
    def __init__(self, prompt, workflow_id=None, parameters=None, project_manager=None, current_project_name=None, generation_params=None, parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.workflow_id = workflow_id
        self.parameters = generation_params or parameters or {}
        self.project_manager = project_manager
        self.current_project_name = current_project_name
        self.image_service = None
        self._is_cancelled = False
        
        logger.info(f"图像生成线程初始化完成")
        logger.info(f"提示词: {prompt}")
        logger.info(f"工作流ID: {workflow_id}")
        logger.info(f"参数: {parameters}")
    
    def set_image_service(self, image_service: ImageGenerationService):
        """设置图像生成服务"""
        self.image_service = image_service
        logger.info("已设置图像生成服务")
    
    def cancel(self):
        """取消图像生成"""
        self._is_cancelled = True
        logger.info("图像生成已被取消")
    
    def run(self):
        """线程主执行方法"""
        logger.info("=== 图像生成线程开始执行 ===")
        
        try:
            # 检查是否已取消
            if self._is_cancelled:
                logger.info("图像生成已取消")
                self.generation_failed.emit("图像生成已取消")
                return
            
            # 发送进度更新
            self.progress_updated.emit("正在初始化图像生成服务...")
            
            # 检查图像生成服务
            if not self.image_service:
                error_msg = "图像生成服务未初始化"
                logger.error(error_msg)
                self.generation_failed.emit(error_msg)
                return
            
            # 检查是否已取消
            if self._is_cancelled:
                logger.info("图像生成已取消")
                self.generation_failed.emit("图像生成已取消")
                return
            
            # 发送进度更新
            self.progress_updated.emit("正在生成图像...")
            
            # 调用图像生成服务
            logger.info("开始调用图像生成服务")
            result = self.image_service.generate_image(
                prompt=self.prompt,
                workflow_id=self.workflow_id,
                parameters=self.parameters,
                project_manager=self.project_manager,
                current_project_name=self.current_project_name
            )
            
            # 检查是否已取消
            if self._is_cancelled:
                logger.info("图像生成已取消")
                self.generation_failed.emit("图像生成已取消")
                return
            
            # 处理结果
            if result and isinstance(result, list) and len(result) > 0:
                first_result = result[0]
                
                # 检查是否为错误信息
                if first_result.startswith("ERROR:"):
                    error_msg = first_result[6:].strip()  # 移除"ERROR:"前缀
                    logger.error(f"图像生成失败: {error_msg}")
                    self.generation_failed.emit(error_msg)
                else:
                    # 生成成功
                    logger.info(f"图像生成成功: {first_result}")
                    self.progress_updated.emit("图像生成完成")
                    self.image_generated.emit(first_result)
            else:
                error_msg = "图像生成失败：未返回有效结果"
                logger.error(error_msg)
                self.generation_failed.emit(error_msg)
                
        except Exception as e:
            # 统一异常处理，不使用SystemExit
            error_msg = f"图像生成过程中发生错误: {str(e)}"
            logger.error(error_msg)
            logger.error(f"异常类型: {type(e).__name__}")
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            
            # 发送错误信号
            self.generation_failed.emit(error_msg)
            self.error_occurred.emit(error_msg)
            
        finally:
            logger.info("=== 图像生成线程执行结束 ===")
    
    def get_status_info(self):
        """获取状态信息"""
        return {
            'prompt': self.prompt,
            'workflow_id': self.workflow_id,
            'parameters': self.parameters,
            'is_cancelled': self._is_cancelled,
            'is_running': self.isRunning(),
            'is_finished': self.isFinished()
        }