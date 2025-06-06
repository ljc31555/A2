# -*- coding: utf-8 -*-
"""
图像生成服务 - 重写版本
- 简化异常处理，移除SystemExit相关代码
- 专注于ComfyUI引擎，简化架构
- 使用直接错误返回机制
"""
from typing import List, Dict, Optional
from utils.logger import logger
from models.comfyui_client import ComfyUIClient
import os

class ImageGenerationService:
    """统一的图像生成服务"""
    
    def __init__(self, comfyui_url: str = "http://127.0.0.1:8188", llm_api=None):
        """初始化图像生成服务
        
        Args:
            comfyui_url: ComfyUI服务地址
            llm_api: LLM API实例，用于提示词翻译
        """
        self.comfyui_url = comfyui_url
        self.llm_api = llm_api
        self.comfyui_client = None
        self.output_directory = None
        
        # 初始化ComfyUI客户端
        self._initialize_comfyui_client()
        
        logger.info(f"图像生成服务初始化完成，ComfyUI地址: {comfyui_url}")
    
    def _initialize_comfyui_client(self):
        """初始化ComfyUI客户端"""
        try:
            self.comfyui_client = ComfyUIClient(
                api_url=self.comfyui_url,
                llm_api=self.llm_api
            )
            logger.info("ComfyUI客户端初始化成功")
        except Exception as e:
            logger.error(f"ComfyUI客户端初始化失败: {str(e)}")
            self.comfyui_client = None
    
    def set_llm_api(self, llm_api):
        """设置LLM API实例"""
        self.llm_api = llm_api
        if self.comfyui_client:
            self.comfyui_client.set_llm_api(llm_api)
        logger.info("已更新图像生成服务的LLM API实例")
    
    def set_output_directory(self, directory: str):
        """设置输出目录"""
        self.output_directory = directory
        logger.info(f"已设置输出目录: {directory}")
    
    def test_connection(self) -> bool:
        """测试与ComfyUI的连接"""
        if not self.comfyui_client:
            logger.error("ComfyUI客户端未初始化")
            return False
        
        return self.comfyui_client.test_connection()
    
    def generate_image(self, prompt: str, workflow_id: str = None, parameters: Dict = None, 
                      project_manager=None, current_project_name=None) -> List[str]:
        """生成图像
        
        Args:
            prompt: 图像描述提示词
            workflow_id: 工作流ID
            parameters: 生成参数
            project_manager: 项目管理器
            current_project_name: 当前项目名称
        
        Returns:
            生成的图像路径列表，如果失败返回包含错误信息的列表
        """
        logger.info(f"=== 开始生成图像 ===")
        logger.info(f"提示词: {prompt}")
        logger.info(f"工作流ID: {workflow_id}")
        logger.info(f"参数: {parameters}")
        
        # 检查ComfyUI客户端
        if not self.comfyui_client:
            error_msg = "ERROR: ComfyUI客户端未初始化"
            logger.error(error_msg)
            return [error_msg]
        
        # 验证输入参数
        if not prompt or not prompt.strip():
            error_msg = "ERROR: 提示词不能为空"
            logger.error(error_msg)
            return [error_msg]
        
        try:
            # 设置项目信息
            if project_manager and current_project_name:
                self.comfyui_client.set_project_info(project_manager, current_project_name)
            
            # 调用ComfyUI客户端生成图像
            result = self.comfyui_client.generate_image_with_workflow(
                prompt=prompt,
                workflow_id=workflow_id,
                parameters=parameters,
                project_manager=project_manager,
                current_project_name=current_project_name
            )
            
            # 处理结果
            if result and isinstance(result, list):
                if len(result) > 0 and not result[0].startswith("ERROR"):
                    logger.info(f"图像生成成功，共 {len(result)} 张图片")
                    logger.info(f"=== 图像生成完成 ===")
                    return result
                else:
                    error_msg = result[0] if result else "ERROR: 未知错误"
                    logger.error(f"图像生成失败: {error_msg}")
                    logger.error(f"=== 图像生成失败 ===")
                    return result
            else:
                error_msg = "ERROR: ComfyUI返回无效结果"
                logger.error(error_msg)
                logger.error(f"=== 图像生成失败 ===")
                return [error_msg]
                
        except Exception as e:
            error_msg = f"ERROR: 图像生成过程中发生异常: {str(e)}"
            logger.error(error_msg)
            logger.error(f"异常类型: {type(e).__name__}")
            logger.error(f"=== 图像生成异常 ===")
            return [error_msg]
    
    def get_available_workflows(self) -> List[Dict[str, str]]:
        """获取可用的工作流列表"""
        if not self.comfyui_client:
            logger.error("ComfyUI客户端未初始化")
            return []
        
        try:
            workflows = self.comfyui_client.get_available_workflows()
            logger.info(f"获取到 {len(workflows)} 个可用工作流")
            return workflows
        except Exception as e:
            logger.error(f"获取工作流列表失败: {str(e)}")
            return []
    
    def set_current_workflow(self, workflow_id: str) -> bool:
        """设置当前工作流"""
        if not self.comfyui_client:
            logger.error("ComfyUI客户端未初始化")
            return False
        
        try:
            result = self.comfyui_client.set_current_workflow(workflow_id)
            if result:
                logger.info(f"成功设置当前工作流: {workflow_id}")
            else:
                logger.error(f"设置当前工作流失败: {workflow_id}")
            return result
        except Exception as e:
            logger.error(f"设置当前工作流异常: {str(e)}")
            return False
    
    def get_current_workflow(self) -> Optional[str]:
        """获取当前工作流ID"""
        if not self.comfyui_client:
            logger.error("ComfyUI客户端未初始化")
            return None
        
        try:
            workflow_id = self.comfyui_client.get_current_workflow()
            logger.info(f"当前工作流: {workflow_id}")
            return workflow_id
        except Exception as e:
            logger.error(f"获取当前工作流异常: {str(e)}")
            return None
    
    def get_workflow_config(self, workflow_id: str = None) -> Optional[Dict]:
        """获取工作流配置"""
        if not self.comfyui_client:
            logger.error("ComfyUI客户端未初始化")
            return None
        
        try:
            config = self.comfyui_client.get_workflow_config(workflow_id)
            if config:
                logger.info(f"获取工作流配置成功: {workflow_id or '当前工作流'}")
            else:
                logger.warning(f"工作流配置不存在: {workflow_id or '当前工作流'}")
            return config
        except Exception as e:
            logger.error(f"获取工作流配置异常: {str(e)}")
            return None
    
    def get_service_status(self) -> Dict:
        """获取服务状态"""
        status = {
            'comfyui_url': self.comfyui_url,
            'comfyui_client_initialized': self.comfyui_client is not None,
            'comfyui_connected': False,
            'llm_api_configured': self.llm_api is not None,
            'output_directory': self.output_directory,
            'current_workflow': None,
            'available_workflows_count': 0
        }
        
        try:
            if self.comfyui_client:
                status['comfyui_connected'] = self.comfyui_client.test_connection()
                status['current_workflow'] = self.comfyui_client.get_current_workflow()
                workflows = self.comfyui_client.get_available_workflows()
                status['available_workflows_count'] = len(workflows) if workflows else 0
        except Exception as e:
            logger.error(f"获取服务状态时发生异常: {str(e)}")
        
        return status
    
    def reload_workflows(self) -> bool:
        """重新加载工作流"""
        if not self.comfyui_client:
            logger.error("ComfyUI客户端未初始化")
            return False
        
        try:
            # 重新初始化工作流管理器
            self.comfyui_client.workflow_manager.load_workflows()
            logger.info("工作流重新加载成功")
            return True
        except Exception as e:
            logger.error(f"重新加载工作流失败: {str(e)}")
            return False
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.comfyui_client:
                # 这里可以添加清理ComfyUI客户端的逻辑
                pass
            logger.info("图像生成服务资源清理完成")
        except Exception as e:
            logger.error(f"清理资源时发生异常: {str(e)}")