#!/usr/bin/env python3
"""
postoverlay 项目打包脚本


使用:
python3 build.py                  # 正常构建
python3 build.py --venv ./        # 在当前目录创建虚拟环境
python3 build.py --venv /opt/envs # 在指定目录创建虚拟环境
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# 项目配置
PROJECT_NAME = "postoverlay"
VERSION = "1.0.0"
AUTHOR = "Your Name"
SRC_ROOT = "src"
REQUIREMENTS = "requirements.txt"
RESOURCE_DIR = "resources"
BUILD_DIR = "dist"
OUTPUT_FILE = f"{PROJECT_NAME}-{VERSION}.pyz"
VENV_DIR_NAME = ".venv"  # 虚拟环境目录名称
PYPI_MIRROR = "https://mirrors.aliyun.com/pypi/simple/"


def create_virtual_environment(target_dir):
    """
    在指定目录创建虚拟环境

    参数:
        target_dir: 目标目录 (虚拟环境将创建在此目录下的 .venv 子目录)

    返回:
        venv_path: 创建的虚拟环境路径
    """
    # 解析目标路径
    target_path = Path(target_dir).resolve()
    venv_path = target_path / VENV_DIR_NAME

    # 检查虚拟环境是否已存在
    if venv_path.exists():
        print(f"错误: 虚拟环境已存在于 {venv_path}")
        print("请删除现有虚拟环境或选择其他位置")
        sys.exit(1)

    # 创建虚拟环境
    print(f"在 {venv_path} 创建虚拟环境...")
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)

    # 获取激活脚本路径
    if sys.platform == "win32":
        activate_script = venv_path / "Scripts" / "activate.bat"
    else:
        activate_script = venv_path / "bin" / "activate"

    print(f"虚拟环境创建成功: {venv_path}")
    print("\n使用以下命令激活虚拟环境:")
    if sys.platform == "win32":
        print(f"  {activate_script}")
    else:
        print(f"  source {activate_script}")

    requirements_path = Path(REQUIREMENTS)
    if not requirements_path.is_file():
        print("依赖文件不存在，无需安装依赖")
        return venv_path

    # 安装依赖
    print("\n安装项目依赖...")
    pip_cmd = (
        [str(venv_path / "bin" / "pip")]
        if sys.platform != "win32"
        else [str(venv_path / "Scripts" / "pip.exe")]
    )
    install_cmd = [*pip_cmd, "install", "-r", REQUIREMENTS]

    mirror_url = PYPI_MIRROR.strip()
    if mirror_url:
        install_cmd = [*install_cmd, "-i", mirror_url]

    subprocess.run(install_cmd, check=True)

    print("依赖安装完成")
    return venv_path


def clean_build():
    """清理构建目录"""
    build_path = Path(BUILD_DIR)
    if build_path.exists():
        print(f"清理构建目录: {BUILD_DIR}")
        shutil.rmtree(build_path)
    build_path.mkdir(parents=True, exist_ok=True)


def copy_source(build_dir, skip_dirs=None):
    """
    复制源代码到构建目录，跳过指定目录

    参数:
        build_dir: 构建目录路径
        skip_dirs: 要跳过的目录列表
    """
    skip_dirs = skip_dirs or []
    src_dir = Path(SRC_ROOT)
    print(f"复制源代码: {src_dir} -> {build_dir}")
    print(f"跳过目录: {skip_dirs}")

    # 复制所有文件，跳过指定目录
    for py_file in src_dir.glob("**/*"):
        # 检查是否在跳过目录中
        if any(skip_dir in py_file.parts for skip_dir in skip_dirs):
            continue

        if py_file.is_file():
            rel_path = py_file.relative_to(src_dir)
            dest_path = build_dir / rel_path

            # 确保目标目录存在
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(py_file, dest_path)
            print(f"  - {rel_path}")


def copy_resources(build_dir):
    """复制资源文件到构建目录"""
    if not Path(RESOURCE_DIR).exists():
        print(f"资源目录不存在: {RESOURCE_DIR}, 跳过")
        return

    print(f"复制资源文件: {RESOURCE_DIR} -> {build_dir}")

    # 复制整个资源目录
    for item in Path(RESOURCE_DIR).glob("**/*"):
        if item.is_dir():
            continue

        rel_path = item.relative_to(RESOURCE_DIR)
        dest_path = build_dir / "resources" / rel_path

        # 确保目标目录存在
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, dest_path)
        print(f"  - resources/{rel_path}")


def install_dependencies(build_dir):
    """安装依赖到构建目录"""
    if not Path(REQUIREMENTS).exists():
        print(f"依赖文件不存在: {REQUIREMENTS}, 跳过")
        return

    print("安装Python依赖...")

    # 创建临时虚拟环境
    with tempfile.TemporaryDirectory() as venv_dir:
        # 创建虚拟环境
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        # 获取pip路径
        pip_path = Path(venv_dir) / "bin" / "pip"
        if not pip_path.exists():
            pip_path = Path(venv_dir) / "Scripts" / "pip.exe"

        mirror_url = PYPI_MIRROR.strip()

        # 修复wheel未安装的bug
        wheel_install_cmd = [str(pip_path), "install", "wheel"]
        if mirror_url:
            wheel_install_cmd = [*wheel_install_cmd, "-i", mirror_url]
        subprocess.run(wheel_install_cmd, check=False)

        install_cmd = [
            str(pip_path),
            "install",
            "-r",
            REQUIREMENTS,
            "--target",
            str(build_dir),
        ]

        if mirror_url:
            install_cmd = [*install_cmd, "-i", mirror_url]

        # 安装依赖到构建目录
        subprocess.run(install_cmd, check=True)

        print("依赖安装完成")


def create_zipapp(build_dir, output_file):
    """创建可执行的 .pyz 文件"""
    print(f"创建可执行文件: {output_file}")

    # 安装依赖
    install_dependencies(build_dir)

    # 确保输出目录存在
    output_path = Path(BUILD_DIR) / output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # # 创建zipapp文件
    import zipapp

    zipapp.create_archive(
        build_dir,
        output_path,
        interpreter="/usr/bin/env python3",
    )
    # 设置可执行权限
    output_path.chmod(0o755)
    print(f"创建成功: {output_path}")

    return output_path


def generate_install_script(zipapp_path):
    """生成安装脚本"""
    script_content = f"""#!/bin/bash
# postoverlay 安装脚本
# 版本: {VERSION}

INSTALL_DIR="/usr/local/bin"
ZIPAPP_PATH="{Path(zipapp_path).absolute()}"

# 检查root权限
if [ "$(id -u)" -ne 0 ]; then
    echo "请使用sudo运行此脚本"
    exit 1
fi

# 创建安装目录
mkdir -p "$INSTALL_DIR"

# 复制文件
echo "安装 {PROJECT_NAME} 到 $INSTALL_DIR"
cp "$ZIPAPP_PATH" "$INSTALL_DIR/{PROJECT_NAME}"

# 设置权限
chmod 755 "$INSTALL_DIR/{PROJECT_NAME}"

echo "安装完成!"
echo "运行命令: {PROJECT_NAME} --help"
"""

    script_path = Path(BUILD_DIR) / "install.sh"
    with open(script_path, "w") as f:
        f.write(script_content)

    # 设置可执行权限
    script_path.chmod(0o755)
    print(f"安装脚本已生成: {script_path}")


def build():
    """执行完整构建流程"""
    print(f"开始构建 {PROJECT_NAME} v{VERSION}")

    # 清理构建目录
    clean_build()

    # 创建临时构建目录
    with tempfile.TemporaryDirectory() as temp_build_dir:
        build_path = Path(temp_build_dir)

        # 复制源代码，跳过虚拟环境目录
        copy_source(build_path, skip_dirs=[VENV_DIR_NAME])

        # 复制资源文件
        copy_resources(build_path)

        # 创建zipapp
        zipapp_path = create_zipapp(build_path, OUTPUT_FILE)

        # 生成安装脚本
        generate_install_script(zipapp_path)

    print("构建完成!")


def main():
    global SRC_ROOT
    global OUTPUT_FILE
    parser = argparse.ArgumentParser(description=f"{PROJECT_NAME} 项目打包工具")
    parser.add_argument("--clean", action="store_true", help="仅清理构建目录")
    parser.add_argument(
        "--src",
        nargs="?",
        const=SRC_ROOT,
        default=None,
        help=f"指定源代码目录（默认：{Path(SRC_ROOT).as_posix()}）",
    )
    parser.add_argument(
        "--venv",
        nargs="?",
        const=".",
        default=None,
        help="指定目录创建虚拟环境 (默认: 当前目录)",
    )
    parser.add_argument(
        "-o",
        "--output",
        nargs="?",
        const=OUTPUT_FILE,
        default=None,
        help=f"指定输出文件名（默认：{OUTPUT_FILE}）",
    )

    args = parser.parse_args()

    # 处理 --venv 选项
    if args.venv is not None:
        create_virtual_environment(args.venv)
        sys.exit(0)

    if args.src:
        if not Path(args.src).is_dir():
            print(f"错误：源代码目录不存在！")
            sys.exit(1)
        SRC_ROOT = args.src

    if args.output and args.output.strip():
        OUTPUT_FILE = args.output

    # 处理 --clean 选项
    if args.clean:
        clean_build()
        print("清理完成")
    else:
        build()


if __name__ == "__main__":
    main()
