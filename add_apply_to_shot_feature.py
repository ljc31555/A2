#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为AI绘图界面添加"应用到分镜"功能
解决用户反映的生成多张图片后，备选图片栏不显示后续生成图片的问题
"""

import os
import re

def add_apply_to_shot_feature():
    """为AI绘图界面添加应用到分镜的功能"""
    
    main_window_path = "f:\\AI\\AI_Video_Generator\\src\\gui\\main_window.py"
    
    if not os.path.exists(main_window_path):
        print(f"文件不存在: {main_window_path}")
        return
    
    # 读取文件内容
    with open(main_window_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 在清空图片库按钮后添加"应用到分镜"按钮
    clear_gallery_pattern = r'(clear_gallery_btn\.clicked\.connect\(self\.clear_image_gallery\)\s+left_layout\.addWidget\(clear_gallery_btn\))'
    
    apply_button_code = '''\1
        
        # 添加应用到分镜按钮
        apply_to_shot_btn = QPushButton("应用到当前分镜")
        apply_to_shot_btn.clicked.connect(self.apply_selected_image_to_shot)
        left_layout.addWidget(apply_to_shot_btn)'''
    
    if re.search(clear_gallery_pattern, content):
        content = re.sub(clear_gallery_pattern, apply_button_code, content)
        print("✓ 已添加应用到分镜按钮")
    else:
        print("✗ 未找到清空图片库按钮的位置")
    
    # 2. 添加应用到分镜的方法
    method_code = '''
    def apply_selected_image_to_shot(self):
        """将选中的图片应用到当前分镜"""
        try:
            # 检查是否有选中的图片
            if self.selected_image_index < 0 or self.selected_image_index >= len(self.generated_images):
                QMessageBox.warning(self, "警告", "请先选择一张图片！")
                return
            
            # 检查是否有当前分镜
            if not hasattr(self, 'current_shot_index') or self.current_shot_index < 0:
                QMessageBox.warning(self, "警告", "请先选择一个分镜！")
                return
            
            selected_image = self.generated_images[self.selected_image_index]
            image_path = selected_image['path']
            
            # 转换为相对路径
            if hasattr(self, 'current_project_dir') and self.current_project_dir:
                try:
                    relative_path = os.path.relpath(image_path, self.current_project_dir)
                    # 确保使用正斜杠
                    relative_path = relative_path.replace('\\\\', '/')
                except ValueError:
                    # 如果无法转换为相对路径，使用绝对路径
                    relative_path = image_path
            else:
                relative_path = image_path
            
            # 更新分镜数据
            if hasattr(self, 'shots_data') and self.shots_data:
                shot_index = self.current_shot_index
                if 0 <= shot_index < len(self.shots_data):
                    shot = self.shots_data[shot_index]
                    
                    # 如果主图片为空，设置为主图片
                    if not shot.get('image', '').strip():
                        shot['image'] = relative_path
                        QMessageBox.information(self, "成功", f"已将图片设置为第 {shot_index + 1} 个分镜的主图片！")
                    else:
                        # 否则添加到备选图片
                        alternative_images = shot.get('alternative_images', '')
                        if alternative_images:
                            # 如果已有备选图片，追加新图片
                            if relative_path not in alternative_images:
                                shot['alternative_images'] = alternative_images + ',' + relative_path
                                QMessageBox.information(self, "成功", f"已将图片添加到第 {shot_index + 1} 个分镜的备选图片！")
                            else:
                                QMessageBox.information(self, "提示", "该图片已存在于备选图片中！")
                        else:
                            # 如果没有备选图片，直接设置
                            shot['alternative_images'] = relative_path
                            QMessageBox.information(self, "成功", f"已将图片添加到第 {shot_index + 1} 个分镜的备选图片！")
                    
                    # 刷新分镜表格显示
                    self.refresh_shots_table()
                    
                    # 保存项目
                    if hasattr(self, 'save_project'):
                        self.save_project()
                    
                    logger.info(f"已将图片应用到分镜 {shot_index + 1}: {relative_path}")
                else:
                    QMessageBox.warning(self, "错误", "分镜索引超出范围！")
            else:
                QMessageBox.warning(self, "错误", "没有加载分镜数据！")
                
        except Exception as e:
            logger.error(f"应用图片到分镜时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"应用图片到分镜时发生错误: {str(e)}")
'''
    
    # 在get_selected_image_path方法后添加新方法
    get_selected_pattern = r'(def get_selected_image_path\(self\):[^}]+?return None)'
    
    if re.search(get_selected_pattern, content, re.DOTALL):
        content = re.sub(get_selected_pattern, '\\1' + method_code, content, flags=re.DOTALL)
        print("✓ 已添加应用到分镜的方法")
    else:
        print("✗ 未找到get_selected_image_path方法的位置")
    
    # 3. 添加当前分镜索引的跟踪
    init_pattern = r'(self\.selected_image_index = -1  # 当前选中的图片索引)'
    
    if re.search(init_pattern, content):
        content = re.sub(init_pattern, '\\1\n        self.current_shot_index = -1  # 当前选中的分镜索引', content)
        print("✓ 已添加当前分镜索引跟踪")
    else:
        print("✗ 未找到selected_image_index初始化的位置")
    
    # 4. 在分镜表格选择事件中更新当前分镜索引
    # 查找分镜表格的选择事件处理
    table_selection_code = '''
    def on_shot_selection_changed(self):
        """分镜选择改变时的处理"""
        try:
            if hasattr(self, 'shots_settings_table') and self.shots_settings_table:
                current_row = self.shots_settings_table.currentRow()
                self.current_shot_index = current_row
                logger.info(f"当前选中分镜: {current_row + 1 if current_row >= 0 else '无'}")
        except Exception as e:
            logger.error(f"处理分镜选择改变时发生错误: {e}")
'''
    
    # 在apply_selected_image_to_shot方法后添加
    content += table_selection_code
    print("✓ 已添加分镜选择事件处理")
    
    # 写回文件
    with open(main_window_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ 已成功为 {main_window_path} 添加应用到分镜功能")
    print("\n功能说明:")
    print("1. 在AI绘图界面的图片库下方添加了'应用到当前分镜'按钮")
    print("2. 选择图片后点击按钮可将图片应用到当前选中的分镜")
    print("3. 如果分镜没有主图片，会设置为主图片")
    print("4. 如果分镜已有主图片，会添加到备选图片列表")
    print("5. 支持多张图片累积添加到备选图片")

if __name__ == "__main__":
    add_apply_to_shot_feature()