#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动备份脚本 - AI视频生成器项目

功能：
1. 自动备份重要的项目文件
2. 创建带时间戳的备份目录
3. 支持增量备份和完整备份
4. 清理过期的备份文件

使用方法：
1. 直接运行：python auto_backup.py
2. 定时任务：可以设置Windows任务计划程序定期运行
"""

import os
import shutil
import datetime
import json
import hashlib
import argparse
from pathlib import Path

class AutoBackup:
    def __init__(self, project_root=None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.backup_root = self.project_root / "backups"
        self.config_file = self.project_root / "backup_config.json"
        
        # 默认配置
        self.default_config = {
            "important_files": [
                "src/gui/ai_drawing_tab.py",
                "src/gui/main_window.py",
                "src/models/image_generation_service.py",
                "src/models/image_generation_thread.py",
                "src/services/pollinations_service.py",
                "main.py",
                "requirements.txt",
                "README.md"
            ],
            "important_dirs": [
                "src/gui",
                "src/models",
                "src/services",
                "config"
            ],
            "exclude_patterns": [
                "__pycache__",
                "*.pyc",
                "*.log",
                "*.tmp",
                ".git",
                "backups",
                "output",
                "temp"
            ],
            "max_backups": 30,  # 保留最近30个备份
            "backup_types": {
                "daily": True,
                "before_major_changes": True,
                "manual": True
            }
        }
        
        self.load_config()
    
    def load_config(self):
        """加载备份配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                # 合并默认配置
                for key, value in self.default_config.items():
                    if key not in self.config:
                        self.config[key] = value
            except Exception as e:
                print(f"⚠️ 配置文件加载失败，使用默认配置: {e}")
                self.config = self.default_config.copy()
        else:
            self.config = self.default_config.copy()
            self.save_config()
    
    def save_config(self):
        """保存备份配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 配置文件保存失败: {e}")
    
    def get_file_hash(self, file_path):
        """计算文件MD5哈希值"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None
    
    def should_exclude(self, path):
        """检查路径是否应该被排除"""
        path_str = str(path)
        for pattern in self.config["exclude_patterns"]:
            if pattern in path_str:
                return True
        return False
    
    def create_backup(self, backup_type="manual", description=""):
        """创建备份"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{backup_type}_{timestamp}"
        if description:
            backup_name += f"_{description}"
        
        backup_dir = self.backup_root / backup_name
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🔄 开始创建备份: {backup_name}")
        
        # 创建备份信息文件
        backup_info = {
            "timestamp": timestamp,
            "type": backup_type,
            "description": description,
            "files": [],
            "total_size": 0
        }
        
        total_files = 0
        total_size = 0
        
        # 备份重要文件
        for file_path in self.config["important_files"]:
            src_path = self.project_root / file_path
            if src_path.exists() and not self.should_exclude(src_path):
                dst_path = backup_dir / file_path
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    shutil.copy2(src_path, dst_path)
                    file_size = src_path.stat().st_size
                    file_hash = self.get_file_hash(src_path)
                    
                    backup_info["files"].append({
                        "path": file_path,
                        "size": file_size,
                        "hash": file_hash
                    })
                    
                    total_files += 1
                    total_size += file_size
                    print(f"  ✅ {file_path}")
                except Exception as e:
                    print(f"  ❌ {file_path}: {e}")
        
        # 备份重要目录
        for dir_path in self.config["important_dirs"]:
            src_dir = self.project_root / dir_path
            if src_dir.exists() and src_dir.is_dir():
                dst_dir = backup_dir / dir_path
                
                try:
                    for root, dirs, files in os.walk(src_dir):
                        # 过滤排除的目录
                        dirs[:] = [d for d in dirs if not self.should_exclude(Path(root) / d)]
                        
                        for file in files:
                            src_file = Path(root) / file
                            if not self.should_exclude(src_file):
                                rel_path = src_file.relative_to(self.project_root)
                                dst_file = backup_dir / rel_path
                                dst_file.parent.mkdir(parents=True, exist_ok=True)
                                
                                try:
                                    shutil.copy2(src_file, dst_file)
                                    file_size = src_file.stat().st_size
                                    total_files += 1
                                    total_size += file_size
                                except Exception as e:
                                    print(f"  ❌ {rel_path}: {e}")
                    
                    print(f"  ✅ {dir_path}/ (目录)")
                except Exception as e:
                    print(f"  ❌ {dir_path}/: {e}")
        
        backup_info["total_files"] = total_files
        backup_info["total_size"] = total_size
        
        # 保存备份信息
        info_file = backup_dir / "backup_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 备份完成！")
        print(f"   📁 备份位置: {backup_dir}")
        print(f"   📊 文件数量: {total_files}")
        print(f"   💾 总大小: {self.format_size(total_size)}")
        
        # 清理过期备份
        self.cleanup_old_backups()
        
        return backup_dir
    
    def cleanup_old_backups(self):
        """清理过期的备份"""
        if not self.backup_root.exists():
            return
        
        backups = []
        for backup_dir in self.backup_root.iterdir():
            if backup_dir.is_dir():
                info_file = backup_dir / "backup_info.json"
                if info_file.exists():
                    try:
                        with open(info_file, 'r', encoding='utf-8') as f:
                            info = json.load(f)
                        backups.append((backup_dir, info["timestamp"]))
                    except Exception:
                        # 如果无法读取信息文件，使用目录修改时间
                        backups.append((backup_dir, backup_dir.stat().st_mtime))
        
        # 按时间排序，保留最新的
        backups.sort(key=lambda x: x[1], reverse=True)
        
        if len(backups) > self.config["max_backups"]:
            to_remove = backups[self.config["max_backups"]:]
            print(f"🧹 清理过期备份 ({len(to_remove)} 个)...")
            
            for backup_dir, _ in to_remove:
                try:
                    shutil.rmtree(backup_dir)
                    print(f"  🗑️ 已删除: {backup_dir.name}")
                except Exception as e:
                    print(f"  ❌ 删除失败 {backup_dir.name}: {e}")
    
    def list_backups(self):
        """列出所有备份"""
        if not self.backup_root.exists():
            print("📁 暂无备份")
            return
        
        backups = []
        for backup_dir in self.backup_root.iterdir():
            if backup_dir.is_dir():
                info_file = backup_dir / "backup_info.json"
                if info_file.exists():
                    try:
                        with open(info_file, 'r', encoding='utf-8') as f:
                            info = json.load(f)
                        backups.append((backup_dir.name, info))
                    except Exception:
                        # 如果无法读取信息文件，显示基本信息
                        stat = backup_dir.stat()
                        backups.append((backup_dir.name, {
                            "timestamp": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y%m%d_%H%M%S"),
                            "type": "unknown",
                            "description": "信息文件损坏",
                            "total_files": "未知",
                            "total_size": "未知"
                        }))
        
        if not backups:
            print("📁 暂无备份")
            return
        
        backups.sort(key=lambda x: x[1]["timestamp"], reverse=True)
        
        print(f"📋 备份列表 (共 {len(backups)} 个):")
        print("-" * 80)
        
        for name, info in backups:
            timestamp = info["timestamp"]
            backup_type = info.get("type", "unknown")
            description = info.get("description", "")
            total_files = info.get("total_files", "未知")
            total_size = info.get("total_size", 0)
            
            size_str = self.format_size(total_size) if isinstance(total_size, (int, float)) else str(total_size)
            
            print(f"📦 {name}")
            print(f"   ⏰ 时间: {timestamp[:8]}-{timestamp[9:11]}:{timestamp[11:13]}:{timestamp[13:15]}")
            print(f"   🏷️ 类型: {backup_type}")
            if description:
                print(f"   📝 描述: {description}")
            print(f"   📊 文件: {total_files} 个, 大小: {size_str}")
            print()
    
    def restore_backup(self, backup_name, target_dir=None):
        """恢复备份"""
        backup_dir = self.backup_root / backup_name
        if not backup_dir.exists():
            print(f"❌ 备份不存在: {backup_name}")
            return False
        
        if target_dir is None:
            target_dir = self.project_root
        else:
            target_dir = Path(target_dir)
        
        print(f"🔄 开始恢复备份: {backup_name}")
        print(f"📁 目标目录: {target_dir}")
        
        # 确认操作
        response = input("⚠️ 这将覆盖现有文件，确定继续吗？(y/N): ")
        if response.lower() != 'y':
            print("❌ 操作已取消")
            return False
        
        try:
            # 复制备份文件到目标目录
            for item in backup_dir.iterdir():
                if item.name == "backup_info.json":
                    continue
                
                src_path = item
                dst_path = target_dir / item.name
                
                if src_path.is_file():
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_path, dst_path)
                    print(f"  ✅ {item.name}")
                elif src_path.is_dir():
                    if dst_path.exists():
                        shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
                    print(f"  ✅ {item.name}/ (目录)")
            
            print(f"✅ 备份恢复完成！")
            return True
            
        except Exception as e:
            print(f"❌ 恢复失败: {e}")
            return False
    
    @staticmethod
    def format_size(size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"

def main():
    parser = argparse.ArgumentParser(description="AI视频生成器自动备份工具")
    parser.add_argument("action", choices=["backup", "list", "restore"], help="操作类型")
    parser.add_argument("--type", default="manual", help="备份类型 (manual, daily, before_major_changes)")
    parser.add_argument("--description", default="", help="备份描述")
    parser.add_argument("--name", help="备份名称 (用于恢复)")
    parser.add_argument("--target", help="恢复目标目录")
    
    args = parser.parse_args()
    
    backup_tool = AutoBackup()
    
    if args.action == "backup":
        backup_tool.create_backup(args.type, args.description)
    elif args.action == "list":
        backup_tool.list_backups()
    elif args.action == "restore":
        if not args.name:
            print("❌ 请指定要恢复的备份名称 (--name)")
            return
        backup_tool.restore_backup(args.name, args.target)

if __name__ == "__main__":
    # 如果没有命令行参数，进入交互模式
    import sys
    if len(sys.argv) == 1:
        backup_tool = AutoBackup()
        
        print("🔧 AI视频生成器自动备份工具")
        print("=" * 40)
        print("1. 创建备份")
        print("2. 查看备份列表")
        print("3. 恢复备份")
        print("4. 退出")
        
        while True:
            try:
                choice = input("\n请选择操作 (1-4): ").strip()
                
                if choice == "1":
                    backup_type = input("备份类型 (manual/daily/before_major_changes) [manual]: ").strip() or "manual"
                    description = input("备份描述 (可选): ").strip()
                    backup_tool.create_backup(backup_type, description)
                
                elif choice == "2":
                    backup_tool.list_backups()
                
                elif choice == "3":
                    backup_tool.list_backups()
                    backup_name = input("\n请输入要恢复的备份名称: ").strip()
                    if backup_name:
                        backup_tool.restore_backup(backup_name)
                
                elif choice == "4":
                    print("👋 再见！")
                    break
                
                else:
                    print("❌ 无效选择，请输入 1-4")
                    
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 发生错误: {e}")
    else:
        main()