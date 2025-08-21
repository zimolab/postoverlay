"""
usage: postoverlay overlay [-h] [-o OVERLAY] [-s PRE_SCRIPT] [-S POST_SCRIPT] [-q [QEMU_BIN]] [-r REMOVE [REMOVE ...]] [-R REMOVE_LIST] [--show-rootfs-tree] [--depth DEPTH]
                           rootfs

positional arguments:
  rootfs                path to the rootfs image file

options:
  -h, --help            show this help message and exit
  -o OVERLAY, --overlay OVERLAY
                        path to the overlay directory
  -s PRE_SCRIPT, --pre-script PRE_SCRIPT
                        path to script to execute before applying overlay
  -S POST_SCRIPT, --post-script POST_SCRIPT
                        path to script to execute after applying overlay
  -q [QEMU_BIN], --qemu-bin [QEMU_BIN]
                        when specified, the qemu binary will be copied to the bin/ directory of the mount point, and chroot environment will be set up for executing
                        pre/post scripts
  -r REMOVE [REMOVE ...], --remove REMOVE [REMOVE ...]
                        folders/files to remove in the rootfs before applying overlay(in a space-separated list)
  -R REMOVE_LIST, --remove-list REMOVE_LIST
                        path to file containing a list of folders/files to remove in the rootfs before applying overlay
  --show-rootfs-tree    show rootfs file tree when mounted
  --depth DEPTH         depth of file tree

"""

from helpers import (
    check_rootfs_file,
    check_overlay_dir,
    check_remove_list,
    check_pre_script_file,
    check_post_script_file,
    check_qemu_bin,
    cleanup_mount_point,
)
from mount import *
from overlay import *
from scripts import *
from utils import c_error, c_info, c_success, c_file_tree


def apply_remove(mount_point, remove_list):
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


def main(args):
    check_rootfs_file(args)
    check_overlay_dir(args)
    check_remove_list(args)
    check_qemu_bin(args)

    remove_list = []
    if args.remove_list:
        remove_list.extend(parse_remove_list(args.remove_list))
    if not args.remove:
        args.remove = []
    args.remove = [*args.remove, *remove_list]

    pre_script_path = (args.pre_script or "").strip()
    if not pre_script_path:
        c_warning(
            "pre-overlay script not specified, pre-overlay scripting will be skipped"
        )
    args.pre_script = pre_script_path
    check_pre_script_file(args)

    post_script_path = (args.post_script or "").strip()
    if not post_script_path:
        c_warning(
            "post-overlay script not specified, post-overlay scripting will be skipped"
        )
    args.post_script = post_script_path
    check_post_script_file(args)

    c_info("validating rootfs image file...")
    if not validate_rootfs_image(args.rootfs):
        c_error(f"{args.rootfs} is not a valid rootfs image file")
        c_info("process terminated")
        return 1
    else:
        c_success(f"{args.rootfs} validated")

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
        mount_rootfs_image(args.rootfs, mount_point)
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
        if args.remove:
            c_info("start to apply remove operations...")
            c_info(f"{len(args.remove)} file(s) about to be removed...")
            apply_remove(mount_point, args.remove)

        # 执行pre-overlay脚本
        if args.pre_script:
            c_info("start to execute pre-overlay script...")
            execute_script(
                mount_point=mount_point,
                script_path=args.pre_script,
                qemu_bin=args.qemu_bin,
            )

        # 执行overlay操作
        if args.overlay:
            c_info("start to apply overlay operations...")
            apply_overlay(mount_point, args.overlay)

        # 执行post-overlay脚本
        if args.post_script:
            c_info("start to execute post-overlay script...")
            execute_script(
                mount_point=mount_point,
                script_path=args.post_script,
                qemu_bin=args.qemu_bin,
            )
        return 0
    except Exception as e:
        raise e
    finally:
        cleanup_mount_point(mount_point, remove_dir=True)
