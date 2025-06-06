import json
import os

class ConfigManager:
    def __init__(self, config_dir='f:\\AI\\AI_Video_Generator\\config'):
        self.config_dir = config_dir
        self.config_file = os.path.join(self.config_dir, 'llm_config.json')
        self.config = self._load_config()

    def _load_config(self):
        all_models = []
        if os.path.exists(self.config_dir):
            for fname in os.listdir(self.config_dir):
                if fname.startswith("llm_") and fname.endswith(".json"):
                    config_path = os.path.join(self.config_dir, fname)
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Check if the file contains a list of models under the 'models' key
                            if isinstance(data, dict) and "models" in data and isinstance(data["models"], list):
                                all_models.extend(data["models"])
                                print(f"Loaded models list from {fname}")
                            # Check if the file contains a single model configuration object
                            elif isinstance(data, dict) and "name" in data:
                                all_models.append(data)
                                print(f"Loaded single model from {fname}: {data['name']}")
                            else:
                                print(f"Warning: File {fname} does not contain a valid model configuration (missing 'models' list or single model object with 'name').")
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON from {fname}: {e}")
                    except Exception as e:
                        print(f"Error reading file {fname}: {e}")

        # If no config files are found, create a default one
        if not all_models:
             default_config_path = os.path.join(self.config_dir, 'llm_config.json')
             if not os.path.exists(default_config_path):
                default_config = {
                    "models": [
                        {
                            "name": "DefaultModel",
                            "type": "tongyi",
                            "key": "YOUR_API_KEY",
                            "url": "YOUR_API_URL"
                        }
                    ]
                }
                os.makedirs(self.config_dir, exist_ok=True)
                with open(default_config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4)
                all_models.extend(default_config["models"])
                print(f"Created and loaded default config file: {default_config_path}")
             else:
                 # If default exists but no other models, load default
                 try:
                     with open(default_config_path, 'r', encoding='utf-8') as f:
                         default_config = json.load(f)
                         if isinstance(default_config, dict) and "models" in default_config and isinstance(default_config["models"], list):
                             all_models.extend(default_config["models"])
                             print(f"Loaded existing default config file: {default_config_path}")
                         elif isinstance(default_config, dict) and "name" in default_config:
                              all_models.append(default_config)
                              print(f"Loaded existing default config file (single model format): {default_config_path}")
                         else:
                             print(f"Warning: Existing default config file {default_config_path} does not contain a valid model configuration.")
                 except Exception as e:
                     print(f"Error reading default config {default_config_path}: {e}")

        return {"models": all_models}

    def get_model_config(self, model_name):
        # This method remains the same, as it iterates through the 'models' list
        for model in self.config.get("models", []):
            if model.get("name") == model_name:
                return model
        return None

    def save_model_config(self, model_name, model_type, api_key, api_url):
        # Simple implementation: find and update, or add if not found
        models = self.config.get("models", [])
        found = False
        for model in models:
            if model.get("name") == model_name:
                model["type"] = model_type
                model["key"] = api_key
                model["url"] = api_url
                found = True
                break
        if not found:
            models.append({
                "name": model_name,
                "type": model_type,
                "key": api_key,
                "url": api_url
            })
        self.config["models"] = models
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config to {self.config_file}: {e}")
    
    def save_app_settings(self, app_config):
        """保存应用设置到app_settings.json文件"""
        try:
            app_settings_file = os.path.join(self.config_dir, 'app_settings.json')
            
            # 如果文件存在，先读取现有设置
            existing_settings = {}
            if os.path.exists(app_settings_file):
                try:
                    with open(app_settings_file, 'r', encoding='utf-8') as f:
                        existing_settings = json.load(f)
                except Exception as e:
                    print(f"Warning: Could not read existing app settings: {e}")
            
            # 更新设置
            existing_settings.update(app_config)
            
            # 确保目录存在
            os.makedirs(self.config_dir, exist_ok=True)
            
            # 保存设置
            with open(app_settings_file, 'w', encoding='utf-8') as f:
                json.dump(existing_settings, f, indent=4, ensure_ascii=False)
            
            print(f"App settings saved to {app_settings_file}")
            return True
            
        except Exception as e:
            print(f"Error saving app settings: {e}")
            return False

    def save_config(self, config_data):
        """保存配置数据到 app_settings.json 文件。"""
        return self.save_app_settings(config_data)

    def get_models(self):
        return self.config

    def get_model_by_name(self, name):
        for model in self.config.get("models", []):
            if model['name'] == name:
                return model
        return None

    def add_model(self, model):
        if "models" not in self.config:
            self.config["models"] = []
        self.config["models"].append(model)
        self._save_config()

    def remove_model(self, name):
        if "models" in self.config:
            self.config["models"] = [model for model in self.config["models"] if model['name'] != name]
            self._save_config()

    def update_model(self, name, updated_model):
        if "models" in self.config:
            for i, model in enumerate(self.config["models"]):
                if model['name'] == name:
                    self.config["models"][i] = updated_model
                    break
            self._save_config()

    def _save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
    
    # TTS相关配置管理
    def get_tts_config(self):
        """获取TTS配置"""
        tts_config_file = os.path.join(self.config_dir, 'tts_config.json')
        if os.path.exists(tts_config_file):
            try:
                with open(tts_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载TTS配置失败: {e}")
        
        # 返回默认TTS配置
        return self._get_default_tts_config()
    
    def _get_default_tts_config(self):
        """获取默认TTS配置"""
        return {
            'default_engine': 'edge',
            'default_voice': 'zh-CN-XiaoxiaoNeural-Female',
            'default_rate': 1.0,
            'default_volume': 1.0,
            'generate_subtitle': True,
            'output_format': 'mp3',
            'edge_tts': {
                'enabled': True
            },
            'siliconflow': {
                'enabled': False,
                'api_key': '',
                'base_url': 'https://api.siliconflow.cn/v1'
            },
            'audio': {
                'output_dir': 'audio',
                'subtitle_dir': 'subtitles'
            }
        }
    
    def save_tts_config(self, config):
        """保存TTS配置"""
        tts_config_file = os.path.join(self.config_dir, 'tts_config.json')
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(tts_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存TTS配置失败: {e}")
    
    def get_tts_setting(self, key, default=None):
        """获取TTS配置项"""
        config = self.get_tts_config()
        keys = key.split('.')
        value = config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_tts_setting(self, key, value):
        """设置TTS配置项"""
        config = self.get_tts_config()
        keys = key.split('.')
        
        # 导航到目标位置
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # 设置值
        current[keys[-1]] = value
        
        # 保存配置
        self.save_tts_config(config)
    
    def get_audio_output_dir(self):
        """获取音频输出目录"""
        output_dir = self.get_tts_setting('audio.output_dir', 'audio')
        # 转换为绝对路径
        if not os.path.isabs(output_dir):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            output_dir = os.path.join(base_dir, output_dir)
        
        # 确保目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        return output_dir
    
    def get_subtitle_output_dir(self):
        """获取字幕输出目录"""
        output_dir = self.get_tts_setting('audio.subtitle_dir', 'subtitles')
        # 转换为绝对路径
        if not os.path.isabs(output_dir):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            output_dir = os.path.join(base_dir, output_dir)
        
        # 确保目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        return output_dir