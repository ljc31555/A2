#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM服务
统一的大语言模型服务，支持多种提供商和模型
"""

import json
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any

from utils.logger import logger
from core.service_base import ServiceBase, ServiceResult
from core.api_manager import APIManager, APIConfig, APIType

class LLMService(ServiceBase):
    """LLM服务类"""
    
    def __init__(self, api_manager: APIManager):
        super().__init__(api_manager, "LLM服务")
        
        # 预设的提示词模板
        self.prompt_templates = {
            'storyboard_generation': """
你是一个专业的影视分镜师。请根据以下文本内容，生成详细的分镜表格。

要求：
1. 每个镜头包含：镜头编号、场景描述、角色、动作、对话、画面描述
2. 场景描述要具体，包含环境、时间、氛围
3. 角色描述要详细，包含外观、表情、动作
4. 画面描述要适合AI绘画，包含构图、光线、风格
5. 输出格式为JSON，包含shots数组

文本内容：
{text}

风格要求：{style}

请生成分镜表格：
""",
            
            'text_rewrite': """
请对以下文本进行改写，要求：
1. 保持原意不变
2. 语言更加生动有趣
3. 适合视频脚本
4. 长度适中

原文：
{text}

改写后的文本：
""",
            
            'prompt_optimization': """
请优化以下AI绘画提示词，要求：
1. 更加详细和具体
2. 包含艺术风格描述
3. 包含技术参数建议
4. 适合Stable Diffusion等模型

原提示词：
{prompt}

风格：{style}

优化后的提示词：
"""
        }
    
    def get_api_type(self) -> APIType:
        return APIType.LLM
    
    async def _execute_request(self, api_config: APIConfig, **kwargs) -> ServiceResult:
        """执行LLM API请求"""
        try:
            prompt = kwargs.get('prompt', '')
            max_tokens = kwargs.get('max_tokens', 2000)
            temperature = kwargs.get('temperature', 0.7)
            
            if not prompt:
                return ServiceResult(success=False, error="提示词不能为空")
            
            # 根据不同提供商构建请求
            if api_config.provider.lower() == 'deepseek':
                response = await self._call_deepseek_api(api_config, prompt, max_tokens, temperature)
            elif api_config.provider.lower() == 'tongyi':
                response = await self._call_tongyi_api(api_config, prompt, max_tokens, temperature)
            elif api_config.provider.lower() == 'zhipu':
                response = await self._call_zhipu_api(api_config, prompt, max_tokens, temperature)
            elif api_config.provider.lower() == 'google':
                response = await self._call_google_api(api_config, prompt, max_tokens, temperature)
            elif api_config.provider.lower() == 'openai':
                response = await self._call_openai_api(api_config, prompt, max_tokens, temperature)
            elif api_config.provider.lower() == 'siliconflow':
                response = await self._call_siliconflow_api(api_config, prompt, max_tokens, temperature)
            else:
                return ServiceResult(success=False, error=f"不支持的提供商: {api_config.provider}")
            
            return ServiceResult(
                success=True,
                data=response,
                metadata={
                    'provider': api_config.provider,
                    'model': api_config.model_name,
                    'tokens_used': response.get('usage', {}).get('total_tokens', 0)
                }
            )
            
        except Exception as e:
            logger.error(f"LLM API请求失败: {e}")
            return ServiceResult(success=False, error=str(e))
    
    async def _call_deepseek_api(self, api_config: APIConfig, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """调用DeepSeek API"""
        headers = {
            'Authorization': f'Bearer {api_config.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': api_config.model_name or 'deepseek-chat',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_config.api_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=api_config.timeout)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        'content': result['choices'][0]['message']['content'],
                        'usage': result.get('usage', {})
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"API请求失败 (状态码: {response.status}): {error_text}")
    
    async def _call_tongyi_api(self, api_config: APIConfig, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """调用通义千问API"""
        headers = {
            'Authorization': f'Bearer {api_config.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': api_config.model_name or 'qwen-turbo',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_config.api_url,
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=api_config.timeout)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        'content': result['choices'][0]['message']['content'],
                        'usage': result.get('usage', {})
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"API请求失败 (状态码: {response.status}): {error_text}")
    
    async def _call_zhipu_api(self, api_config: APIConfig, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """调用智谱AI API"""
        headers = {
            'Authorization': f'Bearer {api_config.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': api_config.model_name or 'glm-4-flash',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_config.api_url,
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=api_config.timeout)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        'content': result['choices'][0]['message']['content'],
                        'usage': result.get('usage', {})
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"API请求失败 (状态码: {response.status}): {error_text}")
    
    async def _call_google_api(self, api_config: APIConfig, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """调用Google Gemini API"""
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            'contents': [{
                'parts': [{'text': prompt}]
            }],
            'generationConfig': {
                'maxOutputTokens': max_tokens,
                'temperature': temperature
            }
        }
        
        url = f"{api_config.api_url}/v1beta/models/{api_config.model_name or 'gemini-1.5-flash'}:generateContent?key={api_config.api_key}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=api_config.timeout)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    return {
                        'content': content,
                        'usage': result.get('usageMetadata', {})
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"API请求失败 (状态码: {response.status}): {error_text}")
    
    async def generate_storyboard(self, text: str, style: str = "电影风格", provider: str = None) -> ServiceResult:
        """生成分镜表格"""
        prompt = self.prompt_templates['storyboard_generation'].format(
            text=text,
            style=style
        )
        
        return await self.execute(
            provider=provider,
            prompt=prompt,
            max_tokens=3000,
            temperature=0.7
        )
    
    async def rewrite_text(self, text: str, provider: str = None) -> ServiceResult:
        """改写文本"""
        prompt = self.prompt_templates['text_rewrite'].format(text=text)
        
        return await self.execute(
            provider=provider,
            prompt=prompt,
            max_tokens=1500,
            temperature=0.8
        )
    
    async def optimize_prompt(self, prompt: str, style: str = "写实风格", provider: str = None) -> ServiceResult:
        """优化绘画提示词"""
        optimization_prompt = self.prompt_templates['prompt_optimization'].format(
            prompt=prompt,
            style=style
        )
        
        return await self.execute(
            provider=provider,
            prompt=optimization_prompt,
            max_tokens=1000,
            temperature=0.6
        )
    
    async def custom_request(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7, provider: str = None) -> ServiceResult:
        """自定义请求"""
        return await self.execute(
            provider=provider,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    async def _call_openai_api(self, api_config: APIConfig, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """调用OpenAI API"""
        headers = {
            'Authorization': f'Bearer {api_config.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': api_config.model_name or 'gpt-3.5-turbo',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        'content': result['choices'][0]['message']['content'],
                        'usage': result.get('usage', {})
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API请求失败 (状态码: {response.status}): {error_text}")
    
    async def _call_siliconflow_api(self, api_config: APIConfig, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """调用SiliconFlow API"""
        headers = {
            'Authorization': f'Bearer {api_config.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': api_config.model_name or 'Qwen/Qwen2.5-7B-Instruct',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        'content': result['choices'][0]['message']['content'],
                        'usage': result.get('usage', {})
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"SiliconFlow API请求失败 (状态码: {response.status}): {error_text}")