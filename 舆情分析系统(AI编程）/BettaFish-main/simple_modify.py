
# -*- coding: utf-8 -*-
import sys

# 读取文件
file_path = 'templates/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("读取成功")

# 简单修改1：修改initSearchHints函数 - 使用更简单的方法
import re

# 找到function initSearchHints
match = re.search(r'function initSearchHints\(\) \{.*?\}', content, re.DOTALL)
if match:
    print("找到initSearchHints")
    old_func = match.group(0)
    print("旧函数:", repr(old_func[:200]))
    new_func = '''        function initSearchHints() {
            renderRandomSearchHints();
        }'''
    content = content.replace(old_func, new_func)
    print("替换initSearchHints成功")

# 简单修改2：历史报告抽屉标题
content = content.replace('🕐 历史巡航记录', '🕐 历史报告记录')
print("替换标题成功")

# 保存
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("保存成功！")
