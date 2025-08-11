import os
import shutil
from pathlib import Path

from utils import bash_exec, c_warning, c_info, c_shell_command


def chroot_mount(mount_point, *args, **kwargs):
    mount_point = Path(mount_point)
    rootfs = mount_point.as_posix()
    script = (
        f"mount -t proc /proc {rootfs}/proc\n"
        f"mount -t sysfs /sys {rootfs}/sys\n"
        f"mount -o bind /dev {rootfs}/dev\n"
        f"mount -o bind /dev/pts {rootfs}/dev/pts\n"
    )
    return bash_exec(script, *args, **kwargs)


def setup_qemu_for_chroot(mount_point, qemu_bin="qemu-aarch64-static"):
    """
    为 chroot 环境设置 QEMU 仿真
    """
    c_info(f"copying {qemu_bin} to chroot environment...")
    mount_point = Path(mount_point)
    host_qemu_path = shutil.which(qemu_bin)
    target_qemu_dir = mount_point / "usr/bin"
    target_qemu_dir.mkdir(parents=True, exist_ok=True)
    target_qemu_path = target_qemu_dir / qemu_bin

    # 复制 QEMU 静态二进制文件
    shutil.copy2(host_qemu_path, target_qemu_path)
    os.chmod(target_qemu_path, 0o755)


def cleanup_qemu_for_chroot(mount_point, qemu_bin="qemu-aarch64-static"):
    """
    清理 chroot 环境的 QEMU 仿真设置
    """
    mount_point = Path(mount_point)
    target_qemu_dir = mount_point / "usr/bin"
    target_qemu_path = target_qemu_dir / qemu_bin
    c_info(f"removing {target_qemu_path} from chroot environment...")
    if target_qemu_path.exists():
        target_qemu_path.unlink()


def chroot_umount(mount_point, *args, **kwargs):
    mount_point = Path(mount_point)
    rootfs = mount_point.as_posix()
    script = (
        f"umount {rootfs}/proc\n"
        f"umount {rootfs}/sys\n"
        f"umount {rootfs}/dev\n"
        f"umount {rootfs}/dev/pts\n"
    )
    return bash_exec(script, *args, **kwargs)


def chroot_exec(mount_point, script, *args, **kwargs):
    mount_point = Path(mount_point)
    script = f"chroot {mount_point.as_posix()} /bin/bash\n" f"cd /\n" f"{script}\n"
    return bash_exec(script, *args, **kwargs)


def execute_script(
    mount_point,
    script_path,
    encoding="utf-8",
    qemu_bin=None,
    *args,
    **kwargs,
):
    mount_point = Path(mount_point)
    script_path = Path(script_path)
    script_content = script_path.read_text(encoding=encoding).strip()
    if not script_content:
        c_warning(f"script is empty, nothing to execute")
        return None

    if not qemu_bin:
        c_info(f"executing script in host environment: {script_path}")
        ret_code, stdout, stderr, exc = bash_exec(
            script_path, mode="file", *args, **kwargs
        )
        c_shell_command(
            command=script_content,
            stdout=stdout,
            stderr=stderr,
            return_code=ret_code,
            tile="Pre-Overlay Script Execution",
        )
        return ret_code, stdout, stderr, exc

    try:
        c_info(f"preparing chroot environment: {mount_point}")
        chroot_mount(mount_point=mount_point, *args, **kwargs)
        setup_qemu_for_chroot(mount_point=mount_point, qemu_bin=qemu_bin)
        c_info(f"executing script in chroot: {script_path}")
        return chroot_exec(
            mount_point=mount_point, script=script_content, *args, **kwargs
        )
    except BaseException as e:
        raise e
    finally:
        try:
            cleanup_qemu_for_chroot(mount_point=mount_point, qemu_bin=qemu_bin)
        except BaseException as e:
            c_warning(f"failed to cleanup qemu for chroot: {e}")

        try:
            chroot_umount(mount_point=mount_point, *args, **kwargs)
        except BaseException as e:
            c_warning(f"failed to umount chroot: {e}")
