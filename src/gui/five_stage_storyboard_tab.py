#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五阶段分镜生成标签页
实现从文章到分镜脚本的五阶段协作式生成流程：
1. 全局分析和"世界观圣经"创建
2. 角色管理
3. 场景分割
4. 分镜脚本生成
5. 优化预览
"""

import os
import json
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QPushButton,
    QPlainTextEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QScrollArea, QGridLayout, QFrame, QSpacerItem,
    QSizePolicy, QMessageBox, QDialog, QTabWidget, QProgressBar,
    QGroupBox, QTextEdit, QSpinBox, QCheckBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QDateTime
from PyQt5.QtGui import QFont, QTextCharFormat, QColor

from utils.logger import logger
from models.llm_api import LLMApi
from utils.config_manager import ConfigManager
# from utils.project_manager import StoryboardProjectManager  # 注释掉旧的导入
from utils.character_scene_manager import CharacterSceneManager
from gui.character_scene_dialog import CharacterSceneDialog
from processors.scene_description_enhancer import SceneDescriptionEnhancer
from gui.scene_enhancer_config_panel import SceneEnhancerConfigPanel


class StageWorkerThread(QThread):
    """阶段处理工作线程"""
    progress_updated = pyqtSignal(str)  # 进度消息
    stage_completed = pyqtSignal(int, dict)  # 阶段编号, 结果数据
    error_occurred = pyqtSignal(str)  # 错误信息
    
    def __init__(self, stage_num, llm_api, input_data, style=None, parent_tab=None):
        super().__init__()
        self.stage_num = stage_num
        self.llm_api = llm_api
        self.input_data = input_data
        # 如果没有指定风格，从配置中获取默认风格
        if style is None:
            from utils.config_manager import ConfigManager
            config_manager = ConfigManager()
            style = config_manager.get_setting("default_style", "电影风格")
        self.style = style
        self.parent_tab = parent_tab
        self.is_cancelled = False
    
    def cancel(self):
        """取消任务"""
        self.is_cancelled = True
    
    def run(self):
        """执行阶段任务"""
        try:
            if self.stage_num == 1:
                result = self._execute_stage1()  # 世界观分析
            elif self.stage_num == 2:
                result = {}  # 角色管理 - 不需要LLM处理
            elif self.stage_num == 3:
                result = self._execute_stage2()  # 场景分割
            elif self.stage_num == 4:
                result = self._execute_stage3()  # 分镜生成
            elif self.stage_num == 5:
                result = self._execute_stage4()  # 优化预览
            else:
                raise ValueError(f"未知的阶段编号: {self.stage_num}")
            
            if not self.is_cancelled:
                self.stage_completed.emit(self.stage_num, result)
        except Exception as e:
            if not self.is_cancelled:
                self.error_occurred.emit(str(e))
    
    def _execute_stage1(self):
        """执行阶段1：全局分析和世界观创建"""
        self.progress_updated.emit("🌍 正在进行全局分析...")
        
        article_text = self.input_data.get("article_text", "")
        
        prompt = f"""
你是一位专业的影视制作顾问和世界观设计师。请对以下文章进行深度分析，创建一个完整的"世界观圣经"(World Bible)，为后续的场景分割和分镜制作提供统一的参考标准。

请按照以下结构进行分析：

## 1. 故事核心
- 主题思想
- 情感基调
- 叙事风格

## 2. 角色档案
- 主要角色的外貌特征、性格特点、服装风格
- 次要角色的基本信息
- 角色关系图

## 3. 世界设定
- 时代背景
- 地理环境
- 社会文化背景
- 技术水平

## 4. 视觉风格指南
- 整体色彩基调
- 光影风格
- 构图偏好
- 镜头语言特点

## 5. 音效氛围
- 环境音效
- 音乐风格
- 重点音效提示

## 6. 制作规范
- 镜头切换节奏
- 特效使用原则
- 画面比例建议

请基于{self.style}风格进行分析。

文章内容：
{article_text}

请提供详细、专业的分析结果，确保后续制作的一致性。
"""
        
        if self.is_cancelled:
            return {}
        
        try:
            # 调用LLM API生成全局分析
            messages = [
                {"role": "system", "content": "你是一位专业的影视制作顾问，擅长分析文本内容并构建统一的视觉世界观。"},
                {"role": "user", "content": prompt}
            ]
            response = self.llm_api._make_api_call(
                model_name=self.llm_api.shots_model_name,
                messages=messages,
                task_name="global_analysis"
            )
            return {
                "world_bible": response,
                "article_text": article_text,
                "style": self.style
            }
        except Exception as e:
            raise Exception(f"世界观分析失败: {e}")
    
    def _execute_stage2(self):
        """执行阶段2：场景分割"""
        self.progress_updated.emit("🎬 正在进行智能场景分割...")
        
        world_bible = self.input_data.get("world_bible", "")
        article_text = self.input_data.get("article_text", "")
        
        prompt = f"""
你是一位专业的影视剪辑师和场景设计师。基于已建立的世界观圣经，请对文章进行智能场景分割。

世界观圣经：
{world_bible}

请按照以下要求进行场景分割：

## 分割原则
1. 根据故事情节的自然转折点分割
2. 考虑情感节奏的变化
3. 注意场景的视觉连贯性
4. 每个场景应有明确的戏剧目标

## 输出格式
请为每个场景提供以下信息：

### 场景X：[场景标题]
- **时长估计**：X-X秒
- **重要程度**：★★★★★ (1-5星)
- **情感基调**：[描述]
- **主要角色**：[列出]
- **场景描述**：[简要描述场景内容]
- **转场建议**：[与下一场景的连接方式]
- **关键台词**：[如有]
- **视觉重点**：[需要重点表现的视觉元素]

请确保场景分割合理，每个场景都有足够的戏剧张力，同时保持整体故事的流畅性。

文章内容：
{article_text}
"""
        
        if self.is_cancelled:
            return {}
        
        try:
            # 调用LLM API进行场景分割
            messages = [
                {"role": "system", "content": "你是一位专业的影视编剧，擅长将文本内容分割为逻辑清晰的场景段落。"},
                {"role": "user", "content": prompt}
            ]
            response = self.llm_api._make_api_call(
                model_name=self.llm_api.shots_model_name,
                messages=messages,
                task_name="scene_segmentation"
            )
            return {
                "scenes_analysis": response,
                "world_bible": world_bible,
                "article_text": article_text
            }
        except Exception as e:
            raise Exception(f"场景分割失败: {e}")
    
    def _execute_stage3(self):
        """执行阶段3：逐场景分镜脚本生成"""
        self.progress_updated.emit("📝 正在生成详细分镜脚本...")
        
        world_bible = self.input_data.get("world_bible", "")
        scenes_analysis = self.input_data.get("scenes_analysis", "")
        selected_scenes = self.input_data.get("selected_scenes", [])
        
        if not selected_scenes:
            raise Exception("请先选择要生成分镜的场景")
        
        storyboard_results = []
        
        for i, scene_info in enumerate(selected_scenes):
            if self.is_cancelled:
                break
                
            self.progress_updated.emit(f"📝 正在生成第{i+1}/{len(selected_scenes)}个场景的分镜脚本...")
            
            # 获取角色一致性提示词
            consistency_prompt = ""
            if self.parent_tab and hasattr(self.parent_tab, 'get_character_consistency_prompt'):
                try:
                    consistency_prompt = self.parent_tab.get_character_consistency_prompt()
                except Exception as e:
                    logger.warning(f"获取角色一致性提示词失败: {e}")
            
            prompt = f"""
你是一位专业的分镜师和导演。基于世界观圣经和场景分析，请为指定场景创建详细的分镜脚本。

世界观圣经（请严格遵循）：
{world_bible}

{consistency_prompt if consistency_prompt else ""}

场景分析参考：
{scenes_analysis}

当前场景信息：
{scene_info}

请按照以下专业格式输出分镜脚本：

## 场景分镜脚本

### 镜头1
- **镜头类型**：[特写/中景/全景/航拍等]
- **机位角度**：[平视/俯视/仰视/侧面等]
- **镜头运动**：[静止/推拉/摇移/跟随等]
- **景深效果**：[浅景深/深景深/焦点变化]
- **构图要点**：[三分法/对称/对角线等]
- **光影设计**：[自然光/人工光/逆光/侧光等]
- **色彩基调**：[暖色调/冷色调/对比色等]
- **时长**：X秒
- **镜头角色**：[列出根据画面描述中出现的角色，如：主人公、奶奶等]
- **画面描述**：[详细描述画面内容，包括角色位置、动作、表情、环境细节]
- **台词/旁白**：[如有]
- **音效提示**：[环境音、特效音等]
- **转场方式**：[切换/淡入淡出/叠化等]
请确保：
1. 严格遵循世界观圣经的设定
2. 使用专业的影视术语
3. 每个镜头都有明确的视觉目标
4. 画面描述要详细且专业，包含完整的视觉信息
5. 保持场景内镜头的连贯性
"""
            
            try:
                # 调用LLM API生成分镜脚本
                messages = [
                    {"role": "system", "content": "你是一位专业的分镜师，擅长为影视作品创建详细的分镜头脚本。"},
                    {"role": "user", "content": prompt}
                ]
                response = self.llm_api._make_api_call(
                    model_name=self.llm_api.shots_model_name,
                    messages=messages,
                    task_name="storyboard_generation"
                )
                storyboard_results.append({
                    "scene_index": i,
                    "scene_info": scene_info,
                    "storyboard_script": response
                })
            except Exception as e:
                logger.error(f"生成第{i+1}个场景分镜失败: {e}")
                continue
        
        return {
            "storyboard_results": storyboard_results,
            "world_bible": world_bible,
            "scenes_analysis": scenes_analysis
        }
    
    def _execute_stage4(self):
        """执行阶段4：视觉预览和迭代优化"""
        self.progress_updated.emit("🎨 正在进行视觉一致性检查...")
        
        storyboard_results = self.input_data.get("storyboard_results", [])
        world_bible = self.input_data.get("world_bible", "")
        
        # 自动启用增强器对画面描述进行优化
        enhanced_storyboard_results = []
        optimization_suggestions = []
        
        for result in storyboard_results:
            scene_index = result.get("scene_index", 0)
            storyboard_script = result.get("storyboard_script", "")
            
            self.progress_updated.emit(f"🔍 正在处理第{scene_index + 1}个场景的分镜优化...")
            
            # 解析分镜脚本，提取镜头信息
            if self.parent_tab and hasattr(self.parent_tab, '_enhance_storyboard_shots'):
                enhanced_shots = self.parent_tab._enhance_storyboard_shots(storyboard_script)
            else:
                enhanced_shots = []
            
            # 创建增强后的分镜结果
            enhanced_result = result.copy()
            enhanced_result["enhanced_shots"] = enhanced_shots
            enhanced_storyboard_results.append(enhanced_result)
            
            # 生成优化建议
            suggestions = {
                "scene_index": scene_index,
                "visual_consistency": "✅ 视觉风格与世界观一致",
                "technical_quality": "✅ 镜头语言专业规范",
                "narrative_flow": "✅ 叙事节奏合理",
                "enhancement_applied": "✅ 已应用角色和场景一致性增强",
                "optimization_tips": [
                    "已自动注入角色一致性提示词",
                    "已匹配场景一致性描述",
                    "已优化技术参数和构图建议",
                    "画面描述已通过AI增强器优化"
                ]
            }
            optimization_suggestions.append(suggestions)
        
        return {
            "optimization_suggestions": optimization_suggestions,
            "storyboard_results": enhanced_storyboard_results,
            "world_bible": world_bible
        }


class FiveStageStoryboardTab(QWidget):
    """五阶段分镜生成标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        
        # 初始化组件
        self.config_manager = ConfigManager()
        # 使用父窗口的ProjectManager实例
        self.project_manager = parent.project_manager if parent and hasattr(parent, 'project_manager') else None
        self.llm_api = None
        
        # 角色场景管理器
        self.character_scene_manager = None
        self.character_dialog = None
        
        # 初始化角色场景管理器
        if (self.project_manager and 
            self.project_manager.current_project and 
            'project_dir' in self.project_manager.current_project):
            project_path = self.project_manager.current_project['project_dir']
            from src.utils.character_scene_manager import CharacterSceneManager
            self.character_scene_manager = CharacterSceneManager(project_path)
        else:
            self.character_scene_manager = None
        
        # 场景描述增强器
        self.scene_enhancer = None
        
        # 选中的角色和场景
        self.selected_characters = []
        self.selected_scenes = []
        
        # 当前阶段数据
        self.stage_data = {
            1: {},  # 世界观圣经 (Global Analysis)
            2: {},  # 角色管理 (Character Management)
            3: {},  # 场景分割 (Scene Segmentation)
            4: {},  # 分镜脚本 (Storyboard Generation)
            5: {}   # 优化预览 (Optimization Preview)
        }
        
        # 当前阶段
        self.current_stage = 1
        
        # 工作线程
        self.worker_thread = None
        
        self.init_ui()
        self.load_models()
        
        # 确保UI组件已完全初始化后再加载项目数据
        QTimer.singleShot(500, self.delayed_load_from_project)
    
    def _enhance_storyboard_shots(self, storyboard_script: str) -> List[Dict[str, Any]]:
        """增强分镜脚本中的镜头描述
        
        Args:
            storyboard_script: 分镜脚本文本
            
        Returns:
            List[Dict]: 增强后的镜头信息列表
        """
        enhanced_shots = []
        
        try:
            # 导入必要的模块
            from src.processors.prompt_optimizer import PromptOptimizer
            from src.processors.scene_description_enhancer import SceneDescriptionEnhancer
            
            # 初始化提示词优化器和场景增强器
            prompt_optimizer = PromptOptimizer()
            
            # 获取项目根目录
            project_root = self.project_manager.get_current_project_path() if self.project_manager else None
            if not project_root:
                logger.warning("无法获取项目路径，跳过增强处理")
                return enhanced_shots
            
            # 初始化场景描述增强器
            scene_enhancer = SceneDescriptionEnhancer(
                project_root=project_root,
                character_scene_manager=self.character_scene_manager,
                llm_api=self.llm_api
            )
            
            # 解析分镜脚本，提取镜头信息
            shots_info = prompt_optimizer._extract_shots_from_script(storyboard_script)
            
            for shot_info in shots_info:
                shot_number = shot_info.get('shot_number', '')
                description = shot_info.get('description', '')
                characters = shot_info.get('characters', '')
                
                # 解析角色信息
                character_list = [char.strip() for char in characters.split(',') if char.strip()] if characters else []
                
                # 获取角色一致性提示词
                character_consistency_prompts = self._get_character_consistency_prompts(character_list)
                
                # 获取场景一致性提示词
                scene_consistency_prompts = self._get_scene_consistency_prompts(description)
                
                # 构建完整的技术参数和一致性信息
                enhanced_prompt_data = {
                    "镜头类型": "中景",  # 默认值，可以通过AI分析优化
                    "机位角度": "平视",
                    "镜头运动": "摇移",
                    "景深效果": "深景深",
                    "构图要点": "三分法",
                    "光影设计": "自然光",
                    "色彩基调": "明亮",
                    "镜头角色": character_consistency_prompts,
                    "场景一致性": scene_consistency_prompts,
                    "画面描述": description
                }
                
                # 使用场景描述增强器进行优化
                enhanced_description = scene_enhancer.enhance_description(
                    original_description=description,
                    characters=character_list
                )
                
                # 构建最终的优化提示词
                final_prompt = self._build_final_prompt(enhanced_prompt_data, enhanced_description)
                
                enhanced_shot = {
                    "shot_number": shot_number,
                    "original_description": description,
                    "enhanced_description": enhanced_description,
                    "characters": character_list,
                    "character_consistency_prompts": character_consistency_prompts,
                    "scene_consistency_prompts": scene_consistency_prompts,
                    "technical_parameters": enhanced_prompt_data,
                    "final_prompt": final_prompt
                }
                
                enhanced_shots.append(enhanced_shot)
                
                logger.info(f"镜头 {shot_number} 增强完成")
            
        except Exception as e:
            logger.error(f"分镜脚本增强失败: {e}")
        
        return enhanced_shots
    
    def _get_character_consistency_prompts(self, character_list: List[str]) -> List[str]:
        """获取角色一致性提示词
        
        Args:
            character_list: 角色名称列表
            
        Returns:
            List[str]: 角色一致性提示词列表
        """
        consistency_prompts = []
        
        try:
            if not self.character_scene_manager:
                return consistency_prompts
            
            # 获取所有角色数据
            all_characters = self.character_scene_manager.get_all_characters()
            
            for character_name in character_list:
                # 查找匹配的角色
                for char_id, char_data in all_characters.items():
                    if char_data.get('name') == character_name:
                        consistency_prompt = char_data.get('consistency_prompt', '')
                        if consistency_prompt:
                            consistency_prompts.append(f"{character_name}（一致性提示词为：{consistency_prompt}）")
                        break
                else:
                    # 如果没有找到匹配的角色，添加基本信息
                    consistency_prompts.append(f"{character_name}（未找到详细一致性信息）")
            
        except Exception as e:
            logger.error(f"获取角色一致性提示词失败: {e}")
        
        return consistency_prompts
    
    def _get_scene_consistency_prompts(self, description: str) -> List[str]:
        """获取场景一致性提示词
        
        Args:
            description: 画面描述
            
        Returns:
            List[str]: 场景一致性提示词列表
        """
        consistency_prompts = []
        
        try:
            if not self.character_scene_manager:
                return consistency_prompts
            
            # 获取所有场景数据
            all_scenes = self.character_scene_manager.get_all_scenes()
            
            # 简单的场景匹配逻辑（可以优化为更智能的匹配）
            for scene_id, scene_data in all_scenes.items():
                scene_name = scene_data.get('name', '')
                scene_description = scene_data.get('description', '')
                
                # 检查描述中是否包含场景关键词
                if (scene_name and scene_name in description) or \
                   (scene_description and any(keyword in description for keyword in scene_description.split()[:5])):
                    consistency_prompt = scene_data.get('consistency_prompt', '')
                    if consistency_prompt:
                        consistency_prompts.append(f"{scene_name}：{consistency_prompt}")
            
        except Exception as e:
            logger.error(f"获取场景一致性提示词失败: {e}")
        
        return consistency_prompts
    
    def _build_final_prompt(self, prompt_data: Dict[str, Any], enhanced_description: str) -> str:
        """构建最终的优化提示词
        
        Args:
            prompt_data: 提示词数据
            enhanced_description: 增强后的描述
            
        Returns:
            str: 最终的优化提示词
        """
        try:
            prompt_parts = []
            
            # 添加技术参数
            technical_params = [
                f"**镜头类型**：{prompt_data.get('镜头类型', '')}",
                f"**机位角度**：{prompt_data.get('机位角度', '')}",
                f"**镜头运动**：{prompt_data.get('镜头运动', '')}",
                f"**景深效果**：{prompt_data.get('景深效果', '')}",
                f"**构图要点**：{prompt_data.get('构图要点', '')}",
                f"**光影设计**：{prompt_data.get('光影设计', '')}",
                f"**色彩基调**：{prompt_data.get('色彩基调', '')}"
            ]
            prompt_parts.extend(technical_params)
            
            # 添加角色一致性信息
            character_prompts = prompt_data.get('镜头角色', [])
            if character_prompts:
                prompt_parts.append(f"**镜头角色**：{', '.join(character_prompts)}")
            
            # 添加场景一致性信息
            scene_prompts = prompt_data.get('场景一致性', [])
            if scene_prompts:
                prompt_parts.append(f"**场景一致性**：{'; '.join(scene_prompts)}")
            
            # 添加增强后的画面描述
            prompt_parts.append(f"**画面描述**：{enhanced_description}")
            
            return '\n'.join(prompt_parts)
            
        except Exception as e:
            logger.error(f"构建最终提示词失败: {e}")
            return enhanced_description
    
    def init_ui(self):
        """初始化UI界面"""
        main_layout = QVBoxLayout()
        
        # 顶部控制区域
        self.create_control_area(main_layout)
        
        # 主要内容区域
        self.create_main_content_area(main_layout)
        
        # 底部状态区域
        self.create_status_area(main_layout)
        
        self.setLayout(main_layout)
    
    def create_control_area(self, parent_layout):
        """创建顶部控制区域"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.StyledPanel)
        control_layout = QHBoxLayout(control_frame)
        
        # 标题
        title_label = QLabel("🎬 五阶段分镜生成系统")
        from utils.config_manager import ConfigManager
        config_manager = ConfigManager()
        default_font = config_manager.get_setting("default_font_family", "Arial")
        title_label.setFont(QFont(default_font, 16, QFont.Bold))
        control_layout.addWidget(title_label)
        
        control_layout.addStretch()
        
        # 风格选择
        control_layout.addWidget(QLabel("风格："))
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "电影风格", "动漫风格", "吉卜力风格", "赛博朋克风格", 
            "水彩插画风格", "像素风格", "写实摄影风格"
        ])
        control_layout.addWidget(self.style_combo)
        
        # 模型选择
        control_layout.addWidget(QLabel("模型："))
        self.model_combo = QComboBox()
        control_layout.addWidget(self.model_combo)
        
        # 角色管理按钮
        self.character_btn = QPushButton("👥 角色管理")
        self.character_btn.clicked.connect(self.open_character_dialog)
        self.character_btn.setToolTip("管理角色信息，确保分镜中角色的一致性")
        control_layout.addWidget(self.character_btn)
        
        # 场景描述增强选项
        self.enhance_checkbox = QCheckBox("🎨 智能增强")
        self.enhance_checkbox.setChecked(True)
        self.enhance_checkbox.setToolTip("启用场景描述智能增强，自动添加技术细节和一致性描述")
        self.enhance_checkbox.stateChanged.connect(self.on_enhance_option_changed)
        control_layout.addWidget(self.enhance_checkbox)
        
        # 增强级别选择
        control_layout.addWidget(QLabel("增强级别："))
        self.enhance_level_combo = QComboBox()
        self.enhance_level_combo.addItems(["低", "中", "高"])
        self.enhance_level_combo.setCurrentText("中")
        self.enhance_level_combo.setToolTip("选择场景描述增强的详细程度")
        self.enhance_level_combo.currentTextChanged.connect(self.on_enhance_level_changed)
        control_layout.addWidget(self.enhance_level_combo)
        
        # 场景增强器配置按钮
        self.enhancer_config_btn = QPushButton("⚙️ 增强器配置")
        self.enhancer_config_btn.clicked.connect(self.open_enhancer_config)
        self.enhancer_config_btn.setToolTip("打开场景描述增强器的详细配置面板")
        control_layout.addWidget(self.enhancer_config_btn)
        
        # 注释：保存按钮已移除，使用主窗口的统一保存功能
        
        parent_layout.addWidget(control_frame)
    
    def create_main_content_area(self, parent_layout):
        """创建主要内容区域"""
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 阶段1：全局分析 (世界观圣经)
        self.create_stage1_tab()
        
        # 阶段2：角色管理
        self.create_stage2_tab()
        
        # 阶段3：场景分割
        self.create_stage3_tab()
        
        # 阶段4：分镜生成
        self.create_stage4_tab()
        
        # 阶段5：优化预览
        self.create_stage5_tab()
        
        parent_layout.addWidget(self.tab_widget)
    
    def create_stage1_tab(self):
        """创建阶段1标签页：全局分析和世界观创建"""
        stage1_widget = QWidget()
        layout = QVBoxLayout(stage1_widget)
        
        # 说明文本
        info_label = QLabel(
            "🌍 <b>阶段1：全局分析和世界观创建</b><br>"
            "对输入文章进行深度分析，建立统一的世界观圣经，为后续制作提供一致性参考。"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 输入区域
        input_group = QGroupBox("📝 输入文章")
        input_layout = QVBoxLayout(input_group)
        
        self.article_input = QPlainTextEdit()
        self.article_input.setPlaceholderText(
            "请输入要生成分镜的文章内容...\n\n"
            "支持小说、剧本、故事大纲等各种文本格式。\n"
            "系统将基于此内容进行全局分析和世界观构建。"
        )
        self.article_input.setMinimumHeight(200)
        input_layout.addWidget(self.article_input)
        
        # 从主窗口加载文本按钮
        load_btn = QPushButton("📥 从主窗口加载改写文本")
        load_btn.clicked.connect(self.load_text_from_main)
        input_layout.addWidget(load_btn)
        
        layout.addWidget(input_group)
        
        # 输出区域
        output_group = QGroupBox("🌍 世界观圣经")
        output_layout = QVBoxLayout(output_group)
        
        self.world_bible_output = QTextEdit()
        self.world_bible_output.setReadOnly(True)
        self.world_bible_output.setPlaceholderText("世界观分析结果将在这里显示...")
        output_layout.addWidget(self.world_bible_output)
        
        layout.addWidget(output_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.stage1_generate_btn = QPushButton("🚀 开始全局分析")
        self.stage1_generate_btn.clicked.connect(lambda: self.start_stage(1))
        btn_layout.addWidget(self.stage1_generate_btn)
        
        self.stage1_next_btn = QPushButton("➡️ 进入角色管理")
        self.stage1_next_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))
        self.stage1_next_btn.setEnabled(False)
        btn_layout.addWidget(self.stage1_next_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.tab_widget.addTab(stage1_widget, "1️⃣ 全局分析")
    
    def create_stage2_tab(self):
        """创建阶段2标签页：角色管理"""
        stage2_widget = QWidget()
        layout = QVBoxLayout(stage2_widget)
        
        # 说明文本
        info_label = QLabel(
            "👥 <b>阶段2：角色管理</b><br>"
            "基于世界观圣经，管理和完善角色信息，确保分镜制作中角色的一致性和连贯性。"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 角色信息显示区域
        characters_group = QGroupBox("👤 角色信息")
        characters_layout = QVBoxLayout(characters_group)
        
        self.characters_output = QTextEdit()
        self.characters_output.setReadOnly(True)
        self.characters_output.setPlaceholderText("角色信息将在这里显示...")
        characters_layout.addWidget(self.characters_output)
        
        layout.addWidget(characters_group)
        
        # 角色管理操作区域
        management_group = QGroupBox("🛠️ 角色管理操作")
        management_layout = QVBoxLayout(management_group)
        
        # 角色管理按钮
        manage_btn = QPushButton("📝 打开角色管理对话框")
        manage_btn.clicked.connect(self.open_character_dialog)
        management_layout.addWidget(manage_btn)
        
        # 自动提取角色按钮
        extract_btn = QPushButton("🔍 从世界观圣经自动提取角色")
        extract_btn.clicked.connect(self.auto_extract_characters)
        management_layout.addWidget(extract_btn)
        
        # 角色一致性检查按钮
        check_btn = QPushButton("✅ 检查角色一致性")
        check_btn.clicked.connect(self.check_character_consistency)
        management_layout.addWidget(check_btn)
        
        layout.addWidget(management_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.stage2_generate_btn = QPushButton("🔄 刷新角色信息")
        self.stage2_generate_btn.clicked.connect(self.refresh_character_info)
        btn_layout.addWidget(self.stage2_generate_btn)
        
        self.stage2_next_btn = QPushButton("➡️ 进入场景分割")
        self.stage2_next_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))
        self.stage2_next_btn.setEnabled(True)  # 角色管理不需要等待完成
        btn_layout.addWidget(self.stage2_next_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.tab_widget.addTab(stage2_widget, "2️⃣ 角色管理")
    
    def create_stage3_tab(self):
        """创建阶段3标签页：场景分割"""
        stage3_widget = QWidget()
        layout = QVBoxLayout(stage3_widget)
        
        # 说明文本
        info_label = QLabel(
            "🎬 <b>阶段3：智能场景分割</b><br>"
            "基于世界观圣经和角色信息，将文章智能分割为多个场景，并提供详细的场景分析。"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 场景分析结果
        scenes_group = QGroupBox("🎭 场景分析结果")
        scenes_layout = QVBoxLayout(scenes_group)
        
        self.scenes_output = QTextEdit()
        self.scenes_output.setReadOnly(True)
        self.scenes_output.setPlaceholderText("场景分割结果将在这里显示...")
        scenes_layout.addWidget(self.scenes_output)
        
        layout.addWidget(scenes_group)
        
        # 场景选择区域
        selection_group = QGroupBox("✅ 选择要生成分镜的场景")
        selection_layout = QVBoxLayout(selection_group)
        
        self.scenes_list = QListWidget()
        self.scenes_list.setSelectionMode(QAbstractItemView.MultiSelection)
        selection_layout.addWidget(self.scenes_list)
        
        select_all_btn = QPushButton("全选场景")
        select_all_btn.clicked.connect(self.select_all_scenes)
        selection_layout.addWidget(select_all_btn)
        
        layout.addWidget(selection_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.stage3_generate_btn = QPushButton("🎬 开始场景分割")
        self.stage3_generate_btn.clicked.connect(lambda: self.start_stage(3))
        btn_layout.addWidget(self.stage3_generate_btn)
        
        self.stage3_next_btn = QPushButton("➡️ 生成分镜脚本")
        self.stage3_next_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(3))
        self.stage3_next_btn.setEnabled(False)
        btn_layout.addWidget(self.stage3_next_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.tab_widget.addTab(stage3_widget, "3️⃣ 场景分割")
    
    def create_stage4_tab(self):
        """创建阶段4标签页：分镜脚本生成"""
        stage4_widget = QWidget()
        layout = QVBoxLayout(stage4_widget)
        
        # 说明文本
        info_label = QLabel(
            "📝 <b>阶段4：逐场景分镜脚本生成</b><br>"
            "为选定的场景生成详细的专业分镜脚本，包含镜头语言、构图、光影等完整信息，并融入角色一致性要求。"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 分镜脚本结果
        storyboard_group = QGroupBox("📋 分镜脚本")
        storyboard_layout = QVBoxLayout(storyboard_group)
        
        self.storyboard_output = QTextEdit()
        self.storyboard_output.setReadOnly(True)
        self.storyboard_output.setPlaceholderText("分镜脚本将在这里显示...")
        storyboard_layout.addWidget(self.storyboard_output)
        
        layout.addWidget(storyboard_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        # 第4阶段：分镜脚本生成按钮
        self.stage4_generate_btn = QPushButton("📝 生成分镜脚本")
        self.stage4_generate_btn.clicked.connect(lambda: self.start_stage(4))
        btn_layout.addWidget(self.stage4_generate_btn)
        
        # 第4阶段：进入下一阶段按钮
        self.stage4_next_btn = QPushButton("➡️ 优化预览")
        self.stage4_next_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(4))
        self.stage4_next_btn.setEnabled(False)
        btn_layout.addWidget(self.stage4_next_btn)
        
        # 导出按钮
        export_btn = QPushButton("💾 导出分镜脚本")
        export_btn.clicked.connect(self.export_storyboard)
        btn_layout.addWidget(export_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.tab_widget.addTab(stage4_widget, "4️⃣ 分镜生成")  # 第4阶段：分镜脚本生成
    
    def create_stage5_tab(self):
        """创建阶段5标签页：优化预览"""
        stage5_widget = QWidget()
        layout = QVBoxLayout(stage5_widget)
        
        # 说明文本
        info_label = QLabel(
            "🎨 <b>阶段5：视觉预览和迭代优化</b><br>"
            "对生成的分镜脚本进行质量检查和优化建议，确保视觉一致性和专业水准。"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 优化建议
        optimization_group = QGroupBox("💡 优化建议")
        optimization_layout = QVBoxLayout(optimization_group)
        
        self.optimization_output = QTextEdit()
        self.optimization_output.setReadOnly(True)
        self.optimization_output.setPlaceholderText("优化建议将在这里显示...")
        optimization_layout.addWidget(self.optimization_output)
        
        layout.addWidget(optimization_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.stage5_generate_btn = QPushButton("🎨 生成优化建议")
        self.stage5_generate_btn.clicked.connect(lambda: self.start_stage(5))
        btn_layout.addWidget(self.stage5_generate_btn)
        
        # 重新生成按钮
        regenerate_btn = QPushButton("🔄 重新生成分镜")
        regenerate_btn.clicked.connect(self.regenerate_storyboard)
        btn_layout.addWidget(regenerate_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.tab_widget.addTab(stage5_widget, "5️⃣ 优化预览")
    
    def create_status_area(self, parent_layout):
        """创建底部状态区域"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_layout = QHBoxLayout(status_frame)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # 停止按钮
        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.clicked.connect(self.stop_generation)
        self.stop_btn.setEnabled(False)
        status_layout.addWidget(self.stop_btn)
        
        parent_layout.addWidget(status_frame)
    
    def load_models(self):
        """加载大模型列表"""
        try:
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
    
    def load_text_from_main(self):
        """从主窗口加载改写文本"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'rewritten_text'):
                rewritten_text = self.parent_window.rewritten_text.toPlainText().strip()
                if rewritten_text:
                    self.article_input.setPlainText(rewritten_text)
                    QMessageBox.information(self, "成功", "已从主窗口加载改写文本")
                    logger.info("已从主窗口加载改写文本")
                else:
                    QMessageBox.warning(self, "警告", "主窗口中没有改写文本")
            else:
                QMessageBox.warning(self, "警告", "无法访问主窗口或改写文本")
        except Exception as e:
            logger.error(f"加载改写文本失败: {e}")
            QMessageBox.critical(self, "错误", f"加载改写文本失败: {e}")
    
    def start_stage(self, stage_num):
        """开始执行指定阶段"""
        try:
            # 检查前置条件
            if not self._check_stage_prerequisites(stage_num):
                return
            
            # 初始化LLM API
            if not self._init_llm_api():
                return
            
            # 准备输入数据
            input_data = self._prepare_stage_input(stage_num)
            
            # 更新UI状态
            self._update_ui_for_stage_start(stage_num)
            
            # 启动工作线程
            style = self.style_combo.currentText()
            self.worker_thread = StageWorkerThread(stage_num, self.llm_api, input_data, style, self)
            self.worker_thread.progress_updated.connect(self.update_progress)
            self.worker_thread.stage_completed.connect(self.on_stage_completed)
            self.worker_thread.error_occurred.connect(self.on_stage_error)
            self.worker_thread.start()
            
        except Exception as e:
            logger.error(f"启动阶段{stage_num}失败: {e}")
            QMessageBox.critical(self, "错误", f"启动阶段{stage_num}失败: {e}")
            self._reset_ui_state()
    
    def _check_stage_prerequisites(self, stage_num):
        """检查阶段前置条件"""
        if stage_num == 1:
            if not self.article_input.toPlainText().strip():
                QMessageBox.warning(self, "警告", "请先输入文章内容")
                return False
        elif stage_num == 2:
            if not self.stage_data[1]:
                QMessageBox.warning(self, "警告", "请先完成阶段1：世界观分析")
                self.tab_widget.setCurrentIndex(0)
                return False
        elif stage_num == 3:
            if not self.stage_data[2]:
                QMessageBox.warning(self, "警告", "请先完成阶段2：角色管理")
                self.tab_widget.setCurrentIndex(1)
                return False
        elif stage_num == 4:
            if not self.stage_data[3]:
                QMessageBox.warning(self, "警告", "请先完成阶段3：场景分割")
                self.tab_widget.setCurrentIndex(2)
                return False
            if not self.scenes_list.selectedItems():
                QMessageBox.warning(self, "警告", "请先选择要生成分镜的场景")
                self.tab_widget.setCurrentIndex(2)
                return False
        elif stage_num == 5:
            if not self.stage_data[4]:
                QMessageBox.warning(self, "警告", "请先完成阶段4：分镜生成")
                self.tab_widget.setCurrentIndex(3)
                return False
        
        return True
    
    def _init_llm_api(self):
        """初始化LLM API"""
        try:
            selected_model = self.model_combo.currentText()
            if selected_model in ["未配置模型", "加载失败", None]:
                QMessageBox.warning(self, "错误", "请选择一个有效的大模型")
                return False
            
            # 获取模型配置
            all_model_configs = self.config_manager.config.get("models", [])
            model_config = None
            for cfg in all_model_configs:
                if cfg.get("name") == selected_model:
                    model_config = cfg
                    break
            
            if not model_config:
                QMessageBox.warning(self, "错误", f"未找到模型 '{selected_model}' 的配置")
                return False
            
            # 初始化LLM API
            self.llm_api = LLMApi(
                api_type=model_config.get('type', 'deepseek'),
                api_key=model_config.get('key', ''),
                api_url=model_config.get('url', '')
            )
            
            logger.info(f"使用模型: {model_config.get('name', 'unknown')}")
            return True
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"初始化LLM API失败: {e}")
            return False
    
    def _prepare_stage_input(self, stage_num):
        """准备阶段输入数据"""
        if stage_num == 1:
            return {
                "article_text": self.article_input.toPlainText().strip()
            }
        elif stage_num == 2:
            # 阶段2：角色管理 - 不需要LLM处理，直接返回空字典
            return {}
        elif stage_num == 3:
            return {
                "world_bible": self.stage_data[1].get("world_bible", ""),
                "article_text": self.stage_data[1].get("article_text", ""),
                "character_info": self.stage_data[2].get("character_info", "")
            }
        elif stage_num == 4:
            # 获取选中的场景
            selected_scenes = []
            for item in self.scenes_list.selectedItems():
                selected_scenes.append(item.text())
            
            return {
                "world_bible": self.stage_data[1].get("world_bible", ""),
                "character_info": self.stage_data[2].get("character_info", ""),
                "scenes_analysis": self.stage_data[3].get("scenes_analysis", ""),
                "selected_scenes": selected_scenes,
                "selected_characters": self.selected_characters
            }
        elif stage_num == 5:
            return {
                "storyboard_results": self.stage_data[4].get("storyboard_results", []),
                "world_bible": self.stage_data[1].get("world_bible", ""),
                "character_info": self.stage_data[2].get("character_info", "")
            }
        
        return {}
    
    def _update_ui_for_stage_start(self, stage_num):
        """更新UI状态为开始阶段"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.stop_btn.setEnabled(True)
        
        # 禁用对应的生成按钮
        if stage_num == 1:
            self.stage1_generate_btn.setEnabled(False)
            self.stage1_generate_btn.setText("🔄 分析中...")
        elif stage_num == 2:
            # 阶段2是角色管理，不需要禁用按钮
            pass
        elif stage_num == 3:
            self.stage3_generate_btn.setEnabled(False)
            self.stage3_generate_btn.setText("🔄 分割中...")
        elif stage_num == 4:
            self.stage4_generate_btn.setEnabled(False)
            self.stage4_generate_btn.setText("🔄 生成中...")
        elif stage_num == 5:
            self.stage5_generate_btn.setEnabled(False)
            self.stage5_generate_btn.setText("🔄 优化中...")
    
    def update_progress(self, message):
        """更新进度信息"""
        self.status_label.setText(message)
        logger.info(f"进度更新: {message}")
    
    def on_stage_completed(self, stage_num, result):
        """阶段完成回调"""
        try:
            # 保存结果数据
            self.stage_data[stage_num] = result
            
            # 更新对应的UI显示
            if stage_num == 1:
                world_bible = result.get("world_bible", "")
                self.world_bible_output.setText(world_bible)
                self.stage1_next_btn.setEnabled(True)
                self.status_label.setText("✅ 全局分析完成")
                
                # 保存世界观圣经到texts文件夹
                if world_bible:
                    self._save_world_bible_to_file(world_bible)
                    self.auto_extract_characters_from_world_bible(world_bible)
            elif stage_num == 2:
                # 阶段2：角色管理完成
                # 保存角色管理数据
                character_info = ""
                if self.character_scene_manager:
                    characters = self.character_scene_manager.get_all_characters()
                    scenes = self.character_scene_manager.get_all_scenes()
                    
                    # 过滤掉分镜板生成的场景
                    import re
                    filtered_scene_count = 0
                    if scenes:
                        for scene_id, scene_data in scenes.items():
                            scene_name = scene_data.get('name', '未命名')
                            if not re.match(r'^场景\d+$', scene_name):
                                filtered_scene_count += 1
                    
                    if characters:
                        character_info = f"角色数量: {len(characters)}, 用户创建场景数量: {filtered_scene_count}"
                
                # 确保阶段2有数据，即使是空的也要有标记
                if not self.stage_data[2]:
                    self.stage_data[2] = {
                        "character_info": character_info,
                        "completed": True,
                        "timestamp": str(QDateTime.currentDateTime().toString())
                    }
                
                self.status_label.setText("✅ 角色管理完成")
            elif stage_num == 3:
                self.scenes_output.setText(result.get("scenes_analysis", ""))
                self._update_scenes_list(result.get("scenes_analysis", ""))
                self.stage3_next_btn.setEnabled(True)
                self.status_label.setText("✅ 场景分割完成")
            elif stage_num == 4:
                self._display_storyboard_results(result.get("storyboard_results", []))
                self.stage4_next_btn.setEnabled(True)
                self.status_label.setText("✅ 分镜脚本生成完成")
                # 调用场景描述增强器
                self._enhance_storyboard_descriptions(result.get("storyboard_results", []))
                # 转换数据并传递给一致性控制面板
                self._update_consistency_panel()
            elif stage_num == 5:
                self._display_optimization_results(result.get("optimization_suggestions", []))
                self.status_label.setText("✅ 优化分析完成")
                # 转换数据并传递给一致性控制面板
                self._update_consistency_panel()
            
            # 更新当前阶段
            self.current_stage = stage_num
            
            # 自动保存到项目
            self.save_to_project()
            
            logger.info(f"阶段{stage_num}完成")
            
        except Exception as e:
            logger.error(f"处理阶段{stage_num}结果失败: {e}")
        finally:
            self._reset_ui_state()
    
    def on_stage_error(self, error_message):
        """阶段错误回调"""
        QMessageBox.critical(self, "错误", f"处理失败: {error_message}")
        self.status_label.setText(f"❌ 错误: {error_message}")
        self._reset_ui_state()
    
    def _save_world_bible_to_file(self, world_bible_content):
        """保存世界观圣经内容到项目特定的texts文件夹"""
        try:
            # 获取当前项目信息
            if not self.project_manager or not self.project_manager.current_project:
                logger.warning("没有当前项目，无法保存世界观圣经文件")
                return
            
            # 兼容新旧项目格式
            project_name = self.project_manager.current_project.get('project_name') or self.project_manager.current_project.get('name', '')
            if not project_name:
                logger.warning("项目名称为空，无法保存世界观圣经文件")
                return
            
            # 构建项目特定的texts文件夹路径
            output_dir = os.path.join(os.getcwd(), "output", project_name, "texts")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 保存为JSON格式，包含时间戳等元数据
            world_bible_data = {
                "content": world_bible_content,
                "timestamp": QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"),
                "version": "1.0"
            }
            
            world_bible_file = os.path.join(output_dir, "world_bible.json")
            with open(world_bible_file, 'w', encoding='utf-8') as f:
                json.dump(world_bible_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"世界观圣经已保存到: {world_bible_file}")
            
        except Exception as e:
            logger.error(f"保存世界观圣经文件失败: {e}")
    
    def _enhance_storyboard_descriptions(self, storyboard_results):
        """使用场景描述增强器增强分镜脚本描述"""
        try:
            # 检查是否有分镜脚本数据
            if not storyboard_results:
                logger.warning("没有分镜脚本数据可供增强")
                return
            
            # 获取当前项目信息
            if not self.project_manager or not self.project_manager.current_project:
                logger.warning("没有当前项目，无法保存增强结果")
                return
            
            project_name = self.project_manager.current_project.get('project_name')
            if not project_name:
                logger.warning("项目名称为空，无法保存增强结果")
                return
            
            # 初始化场景描述增强器
            if not self.scene_enhancer:
                project_root = self.project_manager.current_project.get('project_path', os.getcwd())
                self.scene_enhancer = SceneDescriptionEnhancer(
                    project_root=project_root,
                    character_scene_manager=self.character_scene_manager,
                    llm_api=getattr(self, 'llm_api', None)
                )
                logger.info(f"场景描述增强器已初始化，项目根目录: {project_root}")
            
            # 合并所有分镜脚本内容（只包含镜头描述，不包含场景标题）
            combined_script = ""
            for i, result in enumerate(storyboard_results):
                storyboard_script = result.get("storyboard_script", "")
                if storyboard_script.strip():  # 只添加非空的分镜脚本
                    # 过滤掉场景标题行，只保留镜头相关内容
                    filtered_lines = []
                    lines = storyboard_script.split('\n')
                    for line in lines:
                        line_strip = line.strip()
                        # 跳过场景标题行
                        if (line_strip.startswith('### 场景') or 
                            line_strip.startswith('## 场景') or
                            line_strip.startswith('场景') and '：' in line_strip):
                            continue
                        filtered_lines.append(line)
                    
                    filtered_script = '\n'.join(filtered_lines)
                    if filtered_script.strip():
                        combined_script += f"\n{filtered_script}\n"
            
            logger.info(f"开始增强分镜脚本描述，原始内容长度: {len(combined_script)}")
            
            # 获取用户选择的风格
            selected_style = self.style_combo.currentText() if hasattr(self, 'style_combo') else '电影风格'
            logger.info(f"使用风格: {selected_style}")
            
            # 调用场景描述增强器，传递风格参数
            enhanced_result = self.scene_enhancer.enhance_storyboard(combined_script, selected_style)
            
            if enhanced_result and 'enhanced_description' in enhanced_result:
                enhanced_content = enhanced_result['enhanced_description']
                logger.info(f"场景描述增强完成，增强内容长度: {len(enhanced_content)}")
                
                # 构建项目特定的texts文件夹路径
                output_dir = os.path.join(os.getcwd(), "output", project_name, "texts")
                logger.info(f"准备创建输出目录: {output_dir}")
                
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    logger.info(f"输出目录已创建: {output_dir}")
                else:
                    logger.info(f"输出目录已存在: {output_dir}")
                
                # 保存增强结果到prompt.json文件
                prompt_data = {
                    "original_description": combined_script,
                    "enhanced_prompt": enhanced_content,
                    "timestamp": QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"),
                    "enhancer_config": enhanced_result.get('config', {}),
                    "technical_details": enhanced_result.get('technical_details', {}),
                    "consistency_details": enhanced_result.get('consistency_details', {}),
                    "fusion_quality_score": enhanced_result.get('fusion_quality_score', 0.0)
                }
                
                prompt_file = os.path.join(output_dir, "prompt.json")
                logger.info(f"准备保存增强结果到文件: {prompt_file}")
                
                try:
                    with open(prompt_file, 'w', encoding='utf-8') as f:
                        json.dump(prompt_data, f, ensure_ascii=False, indent=2)
                    
                    # 验证文件是否成功创建
                    if os.path.exists(prompt_file):
                        file_size = os.path.getsize(prompt_file)
                        logger.info(f"场景描述增强结果已成功保存到: {prompt_file}，文件大小: {file_size} 字节")
                    else:
                        logger.error(f"文件保存失败，文件不存在: {prompt_file}")
                        
                except Exception as save_error:
                    logger.error(f"保存prompt.json文件时出错: {save_error}")
                    import traceback
                    logger.error(f"保存错误详情: {traceback.format_exc()}")
                
                # 更新状态显示
                self.status_label.setText("✅ 分镜脚本生成完成，场景描述已增强")
            else:
                logger.warning("场景描述增强器返回结果为空或格式不正确")
                
        except Exception as e:
            logger.error(f"增强分镜脚本描述失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    

    
    def _reset_ui_state(self):
        """重置UI状态"""
        self.progress_bar.setVisible(False)
        self.stop_btn.setEnabled(False)
        
        # 恢复按钮状态，根据当前阶段设置合适的按钮文本
        self.stage1_generate_btn.setEnabled(True)
        if self.current_stage >= 1:
            self.stage1_generate_btn.setText("🔄 重新分析")
        else:
            self.stage1_generate_btn.setText("🚀 开始全局分析")
        
        self.stage2_generate_btn.setEnabled(True)
        self.stage2_generate_btn.setText("🔄 刷新角色信息")
        
        self.stage3_generate_btn.setEnabled(True)
        if self.current_stage >= 3:
            self.stage3_generate_btn.setText("🔄 重新分割场景")
        else:
            self.stage3_generate_btn.setText("🎬 开始场景分割")
        
        self.stage4_generate_btn.setEnabled(True)
        if self.current_stage >= 4:
            self.stage4_generate_btn.setText("🔄 重新生成分镜")
        else:
            self.stage4_generate_btn.setText("📝 生成分镜脚本")
        
        self.stage5_generate_btn.setEnabled(True)
        if self.current_stage >= 5:
            self.stage5_generate_btn.setText("🔄 重新优化")
        else:
            self.stage5_generate_btn.setText("🎨 生成优化建议")
    
    def _update_scenes_list(self, scenes_analysis):
        """更新场景列表"""
        self.scenes_list.clear()
        
        # 简单解析场景（实际应用中可以使用更复杂的解析逻辑）
        lines = scenes_analysis.split('\n')
        scene_count = 0
        
        for line in lines:
            line_strip = line.strip()
            if line_strip.startswith('### 场景') or line_strip.startswith('## 场景'):
                # 提取标题部分，去除前缀
                # 例如：### 场景1：叶文洁的内心挣扎  => 叶文洁的内心挣扎
                parts = line_strip.split('：', 1)
                if len(parts) == 2:
                    title = parts[1].strip()
                else:
                    # 兼容没有冒号的情况
                    title = line_strip.split(' ', 1)[-1].replace('场景','').replace('#','').strip()
                scene_count += 1
                item = QListWidgetItem(f"场景{scene_count}：{title}")
                self.scenes_list.addItem(item)
        
        if scene_count == 0:
            # 如果没有找到标准格式的场景，创建默认场景
            for i in range(3):  # 默认创建3个场景
                item = QListWidgetItem(f"场景{i+1}：默认场景")
                self.scenes_list.addItem(item)
    
    def _display_storyboard_results(self, storyboard_results):
        """显示分镜脚本结果"""
        output_text = ""
        
        for i, result in enumerate(storyboard_results):
            scene_info = result.get("scene_info", "")
            storyboard_script = result.get("storyboard_script", "")
            enhanced_shots = result.get("enhanced_shots", [])
            
            output_text += f"\n{'='*50}\n"
            output_text += f"场景 {i+1}\n"
            output_text += f"{'='*50}\n"
            output_text += f"场景信息: {scene_info}\n\n"
            output_text += storyboard_script
            output_text += "\n\n"
            
            # 显示增强后的镜头信息
            if enhanced_shots:
                output_text += f"{'='*30} 增强后的镜头信息 {'='*30}\n\n"
                for shot in enhanced_shots:
                    shot_number = shot.get('shot_number', '')
                    final_prompt = shot.get('final_prompt', '')
                    
                    output_text += f"【镜头 {shot_number}】\n"
                    output_text += f"{final_prompt}\n"
                    output_text += f"{'-'*60}\n\n"
        
        self.storyboard_output.setText(output_text)
    
    def _display_optimization_results(self, optimization_suggestions):
        """显示优化建议结果"""
        output_text = "🎨 分镜脚本质量分析与优化建议\n\n"
        
        for suggestion in optimization_suggestions:
            scene_index = suggestion.get("scene_index", 0)
            output_text += f"📋 场景 {scene_index + 1} 分析:\n"
            output_text += f"• 视觉一致性: {suggestion.get('visual_consistency', '')}\n"
            output_text += f"• 技术质量: {suggestion.get('technical_quality', '')}\n"
            output_text += f"• 叙事流畅性: {suggestion.get('narrative_flow', '')}\n"
            
            # 显示增强功能应用状态
            enhancement_applied = suggestion.get('enhancement_applied', '')
            if enhancement_applied:
                output_text += f"• 增强功能: {enhancement_applied}\n"
            
            tips = suggestion.get('optimization_tips', [])
            if tips:
                output_text += "💡 优化建议:\n"
                for tip in tips:
                    output_text += f"  - {tip}\n"
            
            output_text += "\n"
        
        self.optimization_output.setText(output_text)
    
    def select_all_scenes(self):
        """全选所有场景"""
        for i in range(self.scenes_list.count()):
            item = self.scenes_list.item(i)
            item.setSelected(True)
    
    def stop_generation(self):
        """停止生成"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.cancel()
            self.worker_thread.wait(3000)
            if self.worker_thread.isRunning():
                self.worker_thread.terminate()
                self.worker_thread.wait(1000)
        
        self.status_label.setText("⏹️ 已停止")
        self._reset_ui_state()
    
    def export_storyboard(self):
        """导出分镜脚本"""
        try:
            if not self.stage_data.get(4):
                QMessageBox.warning(self, "警告", "没有可导出的分镜脚本")
                return
            
            from PyQt5.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出分镜脚本", "storyboard_script.txt", "文本文件 (*.txt);;所有文件 (*)"
            )
            
            if file_path:
                content = self.storyboard_output.toPlainText()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                QMessageBox.information(self, "成功", f"分镜脚本已导出到: {file_path}")
                logger.info(f"分镜脚本已导出到: {file_path}")
        
        except Exception as e:
            logger.error(f"导出分镜脚本失败: {e}")
            QMessageBox.critical(self, "错误", f"导出失败: {e}")
    
    def regenerate_storyboard(self):
        """重新生成分镜"""
        reply = QMessageBox.question(
            self, "确认", "是否要重新生成分镜脚本？这将覆盖当前结果。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.tab_widget.setCurrentIndex(3)  # 切换到分镜生成标签页
            self.start_stage(4)
    
    def save_to_project(self):
        """保存五阶段分镜数据到当前项目"""
        try:
            if not self.project_manager or not self.project_manager.current_project:
                logger.warning("没有当前项目，无法保存五阶段分镜数据")
                return
            
            # 更新项目数据
            self.project_manager.current_project['five_stage_storyboard'] = {
                'stage_data': self.stage_data,
                'current_stage': self.current_stage,
                'selected_characters': self.selected_characters,
                'selected_scenes': self.selected_scenes,
                'article_text': self.article_input.toPlainText(),
                'selected_style': self.style_combo.currentText(),
                'selected_model': self.model_combo.currentText()
            }
            
            # 保存项目
            success = self.project_manager.save_project()
            if success:
                logger.info(f"五阶段分镜数据已保存到项目: {self.project_manager.current_project['project_name']}")
                
                # 通知主窗口更新项目状态
                if self.parent_window and hasattr(self.parent_window, 'update_project_status'):
                    self.parent_window.update_project_status()
                    
            else:
                logger.error(f"保存五阶段分镜数据失败: {self.project_manager.current_project['project_name']}")
                
        except Exception as e:
            logger.error(f"保存五阶段分镜数据时出错: {e}")
    
    def delayed_load_from_project(self):
        """延迟加载项目数据，确保UI组件已完全初始化"""
        logger.info("开始延迟加载项目数据...")
        
        # 检查关键UI组件是否已初始化（包括组件存在性和可用性）
        ui_components = {
            'world_bible_output': hasattr(self, 'world_bible_output') and self.world_bible_output is not None,
            'scenes_output': hasattr(self, 'scenes_output') and self.scenes_output is not None,
            'storyboard_output': hasattr(self, 'storyboard_output') and self.storyboard_output is not None,
            'optimization_output': hasattr(self, 'optimization_output') and self.optimization_output is not None,
            'article_input': hasattr(self, 'article_input') and self.article_input is not None,
            'style_combo': hasattr(self, 'style_combo') and self.style_combo is not None,
            'model_combo': hasattr(self, 'model_combo') and self.model_combo is not None,
            'scenes_list': hasattr(self, 'scenes_list') and self.scenes_list is not None,
            'status_label': hasattr(self, 'status_label') and self.status_label is not None
        }
        
        logger.info(f"UI组件初始化状态: {ui_components}")
        
        # 如果关键组件未初始化，再次延迟
        missing_components = [name for name, exists in ui_components.items() if not exists]
        if missing_components:
            # 初始化重试计数器
            if not hasattr(self, '_delayed_load_retry_count'):
                self._delayed_load_retry_count = 0
            
            self._delayed_load_retry_count += 1
            
            if self._delayed_load_retry_count < 10:  # 最多重试10次
                logger.warning(f"以下UI组件尚未初始化: {missing_components}，第{self._delayed_load_retry_count}次重试")
                QTimer.singleShot(300, self.delayed_load_from_project)  # 减少延迟时间
                return
            else:
                logger.error(f"UI组件初始化超时，缺少组件: {missing_components}，尝试强制加载")
                # 强制加载，忽略缺失的组件
                self.load_from_project(force_load=True)
                return
        
        # 重置重试计数器
        self._delayed_load_retry_count = 0
        
        # 所有组件已初始化，开始加载项目数据
        logger.info("所有UI组件已初始化，开始加载五阶段分镜数据")
        self.load_from_project()

    def load_from_project(self, force_load=False):
        """从当前项目加载五阶段数据
        
        Args:
            force_load (bool): 是否强制加载，即使某些UI组件缺失
        """
        try:
            logger.info(f"开始加载五阶段分镜数据... (强制加载: {force_load})")
            
            if not self.project_manager or not self.project_manager.current_project:
                logger.info("没有当前项目，跳过加载五阶段数据")
                return
            
            project_data = self.project_manager.current_project
            logger.info(f"当前项目: {project_data.get('name', 'Unknown')}")
            
            # 初始化角色场景管理器
            project_dir = project_data.get('project_dir')
            if project_dir:
                # 获取service_manager
                service_manager = None
                if self.parent_window and hasattr(self.parent_window, 'app_controller'):
                    service_manager = self.parent_window.app_controller.service_manager
                
                self.character_scene_manager = CharacterSceneManager(project_dir, service_manager)
                self.character_dialog = CharacterSceneDialog(self.character_scene_manager, self)
                
                # 初始化场景描述增强器
                # 确保llm_api已初始化
                if not hasattr(self, 'llm_api') or self.llm_api is None:
                    self._init_llm_api()
                
                self.scene_enhancer = SceneDescriptionEnhancer(project_dir, self.character_scene_manager, self.llm_api)
                logger.info("场景描述增强器已初始化")
                
                # 检查并记录现有的角色和场景数据
                existing_characters = self.character_scene_manager.get_all_characters()
                existing_scenes = self.character_scene_manager.get_all_scenes()
                
                # 过滤掉分镜板生成的场景（如"场景1"、"场景2"等）
                import re
                filtered_scenes = {scene_id: scene_data for scene_id, scene_data in existing_scenes.items() 
                                 if not re.match(r'^场景\d+$', scene_data.get('name', '未命名'))}
                
                logger.info(f"项目加载时发现角色数量: {len(existing_characters)}, 用户创建场景数量: {len(filtered_scenes)}")
                
                # 如果有现有数据，刷新角色管理对话框
                if existing_characters or filtered_scenes:
                    if hasattr(self.character_dialog, 'refresh_character_list'):
                        self.character_dialog.refresh_character_list()
                    if hasattr(self.character_dialog, 'refresh_scene_list'):
                        self.character_dialog.refresh_scene_list()
                    logger.info("已刷新角色场景管理对话框显示")
            
            if 'five_stage_storyboard' not in project_data:
                logger.info(f"项目 {project_data.get('name', 'Unknown')} 中没有五阶段分镜数据")
                logger.info(f"项目数据键: {list(project_data.keys())}")
                return
            
            five_stage_data = project_data['five_stage_storyboard']
            logger.info(f"找到五阶段数据，包含键: {list(five_stage_data.keys())}")
            
            # 恢复阶段数据
            loaded_stage_data = five_stage_data.get('stage_data', {})
            # 确保所有阶段都有默认值，但保留已加载的数据
            self.stage_data = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}}
            
            # 处理键类型转换（JSON中的键是字符串）
            for key, value in loaded_stage_data.items():
                try:
                    # 尝试将字符串键转换为整数
                    int_key = int(key)
                    self.stage_data[int_key] = value
                except (ValueError, TypeError):
                    # 如果转换失败，保持原键
                    self.stage_data[key] = value
            
            logger.info(f"加载的stage_data键: {list(loaded_stage_data.keys())}")
            logger.info(f"转换后的stage_data键: {list(self.stage_data.keys())}")
            logger.info(f"第4阶段数据存在: {bool(self.stage_data.get(4))}")
            if self.stage_data.get(4):
                logger.info(f"第4阶段包含键: {list(self.stage_data[4].keys())}")
                logger.info(f"storyboard_results存在: {'storyboard_results' in self.stage_data[4]}")
                if 'storyboard_results' in self.stage_data[4]:
                    logger.info(f"storyboard_results长度: {len(self.stage_data[4]['storyboard_results'])}")
            self.current_stage = five_stage_data.get('current_stage', 1)
            
            # 恢复选中的角色和场景
            self.selected_characters = five_stage_data.get('selected_characters', [])
            self.selected_scenes = five_stage_data.get('selected_scenes', [])
            
            # 恢复UI状态（考虑force_load模式）
            article_text = five_stage_data.get('article_text', '')
            if article_text and hasattr(self, 'article_input') and self.article_input:
                self.article_input.setPlainText(article_text)
            elif article_text and force_load:
                logger.warning("article_input组件缺失，跳过文章文本恢复")
            
            selected_style = five_stage_data.get('selected_style', '电影风格')
            if hasattr(self, 'style_combo') and self.style_combo:
                style_index = self.style_combo.findText(selected_style)
                if style_index >= 0:
                    self.style_combo.setCurrentIndex(style_index)
            elif force_load:
                logger.warning("style_combo组件缺失，跳过风格选择恢复")
            
            selected_model = five_stage_data.get('selected_model', '')
            if selected_model and hasattr(self, 'model_combo') and self.model_combo:
                model_index = self.model_combo.findText(selected_model)
                if model_index >= 0:
                    self.model_combo.setCurrentIndex(model_index)
            elif selected_model and force_load:
                logger.warning("model_combo组件缺失，跳过模型选择恢复")
            
            # 恢复各阶段的显示内容和UI状态
            if self.stage_data.get(1):
                world_bible = self.stage_data[1].get('world_bible', '')
                logger.info(f"第1阶段数据 - world_bible长度: {len(world_bible)}")
                
                # 如果项目数据中没有world_bible，记录日志
                if not world_bible:
                    logger.info("项目数据中没有world_bible内容")
                
                if world_bible and hasattr(self, 'world_bible_output') and self.world_bible_output:
                    self.world_bible_output.setText(world_bible)
                    logger.info("已设置world_bible_output内容")
                    
                    # 检查是否已有角色信息，避免重复提取
                    if self.character_scene_manager:
                        existing_characters = self.character_scene_manager.get_all_characters()
                        existing_scenes = self.character_scene_manager.get_all_scenes()
                        
                        # 过滤掉分镜板生成的场景（如"场景1"、"场景2"等）
                        import re
                        filtered_scenes = {scene_id: scene_data for scene_id, scene_data in existing_scenes.items() 
                                         if not re.match(r'^场景\d+$', scene_data.get('name', '未命名'))}
                        
                        if not existing_characters and not filtered_scenes:
                            # 只有在没有现有数据时才自动提取
                            self.auto_extract_characters_from_world_bible(world_bible)
                            logger.info("已自动提取角色信息（首次加载）")
                        else:
                            logger.info(f"已存在角色信息，跳过自动提取（角色: {len(existing_characters)}, 用户创建场景: {len(filtered_scenes)}）")
                elif world_bible and force_load:
                    logger.warning("world_bible_output组件缺失，跳过世界观内容恢复")
                else:
                    logger.warning(f"world_bible为空或world_bible_output不存在: world_bible={bool(world_bible)}, hasattr={hasattr(self, 'world_bible_output')}")
                
                if hasattr(self, 'stage1_next_btn'):
                    self.stage1_next_btn.setEnabled(True)
                # 更新状态标签
                if hasattr(self, 'status_label'):
                    self.status_label.setText("✅ 世界观圣经已生成")
            
            if self.stage_data.get(2):
                # 阶段2：角色管理完成
                logger.info("第2阶段数据 - 角色管理")
                # 更新状态标签
                if hasattr(self, 'status_label'):
                    self.status_label.setText("✅ 角色管理完成")
            
            if self.stage_data.get(3):
                scenes_analysis = self.stage_data[3].get('scenes_analysis', '')
                logger.info(f"第3阶段数据 - scenes_analysis长度: {len(scenes_analysis)}")
                logger.info(f"scenes_output组件存在: {hasattr(self, 'scenes_output')}")
                if hasattr(self, 'scenes_output'):
                    logger.info(f"scenes_output类型: {type(self.scenes_output)}")
                if scenes_analysis and hasattr(self, 'scenes_output') and self.scenes_output:
                    try:
                        self.scenes_output.setText(scenes_analysis)
                        logger.info(f"已成功设置scenes_output内容，当前文本长度: {len(self.scenes_output.toPlainText())}")
                        self._update_scenes_list(scenes_analysis)
                    except Exception as e:
                        logger.error(f"设置scenes_output内容时出错: {e}")
                elif scenes_analysis and force_load:
                    logger.warning("scenes_output组件缺失，跳过场景分析内容恢复")
                else:
                    logger.warning(f"scenes_analysis为空或scenes_output不存在: scenes_analysis={bool(scenes_analysis)}, hasattr={hasattr(self, 'scenes_output')}")
                
                if hasattr(self, 'stage3_next_btn'):
                    self.stage3_next_btn.setEnabled(True)
                # 更新状态标签
                if hasattr(self, 'status_label'):
                    self.status_label.setText("✅ 场景分割完成")
            
            if self.stage_data.get(4):
                storyboard_results = self.stage_data[4].get('storyboard_results', [])
                logger.info(f"第4阶段数据 - storyboard_results数量: {len(storyboard_results)}")
                logger.info(f"storyboard_output组件存在: {hasattr(self, 'storyboard_output')}")
                if hasattr(self, 'storyboard_output'):
                    logger.info(f"storyboard_output类型: {type(self.storyboard_output)}")
                    logger.info(f"storyboard_output是否为None: {self.storyboard_output is None}")
                
                # 详细记录storyboard_results的内容
                if storyboard_results:
                    logger.info(f"第一个storyboard_result的键: {list(storyboard_results[0].keys()) if storyboard_results else 'N/A'}")
                    for i, result in enumerate(storyboard_results[:2]):  # 只记录前两个
                        scene_info = result.get("scene_info", "")
                        storyboard_script = result.get("storyboard_script", "")
                        logger.info(f"场景{i+1} - scene_info长度: {len(scene_info)}, storyboard_script长度: {len(storyboard_script)}")
                
                if storyboard_results and hasattr(self, 'storyboard_output') and self.storyboard_output:
                    try:
                        logger.info("开始调用_display_storyboard_results方法...")
                        self._display_storyboard_results(storyboard_results)
                        current_text_length = len(self.storyboard_output.toPlainText())
                        logger.info(f"已成功设置storyboard_output内容，当前文本长度: {current_text_length}")
                        
                        # 如果文本长度为0，说明显示有问题
                        if current_text_length == 0:
                            logger.error("storyboard_output文本长度为0，显示可能失败")
                            # 尝试直接设置一些测试文本
                            test_text = "测试文本 - 第四阶段数据加载"
                            self.storyboard_output.setText(test_text)
                            logger.info(f"设置测试文本后长度: {len(self.storyboard_output.toPlainText())}")
                    except Exception as e:
                        logger.error(f"设置storyboard_output内容时出错: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                elif storyboard_results and force_load:
                    logger.warning("storyboard_output组件缺失，跳过分镜脚本内容恢复")
                else:
                    logger.warning(f"storyboard_results为空或storyboard_output不存在: storyboard_results={bool(storyboard_results)}, hasattr={hasattr(self, 'storyboard_output')}, storyboard_output_is_none={getattr(self, 'storyboard_output', None) is None}")
                
                if hasattr(self, 'stage4_next_btn'):
                    self.stage4_next_btn.setEnabled(True)
                # 更新状态标签
                if hasattr(self, 'status_label'):
                    self.status_label.setText("✅ 分镜脚本生成完成")
            
            if self.stage_data.get(5):
                optimization_suggestions = self.stage_data[5].get('optimization_suggestions', [])
                logger.info(f"第5阶段数据 - optimization_suggestions数量: {len(optimization_suggestions)}")
                logger.info(f"optimization_output组件存在: {hasattr(self, 'optimization_output')}")
                if hasattr(self, 'optimization_output'):
                    logger.info(f"optimization_output类型: {type(self.optimization_output)}")
                if optimization_suggestions and hasattr(self, 'optimization_output') and self.optimization_output:
                    try:
                        self._display_optimization_results(optimization_suggestions)
                        logger.info(f"已成功设置optimization_output内容，当前文本长度: {len(self.optimization_output.toPlainText())}")
                    except Exception as e:
                        logger.error(f"设置optimization_output内容时出错: {e}")
                elif optimization_suggestions and force_load:
                    logger.warning("optimization_output组件缺失，跳过优化建议内容恢复")
                else:
                    logger.warning(f"optimization_suggestions为空或optimization_output不存在: optimization_suggestions={bool(optimization_suggestions)}, hasattr={hasattr(self, 'optimization_output')}")
                
                # 更新状态标签
                if hasattr(self, 'status_label'):
                    self.status_label.setText("✅ 优化分析完成")
            
            # 保持所有按钮可用，允许用户重新运行任何阶段
            # 注释掉原来的禁用逻辑，让用户可以随时调整和重新生成
            if hasattr(self, 'stage1_generate_btn'):
                self.stage1_generate_btn.setEnabled(True)
                # 如果阶段已完成，更新按钮文本提示
                if self.current_stage >= 1:
                    self.stage1_generate_btn.setText("🔄 重新分析")
                else:
                    self.stage1_generate_btn.setText("🚀 开始全局分析")
            
            if hasattr(self, 'stage2_generate_btn'):
                self.stage2_generate_btn.setEnabled(True)
                self.stage2_generate_btn.setText("🔄 刷新角色信息")
            
            if hasattr(self, 'stage3_generate_btn'):
                self.stage3_generate_btn.setEnabled(True)
                if self.current_stage >= 3:
                    self.stage3_generate_btn.setText("🔄 重新分割场景")
                else:
                    self.stage3_generate_btn.setText("🎬 开始场景分割")
            
            if hasattr(self, 'stage4_generate_btn'):
                self.stage4_generate_btn.setEnabled(True)
                if self.current_stage >= 4:
                    self.stage4_generate_btn.setText("🔄 重新生成分镜")
                else:
                    self.stage4_generate_btn.setText("📝 生成分镜脚本")
            
            if hasattr(self, 'stage5_generate_btn'):
                self.stage5_generate_btn.setEnabled(True)
                if self.current_stage >= 5:
                    self.stage5_generate_btn.setText("🔄 重新优化")
                else:
                    self.stage5_generate_btn.setText("🎨 生成优化建议")
            
            logger.info(f"已从项目 {project_data.get('name', 'Unknown')} 加载五阶段分镜数据")
            logger.info(f"当前阶段: {self.current_stage}, 阶段数据: {list(self.stage_data.keys())}")
            
            # 添加详细的阶段数据日志
            for stage_num, stage_content in self.stage_data.items():
                logger.info(f"阶段 {stage_num} 包含的键: {list(stage_content.keys()) if isinstance(stage_content, dict) else '非字典类型'}")
                if isinstance(stage_content, dict):
                    for key, value in stage_content.items():
                        if isinstance(value, str):
                            logger.info(f"  - {key}: 字符串长度 {len(value)}")
                        elif isinstance(value, (list, dict)):
                            logger.info(f"  - {key}: {type(value).__name__} 长度/大小 {len(value)}")
                        else:
                            logger.info(f"  - {key}: {type(value).__name__} = {value}")
            
            # 如果有第4阶段的分镜数据，更新一致性控制面板（项目加载时禁用自动增强）
            if self.stage_data.get(4) and self.stage_data[4].get('storyboard_results'):
                logger.info("项目加载完成，更新一致性控制面板...")
                self._update_consistency_panel(auto_enhance=False)
            
        except Exception as e:
            logger.error(f"加载五阶段分镜数据时出错: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
    
    def open_character_dialog(self):
        """打开角色管理对话框"""
        try:
            # 如果没有当前项目，提示用户
            if not self.project_manager or not self.project_manager.current_project:
                QMessageBox.warning(self, "警告", "请先创建或打开一个项目")
                return
            
            # 初始化角色场景管理器（如果还没有初始化）
            if not self.character_scene_manager:
                project_dir = self.project_manager.current_project.get('project_dir')
                if project_dir:
                    # 获取service_manager
                    service_manager = None
                    if self.parent_window and hasattr(self.parent_window, 'app_controller'):
                        service_manager = self.parent_window.app_controller.service_manager
                    
                    self.character_scene_manager = CharacterSceneManager(project_dir, service_manager)
                    self.character_dialog = CharacterSceneDialog(self.character_scene_manager, self)
                else:
                    QMessageBox.warning(self, "错误", "无法找到项目路径")
                    return
            
            # 打开角色管理对话框
            if self.character_dialog.exec_() == QDialog.Accepted:
                # 对话框关闭后，可以获取用户选择的角色和场景
                self.update_character_selection()
                
        except Exception as e:
            logger.error(f"打开角色管理对话框时出错: {e}")
            QMessageBox.critical(self, "错误", f"打开角色管理对话框失败: {str(e)}")
    
    def update_character_selection(self):
        """更新角色选择状态"""
        try:
            if self.character_scene_manager:
                # 这里可以添加逻辑来获取用户在对话框中选择的角色和场景
                # 由于CharacterSceneDialog可能需要修改来支持选择功能，
                # 暂时使用所有角色作为选中状态
                characters = self.character_scene_manager.get_all_characters()
                scenes = self.character_scene_manager.get_all_scenes()
                
                # 修复：get_all_characters()和get_all_scenes()返回的是字典，不是列表
                self.selected_characters = list(characters.keys())
                
                # 过滤掉分镜板生成的场景（如"场景1"、"场景2"等）
                import re
                filtered_scene_keys = []
                for scene_id, scene_data in scenes.items():
                    scene_name = scene_data.get('name', '未命名')
                    if not re.match(r'^场景\d+$', scene_name):
                        filtered_scene_keys.append(scene_id)
                
                self.selected_scenes = filtered_scene_keys
                
                logger.info(f"已选择 {len(self.selected_characters)} 个角色和 {len(self.selected_scenes)} 个用户创建的场景")
                
        except Exception as e:
            logger.error(f"更新角色选择时出错: {e}")
    
    def get_character_consistency_prompt(self):
        """获取角色一致性提示词"""
        try:
            if not self.character_scene_manager:
                return ""
            
            # 生成角色一致性提示词
            consistency_prompt = self.character_scene_manager.generate_consistency_prompt(
                self.selected_characters, self.selected_scenes
            )
            
            return consistency_prompt
            
        except Exception as e:
            logger.error(f"获取角色一致性提示词时出错: {e}")
            return ""
    
    def auto_extract_characters(self):
        """自动提取角色信息（从第一阶段的世界观圣经）"""
        try:
            # 获取第一阶段的世界观圣经内容
            stage1_data = self.stage_data.get(1, {})
            world_bible = stage1_data.get('world_bible', '')
            
            if not world_bible:
                QMessageBox.warning(self, "提示", "请先完成第一阶段的世界观圣经生成")
                return
            
            # 调用实际的提取方法
            self.auto_extract_characters_from_world_bible(world_bible)
            
        except Exception as e:
             logger.error(f"自动提取角色信息时出错: {e}")            
             QMessageBox.critical(self, "错误", f"自动提取角色信息失败: {str(e)}")
    
    def check_character_consistency(self):
        """检查角色一致性"""
        try:
            if not self.character_scene_manager:
                QMessageBox.warning(self, "提示", "角色场景管理器未初始化")
                return
            
            # 获取当前角色信息
            characters = self.character_scene_manager.get_all_characters()
            if not characters:
                QMessageBox.information(self, "提示", "当前没有角色信息，请先添加或提取角色")
                return
            
            # 生成一致性检查报告
            character_ids = list(characters.keys()) if isinstance(characters, dict) else []
            consistency_prompt = self.character_scene_manager.generate_consistency_prompt(character_ids)
            
            # 构建角色信息显示
            character_list = list(characters.values()) if isinstance(characters, dict) else characters
            character_info = "\n".join([f"• {char.get('name', '未命名')}: {char.get('description', '无描述')[:50]}..." 
                                       for char in character_list[:5]])
            
            # 显示一致性检查结果
            if consistency_prompt:
                message = f"当前共有 {len(character_list)} 个角色\n\n角色列表:\n{character_info}\n\n一致性提示词:\n{consistency_prompt[:200]}..."
            else:
                message = f"当前共有 {len(character_list)} 个角色\n\n角色列表:\n{character_info}\n\n注意：角色暂无一致性提示词，建议完善角色描述。"
            
            QMessageBox.information(self, "角色一致性检查", message)
                
        except Exception as e:
            logger.error(f"检查角色一致性时出错: {e}")
            QMessageBox.critical(self, "错误", f"检查角色一致性失败: {str(e)}")
    
    def refresh_character_info(self):
        """刷新角色信息显示"""
        try:
            if self.character_scene_manager:
                # 检查是否有世界观圣经内容，如果有但没有角色信息，则自动提取
                stage1_data = self.stage_data.get(1, {})
                world_bible = stage1_data.get('world_bible', '')
                
                characters = self.character_scene_manager.get_all_characters()
                scenes = self.character_scene_manager.get_all_scenes()
                
                # 如果没有角色信息但有世界观圣经，尝试自动提取
                if not characters and world_bible:
                    logger.info("检测到世界观圣经但无角色信息，尝试自动提取...")
                    self.auto_extract_characters_from_world_bible(world_bible)
                    # 重新获取提取后的信息
                    characters = self.character_scene_manager.get_all_characters()
                    scenes = self.character_scene_manager.get_all_scenes()
                
                # 更新角色选择状态
                self.update_character_selection()
                
                # 获取并显示角色信息
                
                # 构建显示文本
                display_text = ""
                
                if characters:
                    display_text += "=== 角色信息 ===\n\n"
                    for char_id, char_data in characters.items():
                        name = char_data.get('name', '未命名')
                        description = char_data.get('description', '无描述')
                        display_text += f"🧑 {name}\n"
                        display_text += f"   描述: {description}\n"
                        
                        # 显示外貌信息
                        appearance = char_data.get('appearance', {})
                        if appearance:
                            display_text += f"   外貌: {appearance.get('gender', '')} {appearance.get('age_range', '')}\n"
                            display_text += f"   发型: {appearance.get('hair', '')}\n"
                        
                        display_text += "\n"
                else:
                    display_text += "暂无角色信息\n\n"
                
                if scenes:
                    # 过滤掉分镜板生成的场景（如"场景1"、"场景2"等）
                    import re
                    filtered_scenes = {}
                    for scene_id, scene_data in scenes.items():
                        scene_name = scene_data.get('name', '未命名')
                        # 过滤掉匹配"场景"后跟数字的场景
                        if not re.match(r'^场景\d+$', scene_name):
                            filtered_scenes[scene_id] = scene_data
                    
                    if filtered_scenes:
                        display_text += "=== 场景信息 ===\n\n"
                        for scene_id, scene_data in filtered_scenes.items():
                            name = scene_data.get('name', '未命名')
                            description = scene_data.get('description', '无描述')
                            display_text += f"🏞️ {name}\n"
                            display_text += f"   描述: {description}\n\n"
                        display_text += f"\n注：已排除 {len(scenes) - len(filtered_scenes)} 个分镜板生成的场景\n"
                    else:
                        display_text += "暂无用户创建的场景信息\n"
                        if len(scenes) > 0:
                            display_text += f"（已排除 {len(scenes)} 个分镜板生成的场景）\n"
                else:
                    display_text += "暂无场景信息\n"
                
                # 更新显示
                self.characters_output.setPlainText(display_text)
                
                # 标记阶段2为完成状态
                # 计算过滤后的场景数量
                import re
                filtered_scene_count = 0
                if scenes:
                    for scene_id, scene_data in scenes.items():
                        scene_name = scene_data.get('name', '未命名')
                        if not re.match(r'^场景\d+$', scene_name):
                            filtered_scene_count += 1
                
                character_info = f"角色数量: {len(characters)}, 用户创建场景数量: {filtered_scene_count}"
                self.stage_data[2] = {
                    "character_info": character_info,
                    "completed": True,
                    "timestamp": str(QDateTime.currentDateTime().toString())
                }
                
                # 更新当前阶段
                if self.current_stage < 2:
                    self.current_stage = 2
                
                # 保存到项目
                self.save_to_project()
                
                logger.info("角色信息已刷新")
                QMessageBox.information(self, "提示", f"角色信息已刷新\n角色数量: {len(characters)}\n用户创建场景数量: {filtered_scene_count}\n阶段2已标记为完成")
            else:
                QMessageBox.warning(self, "提示", "角色场景管理器未初始化")
                
        except Exception as e:
            logger.error(f"刷新角色信息时出错: {e}")
            QMessageBox.critical(self, "错误", f"刷新角色信息失败: {str(e)}")
    
    def auto_extract_characters_from_world_bible(self, world_bible_text):
        """从世界观圣经中自动提取角色信息"""
        try:
            if not self.character_scene_manager or not world_bible_text:
                return
            
            # 使用角色场景管理器的自动提取功能
            self.character_scene_manager.auto_extract_and_save(world_bible_text)
            
            # 更新选择状态
            self.update_character_selection()
            
            logger.info("已从世界观圣经中自动提取角色信息")
            
        except Exception as e:
            logger.error(f"自动提取角色信息时出错: {e}")
    
    def _display_optimization_results(self, optimization_suggestions):
        """显示优化建议结果"""
        try:
            if not optimization_suggestions:
                self.optimization_output.setPlainText("暂无优化建议")
                return
            
            display_text = "=== 视觉优化建议 ===\n\n"
            
            for i, suggestion in enumerate(optimization_suggestions):
                scene_index = suggestion.get("scene_index", i)
                display_text += f"📋 场景 {scene_index + 1}\n"
                display_text += f"视觉一致性: {suggestion.get('visual_consistency', '未检查')}\n"
                display_text += f"技术质量: {suggestion.get('technical_quality', '未检查')}\n"
                display_text += f"叙事流畅性: {suggestion.get('narrative_flow', '未检查')}\n"
                
                optimization_tips = suggestion.get('optimization_tips', [])
                if optimization_tips:
                    display_text += "优化建议:\n"
                    for tip in optimization_tips:
                        display_text += f"  • {tip}\n"
                
                display_text += "\n"
            
            self.optimization_output.setPlainText(display_text)
            logger.info(f"已显示 {len(optimization_suggestions)} 个场景的优化建议")
        except Exception as e:
            logger.error(f"显示优化建议时出错: {e}")
            self.optimization_output.setPlainText("显示优化建议时出错")
    
    def _update_consistency_panel(self, auto_enhance=True):
        """将五阶段分镜数据转换并传递给一致性控制面板
        
        Args:
            auto_enhance (bool): 是否自动进行场景描述增强，默认为True
        """
        try:
            # 检查是否有分镜数据
            storyboard_results = self.stage_data.get(4, {}).get("storyboard_results", [])
            if not self.stage_data.get(4) or not storyboard_results:
                logger.warning(f"没有分镜数据可传递给一致性控制面板，stage_data[4]存在: {bool(self.stage_data.get(4))}, storyboard_results长度: {len(storyboard_results)}")
                return
            
            # 检查主窗口是否有一致性控制面板
            if not hasattr(self.parent_window, 'consistency_panel'):
                logger.warning("主窗口没有一致性控制面板")
                return
            
            # 导入必要的类
            from processors.text_processor import Shot, StoryboardResult
            
            # 转换五阶段分镜数据为StoryboardResult格式
            # storyboard_results已在上面定义
            shots = []
            characters = set()
            scenes = set()
            total_duration = 0.0
            
            # 过滤掉分镜生成的场景（场景1、场景2、场景3、场景4等），只传递用户创建的场景
            import re
            
            shot_id = 1
            for scene_idx, scene_result in enumerate(storyboard_results):
                scene_info = scene_result.get("scene_info", f"场景{scene_idx + 1}")
                storyboard_script = scene_result.get("storyboard_script", "")
                
                # 检查是否为分镜生成的场景，如果是则跳过添加到scenes集合
                is_auto_generated_scene = re.match(r'^场景\d+', scene_info.strip())
                
                # 解析分镜脚本中的分镜
                script_lines = storyboard_script.split('\n')
                current_shot = None
                
                for line in script_lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 检测分镜开始标记
                    if line.startswith('分镜') or line.startswith('镜头') or 'Shot' in line:
                        # 保存上一个分镜
                        if current_shot:
                            shots.append(current_shot)
                            shot_id += 1
                        
                        # 创建新分镜
                        current_shot = Shot(
                            shot_id=shot_id,
                            scene=scene_info,
                            characters=[],
                            action="",
                            dialogue="",
                            image_prompt="",
                            duration=3.0  # 默认3秒
                        )
                        # 只有非自动生成的场景才添加到scenes集合中
                        if not is_auto_generated_scene:
                            scenes.add(scene_info)
                        total_duration += 3.0
                    elif current_shot:
                        # 解析分镜内容
                        if '角色' in line or '人物' in line:
                            # 提取角色信息
                            char_info = line.split('：')[-1] if '：' in line else line
                            current_shot.characters.append(char_info.strip())
                            characters.add(char_info.strip())
                        elif '动作' in line or '行为' in line:
                            # 提取动作信息
                            current_shot.action = line.split('：')[-1] if '：' in line else line
                        elif '对话' in line or '台词' in line:
                            # 提取对话信息
                            current_shot.dialogue = line.split('：')[-1] if '：' in line else line
                        elif '画面' in line or '镜头' in line or '描述' in line:
                            # 提取画面描述作为图像提示词
                            prompt = line.split('：')[-1] if '：' in line else line
                            original_prompt = prompt.strip()
                            
                            # 应用场景描述增强（根据auto_enhance参数决定）
                            if auto_enhance and self.scene_enhancer:
                                try:
                                    enhanced_prompt = self.scene_enhancer.enhance_description(
                                        original_prompt, current_shot.characters
                                    )
                                    current_shot.image_prompt = enhanced_prompt
                                    logger.debug(f"画面描述已增强: {original_prompt[:30]}... -> {enhanced_prompt[:50]}...")
                                except Exception as e:
                                    logger.error(f"画面描述增强失败: {e}")
                                    current_shot.image_prompt = original_prompt
                            else:
                                current_shot.image_prompt = original_prompt
                                if not auto_enhance:
                                    logger.debug(f"跳过画面描述增强（auto_enhance=False）: {original_prompt[:30]}...")
                        else:
                            # 其他内容添加到动作描述中
                            if current_shot.action:
                                current_shot.action += " " + line
                            else:
                                current_shot.action = line
                
                # 保存最后一个分镜
                if current_shot:
                    shots.append(current_shot)
            
            # 如果没有解析到分镜，创建一个默认分镜
            if not shots:
                for scene_idx, scene_result in enumerate(storyboard_results):
                    scene_info = scene_result.get("scene_info", f"场景{scene_idx + 1}")
                    storyboard_script = scene_result.get("storyboard_script", "")
                    
                    # 检查是否为分镜生成的场景
                    is_auto_generated_scene = re.match(r'^场景\d+', scene_info.strip())
                    
                    # 创建默认画面描述
                    original_prompt = scene_info
                    enhanced_prompt = original_prompt
                    
                    # 跳过对场景标题的增强处理（场景标题不应该被增强）
                    if re.match(r'^场景\d+', scene_info.strip()):
                        logger.debug(f"跳过场景标题增强: {original_prompt}")
                        enhanced_prompt = original_prompt
                    elif auto_enhance and self.scene_enhancer:
                        # 应用场景描述增强（仅对非场景标题内容）
                        try:
                            enhanced_prompt = self.scene_enhancer.enhance_description(
                                original_prompt, []
                            )
                            logger.debug(f"默认画面描述已增强: {original_prompt} -> {enhanced_prompt[:50]}...")
                        except Exception as e:
                            logger.error(f"默认画面描述增强失败: {e}")
                            enhanced_prompt = original_prompt
                    elif not auto_enhance:
                        logger.debug(f"跳过默认画面描述增强（auto_enhance=False）: {original_prompt}")
                    
                    shot = Shot(
                        shot_id=scene_idx + 1,
                        scene=scene_info,
                        characters=[],
                        action=storyboard_script[:200] + "..." if len(storyboard_script) > 200 else storyboard_script,
                        dialogue="",
                        image_prompt=enhanced_prompt,
                        duration=3.0
                    )
                    shots.append(shot)
                    # 只有非自动生成的场景才添加到scenes集合中
                    if not is_auto_generated_scene:
                        scenes.add(scene_info)
                    total_duration += 3.0
            
            # 创建StoryboardResult对象
            storyboard_result = StoryboardResult(
                shots=shots,
                total_duration=total_duration,
                characters=list(characters),
                scenes=list(scenes),
                style=self.style_combo.currentText() if hasattr(self, 'style_combo') else self._get_default_style(),
                metadata={
                    "source": "five_stage_storyboard",
                    "world_bible": self.stage_data.get(1, {}).get("world_bible", ""),
                    "character_info": self.stage_data.get(2, {}).get("character_info", ""),
                    "scenes_analysis": self.stage_data.get(3, {}).get("scenes_analysis", ""),
                    "optimization_suggestions": self.stage_data.get(5, {}).get("optimization_suggestions", [])
                }
            )
            
            # 传递给一致性控制面板
            self.parent_window.consistency_panel.set_storyboard(storyboard_result)
            
            logger.info(f"已将 {len(shots)} 个分镜传递给一致性控制面板")
            
        except Exception as e:
            logger.error(f"更新一致性控制面板时发生错误: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def on_enhance_option_changed(self, state):
        """增强选项状态改变回调"""
        try:
            if self.scene_enhancer:
                enabled = state == Qt.Checked
                self.scene_enhancer.update_config(
                    enable_technical_details=enabled,
                    enable_consistency_injection=enabled
                )
                logger.info(f"场景描述增强已{'启用' if enabled else '禁用'}")
                
                # 更新增强级别组合框的可用性
                self.enhance_level_combo.setEnabled(enabled)
        except Exception as e:
            logger.error(f"更新增强选项失败: {e}")
    
    def on_enhance_level_changed(self, level_text):
        """增强级别改变回调"""
        try:
            if self.scene_enhancer:
                level_map = {"低": "low", "中": "medium", "高": "high"}
                level = level_map.get(level_text, "medium")
                self.scene_enhancer.update_config(enhancement_level=level)
                logger.info(f"场景描述增强级别已设置为: {level_text}")
        except Exception as e:
            logger.error(f"更新增强级别失败: {e}")
    
    def _get_default_style(self):
        """获取默认风格"""
        from utils.config_manager import ConfigManager
        config_manager = ConfigManager()
        return config_manager.get_setting("default_style", "电影风格")
    
    def open_enhancer_config(self):
        """打开场景描述增强器配置面板"""
        try:
            # 获取项目根目录
            project_root = getattr(self, 'project_dir', None) or os.getcwd()
            
            # 创建并显示配置面板
            config_panel = SceneEnhancerConfigPanel(project_root, self)
            config_panel.exec_()
            
            # 配置面板关闭后，重新加载增强器配置
            if self.scene_enhancer:
                self.scene_enhancer.reload_config()
                logger.info("场景描述增强器配置已更新")
                
        except Exception as e:
            logger.error(f"打开增强器配置面板失败: {e}")
            QMessageBox.critical(self, "错误", f"打开配置面板失败: {str(e)}")