#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试界面增强和性能优化组件
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """测试所有组件导入"""
    print("🧪 开始测试界面增强和性能优化组件...")
    
    # 测试通知系统
    try:
        from gui.notification_system import NotificationType, NotificationWidget
        print("✅ 通知系统导入成功")
    except Exception as e:
        print(f"❌ 通知系统导入失败: {e}")
    
    # 测试加载管理器
    try:
        from gui.loading_manager import LoadingType, LoadingManager
        print("✅ 加载管理器导入成功")
    except Exception as e:
        print(f"❌ 加载管理器导入失败: {e}")
    
    # 测试性能优化工具
    try:
        from utils.performance_optimizer import LRUCache, ImageCache, PerformanceOptimizer
        print("✅ 性能优化工具导入成功")
    except Exception as e:
        print(f"❌ 性能优化工具导入失败: {e}")
    
    # 测试错误处理器
    try:
        from utils.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
        print("✅ 错误处理器导入成功")
    except Exception as e:
        print(f"❌ 错误处理器导入失败: {e}")
    
    # 测试样式系统
    try:
        from gui.modern_styles import StyleManager, ThemeType, ColorScheme
        print("✅ 样式系统导入成功")
    except Exception as e:
        print(f"❌ 样式系统导入失败: {e}")

def test_basic_functionality():
    """测试基本功能"""
    print("\n🔧 测试基本功能...")
    
    try:
        # 测试LRU缓存
        from utils.performance_optimizer import LRUCache
        cache = LRUCache(max_size=10)
        cache.put("test", "value")
        result = cache.get("test")
        assert result == "value"
        print("✅ LRU缓存功能正常")
    except Exception as e:
        print(f"❌ LRU缓存测试失败: {e}")
    
    try:
        # 测试错误分类
        from utils.error_handler import ErrorClassifier, ErrorCategory
        classifier = ErrorClassifier()
        category = classifier.classify_error(ConnectionError("网络错误"))
        assert category == ErrorCategory.NETWORK
        print("✅ 错误分类功能正常")
    except Exception as e:
        print(f"❌ 错误分类测试失败: {e}")
    
    try:
        # 测试主题系统
        from gui.modern_styles import ModernThemes
        light_theme = ModernThemes.get_light_theme()
        dark_theme = ModernThemes.get_dark_theme()
        assert light_theme.name == "Light"
        assert dark_theme.name == "Dark"
        print("✅ 主题系统功能正常")
    except Exception as e:
        print(f"❌ 主题系统测试失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("AI视频生成系统 - 界面增强和性能优化组件测试")
    print("=" * 60)
    
    test_imports()
    test_basic_functionality()
    
    print("\n🎉 测试完成！")
    print("\n📋 组件功能概览:")
    print("• 现代化通知系统 - 美观的用户反馈")
    print("• 智能加载管理器 - 统一的加载状态管理")
    print("• 性能优化工具 - 图片缓存和内存管理")
    print("• 智能错误处理 - 自动分类和用户友好提示")
    print("• 现代化样式系统 - 深色/浅色主题支持")
    
    print("\n🚀 使用方法:")
    print("1. 导入所需组件")
    print("2. 参考 docs/UI_ENHANCEMENTS_GUIDE.md 获取详细使用指南")
    print("3. 查看 src/gui/enhanced_main_window.py 获取集成示例")

if __name__ == "__main__":
    main() 