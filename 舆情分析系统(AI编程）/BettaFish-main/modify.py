
# -*- coding: utf-8 -*-
import os

# 读取文件
file_path = 'templates/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("原始内容长度:", len(content))

# 1. 修改initSearchHints函数
old_init = '''        function initSearchHints() {
            const chips = document.querySelectorAll('.search-hint-chip');
            const input = document.getElementById('searchInput');
            if (!input) return;
            chips.forEach(chip =&gt; {
                chip.addEventListener('click', () =&gt; {
                    input.value = chip.dataset.query || chip.textContent.replace(/"/g, '').trim();
                    input.focus();
                });
            });
        }'''

new_init = '''        function initSearchHints() {
            renderRandomSearchHints();
        }'''

if old_init in content:
    content = content.replace(old_init, new_init)
    print("✓ 修改了initSearchHints函数")
else:
    print("✗ 没有找到initSearchHints函数")
    # 打印一下附近的内容看看
    idx = content.find('function initSearchHints')
    if idx != -1:
        print("找到initSearchHints位置，附近内容:")
        print(repr(content[idx:idx+500]))

# 2. 修改历史报告抽屉标题
if '🕐 历史巡航记录' in content:
    content = content.replace('🕐 历史巡航记录', '🕐 历史报告记录')
    print("✓ 修改了历史报告抽屉标题")
else:
    print("✗ 没有找到历史巡航记录")

# 保存
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("完成！")
