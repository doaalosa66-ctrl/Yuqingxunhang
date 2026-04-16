
# -*- coding: utf-8 -*-

file_path = 'templates/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("读取了", len(lines), "行")

# 直接替换第1912到1927行（索引是1911到1926）
# 第1912行是注释，第1927行是&lt;/div&gt;
new_lines = [
    '                &lt;!-- 搜索提示词条 --&gt;\n',
    '                &lt;div class="search-hint-row" id="searchHintRow" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;"&gt;\n',
    '                    &lt;span class="hint-label"&gt;💡 试试这样搜：&lt;/span&gt;\n',
    '                    &lt;div id="searchHintChipsContainer" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;"&gt;&lt;/div&gt;\n',
    '                &lt;/div&gt;\n'
]

# 替换1911到1926（因为Python索引从0开始）
lines = lines[:1911] + new_lines + lines[1927:]

# 保存
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("搜索提示区域修改完成！")
