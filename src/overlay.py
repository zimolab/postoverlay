import os
import shutil
from pathlib import Path

from utils import c_info, c_error


def do_overlay_copy(
    mount_point, overlay_dir, src_path, preserve_perm=True, preserve_owner=False
):

    src_path = Path(src_path)
    overlay_dir = Path(overlay_dir)
    dest_in_rootfs = Path(src_path).relative_to(overlay_dir).as_posix().lstrip("/")
    display_path = f"$ROOTFS/{dest_in_rootfs}"

    c_info(
        f"[overlay_operation]copying: {src_path.as_posix()} -> {display_path}[/overlay_operation]"
    )

    real_dest = mount_point / dest_in_rootfs

    if not real_dest.parent.is_dir():
        parent_dir = real_dest.parent
        c_info(
            f"[overlay_operation]mkdir: $ROOTFS/{parent_dir.relative_to(mount_point).as_posix().lstrip('/')}[/overlay_operation]"
        )
        parent_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(src_path, real_dest)
    c_info(
        f"[overlay_operation]copied: {src_path.as_posix()} -> {display_path}[/overlay_operation]"
    )

    if not preserve_perm and not preserve_owner:
        return True

    src_stat = os.stat(src_path)
    if preserve_perm:
        os.chmod(real_dest, src_stat.st_mode)
        c_info(
            f"[overlay_operation]restore permission: {display_path } -> {oct(src_stat.st_mode)}[/overlay_operation]"
        )

    if preserve_owner:
        os.chown(real_dest, src_stat.st_uid, src_stat.st_gid)
        c_info(
            f"[overlay_operation]restore owner: {display_path } -> {src_stat.st_uid}:{src_stat.st_gid}[/overlay_operation]"
        )
    return True


def apply_overlay(
    mount_point,
    overlay_dir,
    preserve_perm=True,
    preserve_owner=False,
    print_message=True,
):
    overlay_dir = Path(overlay_dir)
    for src_root, dirs, files in os.walk(overlay_dir):
        # 复制文件
        for file in files:
            src_path = Path(src_root) / file
            try:
                do_overlay_copy(
                    mount_point=mount_point,
                    overlay_dir=overlay_dir,
                    src_path=src_path,
                    preserve_perm=preserve_perm,
                    preserve_owner=preserve_owner,
                )
            except Exception as e:
                c_error(f"failed to copy: {src_path.as_posix()}: {e}", print_message)


def parse_remove_list(file_path):
    """从文件解析要删除的项目列表"""
    file_path = Path(file_path)
    if not file_path.is_file():
        return []
    with open(file_path, "r") as f:
        lines = f.readlines()
    # 去除空行和注释行
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]
