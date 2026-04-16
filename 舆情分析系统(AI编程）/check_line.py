
# -*- coding: utf-8 -*-
with open(r'c:\Users\Administrator\Desktop\舆情分析系统(AI编程）\BettaFish-main\templates\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 打印第1939行 (索引从0开始，所以是1938)
line_num = 1938
if line_num &lt; len(lines):
    line = lines[line_num]
    print(f"第{line_num+1}行内容:")
    print(repr(line))
    print(f"长度: {len(line)}")

# 也打印1938-1940行
print("\n--- 1938-1940行 ---")
for i in range(1937, 1941):
    if i &lt; len(lines):
        print(f"{i+1}: {repr(lines[i])}")
