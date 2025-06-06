# AI视频生成器 - 配置指南

## 快速开始

### 1. 克隆项目
```bash
git clone <your-repository-url>
cd AI_Video_Generator
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置API密钥

#### 3.1 复制配置文件模板
```bash
# 复制配置文件模板
cp config/app_settings.example.json config/app_settings.json
cp config/llm_config.example.json config/llm_config.json
cp config/tts_config.example.json config/tts_config.json
```

#### 3.2 编辑配置文件

**编辑 `config/app_settings.json`：**
- 将 `YOUR_ZHIPU_API_KEY_HERE` 替换为你的智谱AI API密钥
- 将 `YOUR_TONGYI_API_KEY_HERE` 替换为你的通义千问API密钥
- 将 `YOUR_DEEPSEEK_API_KEY_HERE` 替换为你的Deepseek API密钥
- 将 `YOUR_COMFYUI_OUTPUT_DIR_HERE` 替换为你的ComfyUI输出目录路径

**编辑 `config/llm_config.json`：**
- 同样替换相应的API密钥

**编辑 `config/tts_config.json`：**
- 将 `YOUR_SILICONFLOW_API_KEY_HERE` 替换为你的SiliconFlow API密钥（如果使用）

### 4. API密钥获取方式

#### 智谱AI
1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册并登录账号
3. 在控制台中创建API密钥

#### 通义千问
1. 访问 [阿里云DashScope](https://dashscope.aliyuncs.com/)
2. 注册并登录账号
3. 在控制台中获取API密钥

#### Deepseek
1. 访问 [Deepseek开放平台](https://platform.deepseek.com/)
2. 注册并登录账号
3. 在API密钥页面创建新的密钥

#### SiliconFlow（可选）
1. 访问 [SiliconFlow](https://siliconflow.cn/)
2. 注册并登录账号
3. 在控制台中获取API密钥

### 5. 运行程序
```bash
python main.py
```

## 注意事项

⚠️ **重要安全提醒：**
- 配置文件中的API密钥是敏感信息，请勿将其提交到版本控制系统
- 项目已配置 `.gitignore` 文件来防止意外提交敏感信息
- 请妥善保管你的API密钥，避免泄露

## 故障排除

### 常见问题

1. **API密钥无效**
   - 检查密钥是否正确复制
   - 确认密钥是否已激活
   - 检查账户余额是否充足

2. **ComfyUI连接失败**
   - 确认ComfyUI服务是否正在运行
   - 检查端口号是否正确（默认8188）
   - 确认输出目录路径是否存在

3. **依赖安装失败**
   - 尝试使用虚拟环境
   - 更新pip版本：`pip install --upgrade pip`
   - 如果在中国，可以使用国内镜像源

## 开发者指南

如果你想为这个项目贡献代码：

1. Fork 这个仓库
2. 创建你的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。