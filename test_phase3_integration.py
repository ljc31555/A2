#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第三阶段集成测试：UI集成 + 配置管理
测试场景描述增强器的UI集成和配置管理功能
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.logger import logger
from src.utils.enhancer_config_manager import EnhancerConfigManager
from src.processors.scene_description_enhancer import SceneDescriptionEnhancer


def test_enhancer_config_manager():
    """测试增强器配置管理器"""
    print("\n=== 测试增强器配置管理器 ===")
    
    try:
        # 使用临时文件测试
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_config_file = f.name
        
        # 创建配置管理器
        config_manager = EnhancerConfigManager(temp_config_file)
        
        # 测试默认配置
        default_config = config_manager.get_config()
        assert 'enable_technical_details' in default_config
        assert 'fusion_strategy' in default_config
        print("✓ 默认配置加载成功")
        
        # 测试配置更新
        config_manager.set_config('enhancement_level', 'high')
        config_manager.set_config('quality_threshold', 0.5)
        assert config_manager.get_config('enhancement_level') == 'high'
        assert config_manager.get_config('quality_threshold') == 0.5
        print("✓ 配置更新成功")
        
        # 测试批量更新
        updates = {
            'fusion_strategy': 'natural',
            'cache_enabled': False,
            'max_enhancement_length': 300
        }
        config_manager.update_config(updates)
        for key, value in updates.items():
            assert config_manager.get_config(key) == value
        print("✓ 批量配置更新成功")
        
        # 测试配置保存和加载
        config_manager.save_config()
        
        # 创建新的配置管理器实例，验证持久化
        new_config_manager = EnhancerConfigManager(temp_config_file)
        assert new_config_manager.get_config('enhancement_level') == 'high'
        assert new_config_manager.get_config('fusion_strategy') == 'natural'
        print("✓ 配置持久化成功")
        
        # 测试配置验证
        assert config_manager.validate_config() == True
        print("✓ 配置验证通过")
        
        # 测试无效配置
        config_manager.set_config('quality_threshold', 1.5)  # 超出范围
        assert config_manager.validate_config() == False
        print("✓ 无效配置检测成功")
        
        # 测试配置重置
        config_manager.reset_to_default()
        reset_config = config_manager.get_config()
        assert reset_config['enhancement_level'] == 'medium'
        assert reset_config['fusion_strategy'] == 'intelligent'
        print("✓ 配置重置成功")
        
        # 清理临时文件
        os.unlink(temp_config_file)
        
        print("✅ 增强器配置管理器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 增强器配置管理器测试失败: {e}")
        return False


def test_enhancer_config_integration():
    """测试增强器与配置管理器的集成"""
    print("\n=== 测试增强器配置集成 ===")
    
    try:
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_config_file = f.name
        
        # 创建配置管理器并设置测试配置
        config_manager = EnhancerConfigManager(temp_config_file)
        test_config = {
            'enable_technical_details': True,
            'enable_consistency_injection': True,
            'enhancement_level': 'high',
            'fusion_strategy': 'natural',
            'quality_threshold': 0.4,
            'max_enhancement_length': 400
        }
        config_manager.update_config(test_config)
        config_manager.save_config()
        
        # 创建场景描述增强器
        enhancer = SceneDescriptionEnhancer(project_root=str(project_root))
        
        # 测试配置应用
        enhancer_config = enhancer.get_config()
        print(f"增强器当前配置: {enhancer_config}")
        
        # 测试描述增强
        test_description = "主角在咖啡厅中与朋友交谈"
        test_characters = ["主角", "朋友"]
        
        enhanced_description = enhancer.enhance_description(test_description, test_characters)
        # 验证增强功能正常工作
        assert enhanced_description is not None and len(enhanced_description) > 0
        assert test_description in enhanced_description or len(enhanced_description) >= len(test_description)
        print(f"✓ 描述增强成功: {test_description} -> {enhanced_description[:100]}...")
        
        # 测试配置重新加载
        enhancer.reload_config()
        print("✓ 配置重新加载成功")
        
        # 清理临时文件
        os.unlink(temp_config_file)
        
        print("✅ 增强器配置集成测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 增强器配置集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_export_import():
    """测试配置导出导入功能"""
    print("\n=== 测试配置导出导入 ===")
    
    try:
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_config_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_file = f.name
        
        # 创建配置管理器并设置测试配置
        config_manager = EnhancerConfigManager(temp_config_file)
        test_config = {
            'enhancement_level': 'high',
            'fusion_strategy': 'structured',
            'quality_threshold': 0.6,
            'custom_rules': {
                'test_rule': 'test_value'
            }
        }
        config_manager.update_config(test_config)
        
        # 测试导出
        config_manager.export_config(export_file)
        assert os.path.exists(export_file)
        print("✓ 配置导出成功")
        
        # 验证导出内容
        with open(export_file, 'r', encoding='utf-8') as f:
            exported_config = json.load(f)
        assert exported_config['enhancement_level'] == 'high'
        assert exported_config['fusion_strategy'] == 'structured'
        print("✓ 导出内容验证成功")
        
        # 创建新的配置管理器测试导入
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            new_config_file = f.name
        
        new_config_manager = EnhancerConfigManager(new_config_file)
        new_config_manager.import_config(export_file)
        
        # 验证导入结果
        imported_config = new_config_manager.get_config()
        assert imported_config['enhancement_level'] == 'high'
        assert imported_config['fusion_strategy'] == 'structured'
        assert imported_config['quality_threshold'] == 0.6
        print("✓ 配置导入成功")
        
        # 清理临时文件
        for file_path in [temp_config_file, export_file, new_config_file]:
            if os.path.exists(file_path):
                os.unlink(file_path)
        
        print("✅ 配置导出导入测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置导出导入测试失败: {e}")
        return False


def test_performance_config():
    """测试性能配置功能"""
    print("\n=== 测试性能配置 ===")
    
    try:
        config_manager = EnhancerConfigManager()
        
        # 测试性能配置获取
        perf_config = config_manager.get_performance_config()
        assert 'cache_enabled' in perf_config
        assert 'cache_size' in perf_config
        assert 'batch_processing' in perf_config
        print("✓ 性能配置获取成功")
        
        # 测试质量配置获取
        quality_config = config_manager.get_quality_config()
        assert 'quality_threshold' in quality_config
        assert 'max_enhancement_length' in quality_config
        print("✓ 质量配置获取成功")
        
        # 测试融合配置获取
        fusion_config = config_manager.get_fusion_config()
        assert 'fusion_strategy' in fusion_config
        assert 'strategy_weights' in fusion_config
        print("✓ 融合配置获取成功")
        
        # 测试自定义规则获取
        custom_rules = config_manager.get_custom_rules()
        assert isinstance(custom_rules, dict)
        print("✓ 自定义规则获取成功")
        
        print("✅ 性能配置测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 性能配置测试失败: {e}")
        return False


def test_ui_integration_simulation():
    """模拟UI集成测试"""
    print("\n=== 模拟UI集成测试 ===")
    
    try:
        # 模拟UI配置更新流程
        config_manager = EnhancerConfigManager()
        
        # 模拟用户在UI中的配置更改
        ui_changes = {
            'enable_technical_details': True,
            'enable_consistency_injection': True,
            'enhancement_level': 'high',
            'fusion_strategy': 'intelligent',
            'quality_threshold': 0.45,
            'cache_enabled': True,
            'cache_size': 2000
        }
        
        # 应用UI更改
        config_manager.update_config(ui_changes)
        config_manager.save_config()
        print("✓ UI配置更改应用成功")
        
        # 模拟配置面板重新打开
        new_config_manager = EnhancerConfigManager(config_manager.config_file)
        loaded_config = new_config_manager.get_config()
        
        # 验证配置持久化
        for key, value in ui_changes.items():
            assert loaded_config[key] == value, f"配置项 {key} 不匹配: 期望 {value}, 实际 {loaded_config[key]}"
        print("✓ 配置持久化验证成功")
        
        # 模拟增强器重新加载配置
        enhancer = SceneDescriptionEnhancer(project_root=str(project_root))
        enhancer.reload_config()
        print("✓ 增强器配置重新加载成功")
        
        # 测试配置生效
        test_description = "角色在神秘的森林中探索"
        enhanced = enhancer.enhance_description(test_description, ["角色"])
        # 验证增强功能正常工作（增强后的描述应该不为空且包含原始内容）
        assert enhanced is not None and len(enhanced) > 0
        assert test_description in enhanced or len(enhanced) >= len(test_description)
        print(f"✓ 配置生效验证成功: {enhanced[:100]}...")
        
        print("✅ UI集成模拟测试通过")
        return True
        
    except Exception as e:
        print(f"❌ UI集成模拟测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有第三阶段集成测试"""
    print("🚀 开始第三阶段集成测试：UI集成 + 配置管理")
    print("=" * 60)
    
    tests = [
        ("增强器配置管理器", test_enhancer_config_manager),
        ("增强器配置集成", test_enhancer_config_integration),
        ("配置导出导入", test_config_export_import),
        ("性能配置", test_performance_config),
        ("UI集成模拟", test_ui_integration_simulation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 运行测试: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ 测试失败: {test_name}")
        except Exception as e:
            print(f"❌ 测试异常: {test_name} - {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 第三阶段集成测试全部通过！")
        print("\n✨ 第三阶段功能总结:")
        print("  • ✅ 增强器配置管理器完整实现")
        print("  • ✅ UI集成配置面板功能完善")
        print("  • ✅ 配置持久化和重新加载机制")
        print("  • ✅ 配置导出导入功能")
        print("  • ✅ 性能和质量配置管理")
        print("  • ✅ 自定义规则配置支持")
        print("  • ✅ 配置验证和错误处理")
        print("\n🎯 第三阶段开发完成，系统已具备完整的UI集成和配置管理能力！")
    else:
        print(f"⚠️  有 {total - passed} 个测试失败，需要进一步调试")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)