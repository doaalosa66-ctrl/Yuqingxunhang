"""
纯Python调用链 - 不依赖任何Web框架
终端测试: python runner.py "你的搜索主题"
"""
import sys
import os
import threading
import time as _time
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# 导入全局 Token 熔断器
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent / "utils"))
    from token_tracker import tracker as token_tracker, TokenBudgetExceeded
except ImportError:
    token_tracker = None
    class TokenBudgetExceeded(Exception):
        pass

ProgressCallback = None  # 类型提示占位，签名: (stage: str, message: str) -> None


def run_insight(query: str, progress_cb=None) -> dict:
    from InsightEngine.agent import DeepSearchAgent
    from InsightEngine.utils.config import Settings
    config = Settings()
    logger.info(f"[runner] InsightEngine 启动 query={query!r}")
    _t0 = _time.time()
    if progress_cb:
        progress_cb("insight", "InsightEngine 开始采集本地数据库...")
    agent = DeepSearchAgent(config)
    agent._generate_report_structure(query)
    # 用 MAX_PARAGRAPHS 截断段落数
    max_p = int(os.environ.get("MAX_PARAGRAPHS", len(agent.state.paragraphs)))
    if max_p < len(agent.state.paragraphs):
        agent.state.paragraphs = agent.state.paragraphs[:max_p]
        logger.info(f"[runner] InsightEngine 段落截断为 {max_p} 段")
    total = len(agent.state.paragraphs)
    logger.info(f"[runner] InsightEngine 报告结构生成完毕，共 {total} 段")
    for i in range(total):
        try:
            if progress_cb:
                progress_cb("insight", f"InsightEngine 分析段落 {i+1}/{total}...")
            agent._initial_search_and_summary(i)
            agent._reflection_loop(i)
            agent.state.paragraphs[i].research.mark_completed()
        except TokenBudgetExceeded:
            logger.warning(f"[runner] InsightEngine Token预算耗尽，已完成 {i}/{total} 段，带半成品数据继续")
            if progress_cb:
                progress_cb("insight", f"InsightEngine Token预算耗尽，已完成 {i}/{total} 段")
            break
    final_report = agent._generate_final_report()
    agent._save_report(final_report)
    elapsed = _time.time() - _t0
    logger.info(f"[runner] InsightEngine 完成 耗时={elapsed:.1f}s")
    if progress_cb:
        progress_cb("insight", "InsightEngine 采集完成")
    return {"engine": "insight", "report": final_report, "status": "done"}


def run_media(query: str, progress_cb=None) -> dict:
    from MediaEngine.utils.config import Settings
    config = Settings()
    logger.info(f"[runner] MediaEngine 启动 query={query!r} tool={config.SEARCH_TOOL_TYPE}")
    _t0 = _time.time()
    if config.SEARCH_TOOL_TYPE == "AnspireAPI":
        from MediaEngine.agent import AnspireSearchAgent as Agent
    else:
        from MediaEngine.agent import DeepSearchAgent as Agent
    if progress_cb:
        progress_cb("media", f"MediaEngine 开始采集网页数据 ({config.SEARCH_TOOL_TYPE})...")
    agent = Agent(config)
    agent._generate_report_structure(query)
    # 用 MAX_PARAGRAPHS 截断段落数
    max_p = int(os.environ.get("MAX_PARAGRAPHS", len(agent.state.paragraphs)))
    if max_p < len(agent.state.paragraphs):
        agent.state.paragraphs = agent.state.paragraphs[:max_p]
        logger.info(f"[runner] MediaEngine 段落截断为 {max_p} 段")
    total = len(agent.state.paragraphs)
    logger.info(f"[runner] MediaEngine 报告结构生成完毕，共 {total} 段")
    for i in range(total):
        try:
            if progress_cb:
                progress_cb("media", f"MediaEngine 分析段落 {i+1}/{total}...")
            agent._initial_search_and_summary(i)
            agent._reflection_loop(i)
            agent.state.paragraphs[i].research.mark_completed()
        except TokenBudgetExceeded:
            logger.warning(f"[runner] MediaEngine Token预算耗尽，已完成 {i}/{total} 段，带半成品数据继续")
            if progress_cb:
                progress_cb("media", f"MediaEngine Token预算耗尽，已完成 {i}/{total} 段")
            break
    final_report = agent._generate_final_report()
    agent._save_report(final_report)
    elapsed = _time.time() - _t0
    logger.info(f"[runner] MediaEngine 完成 耗时={elapsed:.1f}s")
    if progress_cb:
        progress_cb("media", "MediaEngine 采集完成")
    return {"engine": "media", "report": final_report, "status": "done"}


def run_query(query: str, progress_cb=None) -> dict:
    from QueryEngine.agent import DeepSearchAgent
    from QueryEngine.utils.config import Settings
    config = Settings()
    logger.info(f"[runner] QueryEngine 启动 query={query!r}")
    _t0 = _time.time()
    if progress_cb:
        progress_cb("query", "QueryEngine 开始采集新闻数据...")
    agent = DeepSearchAgent(config)
    agent._generate_report_structure(query)
    # 用 MAX_PARAGRAPHS 截断段落数
    max_p = int(os.environ.get("MAX_PARAGRAPHS", len(agent.state.paragraphs)))
    if max_p < len(agent.state.paragraphs):
        agent.state.paragraphs = agent.state.paragraphs[:max_p]
        logger.info(f"[runner] QueryEngine 段落截断为 {max_p} 段")
    total = len(agent.state.paragraphs)
    logger.info(f"[runner] QueryEngine 报告结构生成完毕，共 {total} 段")
    for i in range(total):
        try:
            if progress_cb:
                progress_cb("query", f"QueryEngine 分析段落 {i+1}/{total}...")
            agent._initial_search_and_summary(i)
            agent._reflection_loop(i)
            agent.state.paragraphs[i].research.mark_completed()
        except TokenBudgetExceeded:
            logger.warning(f"[runner] QueryEngine Token预算耗尽，已完成 {i}/{total} 段，带半成品数据继续")
            if progress_cb:
                progress_cb("query", f"QueryEngine Token预算耗尽，已完成 {i}/{total} 段")
            break
    final_report = agent._generate_final_report()
    agent._save_report(final_report)
    elapsed = _time.time() - _t0
    logger.info(f"[runner] QueryEngine 完成 耗时={elapsed:.1f}s")
    if progress_cb:
        progress_cb("query", "QueryEngine 采集完成")
    return {"engine": "query", "report": final_report, "status": "done"}


def run_all_engines(query: str, progress_cb=None) -> tuple:
    """三路并发采集，返回 (成功的报告列表, 警告列表)"""
    results = {}
    errors = {}
    lock = threading.Lock()
    _t0 = _time.time()
    logger.info(f"[runner] 三路引擎并发启动 query={query!r}")

    def _run(name, fn):
        try:
            r = fn(query, progress_cb)
            with lock:
                results[name] = r
        except Exception as e:
            logger.exception(f"[runner] {name} 引擎异常: {e}")
            with lock:
                errors[name] = str(e)
            if progress_cb:
                progress_cb(name, f"{name} 失败: {e}")

    threads = [
        threading.Thread(target=_run, args=("insight", run_insight), daemon=True),
        threading.Thread(target=_run, args=("media",   run_media),   daemon=True),
        threading.Thread(target=_run, args=("query",   run_query),   daemon=True),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    elapsed = _time.time() - _t0
    if errors:
        logger.warning(f"[runner] 部分引擎失败 errors={errors} 耗时={elapsed:.1f}s")
    logger.info(f"[runner] 三路引擎完成 成功={list(results.keys())} 失败={list(errors.keys())} 耗时={elapsed:.1f}s")

    # 生成人类可读的警告
    engine_names = {"insight": "本地数据库引擎", "media": "媒体采集引擎", "query": "新闻采集引擎"}
    warnings = [f"{engine_names.get(k, k)}跳过（{v}）" for k, v in errors.items()]

    ordered = ["insight", "media", "query"]
    return [results[k]["report"] for k in ordered if k in results], warnings


def run_report(query: str, reports: list, progress_cb=None) -> dict:
    """用 ReportEngine 把多份报告合成最终 HTML，跳过 ForumEngine"""
    from ReportEngine.agent import create_agent
    logger.info(f"[runner] ReportEngine 启动 reports_count={len(reports)}")
    _t0 = _time.time()
    if progress_cb:
        progress_cb("report", "ReportEngine 开始生成最终报告...")
    agent = create_agent()
    try:
        result = agent.generate_report(
            query=query,
            reports=reports,
            forum_logs="",       # 跳过 ForumEngine
            custom_template="",
            save_report=True,
        )
    except TokenBudgetExceeded:
        logger.warning("[runner] ReportEngine 阶段 Token预算耗尽，尝试用已有数据生成简化报告")
        if progress_cb:
            progress_cb("report", "Token预算耗尽，生成截断报告...")
        if agent.state.html_content:
            result = {'html_content': agent.state.html_content, 'warning': 'Token预算耗尽，报告可能不完整'}
        else:
            fallback_html = _build_fallback_html(query, reports)
            result = {'html_content': fallback_html, 'warning': 'Token预算耗尽，仅展示原始采集数据'}
    elapsed = _time.time() - _t0
    # 将 ReportEngine 内部生成的 report_id 透传到结果中，供前端直接使用
    if isinstance(result, dict) and agent.state.task_id:
        result.setdefault('report_task_id', agent.state.task_id)
    report_path = result.get('report_filepath') or result.get('report_relative_path', '') if isinstance(result, dict) else ''
    logger.info(f"[runner] ReportEngine 完成 耗时={elapsed:.1f}s report={report_path!r} report_task_id={result.get('report_task_id') if isinstance(result, dict) else ''!r}")
    if progress_cb:
        progress_cb("report", "报告生成完成")
    return result


def _build_fallback_html(query: str, reports: list) -> str:
    """Token 预算耗尽时的兜底 HTML：直接拼接各引擎原始报告。"""
    parts = [
        f"<html><head><meta charset='utf-8'><title>{query} - 截断报告</title></head><body>",
        f"<h1>{query} - 舆情分析报告（截断版）</h1>",
        "<p style='color:orange;'>⚠ 警告：Token 预算已耗尽，以下为各引擎原始采集数据，未经 AI 综合分析。</p>",
    ]
    engine_names = ["本地数据库分析", "媒体采集分析", "新闻采集分析"]
    for i, name in enumerate(engine_names):
        content = reports[i] if i < len(reports) else ""
        if content:
            parts.append(f"<h2>{name}</h2><pre style='white-space:pre-wrap;'>{content[:5000]}</pre>")
    parts.append("</body></html>")
    return "\n".join(parts)


def run_pipeline(query: str, progress_cb=None, force_refresh: bool = False, task_id: str = None) -> dict:
    """完整流水线：三路采集 → 报告合成，返回 ReportEngine 结果（含 warnings 字段）"""
    logger.info(f"[runner] 流水线启动 query={query!r} force_refresh={force_refresh}")
    _t0 = _time.time()

    # ── 缓存检查（直接读环境变量，避免 Settings 对象冲突） ──
    cache_enabled = os.environ.get('CACHE_ENABLED', 'true').lower() not in ('false', '0', 'no')
    cache_ttl = float(os.environ.get('CACHE_TTL_HOURS', '6.0'))

    report_cache = None
    if cache_enabled and not force_refresh:
        try:
            from utils.report_cache import cache as _cache
            report_cache = _cache
            cached = report_cache.get(query, ttl_hours=cache_ttl)
            if cached is not None:
                elapsed = _time.time() - _t0
                logger.info(f"[runner] 缓存命中 query={query!r} 耗时={elapsed:.3f}s")
                if progress_cb:
                    progress_cb("cache", "命中缓存，直接返回历史报告")
                return cached
        except Exception as e:
            logger.warning(f"[runner] 缓存查询失败，继续正常流水线: {e}")

    if progress_cb:
        progress_cb("cache", "未命中缓存，开始完整分析流程...")

    # ── 正常流水线 ──
    # 每次任务开始前重置 Token 计数器
    if token_tracker:
        token_tracker.reset()

    reports, warnings = run_all_engines(query, progress_cb=progress_cb)
    if not reports:
        logger.error(f"[runner] 所有采集引擎均失败，流水线中止")
        raise RuntimeError("所有采集引擎均失败，无法生成报告")
    result = run_report(query, reports, progress_cb=progress_cb)
    elapsed = _time.time() - _t0

    # 打印本次任务的 Token 消耗摘要
    if token_tracker:
        logger.info(f"[runner] {token_tracker.summary()}")

    logger.info(f"[runner] 流水线完成 总耗时={elapsed:.1f}s warnings={warnings}")
    # 把警告和 Token 消耗挂到结果上，供 app.py 透传给前端
    if isinstance(result, dict):
        result['warnings'] = warnings
        if token_tracker:
            result['token_usage'] = {
                'total_tokens': token_tracker.total_tokens,
                'call_count': token_tracker.call_count,
            }
        result['from_cache'] = False

    # ── 写入缓存 ──
    if cache_enabled and isinstance(result, dict):
        try:
            if report_cache is None:
                from utils.report_cache import cache as _cache
                report_cache = _cache
            report_cache.put(query, result, engine_reports=reports, task_id=task_id)
        except Exception as e:
            logger.warning(f"[runner] 缓存写入失败（不影响结果）: {e}")

    return result


# ── 终端直接测试入口 ──────────────────────────────────────────
def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "人工智能行业舆情分析"

    print(f"\n{'='*55}")
    print(f"  开始分析: {query}")
    print(f"{'='*55}\n")

    def log(stage, msg):
        print(f"  [{stage.upper():8s}] {msg}")

    try:
        result = run_pipeline(query, progress_cb=log)
        print(f"\n{'='*55}")
        print("  完成！")
        if isinstance(result, dict):
            path = result.get("report_filepath") or result.get("report_relative_path", "")
            if path:
                print(f"  报告路径: {path}")
        print(f"{'='*55}\n")
    except Exception as e:
        print(f"\n[错误] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
