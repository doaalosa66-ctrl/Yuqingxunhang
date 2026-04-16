
# -*- coding: utf-8 -*-

# 读取文件
with open(r'c:\Users\Administrator\Desktop\舆情分析系统(AI编程）\BettaFish-main\templates\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

print("原始内容长度:", len(content))

# 1. 先试试简单的替换 - 修改历史报告抽屉标题
if '🕐 历史巡航记录' in content:
    content = content.replace('🕐 历史巡航记录', '🕐 历史报告记录')
    print("✓ 修改了历史报告抽屉标题")
else:
    print("✗ 没有找到历史巡航记录")

# 保存
with open(r'c:\Users\Administrator\Desktop\舆情分析系统(AI编程）\BettaFish-main\templates\index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("完成！")
