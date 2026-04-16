#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BettaFish Bug 修复验证脚本
用于快速验证前端展示阶段的三个 Bug 是否已修复
"""

import re
import sys
import io
from pathlib import Path

# 修复 Windows 控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def check_file_exists(filepath):
    """检查文件是否存在"""
    if not Path(filepath).exists():
        print(f"❌ 文件不存在: {filepath}")
        return False
    print(f"✅ 文件存在: {filepath}")
    return True

def check_bug1_fix(content):
    """检查 Bug 1 (Task ID 错配) 是否已修复"""
    print("\n" + "="*60)
    print("检查 Bug 1: Task ID 错配修复")
    print("="*60)

    issues = []

    # 检查是否还有使用 result.report_task_id 的地方
    pattern1 = r'result\.report_task_id\s*\|\|'
    matches1 = re.findall(pattern1, content)
    if matches1:
        issues.append(f"❌ 发现 {len(matches1)} 处仍在使用 result.report_task_id")
    else:
        print("✅ 已移除所有 result.report_task_id 的使用")

    # 检查是否统一使用 taskId
    pattern2 = r'const reportViewId = taskId;'
    if pattern2 in content:
        print("✅ 已统一使用短 hash (taskId)")
    else:
        issues.append("❌ 未找到统一使用 taskId 的代码")

    # 检查轮询和 WebSocket 是否已修复
    pattern3 = r"report_task_id: ''"
    matches3 = re.findall(pattern3, content)
    if len(matches3) >= 2:
        print(f"✅ 轮询和 WebSocket 已修复 (找到 {len(matches3)} 处)")
    else:
        issues.append(f"❌ 轮询/WebSocket 修复不完整 (只找到 {len(matches3)} 处，应该至少 2 处)")

    if issues:
        print("\n⚠️  Bug 1 修复存在问题:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("\n✅ Bug 1 修复完成")
        return True

def check_bug2_fix(content):
    """检查 Bug 2 (DOM 骨架丢失与蒙版残留) 是否已修复"""
    print("\n" + "="*60)
    print("检查 Bug 2: DOM 骨架丢失与蒙版残留修复")
    print("="*60)

    issues = []

    # 检查 CSS 层面的强制隐藏
    pattern1 = r'body\.immersive-reader #forumState'
    if re.search(pattern1, content):
        print("✅ CSS 层面已添加 #forumState 强制隐藏")
    else:
        issues.append("❌ CSS 层面缺少 #forumState 强制隐藏")

    # 检查 JS 层面的清理逻辑
    pattern2 = r'forumState\.style\.display\s*=\s*[\'"]none[\'"]'
    if re.search(pattern2, content):
        print("✅ JS 层面已添加 forumState 清理逻辑")
    else:
        issues.append("❌ JS 层面缺少 forumState 清理逻辑")

    # 检查 ForumState.reset() 调用
    pattern3 = r'window\.ForumState\.reset\(\)'
    matches3 = re.findall(pattern3, content)
    if len(matches3) >= 2:
        print(f"✅ 已添加 ForumState.reset() 调用 (找到 {len(matches3)} 处)")
    else:
        issues.append(f"❌ ForumState.reset() 调用不足 (只找到 {len(matches3)} 处，应该至少 2 处)")

    # 检查 holoProgressOverlay 的强制移除
    pattern4 = r'holoOverlay\.parentNode\.removeChild\(holoOverlay\)'
    matches4 = re.findall(pattern4, content)
    if len(matches4) >= 2:
        print(f"✅ 已添加 holoProgressOverlay 强制移除 (找到 {len(matches4)} 处)")
    else:
        issues.append(f"❌ holoProgressOverlay 强制移除不完整 (只找到 {len(matches4)} 处，应该至少 2 处)")

    if issues:
        print("\n⚠️  Bug 2 修复存在问题:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("\n✅ Bug 2 修复完成")
        return True

def check_bug3_fix(content):
    """检查 Bug 3 (_holoPolling 未定义) 是否已修复"""
    print("\n" + "="*60)
    print("检查 Bug 3: _holoPolling 未定义修复")
    print("="*60)

    issues = []

    # 检查 _holoPolling 初始化
    pattern1 = r'let _holoPolling = true;'
    if pattern1 in content:
        print("✅ 已初始化 _holoPolling 变量")
    else:
        issues.append("❌ 缺少 _holoPolling 变量初始化")

    # 检查 _holoTimer 初始化
    pattern2 = r'let _holoTimer = null;'
    if pattern2 in content:
        print("✅ 已初始化 _holoTimer 变量")
    else:
        issues.append("❌ 缺少 _holoTimer 变量初始化")

    # 检查历史报告查看时的清理逻辑
    pattern3 = r'修复 Bug 3.*历史报告查看时也要清理 Forum State'
    if re.search(pattern3, content):
        print("✅ 历史报告查看时已添加清理逻辑")
    else:
        issues.append("❌ 历史报告查看时缺少清理逻辑")

    if issues:
        print("\n⚠️  Bug 3 修复存在问题:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("\n✅ Bug 3 修复完成")
        return True

def main():
    print("="*60)
    print("BettaFish Bug 修复验证脚本")
    print("="*60)

    # 检查文件是否存在
    index_html = Path(__file__).parent / "templates" / "index.html"
    if not check_file_exists(index_html):
        sys.exit(1)

    # 读取文件内容
    try:
        with open(index_html, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ 成功读取文件 (共 {len(content)} 字符)")
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        sys.exit(1)

    # 检查三个 Bug 的修复情况
    bug1_ok = check_bug1_fix(content)
    bug2_ok = check_bug2_fix(content)
    bug3_ok = check_bug3_fix(content)

    # 总结
    print("\n" + "="*60)
    print("修复验证总结")
    print("="*60)

    results = [
        ("Bug 1: Task ID 错配", bug1_ok),
        ("Bug 2: DOM 骨架丢失与蒙版残留", bug2_ok),
        ("Bug 3: _holoPolling 未定义", bug3_ok),
    ]

    for name, ok in results:
        status = "✅ 已修复" if ok else "❌ 未修复"
        print(f"{status} - {name}")

    all_ok = all(ok for _, ok in results)

    if all_ok:
        print("\n🎉 所有 Bug 修复验证通过！")
        print("\n下一步:")
        print("1. 启动后端: python app.py")
        print("2. 打开浏览器访问: http://localhost:8080")
        print("3. 按照 BUGFIX_REPORT.md 中的测试清单进行功能测试")
        return 0
    else:
        print("\n⚠️  部分 Bug 修复验证失败，请检查代码")
        return 1

if __name__ == "__main__":
    sys.exit(main())
