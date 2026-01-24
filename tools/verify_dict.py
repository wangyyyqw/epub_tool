#!/usr/bin/env python3
# coding: utf-8

import re

# 检查字典文件
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

total_entries = 0
duplicate_keys = set()
seen_keys = set()

for match in re.finditer(key_value_pattern, dict_content):
    key = match.group(1)
    total_entries += 1
    if key in seen_keys:
        duplicate_keys.add(key)
    else:
        seen_keys.add(key)

print(f'字典中共有 {total_entries} 个条目')
print(f'去重后共有 {len(seen_keys)} 个生僻字')
if duplicate_keys:
    print(f'发现 {len(duplicate_keys)} 个重复键')
    print('重复键示例：', list(duplicate_keys)[:5])
else:
    print('✅ 字典中没有重复键，已完成去重')

# 检查几个示例生僻字
print('\n示例生僻字拼音：')
sample_chars = ['𫘣', '芺', '厈', '盫', '泑']
for char in sample_chars:
    char_pattern = f"'{char}'\s*:\s*\[([^\]]+)\]"
    char_match = re.search(char_pattern, dict_content)
    if char_match:
        pinyins = char_match.group(1)
        pinyin_list = [p.strip().strip("'").strip('"') for p in pinyins.split(',') if p.strip()]
        print(f'{char}: {pinyin_list}')
    else:
        print(f'{char}: 未找到')

# 统计拼音去重情况
print('\n拼音去重检查：')
pinyin_duplicates = 0
for match in re.finditer(key_value_pattern, dict_content):
    key = match.group(1)
    values_str = match.group(2)
    values = [v.strip().strip("'").strip('"') for v in values_str.split(',') if v.strip()]
    unique_values = list(set(values))
    if len(values) != len(unique_values):
        pinyin_duplicates += 1
        # 可选：打印有重复拼音的字
        # print(f'{key}: {values} -> {unique_values}')

print(f'共有 {pinyin_duplicates} 个字的拼音列表中存在重复')
if pinyin_duplicates == 0:
    print('✅ 所有字的拼音列表都已去重')
