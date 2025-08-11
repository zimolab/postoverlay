import shutil

from utils import run_command


def is_qemu_user_static_installed(qemu_bin="qemu-aarch64-static"):
    """检查是否已安装 QEMU 用户模式静态二进制文件"""
    return bool(shutil.which(qemu_bin))


def install_qemu_user_static(*args, **kwargs):
    """安装 QEMU 用户模式静态二进制文件"""
    # 尝试安装
    try:
        result = run_command(["lsb_release", "-is"], *args, **kwargs)
        distro_id = result.stdout.strip().lower()
    except Exception as e:
        raise e

    if distro_id in ["ubuntu", "debian"]:
        run_command(["apt-get", "update"], *args, **kwargs)
        run_command(["apt-get", "install", "-y", "qemu-user-static"], *args, **kwargs)
    elif distro_id in ["centos", "fedora", "redhat"]:
        run_command(["yum", "install", "-y", "qemu-user-static"], *args, **kwargs)
    elif distro_id in ["arch", "manjaro"]:
        run_command(
            ["pacman", "-Sy", "--noconfirm", "qemu-user-static"], *args, **kwargs
        )
    else:
        raise NotImplementedError(f"unsupported distro: {distro_id}")
