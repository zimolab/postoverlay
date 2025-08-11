import shlex
import subprocess
from io import StringIO
from pathlib import Path

from pretty import (
    print_exception_info,
    print_info,
    print_error,
    print_success,
    print_warning,
    print_debug,
    print_file_tree,
    print_shell_command,
)


def c_error(message, print_message=True):
    if not print_message:
        return
    print_error(message)


def c_info(message, print_message=True):
    if not print_message:
        return
    print_info(message)


def c_success(message, print_message=True):
    if not print_message:
        return
    print_success(message)


def c_warning(message, print_message=True):
    if not print_message:
        return
    print_warning(message)


def c_debug(message, print_message=True):
    if not print_message:
        return
    print_debug(message)


def c_exception_info(exception=None, print_exception=True):
    if not print_exception:
        return
    print_exception_info(exception)


def c_file_tree(start_dir, depth=1, title="Directory Structure", print_tree=True):
    if not print_tree:
        return
    start_dir = Path(start_dir)
    if not start_dir.is_dir():
        c_error(f"{start_dir} is not a directory", print_message=True)
        return
    print_file_tree(start_dir=start_dir, depth=depth, title=title)


def c_shell_command(
    command,
    stdout=None,
    stderr=None,
    return_code=0,
    tile="Command Execution",
    command_panel_title="Shell Code",
    output_panel_title="Command Output",
    error_panel_title="Error Output",
    print_command=True,
):
    if not print_command:
        return
    print_shell_command(
        command,
        stdout=stdout,
        stderr=stderr,
        return_code=return_code,
        title=tile,
        command_panel_title=command_panel_title,
        output_panel_title=output_panel_title,
        error_panel_title=error_panel_title,
    )


def bash_exec(
    script,
    mode="string",
    cwd=None,
    encoding="utf-8",
    timeout=None,
    no_bash_exec=False,
):
    if not script:
        return -1, None, None, ValueError("script not provided")

    if mode not in ("string", "file"):
        raise ValueError("mode must be either 'string' or 'file'")

    cmd = ["bash"]
    if mode == "file":
        if no_bash_exec:
            cmd = []
        script = Path(script)
        if not script.is_file():
            raise FileNotFoundError(f"{script} not found")
        cmd.append(script.absolute().as_posix())
    else:
        script = script.replace("\r", "")
        cmd.append("-c")
        cmd.append(script)

    if cwd:
        cwd = Path(cwd).as_posix()

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            encoding=encoding,
            errors="replace",
            timeout=timeout,
        )
        return (
            result.returncode,
            result.stdout.strip(),
            result.stderr.strip(),
            None,
        )
    except subprocess.TimeoutExpired as e:
        return -1, None, None, e

    # stdout_buffer = StringIO()
    # stderr_buffer = StringIO()
    #
    # try:
    #     with subprocess.Popen(
    #         cmd,
    #         cwd=cwd,
    #         stdout=subprocess.PIPE,
    #         stderr=subprocess.PIPE,
    #         shell=False,
    #         encoding=encoding,
    #         errors="replace",
    #         bufsize=1,
    #     ) as p:
    #         for line in p.stdout:
    #             stdout_buffer.write(line)
    #         for line in p.stderr:
    #             stderr_buffer.write(line)
    #         try:
    #             p.wait(timeout=timeout)
    #         except subprocess.TimeoutExpired as e:
    #             p.kill()
    #             raise e
    #         ret_code = p.returncode
    #         return (
    #             ret_code,
    #             stdout_buffer.getvalue().strip(),
    #             stderr_buffer.getvalue().strip(),
    #             None,
    #         )
    # except BaseException as e:
    #     return (
    #         -1,
    #         stdout_buffer.getvalue().strip(),
    #         stderr_buffer.getvalue().strip(),
    #         e,
    #     )


def shlex_join(args):
    return " ".join(shlex.quote(arg) for arg in args)


def run_command(
    command,
    cwd=None,
    encoding="utf-8",
    timeout=None,
    print_command=True,
):
    """执行 shell 命令并返回结果"""
    if isinstance(command, (list, tuple)):
        command = shlex_join(command)

    ret_code, stdout, stderr, exception = bash_exec(
        command, cwd=cwd, encoding=encoding, timeout=timeout
    )

    if print_command:
        c_shell_command(
            command,
            stdout=stdout,
            stderr=stderr,
            return_code=ret_code,
            print_command=print_command,
        )
    return ret_code, stdout, stderr, exception
