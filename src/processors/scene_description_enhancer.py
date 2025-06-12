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
    
    def __post_init__(self):
        if self.characters is None:
            self.characters = []
        if self.scenes is None:
            self.scenes = []
    
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
            
            # 获取角色一致性描述
            for char_name in detected_characters:
                char_consistency = self._get_character_consistency(char_name)
                if char_consistency:
                    consistency_info.characters.append(char_consistency)
            
            # 识别场景
            detected_scenes = self._detect_scenes(description)
            
            # 获取场景一致性描述
            for scene_name in detected_scenes:
                scene_consistency = self._get_scene_consistency(scene_name)
                if scene_consistency:
                    consistency_info.scenes.append(scene_consistency)
                    
        except Exception as e:
            logger.error(f"一致性信息提取失败: {e}")
        
        return consistency_info
    
    def _detect_characters(self, description: str, known_characters: List[str] = None) -> List[str]:
        """动态检测描述中的角色"""
        detected = []
        
        # 优先检测已知角色（从参数传入）
        if known_characters:
            for char in known_characters:
                if char in description:
                    detected.append(char)
        
        # 动态加载项目中的所有角色并进行匹配
        project_characters = self._get_all_project_characters()
        for char_name in project_characters:
            if char_name in description and char_name not in detected:
                detected.append(char_name)
        
        return detected
    
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
    
    def __init__(self, llm_api=None):
        # 初始化LLM API
        self.llm_api = llm_api
        
        # 融合策略配置
        self.fusion_strategies = {
            'natural': self._natural_fusion,
            'structured': self._structured_fusion,
            'minimal': self._minimal_fusion,
            'intelligent': self._intelligent_fusion  # 新增智能融合策略
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
            fusion_func = self.fusion_strategies.get(strategy, self._intelligent_fusion)
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
    
    def _natural_fusion(self, content: Dict[str, Any]) -> FusionResult:
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
        
        # 自然地添加一致性信息
        if content['consistency_parts']:
            consistency_text = "，".join(content['consistency_parts'][:2])
            if consistency_text:
                parts.append(f"（{consistency_text}）")
                result.consistency_additions = content['consistency_parts'][:2]
        
        result.enhanced_description = "".join(parts)
        return result
    
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
    
    def _intelligent_fusion(self, content: Dict[str, Any]) -> FusionResult:
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
            return self._natural_fusion(content)
    
    def _llm_enhanced_fusion(self, content: Dict[str, Any]) -> FusionResult:
        """使用LLM进行智能内容融合"""
        result = FusionResult()
        
        # 构建LLM提示词
        original_desc = content['original']
        technical_parts = content['technical_parts']
        consistency_parts = content['consistency_parts']
        
        logger.info("=== 场景增强器LLM辅助生成开始 ===")
        logger.info(f"原始场景描述: {original_desc[:100]}..." if len(original_desc) > 100 else f"原始场景描述: {original_desc}")
        
        # 构建增强提示
        enhancement_prompt = f"""请对以下画面描述进行智能增强，要求：
1. 保持原始描述的核心内容和风格
2. 自然融入提供的技术细节和一致性信息
3. 确保描述流畅自然，避免生硬拼接
4. 控制总长度在50-150字之间

原始描述：{original_desc}

技术细节补充：{', '.join(technical_parts) if technical_parts else '无'}

角色场景一致性：{', '.join(consistency_parts) if consistency_parts else '无'}

请输出增强后的画面描述："""
        
        logger.info("正在调用LLM进行场景描述增强...")
        logger.debug(f"LLM增强提示词: {enhancement_prompt[:200]}...")
        
        try:
            # 调用LLM进行增强
            enhanced_text = self.llm_api.rewrite_text(enhancement_prompt)
            
            if enhanced_text and len(enhanced_text.strip()) > 0:
                enhanced_content = enhanced_text.strip()
                logger.info(f"✓ LLM增强成功完成")
                logger.info(f"  - 原始描述长度: {len(original_desc)} 字符")
                logger.info(f"  - 增强后长度: {len(enhanced_content)} 字符")
                logger.info(f"  - 增强比例: {len(enhanced_content)/len(original_desc):.2f}x")
                logger.info(f"增强后场景描述: {enhanced_content[:150]}..." if len(enhanced_content) > 150 else f"增强后场景描述: {enhanced_content}")
                
                # 保存生成的文本到项目texts文件夹
                self._save_generated_text_to_file(original_desc, enhanced_content)
                logger.info("✓ 增强结果已保存到generate_text.json文件")
                
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
    
    def _save_generated_text_to_file(self, generated_text):
        """保存生成的文本到项目texts文件夹的generate_text文件"""
        try:
            import os
            import json
            from datetime import datetime
            
            # 获取项目根目录
            if hasattr(self, 'project_root') and self.project_root:
                project_root = self.project_root
            else:
                project_root = os.getcwd()
            
            # 构建texts文件夹路径
            texts_dir = os.path.join(project_root, "texts")
            if not os.path.exists(texts_dir):
                os.makedirs(texts_dir)
            
            # 准备保存的数据
            generate_data = {
                "content": generated_text,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "scene_description_enhancer",
                "version": "1.0"
            }
            
            # 保存到generate_text文件
            generate_text_file = os.path.join(texts_dir, "generate_text.json")
            with open(generate_text_file, 'w', encoding='utf-8') as f:
                json.dump(generate_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"场景增强器生成的优化提示词已保存到: {generate_text_file}")
            
        except Exception as e:
            logger.error(f"保存生成文本到文件失败: {e}")
    
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
        if 50 <= length <= 150:  # 理想长度范围
            length_score = 1.0
        elif length < 50:
            length_score = length / 50.0
        else:
            length_score = max(0.5, 200 / length)
        
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
        self.content_fuser = ContentFuser(llm_api=llm_api)  # 传递LLM API给内容融合器
        
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
            
            # 3. 智能内容融合（第二阶段核心功能）
            fusion_result = self.content_fuser.fuse_content(
                original_description, 
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
                    original_description, technical_details, consistency_info, 'natural'
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