## 简介

postoverlay是一个用于修改根文件系统（ext4）的脚本工具。

一般我们通过Buildroot的overlayfs机制来对根文件系统进行修改（覆盖），但是使用overlayfs存在一个构建的过程，
有时我们希望直接对现有的根文件系统镜像进行修改， 而不是每次都要重新进行构建。考虑到根文件镜像文件一般为ext4格式，
因此要完成这一任务存在一些比较简单的方法，大致的过程如下：

1. 将根文件系统镜像挂载到本地
2. 用本地文件覆盖根文件系统文件
3. 卸载根文件系统

这样就完成了根文件系统的更新。

`postoverlay`就是用于自动化上述过程工具。除此以外，`postoverlay`还提供了一些更加高级的功能，比如在执行overylay
前后在根文件系统环境下执行特定的脚本，这可以用于实现一些比较复杂的定制化操作。

由于根文件系统镜像可能与本地机器（Host）并非同一架构（主机环境为x86_64，而根文件系统镜像为arm64，这是常见的情况），
因此`postoverlay`允许用户在本机架构上模拟根文件系统架构运行环境，并在模拟环境中执行脚本。 这一功能的实现依赖于
`qemu-user-static`与`chroot`。


## 构建本项目

本项目提供了一个`build.py`脚本用于构建本项目，该脚本利用python自带的`zipapp`模块，将本项目代码和依赖项打包成可被
`python3`解释器执行的单一文件。可以通过运行以下命令构建本项目：

```bash
python3 ./build.py
```

如果构建成功，会在dist/目录下生成一个名为`postoverlay-<版本号>-pyz`的可执行文件和一个安装脚本`install.sh`
执行安装脚本会将该可执行文件安装到`/usr/local/bin`目录下，并将其命名为`postoverlay`，如果`/usr/local/bin`路径已经
在PATH环境变量中，那么用户可直接在命令行中输入`postoverlay`来使用该工具。

## 基本用法

<pre>usage: postoverlay [-h] [-o OVERLAY] [-s PRE_SCRIPT] [-S POST_SCRIPT]
                   [-q [QEMU_BIN]] [-r REMOVE [REMOVE ...]] [-R REMOVE_LIST]
                   [--show-rootfs-tree] [--depth DEPTH]
                   image

postoverlay - apply overlay to rootfs image

positional arguments:
  image                 path to the rootfs image file

optional arguments:
  -h, --help            show this help message and exit
  -o OVERLAY, --overlay OVERLAY
                        path to the overlay directory (default: None)
  -s PRE_SCRIPT, --pre-script PRE_SCRIPT
                        path to script to execute before applying overlay
                        (default: None)
  -S POST_SCRIPT, --post-script POST_SCRIPT
                        path to script to execute after applying overlay
                        (default: None)
  -q [QEMU_BIN], --qemu-bin [QEMU_BIN]
                        chroot environment to use, supports qemu-
                        aarch64-static for arm64, qemu-arm-static for armhf, when not
                        specified, chroot will not be used when executing
                        pre/post scripts. (default: None)
  -r REMOVE [REMOVE ...], --remove REMOVE [REMOVE ...]
                        folders/files to remove in the rootfs before applying
                        overlay(in a space-separated list) (default: None)
  -R REMOVE_LIST, --remove-list REMOVE_LIST
                        path to file containing a list of folders/files to
                        remove in the rootfs before applying overlay (default:
                        None)
  --show-rootfs-tree    show rootfs file tree when mounted (default: False)
  --depth DEPTH         depth of file tree (default: 1)
</pre>
