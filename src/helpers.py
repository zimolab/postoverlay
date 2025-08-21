from pathlib import Path

from qemu import is_qemu_user_static_installed
from mount import is_rootfs_image_mounted, unmount_rootfs_image
from utils import c_error, c_info, c_warning, c_exception_info


class InvalidArgumentError(ValueError):
    pass


def check_rootfs_file(args):
    if not args.rootfs or (not Path(args.rootfs).is_file()):
        c_error(f"rootfs image not found: {args.rootfs}")
        c_info("process terminated")
        raise InvalidArgumentError("rootfs image not found")


def check_overlay_dir(args):
    overlay_dir = args.overlay or ""
    if overlay_dir and overlay_dir.strip() == "":
        c_warning("overlay directory not specified, overlay operation will be skipped")
        return
    args.overlay = overlay_dir.strip()
    if args.overlay:
        args.overlay = Path(args.overlay)
        if not args.overlay.is_dir():
            c_error(f"overlay directory not found: {args.overlay}")
            c_info("process terminated")
            raise InvalidArgumentError("overlay directory not found")


def check_remove_list(args):
    args.remove_list = (args.remove_list or "").strip()
    if args.remove_list:
        remove_list_file = Path(args.remove_list)
        if not remove_list_file.is_file():
            c_error(f"remove list file not found: {args.remove_list}")
            c_info("process terminated")
            raise InvalidArgumentError("remove list file not found")


def check_pre_script_file(args):
    if args.pre_script:
        args.pre_script = Path(args.pre_script)
        if not args.pre_script.is_file():
            c_error(f"pre-overlay script file not found: {args.pre_script}")
            c_info("process terminated")
            raise InvalidArgumentError("pre-overlay script file not found")


def check_post_script_file(args):
    if args.post_script:
        args.post_script = Path(args.post_script)
        if not args.post_script.is_file():
            c_error(f"post-overlay script file not found: {args.post_script}")
            c_info("process terminated")
            raise InvalidArgumentError("post-overlay script file not found")


def check_qemu_bin(args):
    args.qemu_bin = (args.qemu_bin or "").strip()
    if args.qemu_bin:
        c_info(f"QEMU user static binary specified: {args.qemu_bin}")
        if not is_qemu_user_static_installed(args.qemu_bin):
            c_error(f"qemu-user-static binary not found: {args.qemu_bin}")
            c_error("Please check your qemu-user-static installation.")
            c_info("process terminated")
            raise InvalidArgumentError("qemu-user-static not installed")


def check_mount_point(args):
    args.mount_point = (args.mount_point or "").strip()
    if not args.mount_point:
        c_error("mount point not specified")
        c_info("process terminated")
        raise InvalidArgumentError("mount point not specified")
    args.mount_point = Path(args.mount_point)
    if not args.mount_point.is_dir():
        c_error(f"mount point not found: {args.mount_point}")
        c_info("process terminated")
        raise InvalidArgumentError("mount point not found")


def cleanup_mount_point(mount_point, remove_dir=False):
    mount_point = Path(mount_point)
    try:
        if not mount_point.is_dir():
            return
        c_info("start to clean up...")

        if is_rootfs_image_mounted(mount_point):
            c_info(f"unmounting rootfs image ...")
            unmount_rootfs_image(mount_point)
        if remove_dir:
            c_info(f"removing mount point directory: {mount_point}")
            mount_point.rmdir()
            c_info(f"t{mount_point} removed")
    except Exception as e:
        c_error(f"an error occurred while cleaning up the mount point: {e}")
        c_exception_info(e)
