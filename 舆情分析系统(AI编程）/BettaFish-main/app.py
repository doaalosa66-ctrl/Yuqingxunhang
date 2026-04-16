"""
Flask主应用 - 统一管理三个Streamlit应用
"""

import os
import sys

# 【修复】尽早设置环境变量，确保所有模块都使用无缓冲模式
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONUNBUFFERED'] = '1'  # 禁用Python输出缓冲，确保日志实时输出

import subprocess
import time
import threading
from datetime import datetime
from queue import Queue
from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
import atexit
import requests
from loguru import logger
import importlib
from pathlib import Path
from MindSpider.main import MindSpider

# 导入ReportEngine
try:
    from ReportEngine.flask_interface import report_bp, initialize_report_engine
    REPORT_ENGINE_AVAILABLE = True
except ImportError as e:
    logger.error(f"ReportEngine导入失败: {e}")
    REPORT_ENGINE_AVAILABLE = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Dedicated-to-creating-a-concise-and-versatile-public-opinion-analysis-platform'
app.config['TEMPLATES_AUTO_RELOAD'] = True
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 纯Python搜索任务注册表
_search_tasks = {}

# eventlet 在客户端主动断开时偶尔会抛出 ConnectionAbortedError，这里做一次防御性包裹，
# 避免无意义的堆栈污染日志（仅在 eventlet 可用时启用）。
def _patch_eventlet_disconnect_logging():
    try:
        import eventlet.wsgi  # type: ignore
    except Exception as exc:  # pragma: no cover - 仅在生产环境有效
        logger.debug(f"eventlet 不可用，跳过断开补丁: {exc}")
        return

    try:
        original_finish = eventlet.wsgi.HttpProtocol.finish  # type: ignore[attr-defined]
    except Exception as exc:  # pragma: no cover
        logger.debug(f"eventlet 缺少 HttpProtocol.finish，跳过断开补丁: {exc}")
        return

    def _safe_finish(self, *args, **kwargs):  # pragma: no cover - 运行时才会触发
        try:
            return original_finish(self, *args, **kwargs)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError) as exc:
            try:
                environ = getattr(self, 'environ', {}) or {}
                method = environ.get('REQUEST_METHOD', '')
                path = environ.get('PATH_INFO', '')
                logger.warning(f"客户端已主动断开，忽略异常: {method} {path} ({exc})")
            except Exception:
                logger.warning(f"客户端已主动断开，忽略异常: {exc}")
            return

    eventlet.wsgi.HttpProtocol.finish = _safe_finish  # type: ignore[attr-defined]
    logger.info("已对 eventlet 连接中断进行安全防护")

_patch_eventlet_disconnect_logging()

# 注册ReportEngine Blueprint
if REPORT_ENGINE_AVAILABLE:
    app.register_blueprint(report_bp, url_prefix='/api/report')
    logger.info("ReportEngine接口已注册")
else:
    logger.info("ReportEngine不可用，跳过接口注册")

# 创建日志目录
LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True)

CONFIG_MODULE_NAME = 'config'
CONFIG_FILE_PATH = Path(__file__).resolve().parent / 'config.py'
CONFIG_KEYS = [
    'HOST',
    'PORT',
    'DB_DIALECT',
    'DB_HOST',
    'DB_PORT',
    'DB_USER',
    'DB_PASSWORD',
    'DB_NAME',
    'DB_CHARSET',
    'INSIGHT_ENGINE_API_KEY',
    'INSIGHT_ENGINE_BASE_URL',
    'INSIGHT_ENGINE_MODEL_NAME',
    'MEDIA_ENGINE_API_KEY',
    'MEDIA_ENGINE_BASE_URL',
    'MEDIA_ENGINE_MODEL_NAME',
    'QUERY_ENGINE_API_KEY',
    'QUERY_ENGINE_BASE_URL',
    'QUERY_ENGINE_MODEL_NAME',
    'REPORT_ENGINE_API_KEY',
    'REPORT_ENGINE_BASE_URL',
    'REPORT_ENGINE_MODEL_NAME',
    'FORUM_HOST_API_KEY',
    'FORUM_HOST_BASE_URL',
    'FORUM_HOST_MODEL_NAME',
    'KEYWORD_OPTIMIZER_API_KEY',
    'KEYWORD_OPTIMIZER_BASE_URL',
    'KEYWORD_OPTIMIZER_MODEL_NAME',
    'TAVILY_API_KEY',
    'SEARCH_TOOL_TYPE',
    'BOCHA_WEB_SEARCH_API_KEY',
    'ANSPIRE_API_KEY',
    'CACHE_ENABLED',
    'CACHE_TTL_HOURS',
]


def _load_config_module():
    """Load or reload the config module to ensure latest values are available."""
    importlib.invalidate_caches()
    module = sys.modules.get(CONFIG_MODULE_NAME)
    try:
        if module is None:
            module = importlib.import_module(CONFIG_MODULE_NAME)
        else:
            module = importlib.reload(module)
    except ModuleNotFoundError:
        return None
    return module


def read_config_values():
    """Return the current configuration values that are exposed to the frontend."""
    try:
        # 重新加载配置以获取最新的 Settings 实例
        from config import reload_settings
        current_settings = reload_settings()

        values = {}
        for key in CONFIG_KEYS:
            # 从 Pydantic Settings 实例读取值
            value = getattr(current_settings, key, None)
            # Convert to string for uniform handling on the frontend.
            if value is None:
                values[key] = ''
            else:
                values[key] = str(value)
        return values
    except Exception as exc:
        logger.exception(f"读取配置失败: {exc}")
        return {}


def _serialize_config_value(value):
    """Serialize Python values back to a config.py assignment-friendly string."""
    if isinstance(value, bool):
        return 'True' if value else 'False'
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return 'None'

    value_str = str(value)
    escaped = value_str.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'


def write_config_values(updates):
    """Persist configuration updates to .env file (Pydantic Settings source)."""
    from pathlib import Path
    
    # 确定 .env 文件路径（与 config.py 中的逻辑一致）
    project_root = Path(__file__).resolve().parent
    cwd_env = Path.cwd() / ".env"
    env_file_path = cwd_env if cwd_env.exists() else (project_root / ".env")
    
    # 读取现有的 .env 文件内容
    env_lines = []
    env_key_indices = {}  # 记录每个键在文件中的索引位置
    if env_file_path.exists():
        env_lines = env_file_path.read_text(encoding='utf-8').splitlines()
        # 提取已存在的键及其索引
        for i, line in enumerate(env_lines):
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith('#'):
                if '=' in line_stripped:
                    key = line_stripped.split('=')[0].strip()
                    env_key_indices[key] = i
    
    # 更新或添加配置项
    for key, raw_value in updates.items():
        # 格式化值用于 .env 文件（不需要引号，除非是字符串且包含空格）
        if raw_value is None or raw_value == '':
            env_value = ''
        elif isinstance(raw_value, (int, float)):
            env_value = str(raw_value)
        elif isinstance(raw_value, bool):
            env_value = 'True' if raw_value else 'False'
        else:
            value_str = str(raw_value)
            # 如果包含空格或特殊字符，需要引号
            if ' ' in value_str or '\n' in value_str or '#' in value_str:
                escaped = value_str.replace('\\', '\\\\').replace('"', '\\"')
                env_value = f'"{escaped}"'
            else:
                env_value = value_str
        
        # 更新或添加配置项
        if key in env_key_indices:
            # 更新现有行
            env_lines[env_key_indices[key]] = f'{key}={env_value}'
        else:
            # 添加新行到文件末尾
            env_lines.append(f'{key}={env_value}')
    
    # 写入 .env 文件
    env_file_path.parent.mkdir(parents=True, exist_ok=True)
    env_file_path.write_text('\n'.join(env_lines) + '\n', encoding='utf-8')
    
    # 重新加载配置模块（这会重新读取 .env 文件并创建新的 Settings 实例）
    _load_config_module()


system_state_lock = threading.Lock()
system_state = {
    'started': False,
    'starting': False,
    'shutdown_in_progress': False
}


def _set_system_state(*, started=None, starting=None):
    """Safely update the cached system state flags."""
    with system_state_lock:
        if started is not None:
            system_state['started'] = started
        if starting is not None:
            system_state['starting'] = starting


def _get_system_state():
    """Return a shallow copy of the system state flags."""
    with system_state_lock:
        return system_state.copy()


def _prepare_system_start():
    """Mark the system as starting if it is not already running or starting."""
    with system_state_lock:
        if system_state['started']:
            return False, '系统已启动'
        if system_state['starting']:
            return False, '系统正在启动'
        system_state['starting'] = True
        return True, None

def _mark_shutdown_requested():
    """标记关机已请求；若已有关机流程则返回 False。"""
    with system_state_lock:
        if system_state.get('shutdown_in_progress'):
            return False
        system_state['shutdown_in_progress'] = True
        return True


def _emit_start_progress(app, status, message):
    """向前端推送启动进度。"""
    try:
        socketio.emit('system_start_progress', {'app': app, 'status': status, 'message': message})
    except Exception:
        pass


def initialize_system_components():
    """启动所有依赖组件（数据库、ForumEngine、ReportEngine）。Streamlit 子应用已废弃，系统改用纯 Python runner。"""
    import time as _time
    _t0 = _time.time()
    logs = []
    errors = []
    logger.info("[系统启动] ========== initialize_system_components 开始 ==========")

    # ---- 数据库 ----
    _emit_start_progress('db', 'starting', '正在初始化数据库...')
    try:
        spider = MindSpider()
        if spider.initialize_database():
            logger.info("[系统启动] 数据库初始化成功")
            _emit_start_progress('db', 'running', '数据库初始化成功')
        else:
            logger.error("[系统启动] 数据库初始化失败（返回False）")
            _emit_start_progress('db', 'error', '数据库初始化失败')
            errors.append("数据库初始化失败")
    except Exception as exc:
        logger.exception(f"[系统启动] 数据库初始化异常: {exc}")
        _emit_start_progress('db', 'error', f'数据库异常: {exc}')
        errors.append(f"数据库异常: {exc}")

    # ---- Streamlit 引擎已废弃，直接标记为跳过 ----
    for app_name in list(STREAMLIT_SCRIPTS.keys()):
        _emit_start_progress(app_name, 'running', f'{app_name} 已由纯Python后端接管，无需启动')
        logger.info(f"[系统启动] 跳过 Streamlit 引擎: {app_name}（纯Python模式）")

    # ---- ForumEngine ----
    try:
        stop_forum_engine()
    except Exception:
        pass
    processes['forum']['status'] = 'stopped'

    _emit_start_progress('forum', 'starting', '正在启动 ForumEngine...')
    logger.info("[系统启动] 启动 ForumEngine...")
    try:
        start_forum_engine()
        processes['forum']['status'] = 'running'
        logs.append("ForumEngine 启动完成")
        _emit_start_progress('forum', 'running', 'ForumEngine 启动成功')
        logger.info("[系统启动] ✓ ForumEngine 启动成功")
    except Exception as exc:
        error_msg = f"ForumEngine 启动失败: {exc}"
        logs.append(error_msg)
        errors.append(error_msg)
        _emit_start_progress('forum', 'error', error_msg)
        logger.exception(f"[系统启动] ✗ ForumEngine 启动异常: {exc}")

    # ---- ReportEngine ----
    if REPORT_ENGINE_AVAILABLE:
        _emit_start_progress('report', 'starting', '正在初始化 ReportEngine...')
        logger.info("[系统启动] 初始化 ReportEngine...")
        try:
            if initialize_report_engine():
                logs.append("ReportEngine 初始化成功")
                _emit_start_progress('report', 'running', 'ReportEngine 初始化成功')
                logger.info("[系统启动] ✓ ReportEngine 初始化成功")
            else:
                msg = "ReportEngine 初始化失败"
                logs.append(msg)
                errors.append(msg)
                _emit_start_progress('report', 'error', msg)
                logger.error("[系统启动] ✗ ReportEngine 初始化失败（返回False）")
        except Exception as exc:
            msg = f"ReportEngine 初始化异常: {exc}"
            logs.append(msg)
            errors.append(msg)
            _emit_start_progress('report', 'error', msg)
            logger.exception(f"[系统启动] ✗ ReportEngine 初始化异常: {exc}")
    else:
        logger.warning("[系统启动] ReportEngine 不可用，跳过初始化")

    _t2 = _time.time()
    logger.info(f"[系统启动] ========== 启动完成 总耗时={_t2-_t0:.1f}s, 错误={len(errors)} ==========")
    if errors:
        logger.warning(f"[系统启动] 错误汇总: {errors}")

    return True, logs, errors

# 初始化ForumEngine的forum.log文件
def init_forum_log():
    """初始化forum.log文件"""
    try:
        forum_log_file = LOG_DIR / "forum.log"
        # 检查文件不存在则创建并且写一个开始，存在就清空写一个开始
        if not forum_log_file.exists():
            with open(forum_log_file, 'w', encoding='utf-8') as f:
                start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"=== ForumEngine 系统初始化 - {start_time} ===\n")
            logger.info(f"ForumEngine: forum.log 已初始化")
        else:
            with open(forum_log_file, 'w', encoding='utf-8') as f:
                start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"=== ForumEngine 系统初始化 - {start_time} ===\n")
            logger.info(f"ForumEngine: forum.log 已初始化")
    except Exception as e:
        logger.exception(f"ForumEngine: 初始化forum.log失败: {e}")

# 初始化forum.log
init_forum_log()

# 启动ForumEngine智能监控
def start_forum_engine():
    """启动ForumEngine论坛"""
    try:
        from ForumEngine.monitor import start_forum_monitoring
        logger.info("ForumEngine: 启动论坛...")
        success = start_forum_monitoring()
        if not success:
            logger.info("ForumEngine: 论坛启动失败")
    except Exception as e:
        logger.exception(f"ForumEngine: 启动论坛失败: {e}")

# 停止ForumEngine智能监控
def stop_forum_engine():
    """停止ForumEngine论坛"""
    try:
        from ForumEngine.monitor import stop_forum_monitoring
        logger.info("ForumEngine: 停止论坛...")
        stop_forum_monitoring()
        logger.info("ForumEngine: 论坛已停止")
    except Exception as e:
        logger.exception(f"ForumEngine: 停止论坛失败: {e}")

def parse_forum_log_line(line):
    """解析forum.log行内容，提取对话信息"""
    import re
    
    # 匹配格式: [时间] [来源] 内容（来源允许大小写及空格）
    pattern = r'\[(\d{2}:\d{2}:\d{2})\]\s*\[([^\]]+)\]\s*(.*)'
    match = re.match(pattern, line)
    
    if not match:
        return None

    timestamp, raw_source, content = match.groups()
    source = raw_source.strip().upper()

    # 过滤掉系统消息和空内容
    if source == 'SYSTEM' or not content.strip():
        return None
    
    # 支持三个Agent和主持人
    if source not in ['QUERY', 'INSIGHT', 'MEDIA', 'HOST']:
        return None
    
    # 解码日志中的转义换行，保留多行格式
    cleaned_content = content.replace('\\n', '\n').replace('\\r', '').strip()
    
    # 根据来源确定消息类型和发送者
    if source == 'HOST':
        message_type = 'host'
        sender = 'Forum Host'
    else:
        message_type = 'agent'
        sender = f'{source.title()} Engine'
    
    return {
        'type': message_type,
        'sender': sender,
        'content': cleaned_content,
        'timestamp': timestamp,
        'source': source
    }

# Forum日志监听器
# 存储每个客户端的历史日志发送位置
forum_log_positions = {}

def monitor_forum_log():
    """监听forum.log文件变化并推送到前端"""
    import time
    from pathlib import Path

    forum_log_file = LOG_DIR / "forum.log"
    last_position = 0
    processed_lines = set()  # 用于跟踪已处理的行，避免重复

    # 如果文件存在，获取初始位置但不跳过内容
    if forum_log_file.exists():
        with open(forum_log_file, 'r', encoding='utf-8', errors='ignore') as f:
            # 记录文件大小，但不添加到processed_lines
            # 这样用户打开forum标签时可以获取历史
            f.seek(0, 2)  # 移到文件末尾
            last_position = f.tell()

    while True:
        try:
            if forum_log_file.exists():
                with open(forum_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(last_position)
                    new_lines = f.readlines()

                    if new_lines:
                        for line in new_lines:
                            line = line.rstrip('\n\r')
                            if line.strip():
                                line_hash = hash(line.strip())

                                # 避免重复处理同一行
                                if line_hash in processed_lines:
                                    continue

                                processed_lines.add(line_hash)

                                # 解析日志行并发送forum消息
                                parsed_message = parse_forum_log_line(line)
                                if parsed_message:
                                    socketio.emit('forum_message', parsed_message)

                                # 只有在控制台显示forum时才发送控制台消息
                                timestamp = datetime.now().strftime('%H:%M:%S')
                                formatted_line = f"[{timestamp}] {line}"
                                socketio.emit('console_output', {
                                    'app': 'forum',
                                    'line': formatted_line
                                })

                        last_position = f.tell()

                        # 清理processed_lines集合，避免内存泄漏（保留最近1000行的哈希）
                        if len(processed_lines) > 1000:
                            # 保留最近500行的哈希
                            recent_hashes = list(processed_lines)[-500:]
                            processed_lines = set(recent_hashes)

            time.sleep(1)  # 每秒检查一次
        except Exception as e:
            logger.error(f"Forum日志监听错误: {e}")
            time.sleep(5)

# 启动Forum日志监听线程
forum_monitor_thread = threading.Thread(target=monitor_forum_log, daemon=True)
forum_monitor_thread.start()

# 全局变量存储进程信息
processes = {
    'insight': {'process': None, 'port': 8501, 'status': 'stopped', 'output': [], 'log_file': None, 'healthcheck_started_at': None},
    'media': {'process': None, 'port': 8502, 'status': 'stopped', 'output': [], 'log_file': None, 'healthcheck_started_at': None},
    'query': {'process': None, 'port': 8503, 'status': 'stopped', 'output': [], 'log_file': None, 'healthcheck_started_at': None},
    'forum': {'process': None, 'port': None, 'status': 'stopped', 'output': [], 'log_file': None}  # 启动后标记为 running
}

STREAMLIT_SCRIPTS = {
    'insight': 'SingleEngineApp/insight_engine_streamlit_app.py',
    'media': 'SingleEngineApp/media_engine_streamlit_app.py',
    'query': 'SingleEngineApp/query_engine_streamlit_app.py'
}

def _log_shutdown_step(message: str):
    """统一记录关机步骤，便于排查。"""
    logger.info(f"[Shutdown] {message}")


def _describe_running_children():
    """列出当前存活的子进程。"""
    running = []
    for name, info in processes.items():
        proc = info.get('process')
        if proc is not None and proc.poll() is None:
            port_desc = f", port={info.get('port')}" if info.get('port') else ""
            running.append(f"{name}(pid={proc.pid}{port_desc})")
    return running

# 输出队列
output_queues = {
    'insight': Queue(),
    'media': Queue(),
    'query': Queue(),
    'forum': Queue()
}

def write_log_to_file(app_name, line):
    """将日志写入文件"""
    try:
        log_file_path = LOG_DIR / f"{app_name}.log"
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
            f.flush()
    except Exception as e:
        logger.error(f"Error writing log for {app_name}: {e}")

def read_log_from_file(app_name, tail_lines=None):
    """从文件读取日志"""
    try:
        log_file_path = LOG_DIR / f"{app_name}.log"
        if not log_file_path.exists():
            return []
        
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            lines = [line.rstrip('\n\r') for line in lines if line.strip()]
            
            if tail_lines:
                return lines[-tail_lines:]
            return lines
    except Exception as e:
        logger.exception(f"Error reading log for {app_name}: {e}")
        return []

def read_process_output(process, app_name):
    """读取进程输出并写入文件"""
    import select
    import sys
    
    while True:
        try:
            if process.poll() is not None:
                # 进程结束，读取剩余输出
                remaining_output = process.stdout.read()
                if remaining_output:
                    lines = remaining_output.decode('utf-8', errors='replace').split('\n')
                    for line in lines:
                        line = line.strip()
                        if line:
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            formatted_line = f"[{timestamp}] {line}"
                            write_log_to_file(app_name, formatted_line)
                            socketio.emit('console_output', {
                                'app': app_name,
                                'line': formatted_line
                            })
                break
            
            # 使用非阻塞读取
            if sys.platform == 'win32':
                # Windows下使用不同的方法
                output = process.stdout.readline()
                if output:
                    line = output.decode('utf-8', errors='replace').strip()
                    if line:
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        formatted_line = f"[{timestamp}] {line}"
                        
                        # 写入日志文件
                        write_log_to_file(app_name, formatted_line)
                        
                        # 发送到前端
                        socketio.emit('console_output', {
                            'app': app_name,
                            'line': formatted_line
                        })
                else:
                    # 没有输出时短暂休眠
                    time.sleep(0.1)
            else:
                # Unix系统使用select
                ready, _, _ = select.select([process.stdout], [], [], 0.1)
                if ready:
                    output = process.stdout.readline()
                    if output:
                        line = output.decode('utf-8', errors='replace').strip()
                        if line:
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            formatted_line = f"[{timestamp}] {line}"
                            
                            # 写入日志文件
                            write_log_to_file(app_name, formatted_line)
                            
                            # 发送到前端
                            socketio.emit('console_output', {
                                'app': app_name,
                                'line': formatted_line
                            })
                            
        except Exception as e:
            error_msg = f"Error reading output for {app_name}: {e}"
            logger.exception(error_msg)
            write_log_to_file(app_name, f"[{datetime.now().strftime('%H:%M:%S')}] {error_msg}")
            break

def start_streamlit_app(app_name, script_path, port):
    """启动Streamlit应用"""
    try:
        if processes[app_name]['process'] is not None:
            logger.info(f"[启动] {app_name} 已在运行，跳过")
            return False, "应用已经在运行"

        # 检查文件是否存在
        if not os.path.exists(script_path):
            logger.error(f"[启动] {app_name} 脚本不存在: {script_path}")
            return False, f"文件不存在: {script_path}"

        # 清空之前的日志文件
        log_file_path = LOG_DIR / f"{app_name}.log"
        if log_file_path.exists():
            log_file_path.unlink()

        # 创建启动日志并推送到前端
        start_msg = f"[{datetime.now().strftime('%H:%M:%S')}] [{app_name.upper()}] 🚀 正在启动引擎，端口 {port}..."
        write_log_to_file(app_name, start_msg)
        socketio.emit('console_output', {'app': app_name, 'line': start_msg})

        cmd = [
            sys.executable, '-m', 'streamlit', 'run',
            script_path,
            '--server.port', str(port),
            '--server.address', '127.0.0.1',
            '--server.headless', 'true',
            '--browser.gatherUsageStats', 'false',
            '--logger.level', 'info',
            '--server.enableXsrfProtection', 'false',
        ]
        logger.info(f"[启动] {app_name} 启动命令: {' '.join(cmd)}")
        
        # 设置环境变量确保UTF-8编码和减少缓冲
        env = os.environ.copy()
        env.update({
            'PYTHONIOENCODING': 'utf-8',
            'PYTHONUTF8': '1',
            'LANG': 'en_US.UTF-8',
            'LC_ALL': 'en_US.UTF-8',
            'PYTHONUNBUFFERED': '1',  # 禁用Python缓冲
            'STREAMLIT_BROWSER_GATHER_USAGE_STATS': 'false'
        })
        
        # 使用当前工作目录而不是脚本目录
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,  # 无缓冲
            universal_newlines=False,
            cwd=os.getcwd(),
            env=env,
            encoding=None,  # 让我们手动处理编码
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        processes[app_name]['process'] = process
        processes[app_name]['status'] = 'starting'
        processes[app_name]['output'] = []
        processes[app_name]['healthcheck_started_at'] = time.time()
        logger.info(f"[启动] {app_name} 子进程已创建, pid={process.pid}, 端口={port}")
        
        # 启动输出读取线程
        output_thread = threading.Thread(
            target=read_process_output,
            args=(process, app_name),
            daemon=True
        )
        output_thread.start()
        
        return True, f"{app_name} 应用启动中..."
        
    except Exception as e:
        error_msg = f"启动失败: {str(e)}"
        ts = datetime.now().strftime('%H:%M:%S')
        full_msg = f"[{ts}] [{app_name.upper()}] ❌ {error_msg}"
        write_log_to_file(app_name, full_msg)
        socketio.emit('console_output', {'app': app_name, 'line': full_msg})
        return False, error_msg

def stop_streamlit_app(app_name):
    """停止Streamlit应用"""
    try:
        process = processes[app_name]['process']
        if process is None:
            _log_shutdown_step(f"{app_name} 未运行，跳过停止")
            return False, "应用未运行"
        
        try:
            pid = process.pid
        except Exception:
            pid = 'unknown'

        _log_shutdown_step(f"正在停止 {app_name} (pid={pid})")
        process.terminate()
        
        # 等待进程结束
        try:
            process.wait(timeout=5)
            _log_shutdown_step(f"{app_name} 退出完成，returncode={process.returncode}")
        except subprocess.TimeoutExpired:
            _log_shutdown_step(f"{app_name} 终止超时，尝试强制结束 (pid={pid})")
            process.kill()
            process.wait()
            _log_shutdown_step(f"{app_name} 已强制结束，returncode={process.returncode}")
        
        processes[app_name]['process'] = None
        processes[app_name]['status'] = 'stopped'
        processes[app_name]['healthcheck_started_at'] = None
        
        return True, f"{app_name} 应用已停止"
        
    except Exception as e:
        _log_shutdown_step(f"{app_name} 停止失败: {e}")
        return False, f"停止失败: {str(e)}"

HEALTHCHECK_PATH = "/_stcore/health"
HEALTHCHECK_PROXIES = {'http': None, 'https': None}
HEALTHCHECK_GRACE_SECONDS = 60


def _build_healthcheck_url(port):
    return f"http://127.0.0.1:{port}{HEALTHCHECK_PATH}"


def _healthcheck_grace_active(app_name: str) -> bool:
    started_at = processes.get(app_name, {}).get('healthcheck_started_at')
    if not started_at:
        return False
    return (time.time() - started_at) < HEALTHCHECK_GRACE_SECONDS


def _log_healthcheck_failure(app_name: str, exc: Exception):
    if _healthcheck_grace_active(app_name):
        logger.debug(f"正在启动{app_name}，请等待")
        return
    logger.warning(f"{app_name} 健康检查失败: {exc}")


def check_app_status():
    """检查应用状态"""
    status_changed = False
    for app_name, info in processes.items():
        if info['process'] is not None:
            if info['process'].poll() is None:
                # 进程仍在运行，检查端口是否可访问
                prev_status = info.get('status', 'unknown')
                try:
                    response = requests.get(
                        _build_healthcheck_url(info['port']),
                        timeout=2,
                        proxies=HEALTHCHECK_PROXIES
                    )
                    if response.status_code == 200:
                        info['status'] = 'running'
                        if prev_status != 'running':
                            ts = datetime.now().strftime('%H:%M:%S')
                            msg = f"[{ts}] [{app_name.upper()}] ✅ 引擎就绪，端口 {info['port']} 健康检查通过"
                            write_log_to_file(app_name, msg)
                            socketio.emit('console_output', {'app': app_name, 'line': msg})
                            status_changed = True
                    else:
                        info['status'] = 'starting'
                except Exception as exc:
                    _log_healthcheck_failure(app_name, exc)
                    info['status'] = 'starting'
            else:
                # 进程已结束
                prev_status = info.get('status', 'unknown')
                info['process'] = None
                info['status'] = 'stopped'
                info['healthcheck_started_at'] = None
                if prev_status not in ('stopped', 'unknown'):
                    ts = datetime.now().strftime('%H:%M:%S')
                    msg = f"[{ts}] [{app_name.upper()}] ⚠️ 引擎进程已退出（上一状态：{prev_status}）"
                    write_log_to_file(app_name, msg)
                    socketio.emit('console_output', {'app': app_name, 'line': msg})
                    status_changed = True
        elif info.get('port') and info.get('status') != 'running':
            # process 为 None（Flask 重启后丢失了子进程句柄），但端口可能仍在监听
            # 做一次端口探测，如果健康检查通过则标记为 running
            try:
                response = requests.get(
                    _build_healthcheck_url(info['port']),
                    timeout=2,
                    proxies=HEALTHCHECK_PROXIES
                )
                if response.status_code == 200:
                    prev_status = info.get('status', 'unknown')
                    info['status'] = 'running'
                    if prev_status != 'running':
                        ts = datetime.now().strftime('%H:%M:%S')
                        msg = f"[{ts}] [{app_name.upper()}] ✅ 检测到引擎已在运行（端口 {info['port']}）"
                        write_log_to_file(app_name, msg)
                        socketio.emit('console_output', {'app': app_name, 'line': msg})
                        status_changed = True
            except Exception:
                pass  # 端口未监听，保持 stopped
    
    # 如果状态发生变化，发送status_update事件
    if status_changed:
        socketio.emit('status_update', {
            app_name: {
                'status': info['status'],
                'port': info['port']
            }
            for app_name, info in processes.items()
        })

def wait_for_app_startup(app_name, max_wait_time=90):
    """等待应用启动完成"""
    import time
    start_time = time.time()
    url = _build_healthcheck_url(processes[app_name]['port'])
    logger.info(f"[健康检查] {app_name} 开始等待启动, 健康检查URL={url}, 超时={max_wait_time}s")
    while time.time() - start_time < max_wait_time:
        info = processes[app_name]
        if info['process'] is None:
            logger.error(f"[健康检查] {app_name} 进程对象为None，已停止")
            return False, "进程已停止"

        poll_result = info['process'].poll()
        if poll_result is not None:
            logger.error(f"[健康检查] {app_name} 进程已退出, returncode={poll_result}")
            return False, f"进程启动失败(exit={poll_result})"

        elapsed = int(time.time() - start_time)
        try:
            response = requests.get(url, timeout=2, proxies=HEALTHCHECK_PROXIES)
            if response.status_code == 200:
                logger.info(f"[健康检查] {app_name} 启动成功! 耗时={elapsed}s, status=200")
                info['status'] = 'running'
                return True, "启动成功"
            else:
                logger.debug(f"[健康检查] {app_name} 返回非200: status={response.status_code}, 已等待{elapsed}s")
        except Exception as exc:
            if elapsed % 10 == 0:  # 每10秒打一次详细日志，避免刷屏
                logger.info(f"[健康检查] {app_name} 连接失败: {type(exc).__name__}, 已等待{elapsed}s/{max_wait_time}s")
            _log_healthcheck_failure(app_name, exc)

        time.sleep(1)

    elapsed = int(time.time() - start_time)
    logger.error(f"[健康检查] {app_name} 启动超时! 已等待{elapsed}s, 进程存活={info['process'] is not None and info['process'].poll() is None}")
    return False, f"启动超时({elapsed}s)"

def cleanup_processes():
    """清理所有进程"""
    _log_shutdown_step("开始串行清理子进程")
    for app_name in STREAMLIT_SCRIPTS:
        stop_streamlit_app(app_name)

    processes['forum']['status'] = 'stopped'
    try:
        stop_forum_engine()
    except Exception:  # pragma: no cover
        logger.exception("停止ForumEngine失败")
    _log_shutdown_step("子进程清理完成")
    _set_system_state(started=False, starting=False)

def cleanup_processes_concurrent(timeout: float = 6.0):
    """并发清理所有子进程，超时后强制杀掉残留进程。"""
    _log_shutdown_step(f"开始并发清理子进程（超时 {timeout}s）")
    _log_shutdown_step("仅终止当前控制台启动并记录的子进程，不做端口扫描")
    running_before = _describe_running_children()
    if running_before:
        _log_shutdown_step("当前存活子进程: " + ", ".join(running_before))
    else:
        _log_shutdown_step("未检测到存活子进程，仍将发送关闭指令")

    threads = []

    # 并发关闭 Streamlit 子进程
    for app_name in STREAMLIT_SCRIPTS:
        t = threading.Thread(target=stop_streamlit_app, args=(app_name,), daemon=True)
        threads.append(t)
        t.start()

    # 并发关闭 ForumEngine
    forum_thread = threading.Thread(target=stop_forum_engine, daemon=True)
    threads.append(forum_thread)
    forum_thread.start()

    # 等待所有线程完成，最多 timeout 秒
    end_time = time.time() + timeout
    for t in threads:
        remaining = end_time - time.time()
        if remaining <= 0:
            break
        t.join(timeout=remaining)

    # 二次检查：强制杀掉仍存活的子进程
    for app_name in STREAMLIT_SCRIPTS:
        proc = processes[app_name]['process']
        if proc is not None and proc.poll() is None:
            try:
                _log_shutdown_step(f"{app_name} 进程仍存活，触发二次终止 (pid={proc.pid})")
                proc.terminate()
                proc.wait(timeout=1)
            except Exception:
                try:
                    _log_shutdown_step(f"{app_name} 二次终止失败，尝试kill (pid={proc.pid})")
                    proc.kill()
                    proc.wait(timeout=1)
                except Exception:
                    logger.warning(f"{app_name} 进程强制退出失败，继续关机")
            finally:
                processes[app_name]['process'] = None
                processes[app_name]['status'] = 'stopped'

    processes['forum']['status'] = 'stopped'
    _log_shutdown_step("并发清理结束，标记系统未启动")
    _set_system_state(started=False, starting=False)

def _schedule_server_shutdown(delay_seconds: float = 0.1):
    """在清理完成后尽快退出，避免阻塞当前请求。"""
    def _shutdown():
        time.sleep(delay_seconds)
        try:
            socketio.stop()
        except Exception as exc:  # pragma: no cover
            logger.warning(f"SocketIO 停止时异常，继续退出: {exc}")
        _log_shutdown_step("SocketIO 停止指令已发送，即将退出主进程")
        os._exit(0)

    threading.Thread(target=_shutdown, daemon=True).start()

def _start_async_shutdown(cleanup_timeout: float = 3.0):
    """异步触发清理并强制退出，避免HTTP请求阻塞。"""
    _log_shutdown_step(f"收到关机指令，启动异步清理（超时 {cleanup_timeout}s）")

    def _force_exit():
        _log_shutdown_step("关机超时，触发强制退出")
        os._exit(0)

    # 硬超时保护，即便清理线程异常也能退出
    hard_timeout = cleanup_timeout + 2.0
    force_timer = threading.Timer(hard_timeout, _force_exit)
    force_timer.daemon = True
    force_timer.start()

    def _cleanup_and_exit():
        try:
            cleanup_processes_concurrent(timeout=cleanup_timeout)
        except Exception as exc:  # pragma: no cover
            logger.exception(f"关机清理异常: {exc}")
        finally:
            _log_shutdown_step("清理线程结束，调度主进程退出")
            _schedule_server_shutdown(0.05)

    threading.Thread(target=_cleanup_and_exit, daemon=True).start()

# 注册清理函数
atexit.register(cleanup_processes)

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/api/status')
def get_status():
    """获取所有应用状态"""
    check_app_status()
    return jsonify({
        app_name: {
            'status': info['status'],
            'port': info['port'],
            'output_lines': len(info['output'])
        }
        for app_name, info in processes.items()
    })

@app.route('/api/start/<app_name>')
def start_app(app_name):
    """启动指定应用"""
    if app_name not in processes:
        return jsonify({'success': False, 'message': '未知应用'})

    if app_name == 'forum':
        try:
            start_forum_engine()
            processes['forum']['status'] = 'running'
            return jsonify({'success': True, 'message': 'ForumEngine已启动'})
        except Exception as exc:  # pragma: no cover
            logger.exception("手动启动ForumEngine失败")
            return jsonify({'success': False, 'message': f'ForumEngine启动失败: {exc}'})

    script_path = STREAMLIT_SCRIPTS.get(app_name)
    if not script_path:
        return jsonify({'success': False, 'message': '该应用不支持启动操作'})

    success, message = start_streamlit_app(
        app_name,
        script_path,
        processes[app_name]['port']
    )

    if success:
        # 等待应用启动
        startup_success, startup_message = wait_for_app_startup(app_name, 15)
        if not startup_success:
            message += f" 但启动检查失败: {startup_message}"
    
    return jsonify({'success': success, 'message': message})

@app.route('/api/stop/<app_name>')
def stop_app(app_name):
    """停止指定应用"""
    if app_name not in processes:
        return jsonify({'success': False, 'message': '未知应用'})

    if app_name == 'forum':
        try:
            stop_forum_engine()
            processes['forum']['status'] = 'stopped'
            return jsonify({'success': True, 'message': 'ForumEngine已停止'})
        except Exception as exc:  # pragma: no cover
            logger.exception("手动停止ForumEngine失败")
            return jsonify({'success': False, 'message': f'ForumEngine停止失败: {exc}'})

    success, message = stop_streamlit_app(app_name)
    return jsonify({'success': success, 'message': message})

@app.route('/api/output/<app_name>')
def get_output(app_name):
    """获取应用输出"""
    if app_name not in processes:
        return jsonify({'success': False, 'message': '未知应用'})
    
    # 特殊处理Forum Engine
    if app_name == 'forum':
        try:
            forum_log_content = read_log_from_file('forum')
            return jsonify({
                'success': True,
                'output': forum_log_content,
                'total_lines': len(forum_log_content)
            })
        except Exception as e:
            return jsonify({'success': False, 'message': f'读取forum日志失败: {str(e)}'})
    
    # 从文件读取完整日志
    output_lines = read_log_from_file(app_name)
    
    return jsonify({
        'success': True,
        'output': output_lines
    })

@app.route('/api/test_log/<app_name>')
def test_log(app_name):
    """测试日志写入功能"""
    if app_name not in processes:
        return jsonify({'success': False, 'message': '未知应用'})
    
    # 写入测试消息
    test_msg = f"[{datetime.now().strftime('%H:%M:%S')}] 测试日志消息 - {datetime.now()}"
    write_log_to_file(app_name, test_msg)
    
    # 通过Socket.IO发送
    socketio.emit('console_output', {
        'app': app_name,
        'line': test_msg
    })
    
    return jsonify({
        'success': True,
        'message': f'测试消息已写入 {app_name} 日志'
    })

@app.route('/api/forum/start')
def start_forum_monitoring_api():
    """手动启动ForumEngine论坛"""
    try:
        from ForumEngine.monitor import start_forum_monitoring
        success = start_forum_monitoring()
        if success:
            return jsonify({'success': True, 'message': 'ForumEngine论坛已启动'})
        else:
            return jsonify({'success': False, 'message': 'ForumEngine论坛启动失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'启动论坛失败: {str(e)}'})

@app.route('/api/forum/stop')
def stop_forum_monitoring_api():
    """手动停止ForumEngine论坛"""
    try:
        from ForumEngine.monitor import stop_forum_monitoring
        stop_forum_monitoring()
        return jsonify({'success': True, 'message': 'ForumEngine论坛已停止'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'停止论坛失败: {str(e)}'})

@app.route('/api/forum/log')
def get_forum_log():
    """获取ForumEngine的forum.log内容"""
    try:
        forum_log_file = LOG_DIR / "forum.log"
        if not forum_log_file.exists():
            return jsonify({
                'success': True,
                'log_lines': [],
                'parsed_messages': [],
                'total_lines': 0
            })
        
        with open(forum_log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            lines = [line.rstrip('\n\r') for line in lines if line.strip()]
        
        # 解析每一行日志并提取对话信息
        parsed_messages = []
        for line in lines:
            parsed_message = parse_forum_log_line(line)
            if parsed_message:
                parsed_messages.append(parsed_message)
        
        return jsonify({
            'success': True,
            'log_lines': lines,
            'parsed_messages': parsed_messages,
            'total_lines': len(lines)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'读取forum.log失败: {str(e)}'})

@app.route('/api/forum/log/history', methods=['POST'])
def get_forum_log_history():
    """获取Forum历史日志（支持从指定位置开始）"""
    try:
        data = request.get_json()
        start_position = data.get('position', 0)  # 客户端上次接收的位置
        max_lines = data.get('max_lines', 1000)   # 最多返回的行数

        forum_log_file = LOG_DIR / "forum.log"
        if not forum_log_file.exists():
            return jsonify({
                'success': True,
                'log_lines': [],
                'position': 0,
                'has_more': False
            })

        with open(forum_log_file, 'r', encoding='utf-8', errors='ignore') as f:
            # 从指定位置开始读取
            f.seek(start_position)
            lines = []
            line_count = 0

            for line in f:
                if line_count >= max_lines:
                    break
                line = line.rstrip('\n\r')
                if line.strip():
                    # 添加时间戳
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    formatted_line = f"[{timestamp}] {line}"
                    lines.append(formatted_line)
                    line_count += 1

            # 记录当前位置
            current_position = f.tell()

            # 检查是否还有更多内容
            f.seek(0, 2)  # 移到文件末尾
            end_position = f.tell()
            has_more = current_position < end_position

        return jsonify({
            'success': True,
            'log_lines': lines,
            'position': current_position,
            'has_more': has_more
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'读取forum历史失败: {str(e)}'})

@app.route('/api/search', methods=['POST'])
def search():
    """纯Python搜索接口 - 直接调用引擎，不依赖Streamlit"""
    print("\n" + "="*50 + "\n[后端断点] 1. /api/search 接口被触发！\n" + "="*50 + "\n", flush=True)
    import uuid as _uuid
    data = request.get_json()
    query = data.get('query', '').strip()
    force_refresh = data.get('force_refresh', False)

    if not query:
        return jsonify({'success': False, 'message': '搜索查询不能为空'})

    task_id = _uuid.uuid4().hex[:8]
    _search_tasks[task_id] = {
        'status': 'running', 'stage': '启动中',
        'query': query, 'result': None, 'error': None,
    }
    logger.info(f"[搜索] 任务创建 task_id={task_id} query={query!r}")

    def _do_search():
        print("[后端断点] 2. 后台搜索线程已成功启动！", flush=True)
        import time as _time
        from runner import run_pipeline
        _t0 = _time.time()
        logger.info(f"[搜索] 任务开始执行 task_id={task_id}")
        try:
            def cb(stage, msg):
                elapsed = _time.time() - _t0
                logger.info(f"[搜索] [{task_id}] [{stage}] {msg} (已用时 {elapsed:.1f}s)")
                _search_tasks[task_id]['stage'] = msg
                socketio.emit('search_progress', {
                    'task_id': task_id, 'stage': stage, 'message': msg,
                })

            result = run_pipeline(query, progress_cb=cb, force_refresh=force_refresh, task_id=task_id)
            elapsed = _time.time() - _t0
            report_path = result.get('report_filepath') or result.get('report_relative_path', '') if isinstance(result, dict) else ''
            warnings = result.get('warnings', []) if isinstance(result, dict) else []
            report_task_id = result.get('report_task_id', '') if isinstance(result, dict) else ''
            logger.info(f"[搜索] 任务完成 task_id={task_id} report_task_id={report_task_id!r} 耗时={elapsed:.1f}s report={report_path!r} warnings={warnings}")
            _search_tasks[task_id].update({'status': 'done', 'result': result, 'warnings': warnings})
            from_cache = result.get('from_cache', False) if isinstance(result, dict) else False
            socketio.emit('search_done', {
                'task_id': task_id,
                'report_task_id': report_task_id,
                'warnings': warnings,
                'from_cache': from_cache,
            })
        except Exception as e:
            elapsed = _time.time() - _t0
            logger.exception(f"[搜索] 任务失败 task_id={task_id} 耗时={elapsed:.1f}s error={e}")
            _search_tasks[task_id].update({'status': 'error', 'error': str(e)})
            socketio.emit('search_error', {'task_id': task_id, 'error': str(e)})

    threading.Thread(target=_do_search, daemon=True).start()
    return jsonify({'success': True, 'task_id': task_id, 'query': query}), 202


@app.route('/api/search/status/<task_id>')
def search_status(task_id):
    """查询搜索任务状态"""
    task = _search_tasks.get(task_id)
    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    # 展开 task 时先剔除 result 字段，避免把 html_content（2MB+）带入响应导致超时
    task_meta = {k: v for k, v in task.items() if k != 'result'}
    resp = {'success': True, 'task_id': task_id, **task_meta}
    # result 可能很大，状态查询时只返回元信息
    if task.get('result') and isinstance(task['result'], dict):
        resp['result'] = {
            'report_filepath': task['result'].get('report_filepath', ''),
            'report_relative_path': task['result'].get('report_relative_path', ''),
            'report_filename': task['result'].get('report_filename', ''),
            'from_cache': task['result'].get('from_cache', False),
        }
        # 透传 report_task_id，供前端直接用 Report Engine 接口取报告
        resp['report_task_id'] = task['result'].get('report_task_id', '')
    return jsonify(resp)


def _fix_mathjax_config(html: str) -> str:
    import re as _re
    if 'processEscapes' not in html:
        return html
    html = _re.sub(r',?\s*processEscapes\s*:\s*true', '', html)
    html = _re.sub(r'\{\s*,', '{', html)
    html = _re.sub(r',\s*\}', '}', html)
    html = _re.sub(r',\s*,', ',', html)
    return html


@app.route('/api/report/result/<task_id>', methods=['GET'])
def search_report_result(task_id):
    """
    桥接接口：统一处理所有 ID 格式的报告请求。
    支持三种 ID 格式：
      - 搜索短 hash（如 056d9ca5）→ _search_tasks / report_cache.task_id
      - ReportEngine Flask ID（如 report_1712345678）→ tasks_registry / report_cache
      - ReportEngine Agent ID（如 report-79b84a58）→ report_cache.report_task_id
    """
    from pathlib import Path as _Path

    def _read_html_from_result(result: dict) -> str:
        html = result.get('html_content', '')
        if not html:
            filepath = result.get('report_filepath') or result.get('report_relative_path', '')
            if filepath:
                try:
                    p = _Path(filepath)
                    if not p.is_absolute():
                        p = _Path(__file__).parent / filepath
                    if p.exists():
                        html = p.read_text(encoding='utf-8')
                except Exception as e:
                    logger.warning(f"[桥接] 读取报告文件失败: {e}")
        if html:
            html = _fix_mathjax_config(html)
        return html

    # 1. 查内存中的搜索任务（短 hash，进程重启前有效）
    task = _search_tasks.get(task_id)
    if task and task.get('result'):
        html = _read_html_from_result(task['result'])
        if html:
            return Response(html, mimetype='text/html')

    # 2. 查 report_cache（同时匹配 task_id 和 report_task_id 两列）
    try:
        from utils.report_cache import cache as _rc
        row = _rc.get_by_task_id(task_id)
        if row:
            html = _read_html_from_result(row)
            if html:
                return Response(html, mimetype='text/html')
    except Exception as e:
        logger.warning(f"[桥接] 从缓存查找报告失败: {e}")

    # 3. report_{timestamp} 格式：委托给 ReportEngine 的 tasks_registry 查找
    if task_id.startswith('report_') or task_id.startswith('report-'):
        try:
            from ReportEngine.flask_interface import _get_task as _re_get_task
            re_task = _re_get_task(task_id)
            if re_task and re_task.status == 'completed' and re_task.html_content:
                return Response(re_task.html_content, mimetype='text/html')
        except Exception as e:
            logger.warning(f"[桥接] 从 ReportEngine 查找失败: {e}")

    # 4. 兜底：返回最新一条有文件的报告
    try:
        from utils.report_cache import cache as _rc
        import os as _os
        conn = _rc._get_conn()
        rows = conn.execute(
            'SELECT html_content, report_filepath, report_relative_path, warnings '
            'FROM report_cache ORDER BY created_at DESC LIMIT 20'
        ).fetchall()
        for r in rows:
            fp = r['report_filepath'] or ''
            if fp and not _os.path.exists(fp):
                continue
            candidate = {
                'html_content': r['html_content'],
                'report_filepath': r['report_filepath'],
                'report_relative_path': r['report_relative_path'],
                'warnings': r['warnings'],
            }
            html = _read_html_from_result(candidate)
            if html:
                logger.info(f"[桥接] task_id={task_id!r} 未命中，已降级返回最新报告")
                return Response(html, mimetype='text/html')
    except Exception as e:
        logger.warning(f"[桥接] 兜底扫描失败: {e}")

    # 5. 都找不到，返回 404
    return jsonify({'success': False, 'error': '任务不存在'}), 404


@app.route('/api/report/history', methods=['GET'])
def get_report_history():
    """从数据库读取历史报告列表，供前端恢复 localStorage。"""
    try:
        from utils.report_cache import cache as _rc
        import os as _os
        conn = _rc._get_conn()
        rows = conn.execute(
            'SELECT task_id, report_task_id, query_raw, created_at, report_filepath FROM report_cache ORDER BY created_at DESC LIMIT 50'
        ).fetchall()
        result = []
        for r in rows:
            tid = r['task_id'] or r['report_task_id']
            if not tid:
                continue  # 两种 ID 都没有的旧记录无法查看，跳过
            fp = r['report_filepath'] or ''
            if fp and not _os.path.exists(fp):
                continue  # 文件已删除，跳过
            from datetime import datetime
            try:
                dt = datetime.strptime(r['created_at'], '%Y-%m-%d %H:%M:%S')
                time_str = dt.strftime('%Y/%m/%d %H:%M')
            except Exception:
                time_str = r['created_at'] or ''
            result.append({
                'id': tid,
                'title': r['query_raw'] or tid,
                'time': time_str,
                'status': 'done'
            })
        return jsonify({'success': True, 'history': result})
    except Exception as e:
        logger.warning(f'[历史记录] 读取失败: {e}')
        return jsonify({'success': False, 'history': [], 'error': str(e)})


@app.route('/api/config', methods=['GET'])
def get_config():
    """Expose selected configuration values to the frontend."""
    try:
        config_values = read_config_values()
        return jsonify({'success': True, 'config': config_values})
    except Exception as exc:
        logger.exception("读取配置失败")
        return jsonify({'success': False, 'message': f'读取配置失败: {exc}'}), 500


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration values and persist them to config.py."""
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict) or not payload:
        return jsonify({'success': False, 'message': '请求体不能为空'}), 400

    updates = {}
    for key, value in payload.items():
        if key in CONFIG_KEYS:
            updates[key] = value if value is not None else ''

    if not updates:
        return jsonify({'success': False, 'message': '没有可更新的配置项'}), 400

    try:
        write_config_values(updates)
        updated_config = read_config_values()
        return jsonify({'success': True, 'config': updated_config})
    except Exception as exc:
        logger.exception("更新配置失败")
        return jsonify({'success': False, 'message': f'更新配置失败: {exc}'}), 500


@app.route('/api/system/status')
def get_system_status():
    """返回系统启动状态。"""
    state = _get_system_state()
    return jsonify({
        'success': True,
        'started': state['started'],
        'starting': state['starting']
    })


@app.route('/api/system/start', methods=['POST'])
def start_system():
    """在接收到请求后启动完整系统（异步，立即返回）。"""
    allowed, message = _prepare_system_start()
    if not allowed:
        return jsonify({'success': False, 'message': message}), 400

    def _do_start():
        logger.info("[系统启动] 后台启动线程开始执行")
        try:
            success, logs, errors = initialize_system_components()
            if success:
                _set_system_state(started=True)
                logger.info(f"[系统启动] 全部组件启动成功, 准备发送 system_start_result(success=True)")
                socketio.emit('system_start_result', {'success': True, 'message': '系统启动成功', 'logs': logs})
                logger.info("[系统启动] system_start_result(success=True) 已发送")
            else:
                _set_system_state(started=False)
                logger.error(f"[系统启动] 启动失败, errors={errors}, 准备发送 system_start_result(success=False)")
                socketio.emit('system_start_result', {'success': False, 'message': '系统启动失败', 'logs': logs, 'errors': errors})
                logger.info("[系统启动] system_start_result(success=False) 已发送")
        except Exception as exc:
            logger.exception(f"[系统启动] 启动过程中出现未捕获异常: {exc}")
            _set_system_state(started=False)
            socketio.emit('system_start_result', {'success': False, 'message': f'系统启动异常: {exc}'})
        finally:
            _set_system_state(starting=False)
            logger.info("[系统启动] 后台启动线程结束")

    t = threading.Thread(target=_do_start, daemon=True)
    t.start()
    return jsonify({'success': True, 'message': '系统正在启动，请稍候...'}), 202

@app.route('/api/system/shutdown', methods=['POST'])
def shutdown_system():
    """优雅停止所有组件并关闭当前服务进程。"""
    state = _get_system_state()
    if state['starting']:
        return jsonify({'success': False, 'message': '系统正在启动/重启，请稍候'}), 400

    target_ports = [
        f"{name}:{info['port']}"
        for name, info in processes.items()
        if info.get('port')
    ]

    # 已有关机请求执行中时，返回当前存活的子进程，便于前端判断进度
    if not _mark_shutdown_requested():
        running = _describe_running_children()
        detail = '关机指令已下发，请稍等...'
        if running:
            detail = f"关机指令已下发，等待进程退出: {', '.join(running)}"
        if target_ports:
            detail = f"{detail}（端口: {', '.join(target_ports)}）"
        return jsonify({'success': True, 'message': detail, 'ports': target_ports})

    running = _describe_running_children()
    if running:
        _log_shutdown_step("开始关闭系统，正在等待子进程退出: " + ", ".join(running))
    else:
        _log_shutdown_step("开始关闭系统，未检测到存活子进程")

    try:
        _set_system_state(started=False, starting=False)
        _start_async_shutdown(cleanup_timeout=6.0)
        message = '关闭系统指令已下发，正在停止进程'
        if running:
            message = f"{message}: {', '.join(running)}"
        if target_ports:
            message = f"{message}（端口: {', '.join(target_ports)}）"
        return jsonify({'success': True, 'message': message, 'ports': target_ports})
    except Exception as exc:  # pragma: no cover - 兜底捕获
        logger.exception("系统关闭过程中出现异常")
        return jsonify({'success': False, 'message': f'系统关闭异常: {exc}'}), 500

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    emit('status', 'Connected to Flask server')

@socketio.on('request_status')
def handle_status_request():
    """请求状态更新"""
    check_app_status()
    emit('status_update', {
        app_name: {
            'status': info['status'],
            'port': info['port']
        }
        for app_name, info in processes.items()
    })

if __name__ == '__main__':
    # 从配置文件读取 HOST 和 PORT
    from config import settings
    HOST = settings.HOST
    PORT = settings.PORT
    
    logger.info("等待配置确认，系统将在前端指令后启动组件...")
    logger.info(f"Flask服务器已启动，访问地址: http://{HOST}:{PORT}")
    
    try:
        socketio.run(app, host=HOST, port=PORT, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("\n正在关闭应用...")
        cleanup_processes()
        
    
