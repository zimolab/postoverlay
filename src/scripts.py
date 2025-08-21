import os
import shutil
import tempfile
from pathlib import Path

from utils import bash_exec, c_warning, c_info, c_shell_command


def chroot_mount(mount_point, *args, **kwargs):
    mount_point = Path(mount_point)
    rootfs = mount_point.as_posix()
    script = (
        f"mount -t proc /proc {rootfs}/proc\n"
        f"mount -t sysfs /sys {rootfs}/sys\n"
        f"mount -o bind /run {rootfs}/run\n"
        f"mount -o bind /dev {rootfs}/dev\n"
        f"mount -o bind /dev/pts {rootfs}/dev/pts\n"
    )
    c_info(f"chroot mounting")

    ret_code, stdout, stderr, exc = bash_exec(script, mode="string", *args, **kwargs)
    c_shell_command(
        command=script,
        stdout=stdout,
        stderr=stderr,
        return_code=ret_code,
        tile="Chroot Mount",
    )
    if exc:
        raise exc
    return ret_code, stdout, stderr, exc


def setup_qemu_for_chroot(mount_point, qemu_bin):
    """
    为 chroot 环境设置 QEMU 仿真
    """
    c_info(f"copying {qemu_bin} to $ROOTFS/usr/bin/")
    mount_point = Path(mount_point)
    host_qemu_path = shutil.which(qemu_bin)
    target_qemu_dir = mount_point / "usr/bin"
    target_qemu_dir.mkdir(parents=True, exist_ok=True)
    target_qemu_path = target_qemu_dir / qemu_bin

    # 复制 QEMU 静态二进制文件
    shutil.copy2(host_qemu_path, target_qemu_path)
    os.chmod(target_qemu_path, 0o777)


def cleanup_qemu_for_chroot(mount_point, qemu_bin):
    """
    清理 chroot 环境的 QEMU 仿真设置
    """
    mount_point = Path(mount_point)
    target_qemu_dir = mount_point / "usr/bin"
    target_qemu_path = target_qemu_dir / qemu_bin
    c_info(f"removing {qemu_bin} from $ROOTFS/usr/bin/")
    if target_qemu_path.exists():
        target_qemu_path.unlink()


def chroot_umount(mount_point, *args, **kwargs):
    mount_point = Path(mount_point)
    rootfs = mount_point.as_posix()
    script = (
        f"umount -l {rootfs}/proc\n"
        f"umount -l {rootfs}/sys\n"
        f"umount -l {rootfs}/dev/pts\n"
        f"umount -l {rootfs}/dev\n"
        f"umount -l {rootfs}/run\n"
    )
    c_info(f"chroot unmounting")
    ret_code, stdout, stderr, exc = bash_exec(script, mode="string", *args, **kwargs)
    c_shell_command(
        command=script,
        stdout=stdout,
        stderr=stderr,
        return_code=ret_code,
        tile="Chroot Umount",
    )
    if exc:
        raise exc
    return ret_code, stdout, stderr, exc


def chroot_exec(
    mount_point,
    script_path,
    encoding="utf-8",
    title="Script Execution",
    *args,
    **kwargs,
):
    mount_point = Path(mount_point)
    script_path = Path(script_path)
    script_content = script_path.read_text(encoding=encoding)

    rootfs = mount_point.as_posix()

    prepare_script = (
        f"#!/bin/bash\n"
        + f"chroot {rootfs} && echo 'chroot activated' || exit 1\n"
        + f"#------------{script_path.as_posix()} start------------#\n"
    )

    # 添加激活chroot的行
    script_content = (
        prepare_script
        + script_content.strip()
        + f"\n#------------{script_path.as_posix()} end-------------#\n"
    )
    tmp_path = None
    try:
        # 将脚本内容写入临时文件
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, encoding=encoding, suffix=".sh"
        ) as tmp:
            tmp.write(script_content)
            tmp_path = tmp.name
        # 设置执行权限
        os.chmod(tmp_path, 0o777)
        # 执行脚本
        ret_code, stdout, stderr, exc = bash_exec(
            tmp_path,
            mode="file",
            encoding=encoding,
            no_bash_exec=True,
            *args,
            **kwargs,
        )

        c_shell_command(
            command=script_content,
            stdout=stdout,
            stderr=stderr,
            return_code=ret_code,
            tile=title,
        )
        return ret_code, stdout, stderr, exc
    except BaseException as e:
        raise e
    finally:
        # 删除临时文件
        if tmp_path and Path(tmp_path).exists():
            os.unlink(tmp_path)


def execute_script(
    mount_point,
    script_path,
    encoding="utf-8",
    qemu_bin=None,
    title="Script Execution",
    *args,
    **kwargs,
):
    mount_point = Path(mount_point)
    script_path = Path(script_path)

    if not qemu_bin:
        script_content = script_path.read_text(encoding=encoding).strip()
        if not script_content:
            c_warning(f"script is empty, nothing to execute")
            return None

        c_info(f"executing script in host environment: {script_path}")
        ret_code, stdout, stderr, exc = bash_exec(
            script_path, mode="file", *args, **kwargs
        )
        c_shell_command(
            command=script_content,
            stdout=stdout,
            stderr=stderr,
            return_code=ret_code,
            tile=title,
        )
        return ret_code, stdout, stderr, exc

    try:
        c_info(f"setting up chroot environment")
        # os.chmod(mount_point, 0o777)
        setup_qemu_for_chroot(mount_point=mount_point, qemu_bin=qemu_bin)
        chroot_mount(mount_point=mount_point, *args, **kwargs)
        c_info(f"executing script in chroot environment")
        return chroot_exec(
            mount_point=mount_point,
            script_path=script_path,
            encoding=encoding,
            *args,
            **kwargs,
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
