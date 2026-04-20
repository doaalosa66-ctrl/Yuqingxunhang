# Mina AI舆情巡航系统 — 架构与 API 接口梳理

> 梳理时间：2026-04-16  
> 代码路径：`舆情分析系统(AI编程）\BettaFish-main\`

---

## 一、系统整体架构

### 核心业务闭环

```
用户输入关键词
    ↓
POST /api/search  （触发后台流水线）
    ↓
runner.run_pipeline()
    ├── InsightEngine  （本地数据库深度搜索，LLM: Kimi-K2）
    ├── MediaEngine    （网页多模态搜索，LLM: Gemini-2.5-Pro）
    └── QueryEngine    （新闻搜索，LLM: DeepSeek-Chat）
    ↓（三路并发，结果汇总）
ReportEngine.generate_report()  （报告编排，LLM: Gemini-2.5-Pro）
    ↓
HTML 报告 → SQLite 缓存
    ↓
前端自动弹出报告 / 历史报告查看
```

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Flask + Flask-SocketIO (eventlet) |
| 实时通信 | Socket.IO (WebSocket) + SSE |
| 数据库（业务数据） | MySQL / PostgreSQL（SQLAlchemy 2.x async） |
| 数据库（报告缓存） | SQLite（`data/report_cache.db`） |
| LLM 调用 | OpenAI SDK 兼容接口（各引擎独立配置） |
| 前端 | 原生 HTML + Vanilla JS + Socket.IO Client |
| PDF 导出 | html2canvas + jsPDF（客户端） / WeasyPrint（服务端） |
| 爬虫 | Playwright（MediaCrawler） |
| NLP | Sentence-Transformers、jieba、WordCloud |

---

## 二、目录结构

```
BettaFish-main/
├── app.py                    # Flask 主服务入口（端口 8080）
├── runner.py                 # 纯 Python 流水线（三路引擎 + 报告合成）
├── config.py                 # Pydantic-Settings 统一配置
├── .env / .env.example       # 环境变量
│
├── InsightEngine/            # 本地数据库深度搜索 Agent
│   ├── agent.py
│   ├── nodes/                # FirstSearch / Reflection / Summary / Formatting
│   ├── tools/                # search.py / keyword_optimizer.py / sentiment_analyzer.py
│   ├── llms/base.py
│   ├── state/state.py
│   └── utils/db.py           # 异步 DB 连接池
│
├── MediaEngine/              # 网页多模态搜索 Agent
│   ├── agent.py
│   ├── nodes/
│   └── tools/search.py       # Bocha / Anspire 搜索
│
├── QueryEngine/              # 新闻查询 Agent
│   ├── agent.py
│   ├── nodes/
│   └── tools/search.py       # Tavily 搜索（6 种工具）
│
├── ReportEngine/             # 报告编排 Agent + Flask 接口
│   ├── agent.py
│   ├── flask_interface.py    # Blueprint: /api/report/*
│   ├── nodes/                # TemplateSelection / DocumentLayout / WordBudget / ChapterGeneration
│   ├── core/                 # chapter_storage.py / stitcher.py
│   ├── ir/schema.py          # JSON 中间表示（IR）
│   ├── renderers/            # html_renderer / pdf_renderer / markdown_renderer / chart_to_svg
│   └── report_template/      # 6 种预设模板
│
├── ForumEngine/              # 论坛讨论模拟 Agent
│   ├── llm_host.py
│   └── monitor.py
│
├── MindSpider/               # 爬虫 + 话题提取 + DB 初始化
│   ├── BroadTopicExtraction/ # 每日新闻抓取 + 话题提取
│   ├── DeepSentimentCrawling/# 关键词定向爬取
│   ├── MediaCrawler/         # 社交媒体爬虫（Playwright）
│   └── schema/               # mindspider_tables.sql / models_sa.py / init_database.py
│
├── SentimentAnalysisModel/   # 情感分析模型（4 种 + BERT 话题检测）
│
├── SingleEngineApp/          # Streamlit 独立应用（已废弃，仅保留）
│
├── templates/index.html      # 前端 SPA 主页面
├── static/
│   ├── css/space-theme.css
│   └── js/
│       ├── forum-state.js    # 论坛状态机 + 打字机终端
│       └── report-reader.js  # 报告阅读器 + ToC + 导出
│
├── utils/
│   └── report_cache.py       # SQLite 报告缓存（精确 + 模糊匹配）
│
└── data/
    └── report_cache.db       # SQLite 缓存文件
```

---

## 三、AI 引擎 LLM 分配

| 引擎 | LLM | 职责 |
|------|-----|------|
| InsightEngine | Kimi-K2 | 本地数据库深度搜索 + 反思迭代 |
| InsightEngine 关键词优化器 | Qwen-Plus | SQL 查询关键词优化 |
| MediaEngine | Gemini-2.5-Pro | 网页多模态搜索与分析 |
| QueryEngine | DeepSeek-Chat | 新闻查询与时事研究 |
| ReportEngine | Gemini-2.5-Pro | 报告编排与章节生成 |
| ForumEngine | Qwen-Plus | 论坛讨论模拟 |

---

## 四、数据库模型

### 4.1 业务数据库（MySQL/PostgreSQL）

**`daily_news`** — 每日新闻
| 字段 | 类型 | 说明 |
|------|------|------|
| news_id | VARCHAR | 新闻 ID |
| source_platform | VARCHAR | 来源平台 |
| title | TEXT | 标题 |
| url | TEXT | 链接 |
| description | TEXT | 摘要 |
| extra_info | JSON | 扩展信息 |
| crawl_date | DATE | 抓取日期 |
| rank_position | INT | 排名位置 |

**`daily_topics`** — 每日话题
| 字段 | 类型 | 说明 |
|------|------|------|
| topic_id | INT PK | 话题 ID |
| topic_name | VARCHAR | 话题名称 |
| topic_description | TEXT | 话题描述 |
| keywords | TEXT | 关键词 |
| extract_date | DATE | 提取日期 |
| relevance_score | FLOAT | 相关度评分 |
| news_count | INT | 关联新闻数 |
| processing_status | VARCHAR | 处理状态 |

**`topic_news_relation`** — 话题-新闻关联
| 字段 | 类型 | 说明 |
|------|------|------|
| topic_id | INT FK | 话题 ID |
| news_id | VARCHAR FK | 新闻 ID |
| relation_score | FLOAT | 关联评分 |
| extract_date | DATE | 提取日期 |

**`crawling_tasks`** — 爬取任务
| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | INT PK | 任务 ID |
| topic_id | INT FK | 话题 ID |
| platform | VARCHAR | 目标平台 |
| search_keywords | TEXT | 搜索关键词 |
| status | VARCHAR | 任务状态 |
| scheduled_date | DATE | 计划日期 |

### 4.2 报告缓存数据库（SQLite）

**`report_cache`** — 报告缓存
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 ID |
| task_id | TEXT | 搜索流水线短 hash |
| report_task_id | TEXT | ReportEngine 内部 ID（report-xxx） |
| query | TEXT | 归一化查询词 |
| query_raw | TEXT | 原始查询词 |
| html_content | TEXT | 报告 HTML 内容 |
| report_filepath | TEXT | 报告文件绝对路径 |
| report_relative_path | TEXT | 报告文件相对路径 |
| report_filename | TEXT | 报告文件名 |
| ir_filepath | TEXT | IR 文件路径 |
| ir_relative_path | TEXT | IR 相对路径 |
| engine_reports | TEXT | 各引擎原始报告（JSON） |
| warnings | TEXT | 警告信息（JSON） |
| token_usage | TEXT | Token 消耗统计（JSON） |
| created_at | TIMESTAMP | 创建时间 |

缓存策略：精确匹配（TTL 6小时）+ 模糊匹配（90天内相似度 ≥ 0.92）

---

## 五、API 接口清单

### 5.1 主服务接口（app.py）

#### 页面
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 返回前端 SPA 主页面 |
| GET | `/favicon.ico` | 返回空 204 |

#### 搜索流水线
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/search` | 启动搜索流水线，返回 `task_id`，进度通过 Socket.IO 推送 |
| GET | `/api/search/status/<task_id>` | 查询搜索任务状态（不含大体积 result） |

**POST /api/search 请求体：**
```json
{
  "query": "搜索关键词",
  "force_refresh": false
}
```
**响应：**
```json
{
  "task_id": "a1b2c3d4",
  "status": "started"
}
```

#### 报告结果与历史
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/report/result/<task_id>` | 获取报告 HTML（支持短 hash / report_1xxx / report-xxx 三种 ID 格式） |
| GET | `/api/report/history` | 获取历史报告列表（最多 50 条，来自 SQLite 缓存） |

#### 引擎生命周期
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/status` | 查询所有引擎进程状态（insight/media/query/forum） |
| GET | `/api/start/<app_name>` | 启动指定引擎 |
| GET | `/api/stop/<app_name>` | 停止指定引擎 |
| GET | `/api/output/<app_name>` | 获取引擎日志输出 |
| GET | `/api/test_log/<app_name>` | 写入测试日志并通过 Socket.IO 推送 |

#### 论坛管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/forum/start` | 启动论坛监控 |
| GET | `/api/forum/stop` | 停止论坛监控 |
| GET | `/api/forum/log` | 获取论坛日志（原始行 + 解析消息） |
| POST | `/api/forum/log/history` | 分页获取论坛日志（按字节位置） |

#### 配置管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/config` | 获取当前配置（过滤敏感字段） |
| POST | `/api/config` | 更新配置（写入 .env 并重载） |

#### 系统控制
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/system/status` | 获取系统启动状态 |
| POST | `/api/system/start` | 异步初始化系统（DB + ForumEngine + ReportEngine） |
| POST | `/api/system/shutdown` | 关闭系统，终止子进程 |

---

### 5.2 ReportEngine 接口（flask_interface.py，挂载于 /api/report）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/report/status` | 引擎就绪状态 + 缺失文件 + 当前任务摘要 |
| POST | `/api/report/generate` | 提交报告生成任务，返回 `task_id` 和 `stream_url` |
| GET | `/api/report/progress/<task_id>` | 轮询任务进度 |
| GET | `/api/report/stream/<task_id>` | SSE 流式进度（status/progress/log/stage 事件 + 心跳） |
| GET | `/api/report/result/<task_id>` | 获取报告 HTML（含缓存/文件兜底） |
| GET | `/api/report/result/<task_id>/json` | 获取报告结构化 JSON 元数据 |
| GET | `/api/report/download/<task_id>` | 下载报告文件 |
| POST | `/api/report/cancel/<task_id>` | 取消运行中的任务 |
| GET | `/api/report/templates` | 获取可用报告模板列表（6 种） |
| GET | `/api/report/log` | 获取 ReportEngine 日志 |
| POST | `/api/report/log/clear` | 清空 ReportEngine 日志 |
| GET | `/api/report/export/md/<task_id>` | 导出 Markdown 格式报告 |
| GET | `/api/report/export/pdf/<task_id>` | 导出 PDF 格式报告 |
| POST | `/api/report/export/pdf-from-ir` | 从 IR 中间表示导出 PDF |

**POST /api/report/generate 请求体：**
```json
{
  "query": "搜索关键词",
  "reports": ["引擎报告1", "引擎报告2"],
  "template": "",
  "forum_logs": ""
}
```

---

### 5.3 Socket.IO 实时事件

| 事件名（服务端发送） | 说明 |
|---------------------|------|
| `search_progress` | 搜索流水线进度推送 `{task_id, stage, message}` |
| `search_done` | 搜索完成 `{task_id, report_task_id, ...}` |
| `search_error` | 搜索失败 `{task_id, error}` |
| `console_output` | 引擎控制台日志输出 |
| `status_update` | 引擎状态变更 |

| 事件名（客户端发送） | 说明 |
|---------------------|------|
| `connect` | 建立连接 |
| `request_status` | 请求当前状态 |

---

## 六、报告模板类型（6 种）

| 模板 | 适用场景 |
|------|---------|
| 企业品牌声誉分析报告 | 品牌舆情监控 |
| 市场竞争格局舆情分析 | 竞品分析 |
| 日常/定期舆情监测 | 常规监测 |
| 特定政策或行业动态 | 政策/行业研究 |
| 社会公共热点事件 | 热点追踪 |
| 突发事件与危机公关 | 危机处理 |

---

## 七、前端页面与 API 对应关系

| 前端功能 | 调用接口 |
|---------|---------|
| 系统初始化 | `POST /api/system/start` |
| 提交搜索 | `POST /api/search` |
| 搜索进度展示 | Socket.IO `search_progress` / `search_done` |
| 报告展示（iframe） | `GET /api/report/result/<task_id>` |
| 历史报告列表 | `GET /api/report/history` |
| 配置查看/修改 | `GET/POST /api/config` |
| 论坛启停 | `GET /api/forum/start` / `GET /api/forum/stop` |
| 论坛日志 | `GET /api/forum/log` |
| 引擎状态面板 | `GET /api/status` |
| 报告导出（客户端PDF） | html2canvas + jsPDF（纯前端） |
| 报告导出（服务端） | `GET /api/report/export/pdf/<task_id>` |

---

## 八、模块依赖关系

```
前端 SPA (templates/index.html)
    │
    ├── HTTP/REST ──────────────────────────────────────────────────┐
    ├── WebSocket (Socket.IO) ──────────────────────────────────┐   │
    └── SSE (/api/report/stream) ──────────────────────────┐   │   │
                                                            │   │   │
                                                    app.py (Flask 主服务)
                                                            │
                                    ┌───────────────────────┼───────────────────────┐
                                    │                       │                       │
                              runner.py                ReportEngine           ForumEngine
                                    │               flask_interface.py
                    ┌───────────────┼───────────────┐       │
                    │               │               │   agent.py
              InsightEngine   MediaEngine    QueryEngine
                    │               │               │
              Kimi-K2        Gemini-2.5-Pro  DeepSeek-Chat
                    │
              MindSpider DB (MySQL/PostgreSQL)
```

---

## 九、搜索工具配置

| 工具 | 使用引擎 | 说明 |
|------|---------|------|
| Bocha AI | InsightEngine, MediaEngine | 多模态搜索（文本/图片/视频，5 种类型） |
| Anspire AI | InsightEngine, MediaEngine | 网页搜索（可选替代 Bocha） |
| Tavily | QueryEngine | 新闻搜索（6 种工具） |

通过 `.env` 中 `SEARCH_TOOL_TYPE` 切换 Bocha / Anspire。
