#!/usr/bin/env python3
# coding: utf-8

import re

# 检查字典文件
print('正在修复字典文件...')

with open('./python_core/utils/dict/ShengPiZi.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 提取字典内容
dict_pattern = r'shengpizi_dict\s*=\s*{([\s\S]*?)}'
match = re.search(dict_pattern, content)

if not match:
    print('未找到字典定义')
    exit()

dict_content = match.group(1)

# 解析字典
key_value_pattern = r"'([^']+)'\s*:\s*\[([^\]]+)\]"

fixed_dict = {}

total_entries = 0
for match in re.finditer(key_value_pattern, dict_content):
    key = match.group(1)
    values_str = match.group(2)
    values = [v.strip().strip("'").strip('"') for v in values_str.split(',') if v.strip()]
    unique_values = sorted(list(set(values)))
    total_entries += 1
    
    # 如果键已存在，合并拼音
    if key in fixed_dict:
        existing_values = fixed_dict[key]
        combined_values = sorted(list(set(existing_values + unique_values)))
        fixed_dict[key] = combined_values
    else:
        fixed_dict[key] = unique_values

print(f'共处理 {total_entries} 个条目')
print(f'去重后剩余 {len(fixed_dict)} 个唯一条目')

# 生成新的字典内容
new_dict_lines = []
for char, pinyins in sorted(fixed_dict.items()):
    pinyins_str = "', '".join(pinyins)
    new_dict_lines.append(f"'{char}': ['{pinyins_str}'],")

new_dict_content = '\n    '.join(new_dict_lines)

# 生成新的文件内容
new_content = content.replace(match.group(0), f"shengpizi_dict = {{{new_dict_content}\n}}")

# 写入修复后的文件
with open('./python_core/utils/dict/ShengPiZi.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('✅ 字典修复完成！')
