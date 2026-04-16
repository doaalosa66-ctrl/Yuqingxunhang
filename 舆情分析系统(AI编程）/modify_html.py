
# -*- coding: utf-8 -*-
import re

# 读取文件
with open(r'c:\Users\Administrator\Desktop\舆情分析系统(AI编程）\BettaFish-main\templates\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

print("开始修改...")

# 1. 修改initSearchHints函数
old_init = r'''        function initSearchHints\(\) \{
            const chips = document.querySelectorAll\('\.search-hint-chip'\);
            const input = document.getElementById\('searchInput'\);
            if \(!input\) return;
            chips.forEach\(chip =&gt; \{
                chip.addEventListener\('click', \(\) =&gt; \{
                    input.value = chip.dataset.query \|\| chip.textContent.replace\(/"/g, ''\)\.trim\(\);
                    input.focus\(\);
                \}\);
            \}\);
        \}'''

new_init = '''        function initSearchHints() {
            renderRandomSearchHints();
        }'''

content = re.sub(old_init, new_init, content)

# 2. 修改搜索提示区域，添加searchHintChipsContainer并移除静态的搜索提示芯片
old_search_hint = r'''                &lt;!-- 搜索提示词条 \+ 历史巡航按钮 --&gt;
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

new_search_hint = '''                &lt;!-- 搜索提示词条 --&gt;
                &lt;div class="search-hint-row" id="searchHintRow" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;"&gt;
                    &lt;span class="hint-label"&gt;💡 试试这样搜：&lt;/span&gt;
                    &lt;div id="searchHintChipsContainer" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;"&gt;&lt;/div&gt;
                &lt;/div&gt;'''

content = re.sub(old_search_hint, new_search_hint, content)

# 3. 修改历史报告抽屉标题
content = content.replace('🕐 历史巡航记录', '🕐 历史报告记录')

# 4. 在使用指引按钮上面添加历史报告按钮
old_guide_button = r'''    &lt;!-- 右下角悬浮球：使用指引 --&gt;
    &lt;button id="guideTrigger" onclick="document.getElementById\('guideOverlay'\)\.classList\.add\('open'\)" style="
        position:fixed;
        bottom:28px;
        right:28px;
        z-index:99999;
        display:flex;
        align-items:center;
        gap:7px;
        padding:9px 18px 9px 14px;
        border:1px solid rgba\(120,180,255,0\.18\);
        border-radius:999px;
        background:rgba\(10,20,40,0\.45\);
        backdrop-filter:blur\(14px\);
        -webkit-backdrop-filter:blur\(14px\);
        color:rgba\(180,210,255,0\.72\);
        font-size:12\.5px;
        font-weight:500;
        letter-spacing:0\.03em;
        cursor:pointer;
        font-family:-apple-system,'SF Pro Display','PingFang SC',sans-serif;
        box-shadow:0 2px 16px rgba\(0,0,0,0\.28\),0 0 0 1px rgba\(59,158,255,0\.06\) inset;
        transition:background 0\.2s,border-color 0\.2s,color 0\.2s,box-shadow 0\.2s;
    "
    onmouseover="this\.style\.background='rgba\(20,40,80,0\.62\)';this\.style\.borderColor='rgba\(120,180,255,0\.32\)';this\.style\.color='rgba\(210,230,255,0\.92\)';this\.style\.boxShadow='0 4px 24px rgba\(59,158,255,0\.18\),0 0 0 1px rgba\(59,158,255,0\.12\) inset';"
    onmouseout="this\.style\.background='rgba\(10,20,40,0\.45\)';this\.style\.borderColor='rgba\(120,180,255,0\.18\)';this\.style\.color='rgba\(180,210,255,0\.72\)';this\.style\.boxShadow='0 2px 16px rgba\(0,0,0,0\.28\),0 0 0 1px rgba\(59,158,255,0\.06\) inset';"&gt;
        &lt;svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1\.5" stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px;flex-shrink:0;opacity:0\.85;"&gt;
            &lt;circle cx="10" cy="10" r="8"/&gt;
            &lt;line x1="10" y1="9" x2="10" y2="14"/&gt;
            &lt;circle cx="10" cy="6\.5" r="0\.8" fill="currentColor" stroke="none"/&gt;
        &lt;/svg&gt;
        &lt;span&gt;使用指引&lt;/span&gt;
    &lt;/button&gt;'''

new_guide_section = r'''    &lt;!-- 右下角悬浮球：历史报告 --&gt;
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

    &lt;!-- 右下角悬浮球：使用指引 --&gt;
    &lt;button id="guideTrigger" onclick="document.getElementById('guideOverlay').classList.add('open')" style="
        position:fixed;
        bottom:28px;
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
        &lt;svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px;flex-shrink:0;opacity:0.85;"&gt;
            &lt;circle cx="10" cy="10" r="8"/&gt;
            &lt;line x1="10" y1="9" x2="10" y2="14"/&gt;
            &lt;circle cx="10" cy="6.5" r="0.8" fill="currentColor" stroke="none"/&gt;
        &lt;/svg&gt;
        &lt;span&gt;使用指引&lt;/span&gt;
    &lt;/button&gt;'''

# 先移除我们之前加的那一行renderRandomSearchHints()，因为现在我们要重新替换
content = content.replace('            renderRandomSearchHints();\n', '')

content = re.sub(old_guide_button, new_guide_section, content, flags=re.DOTALL)

# 5. 现在再修改initSearchHints函数（因为刚才我们去掉了renderRandomSearchHints()）
content = re.sub(r'''        function initSearchHints\(\) \{
            const chips = document.querySelectorAll\('\.search-hint-chip'\);
            const input = document.getElementById\('searchInput'\);
            if \(!input\) return;
            chips.forEach\(chip =&gt; \{
                chip.addEventListener\('click', \(\) =&gt; \{
                    input.value = chip.dataset.query \|\| chip.textContent.replace\(/"/g, ''\)\.trim\(\);
                    input.focus\(\);
                \}\);
            \}\);
        \}''', '''        function initSearchHints() {
            renderRandomSearchHints();
        }''', content)

# 保存修改后的文件
with open(r'c:\Users\Administrator\Desktop\舆情分析系统(AI编程）\BettaFish-main\templates\index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("修改完成！")
