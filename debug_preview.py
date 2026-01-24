import re
import sys

content = """
第一卷 清泉市
第一章 百分之百真实的游戏是有多真实？
　　“……百分之百真实的完全沉浸式游戏是有多真实？”
第二章 404号避难所
"""

rules = [
    {'pattern': r'^\s*第[一二三四五六七八九十零〇百千两0-9]+[卷].*', 'level': 1},
    {'pattern': r'^\s*第[一二三四五六七八九十零〇百千两0-9]+[章].*', 'level': 2},
    {'pattern': r'^\s*第[一二三四五六七八九十零〇百千两0-9]+节.*', 'level': 3},
    {'pattern': r'^\s*Chapter\s+[0-9]+.*', 'level': 2},
    {'pattern': r'^\s*[0-9]+\..*', 'level': 2}
]

print(f"Testing {len(rules)} rules against content...")

lines = content.strip().split('\n')
chapters = []

for line in lines:
    line = line.strip()
    matched = False
    for rule in rules:
        pattern = rule['pattern']
        if re.match(pattern, line):
            print(f"MATCH: '{line}' with pattern '{pattern}'")
            chapters.append(line)
            matched = True
            break
    if not matched:
        print(f"NO MATCH: '{line}'")

print(f"Total chapters matched: {len(chapters)}")
