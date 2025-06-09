#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目管理器
管理AI视频生成项目的创建、保存、文件组织等功能
"""

import os
import json
import time
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from utils.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class ProjectManager:
    """项目管理器"""
    
    def __init__(self, base_output_dir: str = "output"):
        self.base_output_dir = Path(base_output_dir)
        self.current_project: Optional[Dict[str, Any]] = None
        
        # 确保输出目录存在
        self.base_output_dir.mkdir(exist_ok=True)
        
        logger.info(f"项目管理器初始化完成，基础输出目录: {self.base_output_dir}")
    
    def create_new_project(self, project_name: str, description: str = "") -> Dict[str, Any]:
        """创建新项目"""
        try:
            # 清理项目名称（移除不合法的文件名字符）
            clean_name = self._clean_project_name(project_name)
            
            # 创建项目目录
            project_dir = self.base_output_dir / clean_name
            
            # 如果目录已存在，添加时间戳后缀
            if project_dir.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                clean_name = f"{clean_name}_{timestamp}"
                project_dir = self.base_output_dir / clean_name
            
            # 创建项目目录结构
            self._create_project_structure(project_dir)
            
            # 创建项目配置
            project_config = {
                "name": project_name,
                "clean_name": clean_name,
                "description": description,
                "created_time": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "project_dir": str(project_dir),
                "version": "1.0",
                "status": "created",
                "files": {
                    "original_text": None,
                    "rewritten_text": None,
                    "storyboard": None,
                    "images": [],
                    "audio": None,
                    "video": None,
                    "final_video": None,
                    "subtitles": None
                },
                "settings": {
                    "image_provider": None,
                    "image_config": {},
                    "video_config": {},
                    "audio_config": {}
                }
            }
            
            # 保存项目配置
            config_file = project_dir / "project.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(project_config, f, ensure_ascii=False, indent=2)
            
            self.current_project = project_config
            
            logger.info(f"新项目创建成功: {project_name} -> {project_dir}")
            return project_config
            
        except Exception as e:
            logger.error(f"创建项目失败: {e}")
            raise
    
    def _clean_project_name(self, name: str) -> str:
        """清理项目名称，移除不合法的文件名字符"""
        # 移除/替换不合法字符
        invalid_chars = '<>:"/\\|?*'
        clean_name = name
        for char in invalid_chars:
            clean_name = clean_name.replace(char, '_')
        
        # 移除前后空格并限制长度
        clean_name = clean_name.strip()[:50]
        
        # 如果为空，使用默认名称
        if not clean_name:
            clean_name = f"Project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return clean_name
    
    def _create_project_structure(self, project_dir: Path):
        """创建项目目录结构"""
        directories = [
            "texts",        # 文本文件（原始、改写后）
            "storyboard",   # 分镜脚本
            "images",       # 生成的图片
            "audio",        # 音频文件
            "video",        # 视频文件
            "assets",       # 其他资源
            "exports"       # 导出文件
        ]
        
        project_dir.mkdir(exist_ok=True)
        
        for dir_name in directories:
            (project_dir / dir_name).mkdir(exist_ok=True)
        
        logger.info(f"项目目录结构创建完成: {project_dir}")
    
    def load_project(self, project_path: str) -> Dict[str, Any]:
        """加载现有项目"""
        try:
            project_file = Path(project_path)
            
            # 如果是目录，查找project.json
            if project_file.is_dir():
                project_file = project_file / "project.json"
            
            if not project_file.exists():
                raise FileNotFoundError(f"项目文件不存在: {project_file}")
            
            with open(project_file, 'r', encoding='utf-8') as f:
                project_config = json.load(f)
            
            # 更新最后修改时间
            project_config["last_modified"] = datetime.now().isoformat()
            
            self.current_project = project_config
            
            logger.info(f"项目加载成功: {project_config['name']}")
            return project_config
            
        except Exception as e:
            logger.error(f"加载项目失败: {e}")
            raise
    
    def save_project(self) -> bool:
        """保存当前项目"""
        try:
            if not self.current_project:
                raise ValueError("没有当前项目可保存")
            
            # 更新最后修改时间
            self.current_project["last_modified"] = datetime.now().isoformat()
            
            # 保存项目配置
            project_dir = Path(self.current_project["project_dir"])
            config_file = project_dir / "project.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_project, f, ensure_ascii=False, indent=2)
            
            logger.info(f"项目保存成功: {self.current_project['name']}")
            return True
            
        except Exception as e:
            logger.error(f"保存项目失败: {e}")
            return False
    
    def get_project_file_path(self, file_type: str, filename: str = None) -> Path:
        """获取项目文件路径"""
        if not self.current_project:
            raise ValueError("没有当前项目")
        
        project_dir = Path(self.current_project["project_dir"])
        
        # 根据文件类型确定子目录
        type_mapping = {
            "original_text": "texts",
            "rewritten_text": "texts", 
            "storyboard": "storyboard",
            "images": "images",
            "audio": "audio",
            "video": "video",
            "final_video": "video",
            "subtitles": "video",
            "exports": "exports"
        }
        
        if file_type not in type_mapping:
            raise ValueError(f"不支持的文件类型: {file_type}")
        
        subdir = project_dir / type_mapping[file_type]
        
        if filename:
            return subdir / filename
        else:
            return subdir
    
    def save_text_content(self, content: str, text_type: str) -> str:
        """保存文本内容"""
        try:
            if text_type == "original_text":
                filename = "original_text.txt"
            elif text_type == "rewritten_text":
                filename = "rewritten_text.txt"
            else:
                raise ValueError(f"不支持的文本类型: {text_type}")
            
            file_path = self.get_project_file_path(text_type, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 更新项目配置
            self.current_project["files"][text_type] = str(file_path)
            self.save_project()
            
            logger.info(f"文本内容已保存: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"保存文本内容失败: {e}")
            raise
    
    def save_storyboard(self, storyboard_data: Dict[str, Any]) -> str:
        """保存分镜数据"""
        try:
            filename = "storyboard.json"
            file_path = self.get_project_file_path("storyboard", filename)
            
            # 添加保存时间戳
            storyboard_data["saved_time"] = datetime.now().isoformat()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(storyboard_data, f, ensure_ascii=False, indent=2)
            
            # 更新项目配置
            self.current_project["files"]["storyboard"] = str(file_path)
            self.save_project()
            
            logger.info(f"分镜数据已保存: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"保存分镜数据失败: {e}")
            raise
    
    def save_image(self, image_path: str, shot_id: str = None) -> str:
        """保存图像文件"""
        try:
            source_path = Path(image_path)
            
            if shot_id:
                filename = f"shot_{shot_id}_{source_path.name}"
            else:
                filename = source_path.name
            
            target_path = self.get_project_file_path("images", filename)
            
            # 复制文件
            shutil.copy2(source_path, target_path)
            
            # 更新项目配置
            if str(target_path) not in self.current_project["files"]["images"]:
                self.current_project["files"]["images"].append(str(target_path))
                self.save_project()
            
            logger.info(f"图像已保存: {target_path}")
            return str(target_path)
            
        except Exception as e:
            logger.error(f"保存图像失败: {e}")
            raise
    
    def save_video(self, video_path: str, video_type: str = "video") -> str:
        """保存视频文件"""
        try:
            source_path = Path(video_path)
            
            if video_type == "final_video":
                filename = f"final_{source_path.name}"
            else:
                filename = source_path.name
            
            target_path = self.get_project_file_path(video_type, filename)
            
            # 复制文件
            shutil.copy2(source_path, target_path)
            
            # 更新项目配置
            self.current_project["files"][video_type] = str(target_path)
            self.save_project()
            
            logger.info(f"视频已保存: {target_path}")
            return str(target_path)
            
        except Exception as e:
            logger.error(f"保存视频失败: {e}")
            raise
    
    def export_project(self, export_path: str = None) -> str:
        """导出项目"""
        try:
            if not self.current_project:
                raise ValueError("没有当前项目可导出")
            
            if export_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_filename = f"{self.current_project['clean_name']}_export_{timestamp}.json"
                export_path = self.get_project_file_path("exports", export_filename)
            
            export_data = {
                "project_info": self.current_project,
                "export_time": datetime.now().isoformat(),
                "exported_by": "AI Video Generator"
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"项目导出成功: {export_path}")
            return str(export_path)
            
        except Exception as e:
            logger.error(f"导出项目失败: {e}")
            raise
    
    def get_project_status(self) -> Dict[str, Any]:
        """获取项目状态"""
        if not self.current_project:
            return {
                "has_project": False,
                "project_name": None,
                "project_dir": None,
                "files_status": {}
            }
        
        files_status = {}
        for file_type, file_path in self.current_project["files"].items():
            if file_type == "images":
                files_status[file_type] = {
                    "exists": len(file_path) > 0 if isinstance(file_path, list) else False,
                    "count": len(file_path) if isinstance(file_path, list) else 0
                }
            else:
                if file_path:
                    files_status[file_type] = {
                        "exists": Path(file_path).exists() if file_path else False,
                        "path": file_path
                    }
                else:
                    files_status[file_type] = {
                        "exists": False,
                        "path": None
                    }
        
        return {
            "has_project": True,
            "project_name": self.current_project["name"],
            "project_dir": self.current_project["project_dir"],
            "created_time": self.current_project["created_time"],
            "last_modified": self.current_project["last_modified"],
            "files_status": files_status
        }
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """列出所有项目"""
        try:
            projects = []
            
            for item in self.base_output_dir.iterdir():
                if item.is_dir():
                    project_file = item / "project.json"
                    if project_file.exists():
                        try:
                            with open(project_file, 'r', encoding='utf-8') as f:
                                project_config = json.load(f)
                            projects.append({
                                "name": project_config["name"],
                                "clean_name": project_config["clean_name"],
                                "path": str(item),
                                "created_time": project_config["created_time"],
                                "last_modified": project_config["last_modified"]
                            })
                        except Exception as e:
                            logger.warning(f"读取项目配置失败: {project_file}, {e}")
            
            # 按最后修改时间排序
            projects.sort(key=lambda x: x["last_modified"], reverse=True)
            
            return projects
            
        except Exception as e:
            logger.error(f"列出项目失败: {e}")
            return []
    
    def delete_project(self, project_path: str) -> bool:
        """删除项目"""
        try:
            project_dir = Path(project_path)
            
            if project_dir.exists() and project_dir.is_dir():
                shutil.rmtree(project_dir)
                logger.info(f"项目已删除: {project_dir}")
                
                # 如果删除的是当前项目，清空当前项目
                if (self.current_project and 
                    self.current_project["project_dir"] == str(project_dir)):
                    self.current_project = None
                
                return True
            else:
                logger.warning(f"项目目录不存在: {project_dir}")
                return False
                
        except Exception as e:
            logger.error(f"删除项目失败: {e}")
            return False
    
    def clear_current_project(self):
        """清空当前项目"""
        self.current_project = None
        logger.info("当前项目已清空") 