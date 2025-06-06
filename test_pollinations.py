#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Pollinations AI 集成
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.pollinations_client import PollinationsClient
from models.image_generation_service import ImageGenerationService, ImageGenerationEngine

def test_pollinations_client():
    """测试 Pollinations 客户端"""
    print("=== 测试 Pollinations 客户端 ===")
    
    client = PollinationsClient()
    
    # 测试连接
    print("测试连接...")
    if client.test_connection():
        print("✅ 连接成功")
    else:
        print("❌ 连接失败")
        return
    
    # 测试生成图片
    print("\n测试生成图片...")
    prompt = "一只可爱的小猫坐在花园里，阳光明媚，高质量，4K"
    
    try:
        image_paths = client.generate_image(prompt)
        if image_paths and image_paths[0]:
            print(f"✅ 图片生成成功: {image_paths[0]}")
        else:
            print("❌ 图片生成失败")
    except Exception as e:
        print(f"❌ 生成图片时出错: {e}")

def test_image_generation_service():
    """测试统一图像生成服务"""
    print("\n=== 测试统一图像生成服务 ===")
    
    service = ImageGenerationService()
    
    # 测试服务可用性
    print("测试服务可用性...")
    if service.is_service_available():
        print(f"✅ 服务可用，当前引擎: {service.current_engine.value}")
    else:
        print("❌ 服务不可用")
        return
    
    # 测试生成图片
    print("\n测试生成图片...")
    prompt = "一朵美丽的玫瑰花，微距摄影，柔和光线"
    
    try:
        image_paths = service.generate_image(prompt)
        if image_paths and image_paths[0]:
            print(f"✅ 图片生成成功: {image_paths[0]}")
        else:
            print("❌ 图片生成失败")
    except Exception as e:
        print(f"❌ 生成图片时出错: {e}")
    
    # 测试引擎信息
    print("\n获取引擎信息...")
    try:
        info = service.get_engine_info()
        print(f"引擎信息: {info}")
    except Exception as e:
        print(f"获取引擎信息失败: {e}")

if __name__ == "__main__":
    print("Pollinations AI 集成测试")
    print("=" * 50)
    
    test_pollinations_client()
    test_image_generation_service()
    
    print("\n测试完成！")