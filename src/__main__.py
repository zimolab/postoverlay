#! /usr/bin/python3

"""
postoverlay.py - 根文件系统镜像修改工具

- 将本地 overlay 目录内容应用到根文件系统镜像
- 支持文件/目录的添加、替换和删除
- 自动处理文件权限和所有权
- 支持在Overlay前后执行自定义脚本

使用示例：

`overlay`命令

```bash
sudo postoverlay rootfs.img overlay -o my_overlays/
sudo postoverlay rootfs.img overlay -o my_overlays/ -s pre_script.sh -S post_script.sh
sudo postoverlay rootfs.img overlay -o my_overlays/ -q aarch64-static -s pre_script.sh -S post_script.sh
```

`mount`命令

```bash
sudo postoverlay mount rootfs.img -m /mnt/rootfs
sudo postoverlay mount rootfs.img -m /mnt/rootfs -q aarch64-static
```

作者：zimolab
更新：2025/8/8
协议：GPL 3.0

"""

import argparse
import sys

import __mount_command__
import __overlay_command__
from pretty import print_separator
from helpers import InvalidArgumentError
from utils import c_error, c_info, c_exception_info


def create_parser():

    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(
        description="postoverlay - apply overlay to rootfs image",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="sub-command")

    # 子命令：overlay
    overlay_command_parser = subparsers.add_parser(
        "overlay", help="apply overlay to rootfs image"
    )
    overlay_command_parser.add_argument("rootfs", help="path to the rootfs image file")
    overlay_command_parser.add_argument(
        "-o", "--overlay", help="path to the overlay directory"
    )
    overlay_command_parser.add_argument(
        "-s", "--pre-script", help="path to script to execute before applying overlay"
    )
    overlay_command_parser.add_argument(
        "-S", "--post-script", help="path to script to execute after applying overlay"
    )
    overlay_command_parser.add_argument(
        "-q",
        "--qemu-bin",
        default=None,
        nargs="?",
        help="when specified, the qemu binary will be copied to the bin/ directory of the mount point, "
        "and chroot environment will be set up for executing pre/post scripts",
    )
    overlay_command_parser.add_argument(
        "-r",
        "--remove",
        nargs="+",
        help="folders/files to remove in the rootfs before applying overlay(in a space-separated list)",
    )
    overlay_command_parser.add_argument(
        "-R",
        "--remove-list",
        help="path to file containing a  list of folders/files to remove in the rootfs before applying overlay",
    )
    overlay_command_parser.add_argument(
        "--show-rootfs-tree",
        action="store_true",
        help="show rootfs file tree when mounted",
    )
    overlay_command_parser.add_argument(
        "--depth", action="store", type=int, default=1, help="depth of file tree"
    )

    # 子命令：mount
    mount_command_parser = subparsers.add_parser(
        "mount", help="mount rootfs image file to  specified directory"
    )
    mount_command_parser.add_argument("rootfs", help="path to the rootfs image file")
    mount_command_parser.add_argument(
        "-m", "--mount-point", default=None, type=str, help="mount point"
    )
    mount_command_parser.add_argument(
        "-q",
        "--qemu-bin",
        default=None,
        nargs="?",
        help="when specified, the qemu binary will be copied to the bin/ directory of the mount point, "
        "and chroot environment will be set up",
    )

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    command = args.command or ""
    if command == "overlay":
        return __overlay_command__.main(args)
    elif command == "mount":
        return __mount_command__.mount_main(args)
    else:
        if command:
            c_error(f"unknown command: {command}")
        parser.print_help()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        c_info("process terminated by user", print_message=True)
        sys.exit(1)
    except InvalidArgumentError:
        pass
    except Exception as exc:
        print_separator("Exception Occurred")
        c_exception_info(exc, print_exception=True)
        sys.exit(1)
