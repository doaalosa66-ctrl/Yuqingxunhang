#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BettaFish 实时调试工具
在浏览器控制台中运行，实时监控系统状态
"""

DEBUG_SCRIPT = """
// ============================================================
// BettaFish 实时调试工具
// 在浏览器控制台 (F12 → Console) 中粘贴并执行此脚本
// ============================================================

(function() {
    'use strict';

    console.log('%c🔍 BettaFish 调试工具已加载', 'color: #0A84FF; font-size: 16px; font-weight: bold;');

    // ============================================================
    // 1. 系统状态检查
    // ============================================================
    window.BettaDebug = {
        // 检查所有关键 DOM 元素
        checkDOM: function() {
            console.log('%c📋 DOM 元素检查', 'color: #30D158; font-size: 14px; font-weight: bold;');

            const elements = {
                'forumState': document.getElementById('forumState'),
                'reportPreview': document.getElementById('reportPreview'),
                'holoProgressOverlay': document.getElementById('holoProgressOverlay'),
                'reportContent': document.getElementById('reportContent'),
                'consoleSection': document.querySelector('.console-section'),
                'embeddedSection': document.querySelector('.embedded-section'),
            };

            for (const [name, el] of Object.entries(elements)) {
                const exists = !!el;
                const visible = el ? (el.style.display !== 'none' && !el.hidden) : false;
                const status = exists ? (visible ? '✅ 存在且可见' : '⚠️  存在但隐藏') : '❌ 不存在';
                console.log(`  ${name}: ${status}`);
                if (el && visible) {
                    console.log(`    - display: ${el.style.display || 'default'}`);
                    console.log(`    - visibility: ${getComputedStyle(el).visibility}`);
                    console.log(`    - opacity: ${getComputedStyle(el).opacity}`);
                }
            }
        },

        // 检查沉浸式阅读器状态
        checkImmersive: function() {
            console.log('%c🌌 沉浸式阅读器状态', 'color: #FF9F0A; font-size: 14px; font-weight: bold;');

            const isImmersive = document.body.classList.contains('immersive-reader');
            console.log(`  状态: ${isImmersive ? '✅ 已激活' : '❌ 未激活'}`);

            if (isImmersive) {
                const forumState = document.getElementById('forumState');
                const consoleSection = document.querySelector('.console-section');

                console.log(`  forumState 隐藏: ${forumState?.style.display === 'none' ? '✅' : '❌'}`);
                console.log(`  consoleSection 隐藏: ${consoleSection?.style.display === 'none' ? '✅' : '❌'}`);
            }
        },

        // 检查 ForumState 状态机
        checkForumState: function() {
            console.log('%c🤖 ForumState 状态机', 'color: #FF3B30; font-size: 14px; font-weight: bold;');

            if (window.ForumState) {
                console.log('  ✅ ForumState 已加载');
                console.log('  可用方法:', Object.keys(window.ForumState));
            } else {
                console.log('  ❌ ForumState 未加载');
            }
        },

        // 检查全局变量
        checkGlobals: function() {
            console.log('%c🌐 全局变量检查', 'color: #5856D6; font-size: 14px; font-weight: bold;');

            const globals = [
                'viewReport',
                'openReportById',
                'ForumState',
                'ReportReader',
                'switchToApp',
                'currentApp',
                'isViewingHistory',
            ];

            for (const name of globals) {
                const exists = typeof window[name] !== 'undefined';
                console.log(`  ${name}: ${exists ? '✅ 已定义' : '❌ 未定义'}`);
            }
        },

        // 完整诊断
        diagnose: function() {
            console.clear();
            console.log('%c🔍 BettaFish 完整诊断', 'color: #0A84FF; font-size: 18px; font-weight: bold;');
            console.log('');

            this.checkDOM();
            console.log('');

            this.checkImmersive();
            console.log('');

            this.checkForumState();
            console.log('');

            this.checkGlobals();
            console.log('');

            console.log('%c✅ 诊断完成', 'color: #30D158; font-size: 16px; font-weight: bold;');
        },

        // 强制清理 UI
        forceCleanup: function() {
            console.log('%c🧹 强制清理 UI', 'color: #FF9F0A; font-size: 14px; font-weight: bold;');

            // 隐藏 Forum State
            const forumState = document.getElementById('forumState');
            if (forumState) {
                forumState.style.display = 'none';
                forumState.classList.remove('visible');
                forumState.setAttribute('aria-hidden', 'true');
                console.log('  ✅ forumState 已隐藏');
            }

            // 隐藏控制台
            const consoleSection = document.querySelector('.console-section');
            if (consoleSection) {
                consoleSection.style.display = 'none';
                console.log('  ✅ consoleSection 已隐藏');
            }

            // 移除全息进度条
            const holoOverlay = document.getElementById('holoProgressOverlay');
            if (holoOverlay && holoOverlay.parentNode) {
                holoOverlay.parentNode.removeChild(holoOverlay);
                console.log('  ✅ holoProgressOverlay 已移除');
            }

            // 重置 ForumState
            if (window.ForumState && typeof window.ForumState.reset === 'function') {
                window.ForumState.reset();
                console.log('  ✅ ForumState 已重置');
            }

            console.log('%c✅ 清理完成', 'color: #30D158; font-size: 14px; font-weight: bold;');
        },

        // 监控 Network 请求
        monitorNetwork: function() {
            console.log('%c📡 开始监控 Network 请求', 'color: #5856D6; font-size: 14px; font-weight: bold;');
            console.log('  提示: 打开 Network 标签查看详细信息');

            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                const url = args[0];
                if (url.includes('/api/report/')) {
                    console.log(`%c📡 API 请求: ${url}`, 'color: #0A84FF;');
                }
                return originalFetch.apply(this, args)
                    .then(response => {
                        if (url.includes('/api/report/')) {
                            console.log(`%c📡 API 响应: ${url} → ${response.status}`,
                                response.ok ? 'color: #30D158;' : 'color: #FF3B30;');
                        }
                        return response;
                    })
                    .catch(error => {
                        if (url.includes('/api/report/')) {
                            console.error(`%c📡 API 错误: ${url}`, 'color: #FF3B30;', error);
                        }
                        throw error;
                    });
            };

            console.log('  ✅ Network 监控已启动');
        },

        // 显示帮助
        help: function() {
            console.log('%c📖 BettaDebug 使用指南', 'color: #0A84FF; font-size: 16px; font-weight: bold;');
            console.log('');
            console.log('可用命令:');
            console.log('  BettaDebug.diagnose()      - 完整诊断');
            console.log('  BettaDebug.checkDOM()      - 检查 DOM 元素');
            console.log('  BettaDebug.checkImmersive() - 检查沉浸式阅读器');
            console.log('  BettaDebug.checkForumState() - 检查 ForumState');
            console.log('  BettaDebug.checkGlobals()  - 检查全局变量');
            console.log('  BettaDebug.forceCleanup()  - 强制清理 UI');
            console.log('  BettaDebug.monitorNetwork() - 监控 Network 请求');
            console.log('  BettaDebug.help()          - 显示此帮助');
            console.log('');
            console.log('快捷方式:');
            console.log('  bd = BettaDebug (简写)');
            console.log('');
            console.log('示例:');
            console.log('  bd.diagnose()    // 运行完整诊断');
            console.log('  bd.forceCleanup() // 强制清理残留 UI');
        }
    };

    // 创建简写别名
    window.bd = window.BettaDebug;

    // 显示欢迎信息
    console.log('');
    console.log('%c使用方法:', 'color: #FF9F0A; font-size: 14px;');
    console.log('  输入 BettaDebug.help() 或 bd.help() 查看帮助');
    console.log('  输入 BettaDebug.diagnose() 或 bd.diagnose() 运行诊断');
    console.log('');

})();
"""

def main():
    print("="*60)
    print("BettaFish 实时调试工具生成器")
    print("="*60)
    print()
    print("已生成浏览器调试脚本！")
    print()
    print("使用方法:")
    print("1. 打开浏览器访问 http://localhost:8080")
    print("2. 按 F12 打开开发者工具")
    print("3. 切换到 Console 标签")
    print("4. 复制下面的脚本并粘贴到控制台")
    print("5. 按 Enter 执行")
    print()
    print("="*60)
    print("调试脚本 (复制下面的内容):")
    print("="*60)
    print()
    print(DEBUG_SCRIPT)
    print()
    print("="*60)
    print("快速命令:")
    print("="*60)
    print("  bd.diagnose()      - 完整诊断")
    print("  bd.forceCleanup()  - 强制清理 UI")
    print("  bd.monitorNetwork() - 监控 Network 请求")
    print("  bd.help()          - 显示帮助")
    print()

if __name__ == "__main__":
    main()
