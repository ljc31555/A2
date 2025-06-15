# AI视频生成器 - 重构版

## 项目概述

这是AI视频生成器的重构版本，采用了全新的模块化架构，支持多种AI服务提供商，能够将文本自动转换为高质量的动画视频。

## 新架构特性

### 🏗️ 模块化设计
- **核心层 (Core)**: 统一的服务管理和API接口
- **服务层 (Services)**: 独立的AI服务模块
- **处理器层 (Processors)**: 业务逻辑处理
- **界面层 (GUI)**: 现代化的用户界面

### 🔌 多提供商支持
- **LLM服务**: OpenAI, Anthropic, 本地模型
- **图像生成**: ComfyUI, Pollinations, Stability AI
- **语音合成**: Azure, ElevenLabs, OpenAI TTS
- **语音识别**: Azure, OpenAI Whisper

### ⚡ 异步处理
- 全面支持异步操作
- 非阻塞的用户界面
- 并发任务处理

### 🎨 智能优化
- 自动场景和角色一致性
- 智能提示词优化
- 动态效果生成
- 双重翻译保障 (LLM + 百度翻译)

## 项目结构

```
AI_Video_Generator/
├── src/
│   ├── core/                 # 核心架构
│   │   ├── __init__.py
│   │   ├── api_manager.py     # API管理器
│   │   ├── service_base.py    # 服务基类
│   │   ├── service_manager.py # 服务管理器
│   │   └── app_controller.py  # 应用控制器
│   ├── services/             # AI服务层
│   │   ├── __init__.py
│   │   ├── llm_service.py     # LLM服务
│   │   ├── image_service.py   # 图像生成服务
│   │   └── voice_service.py   # 语音服务
│   ├── processors/           # 处理器层
│   │   ├── __init__.py
│   │   ├── text_processor.py  # 文本处理器
│   │   ├── image_processor.py # 图像处理器
│   │   └── video_processor.py # 视频处理器
│   ├── gui/                  # 用户界面
│   │   ├── new_main_window.py # 新主窗口
│   │   └── ...
│   ├── models/               # 原有模型(兼容)
│   ├── utils/                # 工具模块
│   └── ...
├── main.py                   # 主程序入口
├── requirements_new.txt      # 新依赖列表
└── README_REFACTORED.md      # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
# 安装新的依赖
pip install -r requirements_new.txt
```

### 2. 配置API密钥

在 `config/` 目录下创建或编辑配置文件，添加你的API密钥：

#### LLM配置 (config/llm_config.json)
```json
{
  "llm": {
    "openai": {
      "api_key": "your-openai-api-key",
      "base_url": "https://api.openai.com/v1"
    },
    "anthropic": {
      "api_key": "your-anthropic-api-key"
    }
  },
  "image": {
    "comfyui": {
      "server_url": "http://localhost:8188"
    },
    "stability": {
      "api_key": "your-stability-api-key"
    }
  },
  "voice": {
    "azure": {
      "subscription_key": "your-azure-key",
      "region": "your-region"
    },
    "elevenlabs": {
      "api_key": "your-elevenlabs-key"
    }
  }
}
```

#### 百度翻译配置 (config/baidu_translate_config.py)
```python
# -*- coding: utf-8 -*-
"""
百度翻译API配置文件
请在此文件中填入您的百度翻译API配置信息
"""

# 百度翻译API配置
# 请到 https://fanyi-api.baidu.com/ 申请您的APP ID和密钥
BAIDU_TRANSLATE_CONFIG = {
    # 请将下面的占位符替换为您的实际APP ID
    'app_id': 'your_app_id_here',
    
    # 请将下面的占位符替换为您的实际密钥
    'secret_key': 'your_secret_key_here',
    
    # API URL（通常不需要修改）
    'api_url': 'https://fanyi-api.baidu.com/api/trans/vip/translate'
}
```

### 3. 启动应用

```bash
python main.py
```

## 主要功能

### 📝 文本处理
- 智能文本改写和优化
- 多种输入格式支持
- 自动分镜生成
- 智能中英文翻译 (LLM优先，百度翻译备用)

### 🎬 分镜生成
- AI驱动的场景分析
- 角色和场景一致性
- 多种风格模板

### 🖼️ 图像生成
- 批量图像生成
- 风格一致性保持
- 多分辨率支持

### 🎥 视频合成
- 自动视频剪辑
- 转场效果
- 背景音乐和字幕

### 🎙️ 语音合成
- 多语言支持
- 自然语音生成
- 批量处理

## 使用流程

### 一键生成模式
1. 在"文本处理"标签页输入文本
2. 选择风格和提供商
3. 点击"一键生成视频"
4. 等待处理完成

### 分步骤模式
1. **文本处理**: 输入并优化文本
2. **分镜生成**: 生成详细分镜脚本
3. **图像生成**: 为每个镜头生成图像
4. **视频合成**: 合成最终视频
5. **后期处理**: 添加音效和字幕

## API优先级

系统会按照以下优先级选择API：

### LLM服务
1. OpenAI GPT-4
2. Anthropic Claude
3. 本地模型

### 图像生成
1. ComfyUI (本地)
2. Pollinations (免费)
3. Stability AI

### 语音服务
1. Azure Cognitive Services
2. ElevenLabs
3. OpenAI TTS

## 配置说明

### 图像生成配置
- **尺寸**: 支持多种分辨率
- **步数**: 控制生成质量
- **CFG Scale**: 控制提示词遵循度
- **负面提示词**: 避免不想要的元素

### 视频配置
- **帧率**: 15-60 FPS
- **时长**: 每镜头1-10秒
- **转场**: 多种转场效果
- **音频**: 背景音乐和音量控制

## 故障排除

### 常见问题

1. **服务初始化失败**
   - 检查API密钥配置
   - 确认网络连接
   - 查看日志文件

2. **图像生成失败**
   - 确认ComfyUI服务运行
   - 检查提示词长度
   - 尝试其他提供商

3. **视频合成错误**
   - 确认FFmpeg安装
   - 检查输出目录权限
   - 验证图像文件完整性

### 日志查看

日志文件位于 `logs/system.log`，包含详细的错误信息和调试信息。

## 开发说明

### 添加新的AI服务

1. 在 `services/` 目录创建新服务类
2. 继承 `ServiceBase` 基类
3. 实现必要的接口方法
4. 在 `ServiceManager` 中注册服务

### 自定义处理器

1. 在 `processors/` 目录创建处理器
2. 实现业务逻辑
3. 在 `AppController` 中集成

## 性能优化

- 使用异步处理提高响应速度
- 实现智能缓存减少重复请求
- 支持批量处理提高效率
- 动态资源管理避免内存泄漏

## 更新日志

### v2.1.0 (最新版)
- 优化LLM翻译提示词，增强翻译准确性
- 新增百度翻译作为备用翻译方案
- 改进翻译失败处理机制
- 增强系统稳定性和容错能力

### v2.0.0 (重构版)
- 全新的模块化架构
- 多AI服务提供商支持
- 异步处理和现代化UI
- 智能优化和一致性保持
- 完整的错误处理和日志系统

## 贡献指南

欢迎提交Issue和Pull Request来改进项目。请确保：

1. 遵循现有的代码风格
2. 添加适当的测试
3. 更新相关文档
4. 提供清晰的提交信息

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交GitHub Issue
- 发送邮件至项目维护者

---

**注意**: 这是重构版本，与原版本在架构上有重大变化。建议在使用前仔细阅读本文档。