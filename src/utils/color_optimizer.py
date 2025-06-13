#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
颜色优化工具
用于处理角色服装颜色，确保每个角色只保留一个主要颜色
"""

import re
from typing import List, Dict, Any, Optional
from .logger import logger

class ColorOptimizer:
    """颜色优化器 - 处理角色服装颜色一致性"""
    
    def __init__(self):
        # 定义颜色优先级（常见的主要颜色）
        self.color_priority = {
            # 基础颜色（高优先级）
            '黑色': 10, '白色': 10, '红色': 9, '蓝色': 9, '绿色': 8,
            '黄色': 8, '紫色': 7, '橙色': 7, '粉色': 6, '灰色': 6,
            '棕色': 5, '褐色': 5, '咖啡色': 5,
            
            # 深浅变化（中优先级）
            '深蓝': 8, '浅蓝': 7, '深红': 8, '浅红': 6,
            '深绿': 7, '浅绿': 6, '深灰': 6, '浅灰': 5,
            '深紫': 6, '浅紫': 5, '深黄': 7, '浅黄': 5,
            
            # 特殊颜色（低优先级）
            '金色': 4, '银色': 4, '米色': 3, '卡其色': 3,
            '青色': 3, '洋红': 3, '橄榄色': 2, '海军蓝': 4,
            '天蓝': 4, '草绿': 3, '玫瑰红': 3
        }
        
        # 颜色关键词模式
        self.color_patterns = [
            r'(深|浅|亮|暗)?(黑|白|红|蓝|绿|黄|紫|橙|粉|灰|棕|褐|咖啡)色?',
            r'(金|银|米|卡其|青|洋红|橄榄|海军蓝|天蓝|草绿|玫瑰红)色?',
            r'(navy|blue|red|green|yellow|purple|orange|pink|gray|brown|black|white|gold|silver)'
        ]
    
    def extract_primary_color(self, color_text: str) -> str:
        """从颜色文本中提取主要颜色
        
        Args:
            color_text: 包含颜色信息的文本
            
        Returns:
            str: 主要颜色
        """
        if not color_text or not isinstance(color_text, str):
            return ""
        
        # 如果是列表格式，先转换为字符串
        if color_text.startswith('[') and color_text.endswith(']'):
            try:
                import ast
                color_list = ast.literal_eval(color_text)
                if isinstance(color_list, list) and color_list:
                    color_text = ', '.join(str(c) for c in color_list)
            except:
                pass
        
        # 提取所有颜色
        colors = self._extract_colors_from_text(color_text)
        
        if not colors:
            return ""
        
        # 如果只有一个颜色，直接返回
        if len(colors) == 1:
            return colors[0]
        
        # 选择优先级最高的颜色
        primary_color = self._select_primary_color(colors)
        
        logger.info(f"从 '{color_text}' 中提取主要颜色: {primary_color}")
        return primary_color
    
    def _extract_colors_from_text(self, text: str) -> List[str]:
        """从文本中提取所有颜色"""
        colors = []
        
        # 先按逗号分割
        parts = [part.strip() for part in text.split(',')]
        
        for part in parts:
            # 使用正则表达式匹配颜色
            for pattern in self.color_patterns:
                matches = re.findall(pattern, part, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        # 处理分组匹配
                        color = ''.join(match).strip()
                    else:
                        color = match.strip()
                    
                    if color and color not in colors:
                        # 标准化颜色名称
                        normalized_color = self._normalize_color_name(color)
                        if normalized_color:
                            colors.append(normalized_color)
        
        return colors
    
    def _normalize_color_name(self, color: str) -> str:
        """标准化颜色名称"""
        color = color.lower().strip()
        
        # 移除"色"字
        if color.endswith('色'):
            color = color[:-1]
        
        # 颜色映射
        color_mapping = {
            'black': '黑色', 'white': '白色', 'red': '红色', 'blue': '蓝色',
            'green': '绿色', 'yellow': '黄色', 'purple': '紫色', 'orange': '橙色',
            'pink': '粉色', 'gray': '灰色', 'grey': '灰色', 'brown': '棕色',
            'gold': '金色', 'silver': '银色', 'navy': '海军蓝',
            '深蓝': '深蓝色', '浅蓝': '浅蓝色', '深红': '深红色', '浅红': '浅红色',
            '深绿': '深绿色', '浅绿': '浅绿色', '深灰': '深灰色', '浅灰': '浅灰色'
        }
        
        # 查找映射
        for key, value in color_mapping.items():
            if key in color or color in key:
                return value
        
        # 如果没有找到映射，检查是否在优先级列表中
        for priority_color in self.color_priority.keys():
            if color in priority_color.lower() or priority_color.lower() in color:
                return priority_color
        
        # 如果都没找到，返回原始颜色（加上"色"字）
        if color and not color.endswith('色'):
            return color + '色'
        
        return color
    
    def _select_primary_color(self, colors: List[str]) -> str:
        """从多个颜色中选择主要颜色"""
        if not colors:
            return ""
        
        if len(colors) == 1:
            return colors[0]
        
        # 按优先级排序
        color_scores = []
        for color in colors:
            score = self.color_priority.get(color, 1)
            color_scores.append((color, score))
        
        # 按分数降序排序
        color_scores.sort(key=lambda x: x[1], reverse=True)
        
        return color_scores[0][0]
    
    def optimize_character_colors(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """优化角色颜色数据
        
        Args:
            character_data: 角色数据字典
            
        Returns:
            Dict[str, Any]: 优化后的角色数据
        """
        try:
            # 复制数据以避免修改原始数据
            optimized_data = character_data.copy()
            
            # 处理服装颜色
            clothing = optimized_data.get('clothing', {})
            if isinstance(clothing, dict):
                colors = clothing.get('colors', [])
                
                # 如果colors是字符串，先转换
                if isinstance(colors, str):
                    primary_color = self.extract_primary_color(colors)
                    if primary_color:
                        clothing['colors'] = [primary_color]
                    else:
                        clothing['colors'] = []
                elif isinstance(colors, list) and len(colors) > 1:
                    # 如果有多个颜色，选择主要颜色
                    color_text = ', '.join(str(c) for c in colors)
                    primary_color = self.extract_primary_color(color_text)
                    if primary_color:
                        clothing['colors'] = [primary_color]
                    else:
                        clothing['colors'] = colors[:1]  # 保留第一个
                
                optimized_data['clothing'] = clothing
            
            return optimized_data
            
        except Exception as e:
            logger.error(f"优化角色颜色失败: {e}")
            return character_data
    
    def get_character_primary_color(self, character_data: Dict[str, Any]) -> str:
        """获取角色的主要服装颜色
        
        Args:
            character_data: 角色数据
            
        Returns:
            str: 主要颜色
        """
        try:
            clothing = character_data.get('clothing', {})
            if isinstance(clothing, dict):
                colors = clothing.get('colors', [])
                
                if isinstance(colors, str):
                    return self.extract_primary_color(colors)
                elif isinstance(colors, list) and colors:
                    return colors[0]  # 返回第一个颜色
            
            return ""
            
        except Exception as e:
            logger.error(f"获取角色主要颜色失败: {e}")
            return ""
    
    def apply_color_consistency_to_description(self, description: str, 
                                             character_name: str, 
                                             primary_color: str) -> str:
        """将颜色一致性应用到描述中
        
        Args:
            description: 原始描述
            character_name: 角色名称
            primary_color: 主要颜色
            
        Returns:
            str: 应用颜色一致性后的描述
        """
        if not description or not character_name or not primary_color:
            return description
        
        try:
            # 查找角色相关的服装描述
            character_patterns = [
                rf'{character_name}.*?(?:穿着|身着|服装|衣服|打扮)',
                rf'(?:穿着|身着|服装|衣服|打扮).*?{character_name}',
                rf'{character_name}.*?(?:的|之).*?(?:服装|衣服|装扮)'
            ]
            
            enhanced_description = description
            
            # 在角色相关的服装描述中强调主要颜色
            for pattern in character_patterns:
                matches = re.finditer(pattern, enhanced_description, re.IGNORECASE)
                for match in matches:
                    original_text = match.group()
                    
                    # 检查是否包含多个颜色
                    existing_colors = [color for color in self.color_priority.keys() if color in original_text]
                    
                    if len(existing_colors) > 1:
                        # 如果有多个颜色，替换为主要颜色
                        enhanced_text = original_text
                        for color in existing_colors:
                            if color != primary_color:
                                enhanced_text = enhanced_text.replace(color, primary_color)
                        enhanced_description = enhanced_description.replace(original_text, enhanced_text)
                    elif len(existing_colors) == 0:
                        # 如果没有颜色描述，添加主要颜色
                        enhanced_text = original_text.replace(
                            '服装', f'{primary_color}服装'
                        ).replace(
                            '衣服', f'{primary_color}衣服'
                        ).replace(
                            '穿着', f'穿着{primary_color}'
                        )
                        enhanced_description = enhanced_description.replace(original_text, enhanced_text)
            
            # 如果没有找到明确的服装描述，在角色名称后添加颜色信息
            if character_name in enhanced_description and primary_color not in enhanced_description:
                enhanced_description = enhanced_description.replace(
                    character_name, 
                    f'{character_name}（身着{primary_color}服装）',
                    1  # 只替换第一次出现
                )
            
            return enhanced_description
            
        except Exception as e:
            logger.error(f"应用颜色一致性失败: {e}")
            return description
    
    def apply_color_consistency(self, description: str, characters: List[str], 
                              character_scene_manager) -> str:
        """应用颜色一致性到场景描述中
        
        Args:
            description: 原始场景描述
            characters: 角色列表
            character_scene_manager: 角色场景管理器
            
        Returns:
            str: 应用颜色一致性后的描述
        """
        if not description or not characters:
            return description
        
        try:
            enhanced_description = description
            
            for character_name in characters:
                # 获取角色数据
                character_data = self._get_character_data_by_name(
                    character_name, character_scene_manager
                )
                
                if character_data:
                    # 获取主要颜色
                    primary_color = self.get_character_primary_color(character_data)
                    
                    if primary_color:
                        # 应用颜色一致性
                        enhanced_description = self.apply_color_consistency_to_description(
                            enhanced_description, character_name, primary_color
                        )
            
            return enhanced_description
            
        except Exception as e:
            logger.error(f"应用颜色一致性失败: {e}")
            return description
    
    def _get_character_data_by_name(self, character_name: str, 
                                   character_scene_manager) -> Optional[Dict[str, Any]]:
        """根据角色名称获取角色数据
        
        Args:
            character_name: 角色名称
            character_scene_manager: 角色场景管理器
            
        Returns:
            Optional[Dict[str, Any]]: 角色数据
        """
        try:
            characters_data = character_scene_manager._load_json(
                character_scene_manager.characters_file
            )
            
            # 查找角色数据
            for char_id, char_data in characters_data.get('characters', {}).items():
                if char_data.get('name') == character_name:
                    return char_data
            
            return None
            
        except Exception as e:
            logger.error(f"获取角色数据失败 {character_name}: {e}")
            return None