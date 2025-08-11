#! /usr/bin/python3

"""
postoverlay.py - 根文件系统镜像修改工具

- 将本地 overlay 目录内容应用到根文件系统镜像
- 支持文件/目录的添加、替换和删除
- 自动处理文件权限和所有权
- 支持在Overlay前后执行自定义脚本

使用示例：

```bash
sudo postoverlay rootfs.img -o my_overlays/
sudo postoverlay rootfs.img -o my_overlays/ -s pre_script.sh -S post_script.sh

```

作者：zimolab
更新：2025/8/8
协议：GPL 3.0

"""

import argparse
import sys
import tempfile

from mount import *
from overlay import *
from scripts import *
from pretty import print_separator
from qemu import is_qemu_user_static_installed
from utils import c_error, c_info, c_success, c_exception_info, c_file_tree


def parse_args():

    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(
        description="postoverlay - apply overlay to rootfs image",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("image", help="path to the rootfs image file")
    parser.add_argument("-o", "--overlay", help="path to the overlay directory")
    parser.add_argument(
        "-s", "--pre-script", help="path to script to execute before applying overlay"
    )
    parser.add_argument(
        "-S", "--post-script", help="path to script to execute after applying overlay"
    )
    parser.add_argument(
        "-q",
        "--qemu-bin",
        default=None,
        nargs="?",
        help="chroot environment to use, supports qemu-aarch64-static for arm64, armhf for armhf, "
        "when not specified, chroot will not be used when executing pre/post scripts.",
    )
    parser.add_argument(
        "-r",
        "--remove",
        nargs="+",
        help="folders/files to remove in the rootfs before applying overlay(in a space-separated list)",
    )
    parser.add_argument(
        "-R",
        "--remove-list",
        help="path to file containing a  list of folders/files to remove in the rootfs before applying overlay",
    )
    parser.add_argument(
        "--show-rootfs-tree",
        action="store_true",
        help="show rootfs file tree when mounted",
    )
    parser.add_argument(
        "--depth", action="store", type=int, default=1, help="depth of file tree"
    )
    return parser.parse_args()


def do_cleanup(mount_point):
    mount_point = Path(mount_point)
    try:
        if not mount_point.is_dir():
            return
        c_info("start to clean up...")

        if is_rootfs_image_mounted(mount_point):
            c_info(f"unmounting rootfs image ...")
            unmount_rootfs_image(mount_point)
        c_info(f"remove temporary mount point: {mount_point}")
        mount_point.rmdir()
        c_info(f"temporary mount point removed")
    except Exception as e:
        c_error(f"error cleaning up")
        c_exception_info(e)


def do_remove(mount_point, remove_list):
    if not remove_list:
        return
    for file_path in remove_list:
        if not file_path:
            continue

        display_path = f"$ROOTFS/{file_path.strip().lstrip('/')}"
        c_info(f"[remove_operation]removing {display_path}...[/remove_operation]")

        real_path = Path(mount_point) / file_path.strip().lstrip("/")
        if not real_path.exists():
            c_info(
                f"[remove_operation]{display_path} not found, skipped[/remove_operation]"
            )
            continue
        try:
            is_dir = real_path.is_dir()
            if is_dir:
                shutil.rmtree(real_path)
            else:
                real_path.unlink()
            c_info(
                f"[remove_operation]{'directory' if is_dir else 'file'}{display_path} removed[/remove_operation]"
            )
        except Exception as e:
            c_error(f"failed to remove {file_path}: {e}")


def do_pre_overlay_scripting(mount_point, script_path, qemu_bin):
    mount_point = Path(mount_point)
    script_path = Path(script_path)
    qemu_bin = (qemu_bin or "").strip()
    if not qemu_bin:
        execute_script(mount_point, script_path, qemu_bin=None)
        return

    # if not is_qemu_user_static_installed(qemu_bin):
    #     raise RuntimeError(f"qemu-user-static not installed for {qemu_bin}")
    # execute_script(mount_point, script_path, qemu_bin=qemu_bin)


def do_post_overlay_scripting(mount_point, script_path, qemu_bin):
    pass


def do_overlay(mount_point, overlay_dir):
    apply_overlay(mount_point, overlay_dir)


def main():
    args = parse_args()

    if not args.image or (not Path(args.image).is_file()):
        c_error(f"rootfs image not found: {args.image}")
        c_info("process terminated")
        return 1

    c_info("validating rootfs image file...")
    if not validate_rootfs_image(args.image):
        c_error(f"{args.image} is not a valid rootfs image file")
        c_info("process terminated")
        return 1
    else:
        c_success(f"{args.image} validated")

    # 创建临时挂载点
    c_info("create temporary mount point...")
    mount_point = tempfile.mkdtemp(prefix="postoverlay_")
    mount_point = Path(mount_point)
    if not mount_point.exists():
        c_error(f"failed to create mount point: {mount_point}")
        c_info("process terminated")
        return 1
    c_info(f"mount point created at: {mount_point}, rootfs image will be mounted here")

    try:
        c_info("start to mount rootfs image...")
        # 挂载镜像
        mount_rootfs_image(args.image, mount_point)
        if not is_rootfs_image_mounted(mount_point):
            c_info("failed to mount rootfs image")
            c_info("process terminated")
            return -1
    except Exception as e:
        raise e

    c_info(f"rootfs image mounted")
    c_info(f"$ROOTFS = {mount_point.as_posix()}")

    # 显示挂载点文件树
    if args.show_rootfs_tree:
        depth = args.depth
        if not depth or depth < 1:
            depth = 1
        c_file_tree(mount_point, depth=depth, title="rootfs/")

    try:
        # 执行remove操作
        remove_list = []
        if args.remove_list:
            remove_list_file = Path(args.remove_list)
            if not remove_list_file.is_file():
                c_error(f"remove list file not found: {args.remove_list}")
                raise FileNotFoundError(f"file not found: {args.remove_list}")
            remove_list.extend(parse_remove_list(remove_list_file))
        if not args.remove:
            args.remove = []
        args.remove = [*args.remove, *remove_list]
        if args.remove:
            c_info("start remove operations...")
            c_info(f"{len(args.remove)} file(s) about to be removed...")
            do_remove(mount_point, args.remove)

        # 执行pre-overlay脚本
        pre_script_path = args.pre_script or ""
        if pre_script_path and pre_script_path.strip() == "":
            c_warning("pre-overlay script not specified, skip pre-overlay scripting")
        pre_script_path = pre_script_path.strip()
        if pre_script_path:
            pre_script_path = Path(pre_script_path)
            if not pre_script_path.is_file():
                c_error(f"pre-overlay script file not found: {args.pre_script}")
                raise FileNotFoundError(f"file not found: {args.pre_script}")
            c_info("start to execute pre-overlay script...")
            do_pre_overlay_scripting(mount_point, pre_script_path, args.qemu_bin)

        # 执行overlay操作
        overlay_dir = args.overlay or ""
        if overlay_dir and overlay_dir.strip() == "":
            c_warning("overlay directory not specified, skip overlay operation")
        overlay_dir = overlay_dir.strip()
        if overlay_dir:
            overlay_dir = Path(overlay_dir)
            if not overlay_dir.is_dir():
                c_error(f"overlay directory not found: {args.overlay}")
                raise FileNotFoundError(f"directory not found: {args.overlay}")
            c_info("start to apply overlay operation...")
            do_overlay(mount_point, overlay_dir)

        # 执行post-overlay脚本
        post_script_path = args.post_script or ""
        if post_script_path and post_script_path.strip() == "":
            c_warning("post-overlay script not specified, skip post-overlay scripting")
        post_script_path = post_script_path.strip()
        if args.post_script:
            post_script_path = Path(post_script_path)
            if not post_script_path.is_file():
                c_error(f"post-overlay script file not found: {args.post_script}")
                raise FileNotFoundError(f"file not found: {args.post_script}")
            c_info("start to execute post-overlay script...")
            do_post_overlay_scripting(mount_point, post_script_path, args.qemu_bin)

        return 0

    except Exception as e:
        raise e
    finally:
        do_cleanup(mount_point)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        c_info("process terminated by user", print_message=True)
        sys.exit(1)
    except Exception as exc:
        print_separator("Exception occurred")
        c_exception_info(exc, print_exception=True)
        sys.exit(1)
