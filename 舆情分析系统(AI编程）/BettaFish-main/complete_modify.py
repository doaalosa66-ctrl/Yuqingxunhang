
# -*- coding: utf-8 -*-

# 读取文件
file_path = 'templates/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("读取了", len(lines), "行")

# 1. 修复initSearchHints函数的缩进
for i, line in enumerate(lines):
    if 'function initSearchHints' in line:
        print("找到initSearchHints在第", i+1, "行，当前缩进:", len(line) - len(line.lstrip()))
        # 修复缩进
        lines[i] = '        function initSearchHints() {\n'
        break

# 2. 修改搜索提示区域
# 找到开始和结束
search_start = -1
for i, line in enumerate(lines):
    if '搜索提示词条 + 历史巡航按钮' in line:
        search_start = i
        print("搜索提示区域开始在第", i+1, "行")
        break

if search_start != -1:
    # 数div标签找到结束
    div_count = 0
    search_end = -1
    for i in range(search_start, len(lines)):
        if '&lt;div' in lines[i] and 'search-hint-row' in lines[i]:
            div_count += 1
        if '&lt;/div&gt;' in lines[i]:
            div_count -= 1
            if div_count == 0:
                search_end = i
                print("搜索提示区域结束在第", i+1, "行")
                break
    
    if search_end != -1:
        new_search = [
            '                &lt;!-- 搜索提示词条 --&gt;\n',
            '                &lt;div class="search-hint-row" id="searchHintRow" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;"&gt;\n',
            '                    &lt;span class="hint-label"&gt;💡 试试这样搜：&lt;/span&gt;\n',
            '                    &lt;div id="searchHintChipsContainer" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;"&gt;&lt;/div&gt;\n',
            '                &lt;/div&gt;\n'
        ]
        lines = lines[:search_start] + new_search + lines[search_end+1:]

# 3. 在右下角使用指引按钮上面添加历史报告按钮
guide_start = -1
for i, line in enumerate(lines):
    if '右下角悬浮球：使用指引' in line:
        guide_start = i
        print("使用指引按钮在第", i+1, "行")
        break

if guide_start != -1:
    # 找按钮结束
    guide_end = -1
    for i in range(guide_start, len(lines)):
        if '&lt;/button&gt;' in lines[i]:
            guide_end = i
            print("使用指引按钮结束在第", i+1, "行")
            break
    
    if guide_end != -1:
        # 添加历史报告按钮
        history_btn = [
            '    &lt;!-- 右下角悬浮球：历史报告 --&gt;\n',
            '    &lt;button id="historyArchiveBtn" title="历史报告记录" onclick="document.getElementById(\'historyDrawer\').classList.add(\'open\');document.getElementById(\'historyDrawerOverlay\').classList.add(\'visible\');" style="\n',
            '        position:fixed;\n',
            '        bottom:88px;\n',
            '        right:28px;\n',
            '        z-index:99999;\n',
            '        display:flex;\n',
            '        align-items:center;\n',
            '        gap:7px;\n',
            '        padding:9px 18px 9px 14px;\n',
            '        border:1px solid rgba(120,180,255,0.18);\n',
            '        border-radius:999px;\n',
            '        background:rgba(10,20,40,0.45);\n',
            '        backdrop-filter:blur(14px);\n',
            '        -webkit-backdrop-filter:blur(14px);\n',
            '        color:rgba(180,210,255,0.72);\n',
            '        font-size:12.5px;\n',
            '        font-weight:500;\n',
            '        letter-spacing:0.03em;\n',
            '        cursor:pointer;\n',
            '        font-family:-apple-system,\'SF Pro Display\',\'PingFang SC\',sans-serif;\n',
            '        box-shadow:0 2px 16px rgba(0,0,0,0.28),0 0 0 1px rgba(59,158,255,0.06) inset;\n',
            '        transition:background 0.2s,border-color 0.2s,color 0.2s,box-shadow 0.2s;\n',
            '    "\n',
            '    onmouseover="this.style.background=\'rgba(20,40,80,0.62)\';this.style.borderColor=\'rgba(120,180,255,0.32)\';this.style.color=\'rgba(210,230,255,0.92)\';this.style.boxShadow=\'0 4px 24px rgba(59,158,255,0.18),0 0 0 1px rgba(59,158,255,0.12) inset\';"\n',
            '    onmouseout="this.style.background=\'rgba(10,20,40,0.45)\';this.style.borderColor=\'rgba(120,180,255,0.18)\';this.style.color=\'rgba(180,210,255,0.72)\';this.style.boxShadow=\'0 2px 16px rgba(0,0,0,0.28),0 0 0 1px rgba(59,158,255,0.06) inset\';"&gt;\n',
            '        &lt;svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px;flex-shrink:0;opacity:0.85;"&gt;\n',
            '            &lt;circle cx="12" cy="12" r="10"/&gt;\n',
            '            &lt;polyline points="12 6 12 12 16 14"/&gt;\n',
            '        &lt;/svg&gt;\n',
            '        &lt;span&gt;历史报告&lt;/span&gt;\n',
            '    &lt;/button&gt;\n',
            '\n'
        ]
        lines = lines[:guide_start] + history_btn + lines[guide_start:]

# 保存
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("完成！")
