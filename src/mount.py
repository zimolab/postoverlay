import uuid
from pathlib import Path

from utils import run_command, c_warning, c_error, c_info

_probe_filename = f".__postoverlay__probe__{uuid.uuid4().hex}__"


def validate_rootfs_image(image_path):
    """验证是否为有效的根文件系统镜像文件"""
    image_path = Path(image_path)
    # 检查文件类型
    try:
        ext4_symbol = "ext4 filesystem"
        ext2_symbol = "ext2 filesystem"
        _, output, _, exception = run_command(
            ["file", "-b", image_path.absolute().as_posix()]
        )

        if exception is not None:
            raise exception

        if ext4_symbol in output or ext2_symbol in output:
            return True
        return False
    except Exception as e:
        raise e


def create_mount_probe_file(mount_point):
    """创建挂载探针文件"""
    mount_point = Path(mount_point)
    probe_file = mount_point / _probe_filename
    c_info("creating mount probe file...")
    if probe_file.exists():
        c_info("mount probe file already exists")
        return

    try:
        with open(probe_file, "w") as f:
            f.write("")
        c_info("mount probe file created")
    except Exception as e:
        c_error(f"failed to create mount probe file: {str(e)}")
        raise e


def remove_mount_probe_file(mount_point):
    """删除挂载探针文件"""
    mount_point = Path(mount_point)
    probe_file = mount_point / _probe_filename
    if probe_file.is_file():
        try:
            c_info("removing mount probe file...")
            probe_file.unlink()
        except Exception as e:
            c_warning(f"failed to remove mount probe file: {str(e)}")


def mount_probe_file_exists(mount_point):
    """检查挂载点是否存在挂载探针文件"""
    mount_point = Path(mount_point)
    probe_file = mount_point / _probe_filename
    return probe_file.exists()


def is_rootfs_image_mounted(mount_point):
    """检查挂载点是否已挂载"""
    mount_point = Path(mount_point)
    if not mount_point.is_dir():
        return False

    probe_file = mount_point / _probe_filename
    return not probe_file.exists()


def mount_rootfs_image(image_path, mount_point):
    """挂载根文件系统镜像到指定目录"""
    mount_point = Path(mount_point)
    image_path = Path(image_path)
    if not mount_point.is_dir():
        mount_point.mkdir(parents=True, exist_ok=True)
    create_mount_probe_file(mount_point)
    c_info("executing mount command...")
    _, _, _, exception = run_command(
        ["sudo", "mount", "-o", "loop", image_path.as_posix(), mount_point.as_posix()]
    )
    _, _, _, exception = run_command(["sudo", "chmod", "777", mount_point.as_posix()])
    if exception is not None:
        raise exception


def unmount_rootfs_image(mount_point):
    """卸载根文件系统镜像"""
    mount_point = Path(mount_point)
    if not mount_point.is_dir():
        c_warning(f"mount point does not exist: {mount_point.absolute().as_posix()}")
        return

    _, _, _, exception = run_command(
        ["sudo", "umount", "-l", mount_point.absolute().as_posix()]
    )
    remove_mount_probe_file(mount_point)

    if exception is not None:
        raise exception
