#!/usr/bin/env python3
# coding: utf-8

# 修复字典文件的语法错误
print('正在修复字典文件...')

# 重新生成完整的字典文件，直接覆盖

# 1. 创建新的字典文件内容
header = "#!/usr/bin/env python3\n# coding: utf-8\n\n#生僻字拼音字典\n"

# 2. 从CSV文件生成字典内容
import csv
csv_file = './shengpizi_results.csv'

# 读取CSV文件中的生僻字
shengpizi_data = {}
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        if len(row) == 2:
            char = row[0].strip()
            pinyin_str = row[1].strip()
            if pinyin_str.startswith('\"') and pinyin_str.endswith('\"'):
                pinyin_str = pinyin_str[1:-1]
            pinyins = [p.strip() for p in pinyin_str.split(',') if p.strip()]
            if char and pinyins:
                shengpizi_data[char] = pinyins

print(f'从CSV读取了 {len(shengpizi_data)} 个生僻字')

# 3. 生成新的字典内容
new_dict_lines = []
for char, pinyins in sorted(shengpizi_data.items()):
    pinyins_str = "', '".join(pinyins)
    new_dict_lines.append(f"'{char}': ['{pinyins_str}'],")

new_dict_content = '\n    '.join(new_dict_lines)

# 4. 生成新的文件内容 - 使用字符串连接避免f-string转义问题
new_content = header + "shengpizi_dict = {\n    " + new_dict_content + "\n}"

# 5. 写入修复后的文件
with open('./python_core/utils/dict/ShengPiZi.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('✅ 字典文件修复完成！')
print('✅ 已从CSV重新生成完整字典')
