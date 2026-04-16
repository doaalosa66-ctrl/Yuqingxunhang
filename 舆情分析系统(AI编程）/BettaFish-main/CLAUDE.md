# BettaFish 舆情系统 — Claude 强制约束文件

> **每次修改代码前，必须先完整阅读本文件。**

---

## 1. 核心业务闭环（底线，绝对不能断）

```
输入关键词 → 搜索 → 后端生成报告并缓存 → 前端自动弹出报告 → 可在"历史报告"中查看
```

任何修改都不得破坏这条闭环的任意一个环节。

---

## 2. 绝对红线与修改约束

### 禁止大改
- 只针对性修复引发 Bug 的那几行代码
- **绝对不允许**重构整个函数或类
- **绝对不允许**在没有明确指令的情况下重写整个文件

### 必须保护的现有逻辑（不得删除或遗漏）
- 文件读写逻辑
- SQLite 缓存逻辑
- `report_task_id` 透传逻辑
- `[历史存档]` 相关的所有代码

### 输出格式要求
- **不要输出整个文件的完整代码**（文件太长容易遗漏关键逻辑）
- 只给出需要修改的函数片段
- 用注释 `# ...保留原有逻辑...` 标明未改动的部分

---

## 3. 修复 Bug 的标准流程

1. 先读取相关文件的当前实际内容，不做任何假设
2. 定位引发 Bug 的具体行
3. 只修改那几行，保留其余所有逻辑
4. 修改后确认核心闭环未被破坏

---

## 4. 启动环境提醒

- 数据库：Docker 容器 `bettafish-db`，端口 `5444`
- 后端：`python app.py`，端口 `8080`
- 已知问题：WeasyPrint/ReportEngine 可能卡死，遇到时参考 memory 中的解法

---

## 5. Git 维护守则（AI Agent 强制执行）

### 5.1 空文件夹保护
- Whenever asked to prepare a git commit or check directory status, you MUST first run a check for empty directories and ensure `.gitkeep` exists in every empty folder that needs to be tracked.

### 5.2 嵌套仓库拦截
- Never track nested `.git` folders. Warn the user immediately if a nested `.git` is detected outside the project root. These cause gray unclickable submodules on GitHub.
- If a nested `.git` is found, remove it with: `Remove-Item -Recurse -Force <path>/.git`

### 5.3 大文件拦截
- Automatically check for files >50MB and warn the user before running `git add`. Files over 100MB will be rejected by GitHub.
- For large model/data files (`.pth`, `.bin`, `.onnx`, `.csv` >50MB), ensure they are listed in `.gitignore`. Use Git LFS only if the file must be tracked.

### 5.4 标准忽略项
- Ensure standard ignored files (`.env`, logs, build artifacts, `__pycache__`, `node_modules`, `db_data/`, `*.db`, `*.sqlite3`) are not being force-added.
- Never use `git add -f` on ignored files without explicit user approval.

### 5.5 提交前检查清单
Before every commit, run:
1. `Get-ChildItem -Directory -Recurse | Where-Object { (Get-ChildItem $_.FullName -File -Recurse | Measure-Object).Count -eq 0 }` — check for empty dirs
2. `Get-ChildItem -File -Recurse | Where-Object { $_.Length -gt 50MB }` — check for large files
3. `Get-ChildItem -Directory -Recurse -Filter ".git" | Where-Object { $_.FullName -ne (Join-Path (Get-Location) ".git") }` — check for nested .git
4. `git status` — verify no ignored files are staged
