import sys
import traceback
from pathlib import Path

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
    SpinnerColumn,
)
from rich.syntax import Syntax
from rich.text import Text
from rich.theme import Theme
from rich.tree import Tree


# 主题配色方案
_theme = Theme(
    {
        # 消息级别样式
        "info": "bold #4FC3F7",  # 浅蓝色
        "success": "bold #66BB6A",  # 浅绿色
        "warning": "bold #FFD54F",  # 琥珀色
        "error": "bold #EF5350",  # 红色
        "debug": "italic #B0BEC5",  # 灰色调试信息
        "remove_operation": "bold #FFD54F on #004D40",
        "add_operation": "bold #66BB6A on #004D40",
        "overlay_operation": "bold #E0F7FA on #004D40",
        # Shell相关样式
        "source_code": "bold #E0F7FA",  # 青色文字/深青背景
        "shell_output": "#E0F7FA on #004D40",  # 青色文字/深绿背景
        "shell_prompt": "#80DEEA",  # 浅青色
        # 进度条样式
        "progress_bar": "#00897B",  # 青色进度条
        "progress_text": "bold #4DB6AC",  # 进度文本
        "progress_complete": "bold #66BB6A",  # 完成状态
        "progress_error": "bold #EF5350",  # 错误状态
        # 目录树样式
        "tree_dir": "bold #4FC3F7",  # 目录样式
        "tree_file": "#E0F7FA",  # 文件样式
        "tree_special": "#FFD54F",  # 特殊文件样式
        "tree_size": "italic #90A4AE",  # 文件大小样式
    }
)

_console = Console(theme=_theme)

# ======================
# 文件类型图标映射
# ======================

FILE_ICONS = {
    # 目录
    "dir": "📁",
    # 编程语言文件
    "py": "📜",
    "js": "📜",
    "java": "📜",
    "c": "📜",
    "cpp": "📜",
    "html": "🌐",
    "css": "🎨",
    "php": "📜",
    "sh": "📜",
    "bat": "🪟",
    "go": "📜",
    "rs": "📜",
    "swift": "📜",
    "kt": "📜",
    "dart": "📜",
    # 配置文件
    "json": "⚙️",
    "yaml": "⚙️",
    "yml": "⚙️",
    "toml": "⚙️",
    "ini": "⚙️",
    "cfg": "⚙️",
    "conf": "⚙️",
    "env": "⚙️",
    # 文档文件
    "md": "📝",
    "txt": "📄",
    "rst": "📚",
    "doc": "📄",
    "docx": "📄",
    "pdf": "📘",
    "ppt": "📊",
    "pptx": "📊",
    "xls": "📈",
    "xlsx": "📈",
    # 媒体文件
    "jpg": "🖼️",
    "jpeg": "🖼️",
    "png": "🖼️",
    "gif": "🖼️",
    "bmp": "🖼️",
    "svg": "🖼️",
    "webp": "🖼️",
    "mp3": "🎵",
    "wav": "🎵",
    "flac": "🎵",
    "mp4": "🎬",
    "mov": "🎬",
    "avi": "🎬",
    "mkv": "🎬",
    "flv": "🎬",
    # 压缩文件
    "zip": "📦",
    "tar": "📦",
    "gz": "📦",
    "bz2": "📦",
    "7z": "📦",
    "rar": "📦",
    "xz": "📦",
    # 特殊文件
    "gitignore": "🔒",
    "dockerfile": "🐳",
    "makefile": "🔨",
    "license": "📜",
    # 默认文件图标
    "default": "📄",
}

_common_panel_width = 100


def set_common_panel_width(width):
    """设置面板宽度"""
    global _common_panel_width
    _common_panel_width = width


def print_info(msg, icon=""):
    """打印信息消息"""
    _console.print(f"{icon} [info]INFO:[/info] {msg}".lstrip())


def print_success(msg, icon=""):
    """打印成功消息"""
    _console.print(f"{icon} [success]SUCCESS:[/success] {msg}".lstrip())


def print_warning(msg, icon=""):
    """打印警告消息"""
    _console.print(f"{icon} [warning]WARNING:[/warning] {msg}".lstrip())


def print_error(msg, icon=""):
    """打印错误消息"""
    # panel = Panel(
    #     Text(f"{icon} ERROR: {msg}".lstrip(), justify="left"),
    #     style="error",
    #     border_style="error",
    #     box=box.DOUBLE,
    #     padding=(0, 2),
    #     width=_common_panel_width,
    # )
    _console.print(f"{icon} [error]ERROR:[/error] {msg}".lstrip())


def print_debug(msg, icon=""):
    """打印调试信息"""
    _console.print(f"{icon} [debug]DEBUG:[/debug] {msg}".lstrip())


def print_source_code(code, lexer_name, title=""):
    """美观地打印执行的Shell代码"""
    syntax = Syntax(
        code,
        lexer_name,
        line_numbers=True,
        theme="one-dark",
        word_wrap=True,
        code_width=_common_panel_width,
    )

    panel = Panel(
        syntax,
        title=f"[shell_prompt]{title}[/shell_prompt]",
        title_align="left",
        style="source_code",
        border_style="#00897B",
        box=box.ROUNDED,
        padding=(1, 2),
        expand=False,
        width=_common_panel_width,
    )
    _console.print(panel)


def print_shell_code(code, title="Executing Shell Command"):
    """打印执行的Shell代码"""
    print_source_code(code, "bash", title)


def print_shell_output(output, title="Command Output", success=True):
    """美观地打印Shell命令输出"""
    style = "success" if success else "error"
    icon = "✅" if success else "❌"

    panel = Panel(
        output,
        title=f"{icon} [shell_prompt]{title}[/shell_prompt]",
        title_align="left",
        style=style,
        border_style="#66BB6A" if success else "#EF5350",
        box=box.SQUARE,
        padding=(1, 2),
        expand=False,
        width=_common_panel_width,
    )
    _console.print(panel)


def print_separator(title="Shell Command Execution"):
    """打印分隔符"""
    _console.rule(
        f"[reverse][blink]⚡[/blink] {title} ⚡[/reverse]",
        style="#00897B",
        align="center",
    )


def print_shell_command(
    command,
    stdout=None,
    stderr=None,
    return_code=0,
    title="Shell Command Execution",
    command_panel_title="Command",
    output_panel_title="Output",
    error_panel_title="Error Output",
):
    """
    在单个面板中显示 Shell 命令及其执行结果
    """

    command = command.strip()
    if not command:
        return

    stdout = (stdout or "").strip()
    stderr = (stderr or "").strip()

    if return_code is None:
        return_code = 0

    # 创建命令部分
    command_panel = Panel(
        Syntax(command, "bash", theme="monokai", line_numbers=False),
        title=f"[bold]{command_panel_title}[/bold]",
        border_style="dim",
        box=box.SIMPLE,
        padding=(0, 1),
        width=_common_panel_width,
    )

    if not stdout and not stderr:
        command_panel.box = box.ROUNDED
        _console.print(command_panel)
        return

    success = (not stderr.strip()) and (return_code == 0)

    # 确定状态样式

    output_panels = []

    if stdout:
        # 创建输出部分
        output_panel = Panel(
            stdout,
            title=f"[bold]{output_panel_title}[/bold]",
            border_style="dim",
            box=box.SIMPLE,
            padding=(0, 1),
            width=_common_panel_width,
        )
        output_panels.append(output_panel)

    if stderr:
        # 创建错误输出部分
        error_panel = Panel(
            stderr,
            title=f"[bold]{error_panel_title}[/bold]",
            border_style="dim",
            box=box.SIMPLE,
            padding=(0, 1),
            width=_common_panel_width,
        )
        output_panels.append(error_panel)

    # 使用 Group 组合命令和输出
    command_group = Group(command_panel, *output_panels)

    # 创建主面板
    main_panel = Panel(
        command_group,
        title=f"[bold]{title}[/bold]",
        border_style="green" if success else "red",
        box=box.ROUNDED,
        padding=(1, 1),
        width=_common_panel_width,
    )

    _console.print(main_panel)


def print_file_tree(start_dir=".", depth=2, title="Directory Structure"):
    """显示美观的目录树结构"""
    # 获取绝对路径
    start_path = Path(start_dir).resolve()

    # 创建目录树面板
    tree_panel = Panel(
        _generate_file_tree(start_path, depth),
        title=f"[tree_dir]{title}[/tree_dir] - [tree_file]{start_path}[/tree_file]",
        title_align="left",
        style="tree_dir",
        border_style="#00897B",
        box=box.ROUNDED,
        padding=(1, 2),
        expand=False,
        width=_common_panel_width,
    )

    _console.print(tree_panel)


def _generate_file_tree(path, max_depth, current_depth=0):
    """递归生成目录树结构"""
    # 创建根节点
    name = path.name + ("/" if path.is_dir() else "")
    tree = Tree(
        f"[tree_dir]{_get_file_icon(path)} {name}[/tree_dir]", guide_style="dim #546E7A"
    )

    # 达到最大深度时停止递归
    if current_depth >= max_depth:
        tree.add("[italic #90A4AE]... depth limit reached[/italic #90A4AE]")
        return tree

    # 处理目录
    if path.is_dir():
        try:
            # 获取目录内容并按字母顺序排序
            items = sorted(
                path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())
            )

            for item in items:
                if item.is_dir():
                    # 递归添加子目录
                    tree.add(_generate_file_tree(item, max_depth, current_depth + 1))
                else:
                    # 添加文件
                    file_label = _get_file_label(item)
                    tree.add(file_label)
        except PermissionError:
            tree.add("[tree_special]🔒 Permission denied[/tree_special]")
        except Exception as e:
            tree.add(f"[error]⚠ Error: {str(e)}[/error]")

    return tree


def _get_file_icon(path):
    """根据文件类型获取对应的图标"""
    if path.is_dir():
        return FILE_ICONS["dir"]

    # 获取文件扩展名
    ext = path.suffix.lstrip(".").lower()

    # 特殊文件名处理
    if path.name.lower() == "dockerfile":
        return FILE_ICONS["dockerfile"]
    if path.name.lower() == "makefile":
        return FILE_ICONS["makefile"]
    if path.name.lower().startswith(".gitignore"):
        return FILE_ICONS["gitignore"]
    if "license" in path.name.lower():
        return FILE_ICONS["license"]

    # 返回对应扩展名的图标，没有则返回默认图标
    return FILE_ICONS.get(ext, FILE_ICONS["default"])


def _get_file_label(path):
    """获取文件的完整标签（图标+名称+大小）"""
    # 文件图标
    icon = _get_file_icon(path)

    # 文件大小（如果是文件）
    size_str = ""
    if path.is_file():
        size = path.stat().st_size
        # 转换为更友好的格式
        if size < 1024:
            size_str = f" [tree_size]({size}B)[/tree_size]"
        elif size < 1024 * 1024:
            size_str = f" [tree_size]({size/1024:.1f}KB)[/tree_size]"
        else:
            size_str = f" [tree_size]({size/(1024*1024):.1f}MB)[/tree_size]"

    # 文件名样式
    file_style = "tree_special" if path.name.startswith(".") else "tree_file"

    return f"{icon} [{file_style}]{path.name}[/{file_style}]{size_str}"


def print_exception_info(exception=None):
    """
    简单但美观地打印当前异常信息
    """
    # 获取异常信息
    if exception is None:
        # 处理当前异常
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_type is None:
            _console.print("[bold red]No active exception to print[/bold red]")
            return
    else:
        # 处理指定的异常对象
        exc_type = type(exception)
        exc_value = exception
        exc_traceback = exception.__traceback__

    # 提取异常基本信息
    exc_name = exc_type.__name__
    exc_msg = str(exc_value)

    # 获取最后一级堆栈跟踪
    tb = traceback.extract_tb(exc_traceback)[-1]
    file_name = tb.filename
    line_no = tb.lineno
    func_name = tb.name

    # 构建异常信息文本
    error_text = Text()
    error_text.append(" EXCEPTION ", style="bold white on red")
    error_text.append("\n\n")

    error_text.append(f"Type: ", style="bold red")
    error_text.append(f"{exc_name}\n", style="bold")

    error_text.append(f"Message: ", style="bold red")
    error_text.append(f"{exc_msg}\n\n", style="bold")

    error_text.append(f"Location: ", style="bold red")
    error_text.append(f"{file_name}\n", style="")

    error_text.append(f"Function: ", style="bold red")
    error_text.append(f"{func_name}()\n", style="")

    error_text.append(f"Line: ", style="bold red")
    error_text.append(f"{line_no}", style="")

    # 创建面板
    panel = Panel(
        error_text,
        title="[bold]Error Details[/bold]",
        border_style="red",
        box=box.ROUNDED,
        padding=(1, 2),
        width=_common_panel_width,
    )

    _console.print(panel)


class ProgressManager:
    """进度条管理器"""

    def __init__(self):
        self.progress = Progress(
            SpinnerColumn("dots", style="progress_text"),
            TextColumn("[progress_text]{task.description}[/progress_text]"),
            BarColumn(
                bar_width=None,
                complete_style="progress_complete",
                finished_style="progress_complete",
                pulse_style="progress_bar",
            ),
            TextColumn("[progress_text]{task.percentage:>3.0f}%[/progress_text]"),
            TimeRemainingColumn(),
            TimeElapsedColumn(),
            console=_console,
            expand=True,
        )
        self.task_ids = {}

    def __enter__(self):
        self.progress.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.progress.stop()

    def add_task(self, description, total=100):
        """添加新任务并返回任务ID"""
        task_id = self.progress.add_task(
            f"[progress_text]{description}[/progress_text]", total=total
        )
        self.task_ids[description] = task_id
        return task_id

    def update(self, task_id, advance=1, description=None):
        """更新任务进度"""
        if description:
            self.progress.update(task_id, advance=advance, description=description)
        else:
            self.progress.update(task_id, advance=advance)

    def complete_task(self, task_id, message=None):
        """标记任务完成并显示消息"""
        if message:
            self.progress.update(task_id, description=f"[progress_complete]✓ {message}")
        self.progress.stop_task(task_id)

    def fail_task(self, task_id, message=None):
        """标记任务失败并显示消息"""
        if message:
            self.progress.update(
                task_id,
                description=f"[progress_error]✗ {message}[/progress_error]",
                style="progress_error",
            )
        self.progress.stop_task(task_id)


def print_header(title, version="1.0.0"):
    """打印应用标题头 - 带版本号"""
    header = Text()
    header.append("✨ ", style="bold #FFD54F")
    header.append(title, style="bold #4FC3F7")
    header.append(f" v{version}", style="bold #B0BEC5")
    header.append(" ✨", style="bold #FFD54F")

    panel = Panel(
        header,
        style="#4FC3F7",
        border_style="#00897B",
        box=box.DOUBLE,
        padding=(1, 4),
        subtitle="by Rich Terminal",
        subtitle_align="right",
        width=_common_panel_width,
    )
    _console.print(panel)
    _console.print()


def print_footer(message="All tasks completed!"):
    """打印应用底部信息 - 带成功状态"""
    footer = Text()
    footer.append("🎉 ", style="bold #66BB6A")
    footer.append(message, style="bold #66BB6A")
    footer.append(" 🎉", style="bold #66BB6A")

    panel = Panel(
        footer,
        style="success",
        border_style="#66BB6A",
        box=box.ROUNDED,
        padding=(1, 4),
        width=_common_panel_width,
    )
    _console.print("\n")
    _console.print(panel)


def print_quote(text, author=None):
    """打印引用文本"""
    content = Text(text, style="italic #B0BEC5", justify="center")
    if author:
        content.append("\n\n— " + author, style="bold #90A4AE")

    panel = Panel(
        content,
        style="#90A4AE",
        border_style="#546E7A",
        box=box.HEAVY,
        padding=(1, 4),
        width=_common_panel_width,
    )
    _console.print(panel)


# if __name__ == "__main__":
#     import random
#     import time
#     import sys
#
#     # 打印应用标题
#     print_header("Advanced Terminal Printer", "3.0.0")
#
#     # 打印引用
#     print_quote(
#         "Beautiful is better than ugly.\nExplicit is better than implicit.",
#         "The Zen of Python",
#     )
#
#     # 打印消息示例
#     print_info("Application starting up...")
#     print_success("Database connection established")
#     print_warning("Configuration file is using default values")
#     print_error("Failed to load user preferences")
#     print_debug("Cache size: 128MB")
#
#     # 目录树示例
#     print_file_tree("D://", depth=3, title="Project Structure")
#
#     # Shell命令示例
#     print_shell_separator("Docker Setup")
#     print_shell_code(
#         "docker run -it --rm \\ \n  -v $(pwd):/app \\ \n  python:3.9 \\ \n  python -m pip install -r requirements.txt"
#     )
#
#     # 模拟命令输出
#     print_shell_output(
#         "Successfully installed requests-2.28.1 urllib3-1.26.12\n"
#         "Cleaning up... Done!\n"
#         "[✓] 5 packages installed in 2.8 seconds",
#         success=True,
#     )
#
#     # 进度条演示
#     print_shell_separator("Processing Data")
#     with ProgressManager() as progress:
#         # 添加任务
#         task1 = progress.add_task("Processing user data", total=200)
#         task2 = progress.add_task("Analyzing metrics", total=150)
#         task3 = progress.add_task("Generating reports", total=100)
#
#         # 模拟任务进度
#         while not progress.progress.finished:
#             # 随机更新任务进度
#             progress.update(task1, advance=random.uniform(0.5, 3))
#             progress.update(task2, advance=random.uniform(0.2, 2))
#             progress.update(task3, advance=random.uniform(0.1, 1.5))
#             time.sleep(0.05)
#
#         # 标记任务完成
#         progress.complete_task(task1, "User data processed")
#         progress.complete_task(task2, "Metrics analyzed")
#         progress.complete_task(task3, "Reports generated")
#
#     try:
#         # 故意引发一个异常
#         def divide(a, b):
#             return a / b
#
#         x = 10
#         y = 0
#         result = divide(x, y)
#         print_success(f"Result: {result}")
#
#     except Exception as e:
#         # 打印异常详情
#         print_exception_info()
#
#     # 打印结束信息
#     print_footer("All operations completed successfully!")
