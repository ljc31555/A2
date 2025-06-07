import json
import os
import shutil
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from utils.logger import logger
from utils.character_scene_manager import CharacterSceneManager

class ProjectManager:
    """项目状态管理器 - 负责保存和恢复项目工作状态"""
    
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self.projects_dir = os.path.join(config_dir, 'projects')
        os.makedirs(self.projects_dir, exist_ok=True)
        
    def create_project_structure(self, project_name: str) -> str:
        """创建项目文件夹结构
        
        Args:
            project_name: 项目名称
            
        Returns:
            str: 项目根目录路径
        """
        project_root = os.path.join(self.projects_dir, project_name)
        
        # 创建项目根目录
        os.makedirs(project_root, exist_ok=True)
        
        # 创建子目录
        subdirs = [
            'texts',      # 文本文件（原始文本、改写文本）
            'shots',      # 分镜表格文件
            'images',     # 生成的图片
            'audio',      # 配音文件
            'subtitles',  # 字幕文件
            'videos',     # 视频文件
            'temp',       # 临时文件
            'character_scene_db'  # 角色场景数据库
        ]
        
        for subdir in subdirs:
            os.makedirs(os.path.join(project_root, subdir), exist_ok=True)
        
        # 创建图片子目录
        image_subdirs = [
            'images/comfyui',      # ComfyUI生成的图片
            'images/pollinations'  # Pollinations生成的图片
        ]
        
        for subdir in image_subdirs:
            os.makedirs(os.path.join(project_root, subdir), exist_ok=True)
        
        logger.info(f"项目文件夹结构已创建: {project_root}")
        return project_root
        
    def get_project_path(self, project_name: str) -> str:
        """获取项目根目录路径"""
        return os.path.join(self.projects_dir, project_name)
        
    def get_project_config_path(self, project_name: str) -> str:
        """获取项目配置文件路径"""
        return os.path.join(self.get_project_path(project_name), 'project.json')
        
    def save_project(self, project_name: str, project_data: Dict[str, Any]) -> bool:
        """保存项目状态
        
        Args:
            project_name: 项目名称
            project_data: 项目数据，包含以下字段：
                - original_text: 原始文本
                - rewritten_text: 改写后文本
                - shots_data: 分镜数据
                - drawing_settings: 绘图设置
                - voice_settings: 配音设置
                - workflow_settings: 工作流设置
                - progress_status: 进度状态
                - created_time: 创建时间
                - last_modified: 最后修改时间
        
        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保项目文件夹结构存在
            project_root = self.create_project_structure(project_name)
            
            # 添加时间戳
            current_time = datetime.now().isoformat()
            project_data['last_modified'] = current_time
            if 'created_time' not in project_data:
                project_data['created_time'] = current_time
            
            # 保存文本文件
            texts_dir = os.path.join(project_root, 'texts')
            
            # 保存原始文本
            if project_data.get('original_text'):
                original_file = os.path.join(texts_dir, 'original.txt')
                with open(original_file, 'w', encoding='utf-8') as f:
                    f.write(project_data['original_text'])
            
            # 保存改写文本
            if project_data.get('rewritten_text'):
                rewritten_file = os.path.join(texts_dir, 'rewritten.txt')
                with open(rewritten_file, 'w', encoding='utf-8') as f:
                    f.write(project_data['rewritten_text'])
            
            # 保存分镜数据
            if project_data.get('shots_data'):
                shots_dir = os.path.join(project_root, 'shots')
                shots_file = os.path.join(shots_dir, 'shots.json')
                
                # 处理分镜数据中的图片路径
                processed_shots_data = []
                for shot in project_data['shots_data']:
                    processed_shot = shot.copy()
                    
                    # 处理主图片路径
                    if 'image' in processed_shot and processed_shot['image']:
                        image_path = processed_shot['image']
                        if os.path.isabs(image_path) and image_path.startswith(project_root):
                            processed_shot['image'] = os.path.normpath(os.path.relpath(image_path, project_root))
                    
                    # 处理备选图片路径
                    if 'alternative_images' in processed_shot and processed_shot['alternative_images']:
                        alt_images = processed_shot['alternative_images']
                        if alt_images:
                            alt_paths = [p.strip() for p in alt_images.split(';') if p.strip()]
                            processed_alt_paths = []
                            for alt_path in alt_paths:
                                if os.path.isabs(alt_path) and alt_path.startswith(project_root):
                                    rel_path = os.path.normpath(os.path.relpath(alt_path, project_root))
                                    processed_alt_paths.append(rel_path)
                                else:
                                    processed_alt_paths.append(alt_path)
                            processed_shot['alternative_images'] = ';'.join(processed_alt_paths)
                    
                    processed_shots_data.append(processed_shot)
                
                with open(shots_file, 'w', encoding='utf-8') as f:
                    json.dump(processed_shots_data, f, ensure_ascii=False, indent=2)
            
            # 保存生成的图片文件
            drawing_settings = project_data.get('drawing_settings', {})
            generated_images = drawing_settings.get('generated_images', [])
            if generated_images:
                images_dir = os.path.join(project_root, 'images')
                saved_images = []
                
                for i, image_info in enumerate(generated_images):
                    if isinstance(image_info, dict) and 'path' in image_info:
                        source_path = image_info['path']
                        if os.path.exists(source_path):
                            # 生成新的文件名
                            file_ext = os.path.splitext(source_path)[1]
                            new_filename = f"image_{i+1:03d}{file_ext}"
                            dest_path = os.path.join(images_dir, new_filename)
                            
                            try:
                                # 复制图片文件到项目文件夹
                                import shutil
                                shutil.copy2(source_path, dest_path)
                                
                                # 更新图片信息中的路径为相对路径
                                saved_image_info = image_info.copy()
                                # 使用os.path.join确保路径分隔符正确
                                saved_image_info['path'] = os.path.join("images", new_filename)
                                saved_images.append(saved_image_info)
                                
                                logger.info(f"图片已保存: {source_path} -> {dest_path}")
                            except Exception as e:
                                logger.error(f"复制图片文件失败: {source_path} -> {dest_path}, 错误: {e}")
                        else:
                            logger.warning(f"图片文件不存在: {source_path}")
                
                # 更新绘图设置中的图片路径
                if saved_images:
                    project_data['drawing_settings']['generated_images'] = saved_images
            
            # 构建项目配置文件路径
            project_config_file = self.get_project_config_path(project_name)
            
            # 创建配置数据（不包含大文本内容，只保存元数据和设置）
            config_data = {
                'project_name': project_name,
                'description': project_data.get('description', ''),
                'created_time': project_data['created_time'],
                'last_modified': project_data['last_modified'],
                'progress_status': project_data.get('progress_status', {}),
                'drawing_settings': project_data.get('drawing_settings', {}),
                'voice_settings': project_data.get('voice_settings', {}),
                'workflow_settings': project_data.get('workflow_settings', {}),
                'file_paths': {
                    'original_text': 'texts/original.txt' if project_data.get('original_text') else '',
                    'rewritten_text': 'texts/rewritten.txt' if project_data.get('rewritten_text') else '',
                    'shots_data': 'shots/shots.json' if project_data.get('shots_data') else ''
                }
            }
            
            # 保存项目配置
            with open(project_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"项目已保存: {project_name} -> {project_root}")
            return True
            
        except Exception as e:
            logger.error(f"保存项目失败: {e}")
            return False
    
    def load_project(self, project_name: str) -> Optional[Dict[str, Any]]:
        """加载项目状态
        
        Args:
            project_name: 项目名称
        
        Returns:
            Optional[Dict[str, Any]]: 项目数据，如果加载失败返回None
        """
        try:
            project_config_file = self.get_project_config_path(project_name)
            
            if not os.path.exists(project_config_file):
                logger.warning(f"项目配置文件不存在: {project_config_file}")
                return None
            
            # 加载项目配置
            with open(project_config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            project_root = self.get_project_path(project_name)
            
            # 加载文本文件
            original_text = ''
            rewritten_text = ''
            shots_data = []
            
            # 加载原始文本
            original_file = os.path.join(project_root, 'texts', 'original.txt')
            if os.path.exists(original_file):
                with open(original_file, 'r', encoding='utf-8') as f:
                    original_text = f.read()
            
            # 加载改写文本
            rewritten_file = os.path.join(project_root, 'texts', 'rewritten.txt')
            if os.path.exists(rewritten_file):
                with open(rewritten_file, 'r', encoding='utf-8') as f:
                    rewritten_text = f.read()
            
            # 加载分镜数据
            shots_file = os.path.join(project_root, 'shots', 'shots.json')
            if os.path.exists(shots_file):
                with open(shots_file, 'r', encoding='utf-8') as f:
                    shots_data = json.load(f)
                
                # 处理分镜数据中的图片路径，将相对路径转换为绝对路径
                for shot in shots_data:
                    # 处理主图片路径
                    if 'image' in shot and shot['image']:
                        image_path = shot['image']
                        if not os.path.isabs(image_path):
                            shot['image'] = os.path.join(project_root, image_path)
                    
                    # 处理备选图片路径
                    if 'alternative_images' in shot and shot['alternative_images']:
                        alt_images = shot['alternative_images']
                        if alt_images:
                            alt_paths = [p.strip() for p in alt_images.split(';') if p.strip()]
                            processed_alt_paths = []
                            for alt_path in alt_paths:
                                if not os.path.isabs(alt_path):
                                    abs_path = os.path.join(project_root, alt_path)
                                    processed_alt_paths.append(abs_path)
                                else:
                                    processed_alt_paths.append(alt_path)
                            shot['alternative_images'] = ';'.join(processed_alt_paths)
            
            # 处理绘图设置中的图片路径
            drawing_settings = config_data.get('drawing_settings', {})
            generated_images = drawing_settings.get('generated_images', [])
            if generated_images:
                # 将相对路径转换为绝对路径
                for image_info in generated_images:
                    if isinstance(image_info, dict) and 'path' in image_info:
                        relative_path = image_info['path']
                        if not os.path.isabs(relative_path):
                            # 转换为绝对路径
                            absolute_path = os.path.join(project_root, relative_path)
                            image_info['path'] = absolute_path
            
            # 初始化角色场景管理器
            character_scene_manager = CharacterSceneManager(project_root)
            
            # 组合完整的项目数据
            project_data = {
                'project_name': config_data.get('project_name', project_name),
                'description': config_data.get('description', ''),
                'created_time': config_data.get('created_time', ''),
                'last_modified': config_data.get('last_modified', ''),
                'progress_status': config_data.get('progress_status', {}),
                'drawing_settings': drawing_settings,
                'voice_settings': config_data.get('voice_settings', {}),
                'workflow_settings': config_data.get('workflow_settings', {}),
                'original_text': original_text,
                'rewritten_text': rewritten_text,
                'shots_data': shots_data,
                'project_root': project_root,
                'character_scene_manager': character_scene_manager
            }
            
            logger.info(f"项目已加载: {project_name} <- {project_root}")
            return project_data
            
        except Exception as e:
            logger.error(f"加载项目失败: {e}")
            return None
    
    def list_projects(self) -> List[Dict[str, str]]:
        """列出所有项目
        
        Returns:
            List[Dict[str, str]]: 项目列表，每个项目包含name, created_time, last_modified
        """
        projects = []
        try:
            if not os.path.exists(self.projects_dir):
                return projects
            
            for item in os.listdir(self.projects_dir):
                item_path = os.path.join(self.projects_dir, item)
                # 检查是否为目录且包含project.json配置文件
                if os.path.isdir(item_path):
                    config_file = os.path.join(item_path, 'project.json')
                    if os.path.exists(config_file):
                        try:
                            with open(config_file, 'r', encoding='utf-8') as f:
                                project_data = json.load(f)
                            
                            projects.append({
                                'name': item,
                                'created_time': project_data.get('created_time', '未知'),
                                'last_modified': project_data.get('last_modified', '未知'),
                                'progress_status': project_data.get('progress_status', {})
                            })
                        except Exception as e:
                            logger.warning(f"读取项目文件失败: {config_file}, 错误: {e}")
                            continue
            
            # 按最后修改时间排序
            projects.sort(key=lambda x: x['last_modified'], reverse=True)
            
        except Exception as e:
            logger.error(f"列出项目失败: {e}")
        
        return projects
    
    def get_project_list(self) -> List[str]:
        """获取所有项目名称列表
        
        Returns:
            List[str]: 项目名称列表
        """
        try:
            projects = []
            for item in os.listdir(self.projects_dir):
                item_path = os.path.join(self.projects_dir, item)
                # 检查是否为目录且包含project.json配置文件
                if os.path.isdir(item_path):
                    config_file = os.path.join(item_path, 'project.json')
                    if os.path.exists(config_file):
                        projects.append(item)
            
            return sorted(projects)
            
        except Exception as e:
            logger.error(f"获取项目列表失败: {e}")
            return []
    
    def delete_project(self, project_name: str) -> bool:
        """删除项目及其所有相关文件
        
        Args:
            project_name: 项目名称
        
        Returns:
            bool: 删除是否成功
        """
        try:
            project_root = self.get_project_path(project_name)
            
            if os.path.exists(project_root):
                # 删除整个项目文件夹
                shutil.rmtree(project_root)
                logger.info(f"项目及所有相关文件已删除: {project_name} -> {project_root}")
                return True
            else:
                logger.warning(f"项目文件夹不存在: {project_root}")
                return False
                
        except Exception as e:
            logger.error(f"删除项目失败: {e}")
            return False
    
    def export_project(self, project_name: str, export_path: str) -> bool:
        """导出项目到指定路径
        
        Args:
            project_name: 项目名称
            export_path: 导出路径
            
        Returns:
            bool: 导出是否成功
        """
        try:
            project_data = self.load_project(project_name)
            if not project_data:
                return False
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"项目已导出: {project_name} -> {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出项目失败: {e}")
            return False
    
    def import_project(self, import_path: str, project_name: str = None) -> bool:
        """从指定路径导入项目
        
        Args:
            import_path: 导入路径
            project_name: 项目名称，如果为None则使用文件名
            
        Returns:
            bool: 导入是否成功
        """
        try:
            if not os.path.exists(import_path):
                logger.error(f"导入文件不存在: {import_path}")
                return False
            
            with open(import_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            if not project_name:
                project_name = os.path.splitext(os.path.basename(import_path))[0]
            
            return self.save_project(project_name, project_data)
            
        except Exception as e:
            logger.error(f"导入项目失败: {e}")
            return False
    
    def get_project_status(self, project_name: str) -> Dict[str, Any]:
        """获取项目状态信息
        
        Args:
            project_name: 项目名称
            
        Returns:
            Dict[str, Any]: 项目状态信息
        """
        project_data = self.load_project(project_name)
        if not project_data:
            return {}
        
        progress_status = project_data.get('progress_status', {})
        
        return {
            'name': project_name,
            'created_time': project_data.get('created_time'),
            'last_modified': project_data.get('last_modified'),
            'has_original_text': bool(project_data.get('original_text')),
            'has_rewritten_text': bool(project_data.get('rewritten_text')),
            'shots_count': len(project_data.get('shots_data', [])),
            'progress_status': progress_status,
            'completion_percentage': self._calculate_completion_percentage(progress_status)
        }
    
    def add_image_to_project(self, project_name: str, image_path: str, metadata: Dict[str, Any] = None) -> Optional[str]:
        """将图片添加到项目中
        
        Args:
            project_name: 项目名称
            image_path: 图片路径
            metadata: 图片元数据
            
        Returns:
            Optional[str]: 项目中的图片路径，如果保存失败返回None
        """
        try:
            if not project_name or not image_path:
                logger.warning("项目名称或图片路径为空")
                return None
                
            if not os.path.exists(image_path):
                logger.warning(f"图片文件不存在: {image_path}")
                return None
            
            # 获取项目路径
            project_root = self.get_project_path(project_name)
            
            # 根据图片来源确定保存目录
            if 'comfyui' in image_path.lower() or 'ComfyUI' in image_path:
                project_images_dir = os.path.join(project_root, 'images', 'comfyui')
            elif 'pollinations' in image_path.lower():
                project_images_dir = os.path.join(project_root, 'images', 'pollinations')
            else:
                # 根据metadata中的source字段判断
                source = metadata.get('source', '').lower() if metadata else ''
                if 'pollinations' in source:
                    project_images_dir = os.path.join(project_root, 'images', 'pollinations')
                else:
                    project_images_dir = os.path.join(project_root, 'images', 'comfyui')
            
            # 确保目标目录存在
            os.makedirs(project_images_dir, exist_ok=True)
            
            # 检查图片是否已经在项目目录中
            if os.path.commonpath([image_path, project_images_dir]) == project_images_dir:
                # 图片已经在项目目录中，直接返回路径
                logger.info(f"图片已在项目目录中: {image_path}")
                return image_path
            
            # 生成新的文件名（避免重复）
            timestamp = int(time.time() * 1000)  # 毫秒级时间戳
            original_filename = os.path.basename(image_path)
            name, ext = os.path.splitext(original_filename)
            new_filename = f"{name}_{timestamp}{ext}"
            
            # 目标路径
            target_path = os.path.join(project_images_dir, new_filename)
            
            # 复制文件
            shutil.copy2(image_path, target_path)
            
            logger.info(f"图片已添加到项目: {image_path} -> {target_path}")
            return target_path
            
        except Exception as e:
            logger.error(f"添加图片到项目失败: {e}")
            return None
    
    def _calculate_completion_percentage(self, progress_status: Dict[str, Any]) -> int:
        """计算项目完成百分比"""
        total_steps = 5  # 文本改写、分镜生成、绘图、配音、视频合成
        completed_steps = 0
        
        if progress_status.get('text_rewritten', False):
            completed_steps += 1
        if progress_status.get('shots_generated', False):
            completed_steps += 1
        if progress_status.get('images_generated', False):
            completed_steps += 1
        if progress_status.get('voices_generated', False):
            completed_steps += 1
        if progress_status.get('video_composed', False):
            completed_steps += 1
        
        return int((completed_steps / total_steps) * 100)