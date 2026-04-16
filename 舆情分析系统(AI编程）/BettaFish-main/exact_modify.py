
# -*- coding: utf-8 -*-
import re

# 读取文件
file_path = 'templates/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("原始内容长度:", len(content))

# 1. 先找到initSearchHints函数
idx = content.find('function initSearchHints')
if idx != -1:
    print("找到initSearchHints，位置:", idx)
    # 找到函数结束位置
    brace_count = 0
    end_idx = idx
    in_func = False
    for i in range(idx, len(content)):
        if content[i] == '{':
            brace_count += 1
            in_func = True
        elif content[i] == '}':
            brace_count -= 1
            if in_func and brace_count == 0:
                end_idx = i + 1
                break
    
    old_func = content[idx:end_idx]
    print("\n旧函数内容:")
    print(repr(old_func))
    
    # 替换函数
    new_func = '''        function initSearchHints() {
            renderRandomSearchHints();
        }'''
    content = content[:idx] + new_func + content[end_idx:]
    print("\n✓ 替换了initSearchHints函数")
else:
    print("✗ 没有找到initSearchHints函数")

# 2. 修改历史报告抽屉标题
content = content.replace('🕐 历史巡航记录', '🕐 历史报告记录')
print("✓ 修改了历史报告抽屉标题")

# 3. 修改搜索提示区域
old_search = '''                &lt;!-- 搜索提示词条 + 历史巡航按钮 --&gt;
                &lt;div class="search-hint-row" id="searchHintRow" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;"&gt;
                    &lt;div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;"&gt;
                        &lt;span class="hint-label"&gt;💡 试试这样搜：&lt;/span&gt;
                        &lt;span class="search-hint-chip" data-query="比亚迪近期降价舆情分析"&gt;"比亚迪近期降价舆情分析"&lt;/span&gt;
                        &lt;span class="search-hint-chip" data-query="某品牌咖啡公关危机复盘"&gt;"某品牌咖啡公关危机复盘"&lt;/span&gt;
                        &lt;span class="search-hint-chip" data-query="今年双十一美妆热点趋势"&gt;"今年双十一美妆热点趋势"&lt;/span&gt;
                    &lt;/div&gt;
                    &lt;button class="history-archive-btn" id="historyArchiveBtn" title="历史报告记录"&gt;
                        &lt;svg viewBox="0 0 24 24"&gt;
                            &lt;circle cx="12" cy="12" r="10"/&gt;
                            &lt;polyline points="12 6 12 12 16 14"/&gt;
                        &lt;/svg&gt;
                        历史报告
                    &lt;/button&gt;
                &lt;/div&gt;'''

new_search = '''                &lt;!-- 搜索提示词条 --&gt;
                &lt;div class="search-hint-row" id="searchHintRow" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;"&gt;
                    &lt;span class="hint-label"&gt;💡 试试这样搜：&lt;/span&gt;
                    &lt;div id="searchHintChipsContainer" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;"&gt;&lt;/div&gt;
                &lt;/div&gt;'''

# 用正则来匹配，忽略一些可能的空格差异
old_search_pattern = re.escape(old_search)
# 但是先试试直接替换
if old_search in content:
    content = content.replace(old_search, new_search)
    print("✓ 修改了搜索提示区域")
else:
    print("✗ 直接替换搜索提示区域失败，尝试正则匹配")
    # 尝试更宽松的匹配
    pattern = r'&lt;!-- 搜索提示词条 \+ 历史巡航按钮 --&gt;.*?&lt;/div&gt;'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        print("找到匹配，替换中...")
        content = content[:match.start()] + new_search + content[match.end():]
        print("✓ 通过正则修改了搜索提示区域")
    else:
        print("✗ 正则匹配也失败了")

# 4. 在使用指引按钮上面添加历史报告按钮
# 先找到使用指引按钮
guide_btn_start = content.find('&lt;!-- 右下角悬浮球：使用指引 --&gt;')
if guide_btn_start != -1:
    print("找到使用指引按钮，位置:", guide_btn_start)
    
    # 找到按钮结束位置
    guide_btn_end = guide_btn_start
    button_end_found = False
    # 找&lt;/button&gt;标签
    button_close_tag = '&lt;/button&gt;'
    button_close_idx = content.find(button_close_tag, guide_btn_start)
    if button_close_idx != -1:
        guide_btn_end = button_close_idx + len(button_close_tag)
        old_guide_section = content[guide_btn_start:guide_btn_end]
        
        # 创建新的历史报告按钮 + 使用指引按钮
        history_button = '''    &lt;!-- 右下角悬浮球：历史报告 --&gt;
    &lt;button id="historyArchiveBtn" title="历史报告记录" onclick="document.getElementById('historyDrawer').classList.add('open');document.getElementById('historyDrawerOverlay').classList.add('visible');" style="
        position:fixed;
        bottom:88px;
        right:28px;
        z-index:99999;
        display:flex;
        align-items:center;
        gap:7px;
        padding:9px 18px 9px 14px;
        border:1px solid rgba(120,180,255,0.18);
        border-radius:999px;
        background:rgba(10,20,40,0.45);
        backdrop-filter:blur(14px);
        -webkit-backdrop-filter:blur(14px);
        color:rgba(180,210,255,0.72);
        font-size:12.5px;
        font-weight:500;
        letter-spacing:0.03em;
        cursor:pointer;
        font-family:-apple-system,'SF Pro Display','PingFang SC',sans-serif;
        box-shadow:0 2px 16px rgba(0,0,0,0.28),0 0 0 1px rgba(59,158,255,0.06) inset;
        transition:background 0.2s,border-color 0.2s,color 0.2s,box-shadow 0.2s;
    "
    onmouseover="this.style.background='rgba(20,40,80,0.62)';this.style.borderColor='rgba(120,180,255,0.32)';this.style.color='rgba(210,230,255,0.92)';this.style.boxShadow='0 4px 24px rgba(59,158,255,0.18),0 0 0 1px rgba(59,158,255,0.12) inset';"
    onmouseout="this.style.background='rgba(10,20,40,0.45)';this.style.borderColor='rgba(120,180,255,0.18)';this.style.color='rgba(180,210,255,0.72)';this.style.boxShadow='0 2px 16px rgba(0,0,0,0.28),0 0 0 1px rgba(59,158,255,0.06) inset';"&gt;
        &lt;svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px;flex-shrink:0;opacity:0.85;"&gt;
            &lt;circle cx="12" cy="12" r="10"/&gt;
            &lt;polyline points="12 6 12 12 16 14"/&gt;
        &lt;/svg&gt;
        &lt;span&gt;历史报告&lt;/span&gt;
    &lt;/button&gt;

'''
        new_guide_section = history_button + old_guide_section
        content = content[:guide_btn_start] + new_guide_section + content[guide_btn_end:]
        print("✓ 添加了历史报告按钮到右下角")
    else:
        print("✗ 没有找到&lt;/button&gt;标签")
else:
    print("✗ 没有找到使用指引按钮")

# 保存修改后的文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n所有修改完成！")
