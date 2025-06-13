# -*- coding: utf-8 -*-
"""
场景描述智能增强器

实现对五阶段分镜脚本中画面描述的智能增强，包括：
1. 技术细节分析和补充
2. 角色场景一致性描述注入
3. 内容融合和优化
"""

import re
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from src.utils.logger import logger
from src.utils.character_scene_manager import CharacterSceneManager
from src.utils.color_optimizer import ColorOptimizer


@dataclass
class TechnicalDetails:
    """技术细节数据结构"""
    shot_type: str = ""  # 镜头类型
    camera_angle: str = ""  # 机位角度
    camera_movement: str = ""  # 镜头运动
    depth_of_field: str = ""  # 景深
    lighting: str = ""  # 光线
    composition: str = ""  # 构图
    color_tone: str = ""  # 色调
    
    def to_description(self) -> str:
        """转换为描述文本"""
        parts = []
        if self.shot_type:
            parts.append(f"镜头类型：{self.shot_type}")
        if self.camera_angle:
            parts.append(f"机位角度：{self.camera_angle}")
        if self.camera_movement:
            parts.append(f"镜头运动：{self.camera_movement}")
        if self.depth_of_field:
            parts.append(f"景深：{self.depth_of_field}")
        if self.lighting:
            parts.append(f"光线：{self.lighting}")
        if self.composition:
            parts.append(f"构图：{self.composition}")
        if self.color_tone:
            parts.append(f"色调：{self.color_tone}")
        return "，".join(parts)


@dataclass
class ConsistencyInfo:
    """一致性信息数据结构"""
    characters: List[str] = None  # 角色一致性描述
    scenes: List[str] = None  # 场景一致性描述
    detected_characters: List[str] = None  # 检测到的角色名称
    detected_scenes: List[str] = None  # 检测到的场景名称
    
    def __post_init__(self):
        if self.characters is None:
            self.characters = []
        if self.scenes is None:
            self.scenes = []
        if self.detected_characters is None:
            self.detected_characters = []
        if self.detected_scenes is None:
            self.detected_scenes = []
    
    def to_description(self) -> str:
        """转换为描述文本"""
        parts = []
        if self.characters:
            parts.extend([f"角色一致性：{char}" for char in self.characters])
        if self.scenes:
            parts.extend([f"场景一致性：{scene}" for scene in self.scenes])
        return "；".join(parts)


class TechnicalDetailsAnalyzer:
    """技术细节分析器"""
    
    def __init__(self):
        # 技术细节推理规则
        self.shot_type_rules = {
            r'(特写|close.?up|特写镜头)': '特写',
            r'(近景|medium.?shot|中景)': '近景',
            r'(中景|medium.?shot)': '中景',
            r'(远景|long.?shot|全景)': '远景',
            r'(全景|wide.?shot|大全景)': '全景',
            r'(大全景|extreme.?wide)': '大全景'
        }
        
        self.camera_angle_rules = {
            r'(俯视|俯拍|bird.?eye|从上往下)': '俯视角度',
            r'(仰视|仰拍|worm.?eye|从下往上)': '仰视角度',
            r'(平视|水平|eye.?level)': '平视角度',
            r'(侧面|侧视|profile)': '侧面角度'
        }
        
        self.camera_movement_rules = {
            r'(推进|推镜|dolly.?in|zoom.?in)': '推镜',
            r'(拉远|拉镜|dolly.?out|zoom.?out)': '拉镜',
            r'(摇镜|摇摆|pan)': '摇镜',
            r'(跟拍|跟随|follow)': '跟拍',
            r'(环绕|围绕|orbit)': '环绕拍摄',
            r'(手持|晃动|handheld)': '手持拍摄'
        }
        
        self.lighting_rules = {
            r'(自然光|阳光|日光|daylight)': '自然光',
            r'(室内光|灯光|artificial)': '人工光源',
            r'(柔光|soft.?light)': '柔光',
            r'(硬光|hard.?light)': '硬光',
            r'(逆光|backlight)': '逆光',
            r'(侧光|side.?light)': '侧光',
            r'(顶光|top.?light)': '顶光',
            r'(暖光|warm.?light)': '暖色调光线',
            r'(冷光|cool.?light)': '冷色调光线'
        }
        
        self.composition_rules = {
            r'(三分法|rule.?of.?thirds)': '三分法构图',
            r'(对称|symmetr)': '对称构图',
            r'(对角线|diagonal)': '对角线构图',
            r'(中心|center)': '中心构图',
            r'(框架|frame)': '框架构图',
            r'(引导线|leading.?line)': '引导线构图'
        }
        
        self.depth_rules = {
            r'(浅景深|shallow.?depth)': '浅景深',
            r'(深景深|deep.?depth)': '深景深',
            r'(背景虚化|blur|bokeh)': '背景虚化',
            r'(前景|foreground)': '前景突出',
            r'(背景|background)': '背景清晰'
        }
        
        self.color_tone_rules = {
            r'(暖色调|warm.?tone)': '暖色调',
            r'(冷色调|cool.?tone)': '冷色调',
            r'(高对比|high.?contrast)': '高对比度',
            r'(低对比|low.?contrast)': '低对比度',
            r'(饱和|saturated)': '高饱和度',
            r'(淡雅|desaturated)': '低饱和度',
            r'(黑白|monochrome)': '黑白色调'
        }
    
    def analyze_description(self, description: str) -> TechnicalDetails:
        """分析画面描述，推理技术细节
        
        Args:
            description: 原始画面描述
            
        Returns:
            TechnicalDetails: 推理出的技术细节
        """
        details = TechnicalDetails()
        
        try:
            # 分析镜头类型
            details.shot_type = self._analyze_with_rules(description, self.shot_type_rules)
            
            # 分析机位角度
            details.camera_angle = self._analyze_with_rules(description, self.camera_angle_rules)
            
            # 分析镜头运动
            details.camera_movement = self._analyze_with_rules(description, self.camera_movement_rules)
            
            # 分析光线
            details.lighting = self._analyze_with_rules(description, self.lighting_rules)
            
            # 分析构图
            details.composition = self._analyze_with_rules(description, self.composition_rules)
            
            # 分析景深
            details.depth_of_field = self._analyze_with_rules(description, self.depth_rules)
            
            # 分析色调
            details.color_tone = self._analyze_with_rules(description, self.color_tone_rules)
            
            # 智能推理补充
            self._intelligent_inference(description, details)
            
        except Exception as e:
            logger.error(f"技术细节分析失败: {e}")
        
        return details
    
    def _analyze_with_rules(self, text: str, rules: Dict[str, str]) -> str:
        """使用规则分析文本"""
        for pattern, result in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                return result
        return ""
    
    def _get_character_consistency(self, character_name: str) -> str:
        """获取角色一致性描述"""
        try:
            characters_data = self.character_scene_manager._load_json(
                self.character_scene_manager.characters_file
            )
            
            # 查找角色数据
            for char_id, char_data in characters_data.get('characters', {}).items():
                if char_data.get('name') == character_name or char_data.get('id') == character_name:
                    return char_data.get('consistency_prompt', '')
            
        except Exception as e:
            logger.error(f"获取角色一致性描述失败 {character_name}: {e}")
        
        return ""
    
    def _get_scene_consistency(self, scene_name: str) -> str:
        """获取场景一致性描述"""
        try:
            scenes_data = self.character_scene_manager._load_json(
                self.character_scene_manager.scenes_file
            )
            
            # 查找场景数据
            for scene_id, scene_data in scenes_data.get('scenes', {}).items():
                if scene_data.get('name') == scene_name or scene_data.get('id') == scene_name:
                    return scene_data.get('consistency_prompt', '')
            
        except Exception as e:
            logger.error(f"获取场景一致性描述失败 {scene_name}: {e}")
        
        return ""
    
    def _intelligent_inference(self, description: str, details: TechnicalDetails):
        """智能推理补充技术细节"""
        # 基于内容推理镜头类型
        if not details.shot_type:
            if any(word in description for word in ['脸部', '表情', '眼神', '面部']):
                details.shot_type = '特写'
            elif any(word in description for word in ['全身', '整个人', '站立', '走路']):
                details.shot_type = '全景'
            elif any(word in description for word in ['上半身', '胸部以上', '肩膀']):
                details.shot_type = '中景'
        
        # 基于场景推理光线
        if not details.lighting:
            if any(word in description for word in ['室外', '阳光', '白天', '户外']):
                details.lighting = '自然光'
            elif any(word in description for word in ['室内', '灯光', '夜晚']):
                details.lighting = '人工光源'
        
        # 基于动作推理镜头运动
        if not details.camera_movement:
            if any(word in description for word in ['走向', '靠近', '接近']):
                details.camera_movement = '推镜'
            elif any(word in description for word in ['远离', '后退', '离开']):
                details.camera_movement = '拉镜'
            elif any(word in description for word in ['转身', '环顾', '四周']):
                details.camera_movement = '摇镜'


class ConsistencyInjector:
    """一致性描述注入器 - 使用通用NLP技术动态识别角色和场景"""
    
    def __init__(self, character_scene_manager: CharacterSceneManager):
        self.character_scene_manager = character_scene_manager
        
        # 缓存已加载的角色和场景数据
        self._characters_cache = None
        self._scenes_cache = None
        self._last_cache_update = 0
        
        # 通用场景类型关键词（不依赖特定小说）
        self.generic_scene_patterns = {
            '室内': ['室内', '房间', '屋内', '内部', '里面'],
            '室外': ['室外', '户外', '外面', '野外', '街道'],
            '办公场所': ['办公室', '会议室', '工作室', '书房'],
            '居住场所': ['家', '客厅', '卧室', '厨房', '浴室'],
            '教育场所': ['学校', '教室', '实验室', '图书馆', '校园'],
            '自然环境': ['山', '海', '森林', '草原', '沙漠', '河流'],
            '城市环境': ['城市', '街道', '广场', '公园', '商场']
        }
    
    def extract_consistency_info(self, description: str, characters: List[str] = None) -> ConsistencyInfo:
        """从描述中提取一致性信息
        
        Args:
            description: 画面描述
            characters: 已知角色列表
            
        Returns:
            ConsistencyInfo: 一致性信息
        """
        consistency_info = ConsistencyInfo()
        
        try:
            # 识别角色
            detected_characters = self._detect_characters(description, characters)
            consistency_info.detected_characters = detected_characters
            
            # 记录角色检测详情
            logger.debug(f"角色检测结果: {detected_characters}")
            
            # 获取角色一致性描述
            for char_name in detected_characters:
                char_consistency = self._get_character_consistency(char_name)
                if char_consistency:
                    consistency_info.characters.append(char_consistency)
                    logger.debug(f"角色 '{char_name}' 一致性描述: {char_consistency[:50]}...")
                else:
                    logger.debug(f"角色 '{char_name}' 未找到一致性描述")
            
            # 识别场景
            detected_scenes = self._detect_scenes(description)
            consistency_info.detected_scenes = detected_scenes
            
            # 记录场景检测详情
            logger.debug(f"场景检测结果: {detected_scenes}")
            
            # 获取场景一致性描述
            for scene_name in detected_scenes:
                scene_consistency = self._get_scene_consistency(scene_name)
                if scene_consistency:
                    consistency_info.scenes.append(scene_consistency)
                    logger.debug(f"场景 '{scene_name}' 一致性描述: {scene_consistency[:50]}...")
                else:
                    logger.debug(f"场景 '{scene_name}' 未找到一致性描述")
                    
        except Exception as e:
            logger.error(f"一致性信息提取失败: {e}")
        
        return consistency_info
    
    def _detect_characters(self, description: str, known_characters: List[str] = None) -> List[str]:
        """动态检测描述中的角色 - 改进版"""
        detected = []
        
        # 获取项目中的所有角色数据（包含别名和关键词）
        project_characters_data = self._get_all_project_characters_with_data()
        
        # 优先检测已知角色（从参数传入）
        if known_characters:
            for char in known_characters:
                if self._is_character_mentioned(char, description, project_characters_data):
                    if char not in detected:
                        detected.append(char)
        
        # 检测项目中的所有角色
        for char_name, char_data in project_characters_data.items():
            if self._is_character_mentioned(char_name, description, {char_name: char_data}):
                if char_name not in detected:
                    detected.append(char_name)
        
        return detected
    
    def _is_character_mentioned(self, char_name: str, description: str, characters_data: dict) -> bool:
        """检查角色是否在描述中被提及"""
        # 直接名称匹配
        if char_name in description:
            return True
        
        # 检查角色数据中的别名和关键词
        char_data = characters_data.get(char_name, {})
        
        # 检查别名
        aliases = char_data.get('aliases', [])
        if isinstance(aliases, list):
            for alias in aliases:
                if alias and alias in description:
                    return True
        
        # 检查外貌特征关键词
        appearance = char_data.get('appearance', {})
        if appearance:
            # 检查头发特征
            hair = appearance.get('hair', '')
            if hair and any(keyword in description for keyword in hair.split() if len(keyword) > 1):
                return True
            
            # 检查性别和年龄
            gender = appearance.get('gender', '')
            age_range = appearance.get('age_range', '')
            if gender and gender in description:
                return True
            if '大叔' in description and '40-50岁' in age_range:
                return True
            if '光头' in description and '光头' in hair:
                return True
        
        # 检查服装特征
        clothing = char_data.get('clothing', {})
        if clothing:
            style = clothing.get('style', '')
            if style and any(keyword in description for keyword in style.split() if len(keyword) > 1):
                return True
        
        return False
    
    def _detect_scenes(self, description: str) -> List[str]:
        """动态检测描述中的场景"""
        detected = []
        
        # 动态加载项目中的所有场景并进行匹配
        project_scenes = self._get_all_project_scenes()
        for scene_name, scene_keywords in project_scenes.items():
            # 检查场景名称直接匹配
            if scene_name in description:
                detected.append(scene_name)
                continue
            
            # 检查场景关键词匹配
            if scene_keywords and any(keyword in description for keyword in scene_keywords):
                detected.append(scene_name)
        
        # 如果没有匹配到具体场景，尝试匹配通用场景类型
        if not detected:
            for scene_type, keywords in self.generic_scene_patterns.items():
                if any(keyword in description for keyword in keywords):
                    detected.append(f"通用{scene_type}")
                    break
        
        return detected
    
    def _get_character_consistency(self, character_name: str) -> str:
        """获取角色一致性描述"""
        try:
            characters_data = self.character_scene_manager._load_json(
                self.character_scene_manager.characters_file
            )
            
            # 查找角色数据
            for char_id, char_data in characters_data.get('characters', {}).items():
                if char_data.get('name') == character_name or char_data.get('id') == character_name:
                    return char_data.get('consistency_prompt', '')
            
        except Exception as e:
            logger.error(f"获取角色一致性描述失败 {character_name}: {e}")
        
        return ""
    
    def _get_scene_consistency(self, scene_name: str) -> str:
        """获取场景一致性描述"""
        try:
            scenes_data = self.character_scene_manager._load_json(
                self.character_scene_manager.scenes_file
            )
            
            # 查找场景数据
            for scene_id, scene_data in scenes_data.get('scenes', {}).items():
                if scene_data.get('name') == scene_name or scene_data.get('id') == scene_name:
                    return scene_data.get('consistency_prompt', '')
            
        except Exception as e:
            logger.error(f"获取场景一致性描述失败 {scene_name}: {e}")
        
        return ""
    
    def _get_all_project_characters(self) -> List[str]:
        """获取项目中的所有角色名称"""
        try:
            # 检查缓存是否需要更新
            import time
            current_time = time.time()
            if (self._characters_cache is None or 
                current_time - self._last_cache_update > 60):  # 缓存60秒
                
                characters_data = self.character_scene_manager._load_json(
                    self.character_scene_manager.characters_file
                )
                
                character_names = []
                for char_data in characters_data.get('characters', {}).values():
                    char_name = char_data.get('name', '')
                    if char_name:
                        character_names.append(char_name)
                        
                        # 也添加角色的别名或昵称（如果有的话）
                        aliases = char_data.get('aliases', [])
                        if isinstance(aliases, list):
                            character_names.extend(aliases)
                
                self._characters_cache = character_names
                self._last_cache_update = current_time
            
            return self._characters_cache or []
            
        except Exception as e:
            logger.error(f"获取项目角色列表失败: {e}")
            return []
    
    def _get_all_project_characters_with_data(self) -> Dict[str, dict]:
        """获取项目中的所有角色及其完整数据"""
        try:
            characters_data = self.character_scene_manager._load_json(
                self.character_scene_manager.characters_file
            )
            
            character_dict = {}
            for char_data in characters_data.get('characters', {}).values():
                char_name = char_data.get('name', '')
                if char_name:
                    character_dict[char_name] = char_data
            
            return character_dict
            
        except Exception as e:
            logger.error(f"获取项目角色数据失败: {e}")
            return {}
    
    def _get_all_project_scenes(self) -> Dict[str, List[str]]:
        """获取项目中的所有场景及其关键词"""
        try:
            # 检查缓存是否需要更新
            import time
            current_time = time.time()
            if (self._scenes_cache is None or 
                current_time - self._last_cache_update > 60):  # 缓存60秒
                
                scenes_data = self.character_scene_manager._load_json(
                    self.character_scene_manager.scenes_file
                )
                
                scene_info = {}
                for scene_data in scenes_data.get('scenes', {}).values():
                    scene_name = scene_data.get('name', '')
                    if scene_name:
                        # 获取场景关键词
                        keywords = scene_data.get('keywords', [])
                        if not isinstance(keywords, list):
                            keywords = []
                        
                        # 添加场景描述中的关键词（简单提取）
                        description = scene_data.get('description', '')
                        if description:
                            # 简单的关键词提取：分割并过滤常见词汇
                            desc_words = [word.strip('，。！？；：') for word in description.split() 
                                        if len(word.strip('，。！？；：')) > 1]
                            keywords.extend(desc_words[:5])  # 只取前5个词避免过多
                        
                        scene_info[scene_name] = keywords
                
                self._scenes_cache = scene_info
                self._last_cache_update = current_time
            
            return self._scenes_cache or {}
            
        except Exception as e:
            logger.error(f"获取项目场景列表失败: {e}")
            return {}


@dataclass
class FusionResult:
    """内容融合结果数据结构"""
    enhanced_description: str = ""
    technical_additions: List[str] = None
    consistency_additions: List[str] = None
    fusion_quality_score: float = 0.0
    
    def __post_init__(self):
        if self.technical_additions is None:
            self.technical_additions = []
        if self.consistency_additions is None:
            self.consistency_additions = []


class ContentFuser:
    """智能内容融合器 - 第二阶段核心组件"""
    
    def __init__(self, llm_api=None, character_scene_manager=None):
        # 初始化LLM API
        self.llm_api = llm_api
        # 初始化角色场景管理器
        self.character_scene_manager = character_scene_manager
        
        # 融合策略配置
        self.fusion_strategies = {
            'natural': self._natural_fusion,
            'structured': self._structured_fusion,
            'minimal': self._minimal_fusion,
            'intelligent': self._natural_fusion  # 新增智能融合策略
        }
        
        # 内容优先级权重
        self.priority_weights = {
            'original_description': 1.0,
            'character_consistency': 0.8,
            'scene_consistency': 0.7,
            'technical_details': 0.6
        }
        
        # 融合质量评估规则
        self.quality_rules = {
            'length_balance': 0.3,  # 长度平衡
            'content_coherence': 0.4,  # 内容连贯性
            'information_density': 0.3  # 信息密度
        }
    
    def _get_character_consistency(self, character_name: str) -> str:
        """获取角色一致性描述"""
        try:
            characters_data = self.character_scene_manager._load_json(
                self.character_scene_manager.characters_file
            )
            
            # 查找角色数据
            for char_id, char_data in characters_data.get('characters', {}).items():
                if char_data.get('name') == character_name or char_data.get('id') == character_name:
                    return char_data.get('consistency_prompt', '')
            
        except Exception as e:
            logger.error(f"获取角色一致性描述失败 {character_name}: {e}")
        
        return ""
    
    def fuse_content(self, original: str, technical: TechnicalDetails, 
                    consistency: ConsistencyInfo, strategy: str = 'intelligent') -> FusionResult:
        """智能融合内容
        
        Args:
            original: 原始描述
            technical: 技术细节
            consistency: 一致性信息
            strategy: 融合策略
            
        Returns:
            FusionResult: 融合结果
        """
        try:
            logger.info(f"开始内容融合，策略: {strategy}")
            
            # 预处理内容
            processed_content = self._preprocess_content(original, technical, consistency)
            
            # 执行融合策略
            fusion_func = self.fusion_strategies.get(strategy, self._natural_fusion)
            result = fusion_func(processed_content)
            
            # 后处理和质量评估
            result = self._postprocess_result(result)
            
            logger.info(f"内容融合完成，质量评分: {result.fusion_quality_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"内容融合失败: {e}")
            return FusionResult(enhanced_description=original)
    
    def _preprocess_content(self, original: str, technical: TechnicalDetails, 
                          consistency: ConsistencyInfo) -> Dict[str, Any]:
        """预处理内容"""
        return {
            'original': original.strip(),
            'technical_parts': self._extract_technical_parts(technical),
            'consistency_parts': self._extract_consistency_parts(consistency),
            'detected_characters': getattr(consistency, 'detected_characters', []) if consistency else [],
            'detected_scenes': getattr(consistency, 'detected_scenes', []) if consistency else [],
            'original_length': len(original),
            'has_punctuation': original.endswith(('。', '！', '？', '.', '!', '?'))
        }
    
    def _extract_technical_parts(self, technical: TechnicalDetails) -> List[str]:
        """提取技术细节部分"""
        parts = []
        if technical:
            if technical.shot_type:
                parts.append(f"{technical.shot_type}镜头")
            if technical.camera_angle:
                parts.append(technical.camera_angle)
            if technical.lighting:
                parts.append(technical.lighting)
            if technical.camera_movement:
                parts.append(technical.camera_movement)
            if technical.composition:
                parts.append(technical.composition)
        return parts
    
    def _extract_consistency_parts(self, consistency: ConsistencyInfo) -> List[str]:
        """提取一致性信息部分"""
        parts = []
        if consistency:
            # 处理角色一致性
            for char_desc in consistency.characters:
                if char_desc and len(char_desc.strip()) > 0:
                    # 提取关键特征描述
                    key_features = self._extract_key_features(char_desc)
                    parts.extend(key_features)
            
            # 处理场景一致性
            for scene_desc in consistency.scenes:
                if scene_desc and len(scene_desc.strip()) > 0:
                    # 提取关键环境描述
                    key_env = self._extract_key_environment(scene_desc)
                    parts.extend(key_env)
        return parts
    
    def _extract_key_features(self, description: str) -> List[str]:
        """从角色描述中提取关键特征"""
        # 简单的关键特征提取逻辑
        features = []
        
        # 外貌特征关键词
        appearance_keywords = ['头发', '眼睛', '身高', '体型', '服装', '穿着', '戴着']
        for keyword in appearance_keywords:
            if keyword in description:
                # 提取包含关键词的短语
                sentences = description.split('，')
                for sentence in sentences:
                    if keyword in sentence and len(sentence.strip()) < 20:
                        features.append(sentence.strip())
                        break
        
        return features[:2]  # 最多返回2个关键特征
    
    def _extract_key_environment(self, description: str) -> List[str]:
        """从场景描述中提取关键环境信息"""
        env_info = []
        
        # 环境特征关键词
        env_keywords = ['光线', '氛围', '背景', '环境', '设备', '装饰']
        for keyword in env_keywords:
            if keyword in description:
                sentences = description.split('，')
                for sentence in sentences:
                    if keyword in sentence and len(sentence.strip()) < 25:
                        env_info.append(sentence.strip())
                        break
        
        return env_info[:1]  # 最多返回1个环境信息
    
    def _natural_fusion_impl(self, content: Dict[str, Any]) -> FusionResult:
        """自然融合策略"""
        result = FusionResult()
        parts = [content['original']]
        
        # 自然地添加技术细节
        if content['technical_parts']:
            tech_text = "，".join(content['technical_parts'][:2])  # 限制技术细节数量
            if content['has_punctuation']:
                parts[0] = parts[0].rstrip('。！？.!?') + f"，{tech_text}。"
            else:
                parts[0] += f"，{tech_text}"
            result.technical_additions = content['technical_parts'][:2]
        
        # 自然地添加一致性信息（使用完整的角色描述）
        if content['consistency_parts']:
            # 只取第一个完整的角色描述，避免过长
            consistency_text = content['consistency_parts'][0] if content['consistency_parts'] else ""
            if consistency_text:
                parts.append(f"（{consistency_text}）")
                result.consistency_additions = content['consistency_parts'][:1]
        
        result.enhanced_description = "".join(parts)
        return result

    def _embed_character_descriptions(self, original_desc: str, detected_characters: List[str]) -> str:
        """将角色一致性描述直接嵌入到原始描述中"""
        if not detected_characters:
            return original_desc
        
        enhanced_desc = original_desc
        
        # 获取角色一致性信息
        character_descriptions = {}
        for character_name in detected_characters:
            # 直接使用_get_character_consistency方法获取角色一致性描述
            character_consistency = self._get_character_consistency(character_name)
            if character_consistency:
                character_descriptions[character_name] = character_consistency
        
        # 在原始描述中替换角色名称为详细描述
        for character_name, detailed_desc in character_descriptions.items():
            # 使用正则表达式进行精确替换，支持中文字符
            import re
            # 对于中文字符，使用更宽松的边界匹配
            pattern = re.escape(character_name)
            replacement = f"{character_name}（{detailed_desc}）"
            enhanced_desc = re.sub(pattern, replacement, enhanced_desc)
        
        return enhanced_desc

    def _structured_fusion(self, content: Dict[str, Any]) -> FusionResult:
        """结构化融合策略"""
        result = FusionResult()
        parts = [content['original']]
        
        # 结构化添加技术规格
        if content['technical_parts']:
            tech_section = "\n技术规格：" + "，".join(content['technical_parts'])
            parts.append(tech_section)
            result.technical_additions = content['technical_parts']
        
        # 结构化添加一致性要求
        if content['consistency_parts']:
            consistency_section = "\n一致性要求：" + "，".join(content['consistency_parts'])
            parts.append(consistency_section)
            result.consistency_additions = content['consistency_parts']
        
        result.enhanced_description = "".join(parts)
        return result
    
    def _minimal_fusion(self, content: Dict[str, Any]) -> FusionResult:
        """最小化融合策略"""
        result = FusionResult()
        parts = [content['original']]
        
        # 最小化添加关键信息
        additions = []
        if content['technical_parts']:
            additions.extend(content['technical_parts'][:1])  # 只取最重要的技术细节
            result.technical_additions = content['technical_parts'][:1]
        
        if content['consistency_parts']:
            additions.extend(content['consistency_parts'][:1])  # 只取最重要的一致性信息
            result.consistency_additions = content['consistency_parts'][:1]
        
        if additions:
            parts.append(f" [{','.join(additions)}]")
        
        result.enhanced_description = "".join(parts)
        return result
    
    def _natural_fusion(self, content: Dict[str, Any]) -> FusionResult:
        """智能融合策略 - 根据内容特点自适应选择最佳融合方式"""
        result = FusionResult()
        
        # 如果有LLM API可用，优先使用LLM进行智能融合
        if self.llm_api and self.llm_api.is_configured():
            try:
                return self._llm_enhanced_fusion(content)
            except Exception as e:
                logger.warning(f"LLM增强融合失败，回退到传统方法: {e}")
        
        # 分析原始描述特点
        original_length = content['original_length']
        tech_count = len(content['technical_parts'])
        consistency_count = len(content['consistency_parts'])
        
        # 根据内容长度和信息量选择策略
        if original_length < 20 and (tech_count + consistency_count) > 3:
            # 短描述 + 大量补充信息 -> 使用结构化
            return self._structured_fusion(content)
        elif original_length > 100:
            # 长描述 -> 使用最小化
            return self._minimal_fusion(content)
        else:
            # 中等长度 -> 使用自然融合
            return self._natural_fusion_impl(content)
    
    def _llm_enhanced_fusion(self, content: Dict[str, Any]) -> FusionResult:
        """使用LLM进行智能内容融合"""
        result = FusionResult()
        
        # 构建LLM提示词
        original_desc = content['original']
        technical_parts = content['technical_parts']
        consistency_parts = content['consistency_parts']
        detected_characters = content.get('detected_characters', [])
        detected_scenes = content.get('detected_scenes', [])
        
        logger.info("=== 场景增强器LLM辅助生成开始 ===")
        logger.info(f"原始场景描述: {original_desc[:100]}..." if len(original_desc) > 100 else f"原始场景描述: {original_desc}")
        logger.info(f"检测到的角色: {detected_characters if detected_characters else '无'}")
        logger.info(f"检测到的场景: {detected_scenes if detected_scenes else '无'}")
        
        # 预处理原始描述，将角色一致性描述直接嵌入
        enhanced_original_desc = self._embed_character_descriptions(original_desc, detected_characters)
        logger.info(f"角色描述嵌入后: {enhanced_original_desc[:150]}..." if len(enhanced_original_desc) > 150 else f"角色描述嵌入后: {enhanced_original_desc}")
        
        # 构建增强提示
        enhancement_prompt = f"""请对以下画面描述进行智能增强，要求：
1. 保持原始描述的核心内容和风格
2. 自然融入提供的技术细节
3. 确保描述流畅自然，避免生硬拼接
4. 控制总长度在100-250字之间

原始描述：{enhanced_original_desc}

技术细节补充：{'; '.join(technical_parts) if technical_parts else '无'}

请输出增强后的画面描述："""
        
        logger.info("正在调用LLM进行场景描述增强...")
        # 记录完整的提示词内容，不截断
        logger.debug(f"LLM增强提示词完整内容:\n{enhancement_prompt}")
        
        try:
            # 调用LLM进行增强
            enhanced_text = self.llm_api.rewrite_text(enhancement_prompt)
            
            if enhanced_text and len(enhanced_text.strip()) > 0:
                enhanced_content = enhanced_text.strip()
                logger.info(f"✓ LLM增强成功完成")
                logger.info(f"  - 原始描述长度: {len(original_desc)} 字符")
                logger.info(f"  - 增强后长度: {len(enhanced_content)} 字符")
                logger.info(f"  - 增强比例: {len(enhanced_content)/len(original_desc):.2f}x")
                logger.info(f"技术细节补充：{'; '.join(technical_parts) if technical_parts else '无'}")
                # 角色一致性信息已集成到增强描述中，无需单独显示
                logger.info(f"增强后场景描述: {enhanced_content[:200]}..." if len(enhanced_content) > 200 else f"增强后场景描述: {enhanced_content}")
                
                # 注意：文件保存已移至enhance_storyboard方法中统一处理
                
                result.enhanced_description = enhanced_content
                result.technical_additions = technical_parts
                result.consistency_additions = consistency_parts
                result.fusion_quality_score = 0.85  # LLM增强的质量评分较高
                
                logger.info("=== 场景增强器LLM辅助生成完成 ===")
                return result
            else:
                logger.warning("✗ LLM增强结果质量不佳，回退到自然融合")
                logger.info("=== 场景增强器LLM辅助生成失败，使用备选方案 ===")
                raise Exception("LLM返回空结果")
                
        except Exception as e:
            logger.error(f"✗ LLM增强融合失败: {e}")
            logger.info("=== 场景增强器LLM辅助生成异常，使用备选方案 ===")
            # 回退到自然融合
            return self._natural_fusion(content)
    
    def _postprocess_result(self, result: FusionResult) -> FusionResult:
        """后处理融合结果"""
        # 清理多余的标点符号
        result.enhanced_description = re.sub(r'[，。]{2,}', '，', result.enhanced_description)
        result.enhanced_description = re.sub(r'，+$', '。', result.enhanced_description)
        
        # 计算融合质量评分
        result.fusion_quality_score = self._calculate_quality_score(result)
        
        return result
    
    def _calculate_quality_score(self, result: FusionResult) -> float:
        """计算融合质量评分"""
        score = 0.0
        
        # 长度平衡评分
        length = len(result.enhanced_description)
        if 100 <= length <= 250:  # 理想长度范围
            length_score = 1.0
        elif length < 100:
            length_score = length / 100.0
        else:
            length_score = max(0.5, 300 / length)
        
        score += length_score * self.quality_rules['length_balance']
        
        # 信息密度评分
        info_count = len(result.technical_additions) + len(result.consistency_additions)
        density_score = min(1.0, info_count / 4.0)  # 最多4个补充信息为满分
        score += density_score * self.quality_rules['information_density']
        
        # 内容连贯性评分（简化版）
        coherence_score = 0.8  # 基础连贯性评分
        if '，，' in result.enhanced_description or '。。' in result.enhanced_description:
            coherence_score -= 0.2
        
        score += coherence_score * self.quality_rules['content_coherence']
        
        return min(1.0, score)


class SceneDescriptionEnhancer:
    """场景描述智能增强器 - 主类（第二阶段增强版）"""
    
    def __init__(self, project_root: str, character_scene_manager: CharacterSceneManager = None, llm_api=None):
        self.project_root = project_root
        
        # 初始化角色场景管理器
        if character_scene_manager:
            self.character_scene_manager = character_scene_manager
        else:
            self.character_scene_manager = CharacterSceneManager(project_root)
        
        # 初始化LLM API
        self.llm_api = llm_api
        
        # 初始化组件
        self.technical_analyzer = TechnicalDetailsAnalyzer()
        self.consistency_injector = ConsistencyInjector(self.character_scene_manager)
        self.content_fuser = ContentFuser(llm_api=llm_api, character_scene_manager=self.character_scene_manager)  # 传递LLM API和角色管理器给内容融合器
        self.color_optimizer = ColorOptimizer()  # 初始化颜色优化器
        
        # 配置选项
        self.config = {
            'enable_technical_details': True,
            'enable_consistency_injection': True,
            'enhancement_level': 'medium',  # low, medium, high
            'fusion_strategy': 'intelligent',  # natural, structured, minimal, intelligent
            'quality_threshold': 0.6,  # 质量阈值
            'enable_llm_enhancement': True  # 启用LLM增强
        }
    
    def enhance_description(self, original_description: str, characters: List[str] = None) -> str:
        """增强画面描述（第二阶段增强版）
        
        Args:
            original_description: 原始画面描述
            characters: 相关角色列表
            
        Returns:
            str: 增强后的画面描述
        """
        try:
            logger.info(f"开始增强画面描述: {original_description[:50]}...")
            
            # 1. 技术细节分析
            technical_details = None
            if self.config['enable_technical_details']:
                technical_details = self.technical_analyzer.analyze_description(original_description)
                logger.debug(f"技术细节分析完成: {technical_details.to_description()}")
            
            # 2. 一致性信息提取
            consistency_info = None
            if self.config['enable_consistency_injection']:
                consistency_info = self.consistency_injector.extract_consistency_info(
                    original_description, characters
                )
                logger.debug(f"一致性信息提取完成: {consistency_info.to_description()}")
            
            # 2.5. 颜色一致性处理
            enhanced_description_with_colors = original_description
            if characters:
                enhanced_description_with_colors = self.color_optimizer.apply_color_consistency(
                    original_description, characters, self.character_scene_manager
                )
                logger.debug(f"颜色一致性处理完成")
            
            # 3. 智能内容融合（第二阶段核心功能）
            fusion_result = self.content_fuser.fuse_content(
                enhanced_description_with_colors, 
                technical_details, 
                consistency_info, 
                self.config['fusion_strategy']
            )
            
            # 4. 质量控制
            if fusion_result.fusion_quality_score >= self.config['quality_threshold']:
                enhanced_description = fusion_result.enhanced_description
                logger.info(f"画面描述增强完成，质量评分: {fusion_result.fusion_quality_score:.2f}")
            else:
                # 质量不达标，使用备用策略
                logger.warning(f"融合质量不达标({fusion_result.fusion_quality_score:.2f})，使用备用策略")
                backup_result = self.content_fuser.fuse_content(
                    enhanced_description_with_colors, technical_details, consistency_info, 'natural'
                )
                enhanced_description = backup_result.enhanced_description
            
            return enhanced_description
            
        except Exception as e:
            logger.error(f"画面描述增强失败: {e}")
            return original_description
    
    def enhance_description_with_details(self, original_description: str, characters: List[str] = None) -> Dict[str, Any]:
        """增强画面描述并返回详细信息
        
        Args:
            original_description: 原始画面描述
            characters: 相关角色列表
            
        Returns:
            Dict: 包含增强结果和详细信息的字典
        """
        try:
            logger.info(f"开始详细增强画面描述: {original_description[:50]}...")
            
            # 1. 技术细节分析
            technical_details = None
            if self.config['enable_technical_details']:
                technical_details = self.technical_analyzer.analyze_description(original_description)
            
            # 2. 一致性信息提取
            consistency_info = None
            if self.config['enable_consistency_injection']:
                consistency_info = self.consistency_injector.extract_consistency_info(
                    original_description, characters
                )
            
            # 3. 智能内容融合
            fusion_result = self.content_fuser.fuse_content(
                original_description, 
                technical_details, 
                consistency_info, 
                self.config['fusion_strategy']
            )
            
            # 4. 组装详细结果
            result = {
                'original_description': original_description,
                'enhanced_description': fusion_result.enhanced_description,
                'technical_details': technical_details.to_description() if technical_details else "",
                'consistency_info': consistency_info.to_description() if consistency_info else "",
                'technical_additions': fusion_result.technical_additions,
                'consistency_additions': fusion_result.consistency_additions,
                'fusion_quality_score': fusion_result.fusion_quality_score,
                'fusion_strategy': self.config['fusion_strategy'],
                'enhancement_config': self.config.copy()
            }
            
            logger.info(f"详细增强完成，质量评分: {fusion_result.fusion_quality_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"详细增强失败: {e}")
            return {
                'original_description': original_description,
                'enhanced_description': original_description,
                'error': str(e)
            }
    
    def _fuse_content(self, original: str, technical: TechnicalDetails, consistency: ConsistencyInfo) -> str:
        """融合原始描述、技术细节和一致性信息"""
        parts = [original]
        
        # 添加技术细节
        if technical and self.config['enable_technical_details']:
            tech_desc = technical.to_description()
            if tech_desc:
                if self.config['fusion_strategy'] == 'natural':
                    parts.append(f"（{tech_desc}）")
                elif self.config['fusion_strategy'] == 'structured':
                    parts.append(f"\n技术规格：{tech_desc}")
                else:  # minimal
                    parts.append(f" [{tech_desc}]")
        
        # 添加一致性信息
        if consistency and self.config['enable_consistency_injection']:
            consistency_desc = consistency.to_description()
            if consistency_desc:
                if self.config['fusion_strategy'] == 'natural':
                    parts.append(f"（{consistency_desc}）")
                elif self.config['fusion_strategy'] == 'structured':
                    parts.append(f"\n一致性要求：{consistency_desc}")
                else:  # minimal
                    parts.append(f" [{consistency_desc}]")
        
        return "".join(parts)
    
    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
                logger.info(f"配置已更新: {key} = {value}")
    
    def reload_config(self):
        """重新加载配置"""
        try:
            # 重新初始化配置
            from src.utils.config_manager import ConfigManager
            config_manager = ConfigManager()
            
            # 获取增强器配置
            enhancer_config = config_manager.get_setting("scene_enhancer", {})
            
            # 更新配置对象
            for key, value in enhancer_config.items():
                if key in self.config:
                    self.config[key] = value
            
            # 重新初始化内容融合器
            if hasattr(self, 'content_fuser'):
                self.content_fuser = ContentFuser()
            
            logger.info("场景描述增强器配置已重新加载")
            
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
            raise
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config.copy()
    
    def enhance_storyboard(self, storyboard_script: str, style: str = None) -> Dict[str, Any]:
        """增强整个分镜脚本中的画面描述
        
        Args:
            storyboard_script: 完整的分镜脚本内容
            style: 用户选择的风格（如电影风格、动漫风格等）
            
        Returns:
            Dict: 包含增强结果和详细信息的字典
        """
        try:
            logger.info(f"开始增强分镜脚本，原始长度: {len(storyboard_script)}")
            
            # 解析分镜脚本，提取画面描述和技术细节
            enhanced_descriptions = []
            current_shot_info = {}
            
            lines = storyboard_script.split('\n')
            current_scene = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 检测场景标题 - 跳过所有场景标题，不进行增强
                if line.startswith('## 场景') or line.startswith('### 场景') or line.startswith('场景'):
                    current_scene = line
                    continue  # 跳过场景标题，不增强
                
                # 检测镜头开始
                if line.startswith('### 镜头') or line.startswith('## 镜头'):
                    # 如果有之前的镜头信息，处理它
                    if current_shot_info.get('画面描述'):
                        enhanced_desc = self._enhance_shot_description(current_shot_info, style)
                        enhanced_desc['场景'] = current_scene  # 添加场景信息
                        enhanced_descriptions.append(enhanced_desc)
                    
                    # 重置当前镜头信息
                    current_shot_info = {'镜头编号': line}
                    continue
                
                # 提取技术细节和画面描述
                if '**' in line and ('：' in line or ':' in line):
                    # 提取字段名和值
                    if '：' in line:
                        field_part, value_part = line.split('：', 1)
                    else:
                        field_part, value_part = line.split(':', 1)
                    
                    # 清理字段名
                    field_name = field_part.replace('**', '').replace('-', '').strip()
                    value = value_part.strip()
                    
                    # 存储信息
                    current_shot_info[field_name] = value
            
            # 处理最后一个镜头
            if current_shot_info.get('画面描述'):
                enhanced_desc = self._enhance_shot_description(current_shot_info, style)
                enhanced_desc['场景'] = current_scene  # 添加场景信息
                enhanced_descriptions.append(enhanced_desc)
            
            # 组合所有增强后的画面描述
            enhanced_content = '\n\n'.join([desc['enhanced'] for desc in enhanced_descriptions])
            
            # 计算质量评分
            quality_score = min(1.0, len(enhanced_descriptions) * 0.2) if enhanced_descriptions else 0.5
            
            result = {
                'enhanced_description': enhanced_content,
                'original_description': storyboard_script,
                'enhanced_count': len(enhanced_descriptions),
                'enhanced_details': enhanced_descriptions,
                'fusion_quality_score': quality_score,
                'config': self.config.copy(),
                'technical_details': {},
                'consistency_details': {}
            }
            
            # 保存增强结果到文件
            self._save_generated_text_to_file(enhanced_descriptions)
            logger.info("✓ 增强结果已保存到prompt.json文件")
            
            logger.info(f"分镜脚本增强完成，增强了{len(enhanced_descriptions)}个画面描述")
            return result
            
        except Exception as e:
            logger.error(f"分镜脚本增强失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return {
                'enhanced_description': storyboard_script,
                'original_description': storyboard_script,
                'error': str(e),
                'fusion_quality_score': 0.0
            }
    
    def _enhance_shot_description(self, shot_info: Dict[str, str], style: str = None) -> Dict[str, Any]:
        """增强单个镜头的画面描述
        
        Args:
            shot_info: 包含镜头信息的字典
            style: 用户选择的风格（如电影风格、动漫风格等）
            
        Returns:
            Dict: 包含原始和增强描述的字典
        """
        try:
            original_desc = shot_info.get('画面描述', '')
            if not original_desc:
                return {'original': '', 'enhanced': ''}
            
            # 根据用户选择的风格添加风格提示词
            style_prompts = {
                '电影风格': '电影感，超写实，4K，胶片颗粒，景深',
                '动漫风格': '动漫风，鲜艳色彩，干净线条，赛璐璐渲染，日本动画',
                '吉卜力风格': '吉卜力风，柔和色彩，奇幻，梦幻，丰富背景',
                '赛博朋克风格': '赛博朋克，霓虹灯，未来都市，雨夜，暗色氛围',
                '水彩插画风格': '水彩画风，柔和笔触，粉彩色，插画，温柔',
                '像素风格': '像素风，8位，复古，低分辨率，游戏风',
                '写实摄影风格': '真实光线，高细节，写实摄影，4K'
            }
            
            # 如果有风格选择，在原始描述后添加风格提示词
            enhanced_desc = original_desc
            if style and style in style_prompts:
                style_prompt = style_prompts[style]
                enhanced_desc = f"{original_desc}，{style_prompt}"
                logger.info(f"为镜头描述添加{style}风格提示词: {style_prompt}")
            
            # 提取技术细节
            technical_details = TechnicalDetails(
                shot_type=shot_info.get('镜头类型', ''),
                camera_angle=shot_info.get('机位角度', ''),
                camera_movement=shot_info.get('镜头运动', ''),
                depth_of_field=shot_info.get('景深效果', ''),
                lighting=shot_info.get('光影设计', ''),
                composition=shot_info.get('构图要点', ''),
                color_tone=shot_info.get('色彩基调', '')
            )
            
            # 提取角色信息（从画面描述中识别）
            characters = self._extract_characters_from_description(original_desc)
            
            # 获取一致性信息
            consistency_info = None
            if self.config['enable_consistency_injection']:
                consistency_info = self.consistency_injector.extract_consistency_info(
                    original_desc, characters
                )
            
            # 智能融合内容
            fusion_result = self.content_fuser.fuse_content(
                enhanced_desc,  # 使用带有风格提示词的描述
                technical_details,
                consistency_info,
                self.config['fusion_strategy']
            )
            
            return {
                'original': enhanced_desc,  # 返回带有风格提示词的描述作为原始描述
                'enhanced': fusion_result.enhanced_description,
                'technical_details': technical_details.to_description(),
                'consistency_info': consistency_info.to_description() if consistency_info else '',
                'characters': characters,
                'fusion_quality_score': fusion_result.fusion_quality_score
            }
            
        except Exception as e:
            logger.error(f"增强镜头描述失败: {e}")
            # 即使出错也尝试添加风格提示词
            original_desc = shot_info.get('画面描述', '')
            style_prompts = {
                '电影风格': '电影感，超写实，4K，胶片颗粒，景深',
                '动漫风格': '动漫风，鲜艳色彩，干净线条，赛璐璐渲染，日本动画',
                '吉卜力风格': '吉卜力风，柔和色彩，奇幻，梦幻，丰富背景',
                '赛博朋克风格': '赛博朋克，霓虹灯，未来都市，雨夜，暗色氛围',
                '水彩插画风格': '水彩画风，柔和笔触，粉彩色，插画，温柔',
                '像素风格': '像素风，8位，复古，低分辨率，游戏风',
                '写实摄影风格': '真实光线，高细节，写实摄影，4K'
            }
            enhanced_desc = original_desc
            if style and style in style_prompts:
                style_prompt = style_prompts[style]
                enhanced_desc = f"{original_desc}，{style_prompt}"
            
            return {
                'original': enhanced_desc,
                'enhanced': enhanced_desc,
                'error': str(e)
            }
    
    def _extract_characters_from_description(self, description: str) -> List[str]:
        """从画面描述中提取角色信息
        
        Args:
            description: 画面描述文本
            
        Returns:
            List[str]: 识别出的角色列表
        """
        characters = []
        
        # 常见角色关键词
        character_keywords = ['主角', '奶奶', '男子', '女子', '孩子', '老人', '年轻人']
        
        for keyword in character_keywords:
            if keyword in description:
                characters.append(keyword)
        
        return list(set(characters))  # 去重
    
    def _save_generated_text_to_file(self, enhanced_descriptions):
        """保存生成的文本到项目texts文件夹的prompt文件"""
        try:
            import os
            import json
            from datetime import datetime
            
            # 获取项目根目录
            if hasattr(self, 'project_root') and self.project_root:
                project_root = self.project_root
            else:
                project_root = os.getcwd()
                
            # 构建项目输出目录下的texts文件夹路径
            if 'output' in project_root:
                texts_dir = os.path.join(project_root, "texts")
            else:
                texts_dir = os.path.join(project_root, "output", "new", "texts")
            
            if not os.path.exists(texts_dir):
                os.makedirs(texts_dir)
            
            # 按场景组织数据
            scenes_data = {}
            for desc in enhanced_descriptions:
                scene_name = desc.get('场景', '## 场景一')
                if scene_name not in scenes_data:
                    scenes_data[scene_name] = []
                
                # 从enhanced_descriptions中提取正确的字段
                shot_data = {
                    "shot_number": desc.get('镜头编号', '### 镜头1'),
                    "original_description": desc.get('original', ''),
                    "enhanced_prompt": desc.get('enhanced', '')
                }
                scenes_data[scene_name].append(shot_data)
            
            # 准备保存的数据
            prompt_data = {
                "scenes": scenes_data,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "scene_description_enhancer",
                "version": "2.0"
            }
            
            # 保存到prompt文件
            prompt_file = os.path.join(texts_dir, "prompt.json")
            with open(prompt_file, 'w', encoding='utf-8') as f:
                json.dump(prompt_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"场景增强器生成的优化提示词已保存到: {prompt_file}")
                
        except Exception as e:
            logger.error(f"保存生成文本到文件失败: {e}")