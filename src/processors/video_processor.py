#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频处理器
基于新的服务架构的视频生成和处理功能
"""

import os
import asyncio
import json
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from pathlib import Path

from utils.logger import logger
from core.service_manager import ServiceManager, ServiceType
from core.service_base import ServiceResult
from processors.text_processor import StoryboardResult
from processors.image_processor import BatchImageResult, ImageResult

@dataclass
class VideoConfig:
    """视频生成配置"""
    fps: int = 24
    duration_per_shot: float = 3.0
    resolution: tuple = (1920, 1080)
    codec: str = "libx264"
    bitrate: str = "5M"
    audio_codec: str = "aac"
    audio_bitrate: str = "128k"
    transition_type: str = "fade"  # fade, cut, dissolve, slide
    transition_duration: float = 0.5
    background_music: Optional[str] = None
    background_music_volume: float = 0.3
    
@dataclass
class AudioTrack:
    """音频轨道"""
    file_path: str
    start_time: float
    duration: float
    volume: float = 1.0
    fade_in: float = 0.0
    fade_out: float = 0.0
    track_type: str = "voice"  # voice, music, sfx
    
@dataclass
class VideoClip:
    """视频片段"""
    shot_id: int
    image_path: str
    start_time: float
    duration: float
    audio_tracks: List[AudioTrack]
    effects: List[Dict[str, Any]]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.audio_tracks is None:
            self.audio_tracks = []
        if self.effects is None:
            self.effects = []

@dataclass
class VideoProject:
    """视频项目"""
    clips: List[VideoClip]
    config: VideoConfig
    total_duration: float
    output_path: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class VideoProcessor:
    """视频处理器"""
    
    def __init__(self, service_manager: ServiceManager, output_dir: str = "output/videos"):
        self.service_manager = service_manager
        self.output_dir = Path(output_dir)
        # 不自动创建目录，假设目录已存在
        
        # 默认配置
        self.default_config = VideoConfig()
        
        # 转场效果配置
        self.transition_effects = {
            "fade": {"type": "fade", "duration": 0.5},
            "cut": {"type": "cut", "duration": 0.0},
            "dissolve": {"type": "dissolve", "duration": 0.8},
            "slide_left": {"type": "slide", "direction": "left", "duration": 1.0},
            "slide_right": {"type": "slide", "direction": "right", "duration": 1.0},
            "zoom_in": {"type": "zoom", "direction": "in", "duration": 1.2},
            "zoom_out": {"type": "zoom", "direction": "out", "duration": 1.2}
        }
        
        # 视觉效果预设
        self.visual_effects = {
            "ken_burns": {"type": "ken_burns", "zoom_factor": 1.2, "pan_direction": "random"},
            "parallax": {"type": "parallax", "layers": 3, "speed_factor": 0.5},
            "particle": {"type": "particle", "particle_type": "snow", "density": 50},
            "color_grade": {"type": "color_grade", "preset": "cinematic"},
            "vignette": {"type": "vignette", "strength": 0.3},
            "film_grain": {"type": "film_grain", "strength": 0.2}
        }
        
        logger.info(f"视频处理器初始化完成，输出目录: {self.output_dir}")
    
    async def create_video_from_storyboard(self, storyboard: StoryboardResult, 
                                         image_results: BatchImageResult,
                                         config: VideoConfig = None,
                                         progress_callback: Callable = None) -> VideoProject:
        """从分镜和图像创建视频项目"""
        try:
            if config is None:
                config = self.default_config
            
            logger.info(f"开始创建视频项目，共 {len(storyboard.shots)} 个镜头")
            
            # 创建视频片段
            clips = []
            current_time = 0.0
            
            # 创建图像路径映射
            image_map = {result.shot_id: result.image_path for result in image_results.results}
            
            for i, shot in enumerate(storyboard.shots):
                if progress_callback:
                    progress_callback(i / len(storyboard.shots), f"处理镜头 {i+1}/{len(storyboard.shots)}...")
                
                # 获取对应的图像
                image_path = image_map.get(shot.shot_id)
                if not image_path or not os.path.exists(image_path):
                    logger.warning(f"镜头 {shot.shot_id} 的图像不存在，跳过")
                    continue
                
                # 创建音频轨道
                audio_tracks = []
                if shot.dialogue:
                    # 生成语音
                    voice_result = await self._generate_voice_for_shot(shot, config)
                    if voice_result:
                        audio_tracks.append(voice_result)
                
                # 创建视觉效果
                effects = self._create_shot_effects(shot, config)
                
                # 创建视频片段
                clip = VideoClip(
                    shot_id=shot.shot_id,
                    image_path=image_path,
                    start_time=current_time,
                    duration=shot.duration,
                    audio_tracks=audio_tracks,
                    effects=effects,
                    metadata={
                        "scene": shot.scene,
                        "characters": shot.characters,
                        "action": shot.action,
                        "dialogue": shot.dialogue,
                        "camera_angle": shot.camera_angle,
                        "lighting": shot.lighting,
                        "mood": shot.mood
                    }
                )
                
                clips.append(clip)
                current_time += shot.duration
            
            # 创建输出路径
            import time
            output_filename = f"video_{int(time.time())}.mp4"
            output_path = self.output_dir / output_filename
            
            project = VideoProject(
                clips=clips,
                config=config,
                total_duration=current_time,
                output_path=str(output_path),
                metadata={
                    "storyboard_style": storyboard.style,
                    "total_shots": len(clips),
                    "characters": storyboard.characters,
                    "scenes": storyboard.scenes,
                    "creation_time": time.time()
                }
            )
            
            if progress_callback:
                progress_callback(1.0, "视频项目创建完成")
            
            logger.info(f"视频项目创建完成，总时长: {current_time:.1f}秒")
            return project
            
        except Exception as e:
            logger.error(f"创建视频项目失败: {e}")
            raise
    
    async def _generate_voice_for_shot(self, shot, config: VideoConfig) -> Optional[AudioTrack]:
        """为镜头生成语音"""
        try:
            if not shot.dialogue:
                return None
            
            # 调用语音服务
            result = await self.service_manager.execute_service_method(
                ServiceType.VOICE,
                "text_to_speech",
                text=shot.dialogue,
                voice_id="default",
                speed=1.0,
                pitch=1.0
            )
            
            if not result.success:
                logger.warning(f"镜头 {shot.shot_id} 语音生成失败: {result.error}")
                return None
            
            audio_path = result.data.get('audio_path')
            if not audio_path:
                logger.warning(f"镜头 {shot.shot_id} 语音生成结果中没有音频路径")
                return None
            
            return AudioTrack(
                file_path=audio_path,
                start_time=0.0,
                duration=shot.duration,
                volume=1.0,
                track_type="voice"
            )
            
        except Exception as e:
            logger.error(f"生成镜头 {shot.shot_id} 语音失败: {e}")
            return None
    
    def _create_shot_effects(self, shot, config: VideoConfig) -> List[Dict[str, Any]]:
        """为镜头创建视觉效果"""
        effects = []
        
        # 根据镜头信息添加效果
        if shot.camera_angle == "特写":
            effects.append(self.visual_effects["ken_burns"].copy())
        elif shot.camera_angle == "远景":
            effects.append(self.visual_effects["parallax"].copy())
        
        # 根据情绪添加效果
        if shot.mood in ["紧张", "恐怖"]:
            effects.append(self.visual_effects["vignette"].copy())
        elif shot.mood in ["梦幻", "回忆"]:
            effects.append(self.visual_effects["film_grain"].copy())
        
        # 根据场景添加效果
        if "雪" in shot.scene or "冬" in shot.scene:
            particle_effect = self.visual_effects["particle"].copy()
            particle_effect["particle_type"] = "snow"
            effects.append(particle_effect)
        elif "雨" in shot.scene:
            particle_effect = self.visual_effects["particle"].copy()
            particle_effect["particle_type"] = "rain"
            effects.append(particle_effect)
        
        return effects
    
    async def render_video(self, project: VideoProject, 
                         progress_callback: Callable = None) -> str:
        """渲染视频"""
        try:
            logger.info(f"开始渲染视频: {project.output_path}")
            
            if progress_callback:
                progress_callback(0.0, "准备渲染...")
            
            # 准备渲染参数
            render_params = {
                "clips": [
                    {
                        "image_path": clip.image_path,
                        "start_time": clip.start_time,
                        "duration": clip.duration,
                        "audio_tracks": [
                            {
                                "file_path": track.file_path,
                                "start_time": track.start_time,
                                "duration": track.duration,
                                "volume": track.volume,
                                "fade_in": track.fade_in,
                                "fade_out": track.fade_out
                            }
                            for track in clip.audio_tracks
                        ],
                        "effects": clip.effects
                    }
                    for clip in project.clips
                ],
                "config": {
                    "fps": project.config.fps,
                    "resolution": project.config.resolution,
                    "codec": project.config.codec,
                    "bitrate": project.config.bitrate,
                    "audio_codec": project.config.audio_codec,
                    "audio_bitrate": project.config.audio_bitrate,
                    "transition_type": project.config.transition_type,
                    "transition_duration": project.config.transition_duration
                },
                "output_path": project.output_path,
                "background_music": project.config.background_music,
                "background_music_volume": project.config.background_music_volume
            }
            
            # 调用视频渲染服务
            result = await self.service_manager.execute_service_method(
                ServiceType.VIDEO,
                "render_video",
                **render_params
            )
            
            if not result.success:
                raise Exception(f"视频渲染失败: {result.error}")
            
            if progress_callback:
                progress_callback(1.0, "视频渲染完成")
            
            logger.info(f"视频渲染完成: {project.output_path}")
            return project.output_path
            
        except Exception as e:
            logger.error(f"视频渲染失败: {e}")
            raise
    
    async def create_animated_video(self, image_results: BatchImageResult,
                                  config: VideoConfig = None,
                                  animation_type: str = "ken_burns",
                                  progress_callback: Callable = None) -> str:
        """创建动画视频（图像到动画）"""
        try:
            if config is None:
                config = self.default_config
            
            logger.info(f"开始创建动画视频，动画类型: {animation_type}")
            
            # 创建输出路径
            import time
            output_filename = f"animated_{int(time.time())}.mp4"
            output_path = self.output_dir / output_filename
            
            # 准备动画参数
            animation_params = {
                "images": [
                    {
                        "path": result.image_path,
                        "duration": config.duration_per_shot,
                        "prompt": result.prompt
                    }
                    for result in image_results.results
                ],
                "animation_type": animation_type,
                "fps": config.fps,
                "resolution": config.resolution,
                "output_path": str(output_path)
            }
            
            if progress_callback:
                progress_callback(0.1, "开始图像动画化...")
            
            # 调用动画生成服务
            result = await self.service_manager.execute_service_method(
                ServiceType.VIDEO,
                "create_animation",
                **animation_params
            )
            
            if not result.success:
                raise Exception(f"动画创建失败: {result.error}")
            
            if progress_callback:
                progress_callback(1.0, "动画视频创建完成")
            
            logger.info(f"动画视频创建完成: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"创建动画视频失败: {e}")
            raise
    
    async def add_background_music(self, video_path: str, music_path: str, 
                                 volume: float = 0.3, fade_in: float = 2.0,
                                 fade_out: float = 2.0) -> str:
        """添加背景音乐"""
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
            
            if not os.path.exists(music_path):
                raise FileNotFoundError(f"音乐文件不存在: {music_path}")
            
            # 创建输出路径
            import time
            output_filename = f"with_music_{int(time.time())}.mp4"
            output_path = self.output_dir / output_filename
            
            result = await self.service_manager.execute_service_method(
                ServiceType.VIDEO,
                "add_background_music",
                video_path=video_path,
                music_path=music_path,
                output_path=str(output_path),
                volume=volume,
                fade_in=fade_in,
                fade_out=fade_out
            )
            
            if not result.success:
                raise Exception(f"添加背景音乐失败: {result.error}")
            
            logger.info(f"背景音乐添加完成: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"添加背景音乐失败: {e}")
            raise
    
    async def add_subtitles(self, video_path: str, storyboard: StoryboardResult,
                          subtitle_style: Dict[str, Any] = None) -> str:
        """添加字幕"""
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
            
            # 默认字幕样式
            if subtitle_style is None:
                from utils.config_manager import ConfigManager
                config_manager = ConfigManager()
                default_font = config_manager.get_setting("default_font_family", "Arial")
                
                subtitle_style = {
                    "font_family": default_font,
                    "font_size": 24,
                    "font_color": "white",
                    "background_color": "black",
                    "background_opacity": 0.7,
                    "position": "bottom",
                    "margin": 50
                }
            
            # 准备字幕数据
            subtitles = []
            current_time = 0.0
            
            for shot in storyboard.shots:
                if shot.dialogue:
                    subtitles.append({
                        "start_time": current_time,
                        "end_time": current_time + shot.duration,
                        "text": shot.dialogue
                    })
                current_time += shot.duration
            
            if not subtitles:
                logger.warning("没有找到对话内容，无法添加字幕")
                return video_path
            
            # 创建输出路径
            import time
            output_filename = f"with_subtitles_{int(time.time())}.mp4"
            output_path = self.output_dir / output_filename
            
            result = await self.service_manager.execute_service_method(
                ServiceType.VIDEO,
                "add_subtitles",
                video_path=video_path,
                subtitles=subtitles,
                style=subtitle_style,
                output_path=str(output_path)
            )
            
            if not result.success:
                raise Exception(f"添加字幕失败: {result.error}")
            
            logger.info(f"字幕添加完成: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"添加字幕失败: {e}")
            raise
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频信息"""
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
            
            # 这里可以使用ffprobe或其他工具获取视频信息
            # 暂时返回基本信息
            file_size = os.path.getsize(video_path)
            
            return {
                "file_path": video_path,
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            return {}
    
    def get_available_transitions(self) -> List[str]:
        """获取可用的转场效果"""
        return list(self.transition_effects.keys())
    
    def get_available_effects(self) -> List[str]:
        """获取可用的视觉效果"""
        return list(self.visual_effects.keys())
    
    def update_config(self, **kwargs):
        """更新默认配置"""
        for key, value in kwargs.items():
            if hasattr(self.default_config, key):
                setattr(self.default_config, key, value)
                logger.info(f"已更新视频配置 {key}: {value}")
    
    def export_project(self, project: VideoProject, format: str = "json") -> str:
        """导出视频项目"""
        try:
            if format.lower() == "json":
                project_data = {
                    "clips": [
                        {
                            "shot_id": clip.shot_id,
                            "image_path": clip.image_path,
                            "start_time": clip.start_time,
                            "duration": clip.duration,
                            "audio_tracks": [
                                {
                                    "file_path": track.file_path,
                                    "start_time": track.start_time,
                                    "duration": track.duration,
                                    "volume": track.volume,
                                    "track_type": track.track_type
                                }
                                for track in clip.audio_tracks
                            ],
                            "effects": clip.effects,
                            "metadata": clip.metadata
                        }
                        for clip in project.clips
                    ],
                    "config": {
                        "fps": project.config.fps,
                        "duration_per_shot": project.config.duration_per_shot,
                        "resolution": project.config.resolution,
                        "codec": project.config.codec,
                        "bitrate": project.config.bitrate,
                        "transition_type": project.config.transition_type,
                        "transition_duration": project.config.transition_duration
                    },
                    "total_duration": project.total_duration,
                    "output_path": project.output_path,
                    "metadata": project.metadata
                }
                
                return json.dumps(project_data, ensure_ascii=False, indent=2)
            
            else:
                raise ValueError(f"不支持的导出格式: {format}")
                
        except Exception as e:
            logger.error(f"导出视频项目失败: {e}")
            raise
    
    def cleanup_old_videos(self, days: int = 30):
        """清理旧视频文件"""
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - (days * 24 * 60 * 60)
            
            deleted_count = 0
            for file_path in self.output_dir.rglob("*.mp4"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
            
            logger.info(f"已清理 {deleted_count} 个旧视频文件")
            
        except Exception as e:
            logger.error(f"清理旧视频文件失败: {e}")