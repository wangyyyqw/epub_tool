#!/usr/bin/env python3
# coding: utf-8

import csv
import re

def main():
    # 读取CSV文件，获取生僻字和拼音
    shengpizi_data = {}
    csv_file = './shengpizi_results.csv'
    
    print(f"读取文件: {csv_file}")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) != 2:
                continue
            
            char = row[0].strip()
            pinyin_str = row[1].strip()
            
            # 处理拼音字符串，去除引号并分割
            if pinyin_str.startswith('"') and pinyin_str.endswith('"'):
                pinyin_str = pinyin_str[1:-1]
            
            pinyins = [p.strip() for p in pinyin_str.split(',') if p.strip()]
            
            if char and pinyins:
                shengpizi_data[char] = pinyins
    
    print(f"共读取 {len(shengpizi_data)} 个生僻字")
    
    # 读取现有字典文件
    dict_file = './python_core/utils/dict/ShengPiZi.py'
    print(f"读取字典文件: {dict_file}")
    
    with open(dict_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取现有字典内容
    dict_pattern = r'shengpizi_dict\s*=\s*{([\s\S]*?)}'
    match = re.search(dict_pattern, content)
    
    if not match:
        print("未找到字典定义")
        return
    
    dict_content = match.group(1)
    
    # 解析现有字典
    existing_dict = {}
    # 匹配每一行的键值对
    key_value_pattern = r"'([^']+)'\s*:\s*\[([^\]]+)\]"
    
    for match in re.finditer(key_value_pattern, dict_content):
        key = match.group(1)
        values_str = match.group(2)
        values = [v.strip().strip("'").strip('"') for v in values_str.split(',') if v.strip()]
        existing_dict[key] = values
    
    print(f"现有字典包含 {len(existing_dict)} 个生僻字")
    
    # 合并新数据到现有字典
    added_count = 0
    updated_count = 0
    
    for char, pinyins in shengpizi_data.items():
        if char in existing_dict:
            # 检查拼音是否有变化
            existing_pinyins = existing_dict[char]
            if set(existing_pinyins) != set(pinyins):
                # 更新现有拼音
                existing_dict[char] = sorted(list(set(existing_pinyins + pinyins)))
                updated_count += 1
        else:
            # 添加新字符
            existing_dict[char] = pinyins
            added_count += 1
    
    print(f"新增 {added_count} 个生僻字，更新 {updated_count} 个生僻字")
    
    # 生成新的字典内容
    new_dict_lines = []
    for char, pinyins in sorted(existing_dict.items(), key=lambda x: x[0]):
        # 格式化拼音列表
        pinyins_str = "', '".join(pinyins)
        new_dict_lines.append(f"'{char}': ['{pinyins_str}'],")
    
    new_dict_content = '\n    '.join(new_dict_lines)
    
    # 生成新的文件内容
    new_content = content.replace(match.group(0), f"shengpizi_dict = {{{new_dict_content}\n}}")
    
    # 写入更新后的文件
    with open(dict_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"已更新字典文件: {dict_file}")
    print("操作完成！")

if __name__ == "__main__":
    main()
