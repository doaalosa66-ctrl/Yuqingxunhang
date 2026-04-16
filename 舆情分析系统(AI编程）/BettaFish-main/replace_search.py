
# -*- coding: utf-8 -*-

file_path = 'templates/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("原始长度", len(content))

# 直接替换搜索提示区域
old = '''                &lt;!-- 搜索提示词条 + 历史巡航按钮 --&gt;
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

new = '''                &lt;!-- 搜索提示词条 --&gt;
                &lt;div class="search-hint-row" id="searchHintRow" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;"&gt;
                    &lt;span class="hint-label"&gt;💡 试试这样搜：&lt;/span&gt;
                    &lt;div id="searchHintChipsContainer" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;"&gt;&lt;/div&gt;
                &lt;/div&gt;'''

# 尝试多种换行符
content = content.replace('\r\n', '\n')
old = old.replace('\r\n', '\n')

if old in content:
    content = content.replace(old, new)
    print("✓ 替换搜索提示区域成功")
else:
    print("✗ 直接替换失败，尝试模糊匹配")
    # 用模糊匹配
    import re
    pattern = r'&lt;!-- 搜索提示词条 \+ 历史巡航按钮 --&gt;.*?&lt;/div&gt;\s*&lt;/div&gt;'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        print("找到匹配，长度", len(match.group(0)))
        content = content[:match.start()] + new + content[match.end():]
        print("✓ 模糊匹配替换成功")

# 现在添加历史报告按钮到右下角
guide_old = '''    &lt;!-- 右下角悬浮球：使用指引 --&gt;'''

if guide_old in content:
    history_btn = '''    &lt;!-- 右下角悬浮球：历史报告 --&gt;
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
    content = content.replace(guide_old, history_btn + guide_old)
    print("✓ 添加历史报告按钮成功")

# 保存
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("完成！最终长度", len(content))
