import json

# 读取项目文件
with open('d:/AI_Video_Generator/output/four/project.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 检查第4阶段数据
stage4 = data['five_stage_storyboard']['stage_data']['4']
print('Stage 4 keys:', list(stage4.keys()))
print('Has storyboard_results:', 'storyboard_results' in stage4)
print('Storyboard results length:', len(stage4.get('storyboard_results', [])))

if stage4.get('storyboard_results'):
    print('First result keys:', list(stage4['storyboard_results'][0].keys()))
    print('First result scene_info:', stage4['storyboard_results'][0].get('scene_info', 'No scene_info'))
    print('First result has storyboard_script:', 'storyboard_script' in stage4['storyboard_results'][0])
else:
    print('No storyboard results found')