"""
usage: postoverlay mount [-h] [-m MOUNT_POINT] [-q [QEMU_BIN]] rootfs

positional arguments:
  rootfs                path to the rootfs image file

options:
  -h, --help            show this help message and exit
  -m MOUNT_POINT, --mount-point MOUNT_POINT
                        mount point
  -q [QEMU_BIN], --qemu-bin [QEMU_BIN]
                        when specified, the qemu binary will be copied to the bin/ directory of the mount point,
                        and chroot environment will be set up
"""

from pathlib import Path

from helpers import check_rootfs_file, check_mount_point, check_qemu_bin
from mount import validate_rootfs_image, mount_rootfs_image, is_rootfs_image_mounted
from scripts import setup_qemu_for_chroot, chroot_mount
from utils import c_info, c_error, c_success, c_shell_command


def mount_main(args):
    check_rootfs_file(args)
    check_mount_point(args)
    check_qemu_bin(args)
    c_info("validating rootfs image file...")
    if not validate_rootfs_image(args.rootfs):
        c_error(f"{args.rootfs} is not a valid rootfs image file")
        c_info("process terminated")
        return 1
    else:
        c_success(f"{args.rootfs} validated")
    try:
        c_info("start to mount rootfs image...")
        # 挂载镜像
        mount_point = Path(args.mount_point)
        mount_rootfs_image(args.rootfs, mount_point)
        if not is_rootfs_image_mounted(mount_point):
            c_info("failed to mount rootfs image")
            c_info("process terminated")
            return -1
    except Exception as e:
        raise e

    c_info(f"rootfs image mounted")
    rootfs_dir = mount_point.absolute().as_posix()
    c_info(f"$ROOTFS = {rootfs_dir}")

    c_info(f"now you can access the mounted rootfs image at `{rootfs_dir}`")
    qemu_bin = args.qemu_bin or ""
    c_info(
        "please use the following command to unmount the rootfs image when you don't need it anymore:"
    )

    if not qemu_bin:
        c_shell_command(f"sudo umount -l {rootfs_dir}")
        return 0

    try:
        c_info(f"setting up chroot environment")
        setup_qemu_for_chroot(mount_point=mount_point, qemu_bin=qemu_bin)
        chroot_mount(mount_point=mount_point)
        c_info(f"chroot environment prepared")
        c_info(f"you can now run chroot commands in `{rootfs_dir}`")
        c_info(f"for example: `chroot {rootfs_dir} /bin/bash`")
        c_info(
            "please use the following command to unmount the rootfs image when you don't need it anymore:"
        )
        chroot_umount_cmd = (
            f"sudo umount -l {rootfs_dir}/proc\n"
            f"sudo umount -l {rootfs_dir}/sys\n"
            f"sudo umount -l {rootfs_dir}/dev/pts\n"
            f"sudo umount -l {rootfs_dir}/dev\n"
            f"sudo umount -l {rootfs_dir}/run"
        )
        c_shell_command(
            "# remove qemu binary from $ROOTFS/usr/bin/\n"
            f"sudo rm -f {rootfs_dir}/user/bin/{qemu_bin}\n"
            f"# umount chroot environment \n"
            f"{chroot_umount_cmd}\n"
            f"# unmount rootfs image \n"
            f"sudo umount -l {rootfs_dir}\n"
        )
    except BaseException as e:
        c_error(f"failed to set up chroot environment: {e}")
        raise e
